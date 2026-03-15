import os, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ultimate_movie_cloner_v12_no_missing"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['pro_movie_v12']
sites_col = db['sites']
movies_col = db['movies']
bot_states = db['bot_states']

# --- System Initialization ---
def init_system():
    if sites_col.count_documents({"slug": "main"}) == 0:
        sites_col.insert_one({
            "slug": "main",
            "site_name": "Movie Hub",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome! Configure your site in Admin Panel.",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "English", "Bangla"],
            "tmdb_key": "",
            "bot_token": "",
            "channel_id": "",
            "channel_username": ""
        })
init_system()

# --- Professional Master UI (Integrated Single Variable) ---
def render_full_page(site, content_body, movies=None, sliders=None, m=None):
    # স্লাইডার এবং মুভি লিস্টের লজিক
    site_categories = site.get('categories', [])
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{site['site_name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body {{ background: #080a10; color: #e2e8f0; font-family: 'Inter', sans-serif; }}
            .glass {{ background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: all 0.3s ease; }}
            .card:hover {{ transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 10px 30px -10px rgba(59, 130, 246, 0.5); }}
            .swiper-slide img {{ height: 450px; width: 100%; object-fit: cover; border-radius: 24px; filter: brightness(0.5); }}
            .btn-blue {{ background: #2563eb; transition: 0.3s; }}
            .btn-blue:hover {{ background: #1d4ed8; transform: scale(1.05); }}
        </style>
    </head>
    <body>
        <div class="bg-blue-600 text-white text-center py-2 text-[10px] md:text-sm font-bold tracking-wide uppercase px-4">
            {site['header_notice']}
        </div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter">➕ CLONE SITE</a>
                    <a href="/s/{site['slug']}" class="flex items-center gap-2">
                        <img src="{site['logo_url']}" class="h-8 md:h-10">
                        <span class="text-xl md:text-2xl font-black tracking-tighter text-white">{site['site_name']}</span>
                    </a>
                </div>
                <div class="flex items-center gap-6">
                    <div class="hidden lg:flex gap-6 text-[11px] font-bold uppercase tracking-widest">
                        {" ".join([f'<a href="/s/{site["slug"]}?cat={c.strip()}" class="hover:text-blue-500 transition">{c.strip()}</a>' for c in site_categories])}
                    </div>
                    <a href="/s/{site['slug']}/admin" class="bg-slate-800 hover:bg-slate-700 px-4 py-1.5 rounded-full text-[10px] font-bold border border-white/10">ADMIN</a>
                </div>
            </div>
        </nav>

        <div class="container mx-auto px-4 py-8">
            {content_body}
        </div>

        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>
            const swiper = new Swiper('.swiper', {{ autoplay: {{ delay: 4000 }}, loop: true, pagination: {{ el: '.swiper-pagination', clickable: true }} }});
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template, site=site, movies=movies, sliders=sliders, m=m)

# --- Routes ---

@app.route('/')
def index_root():
    return redirect('/s/main')

@app.route('/s/<slug>')
def home(slug):
    site = sites_col.find_one({"slug": slug})
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    sliders = movies[:5]
    
    slider_html = ""
    if sliders:
        slider_html = '<div class="swiper mb-12 overflow-hidden relative rounded-3xl shadow-2xl"><div class="swiper-wrapper">'
        for s in sliders:
            slider_html += f"""
            <div class="swiper-slide relative">
                <img src="{s['banner']}">
                <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                <div class="absolute bottom-10 left-6 md:left-12">
                    <h2 class="text-3xl md:text-6xl font-black text-white uppercase tracking-tighter mb-4">{s['title']}</h2>
                    <a href="/s/{site['slug']}/movie/{s['_id']}" class="btn-blue px-8 py-3 rounded-full font-bold text-sm inline-block shadow-lg">VIEW DETAILS</a>
                </div>
            </div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'

    movie_grid = f'<h2 class="text-2xl font-black mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest text-blue-500">{cat if cat else "Recently Uploaded"}</h2>'
    movie_grid += '<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">'
    for m in movies:
        movie_grid += f"""
        <a href="/s/{site['slug']}/movie/{m['_id']}" class="card rounded-2xl overflow-hidden group">
            <div class="relative overflow-hidden">
                <img src="{m['poster']}" class="h-60 md:h-80 w-full object-cover group-hover:scale-110 transition duration-500">
                <div class="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-[10px] font-bold">⭐ {m.get('rating', '0.0')}</div>
            </div>
            <div class="p-4 text-center">
                <h3 class="text-[11px] font-black truncate uppercase text-slate-200 group-hover:text-blue-500 transition">{m['title']}</h3>
                <p class="text-[10px] text-slate-500 mt-1 uppercase font-bold">{m['year']} | {m['category']}</p>
            </div>
        </a>"""
    movie_grid += '</div>'
    
    return render_full_page(site, slider_html + movie_grid)

@app.route('/s/<slug>/movie/<id>')
def movie_details(slug, id):
    site = sites_col.find_one({"slug": slug})
    m = movies_col.find_one({"_id": ObjectId(id)})
    if not m: return "Movie Not Found", 404
    
    links_html = ""
    for f in m.get('files', []):
        links_html += f"""
        <a href="https://t.me/{site['channel_username']}/{f['msg_id']}" target="_blank" 
           class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-black transition shadow-xl group">
            <span class="flex items-center gap-3">📥 DOWNLOAD {f['quality']}</span>
            <span class="text-[10px] bg-black/20 px-3 py-1 rounded-full uppercase opacity-60 group-hover:opacity-100">Telegram Server</span>
        </a>"""

    content = f"""
    <div class="flex flex-col lg:flex-row gap-12 mt-4">
        <div class="w-full lg:w-1/3 shrink-0">
            <img src="{m['poster']}" class="rounded-3xl shadow-2xl w-full border border-white/10 sticky top-24">
        </div>
        <div class="flex-1">
            <h1 class="text-4xl md:text-7xl font-black text-white leading-tight uppercase tracking-tighter">{m['title']} ({m['year']})</h1>
            <div class="flex flex-wrap gap-4 mt-8">
                <span class="bg-blue-600 px-5 py-2 rounded-xl text-xs font-black uppercase tracking-widest">CATEGORY: {m['category']}</span>
                <span class="bg-slate-800 px-5 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-yellow-500">⭐ {m['rating']}</span>
            </div>
            <div class="mt-10 p-8 bg-slate-900/50 rounded-3xl border border-white/5">
                <h3 class="text-blue-500 font-black text-sm uppercase mb-4 tracking-widest">Storyline Overview</h3>
                <p class="text-slate-400 text-lg leading-relaxed italic">"{m['plot']}"</p>
            </div>
            <div class="mt-8 grid md:grid-cols-2 gap-6 text-sm">
                <p class="bg-black/20 p-4 rounded-xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">Director</b> {m.get('director', 'Unknown')}</p>
                <p class="bg-black/20 p-4 rounded-xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">Starring Cast</b> {m.get('cast', 'Unknown')}</p>
            </div>
            <div class="mt-12 space-y-4">
                <h2 class="text-3xl font-black uppercase tracking-tighter mb-6 flex items-center gap-3">
                    <span class="w-2 h-8 bg-emerald-500 rounded-full"></span> Get Download Links
                </h2>
                <div class="grid gap-4">
                    {links_html}
                </div>
            </div>
        </div>
    </div>"""
    return render_full_page(site, content)

# --- Admin & Clone ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_system():
    main_site = sites_col.find_one({"slug": "main"})
    if request.method == 'POST':
        name = request.form.get('name')
        new_slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if sites_col.find_one({"slug": new_slug}):
            flash("❌ Site Name Already Taken!")
        else:
            sites_col.insert_one({
                "slug": new_slug, "site_name": name, "logo_url": main_site['logo_url'],
                "header_notice": "Welcome to " + name, "admin_user": "admin",
                "admin_pass": generate_password_hash("admin123"), "categories": ["Action", "Hindi"],
                "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            return f'<div style="background:#000;color:#fff;padding:50px;font-family:sans-serif;text-align:center;"><h1>✅ {name} Is Created!</h1><p>URL: /s/{new_slug}</p><p>Admin: admin | Pass: admin123</p><a href="/s/{new_slug}/admin" style="color:cyan;">Login to Dashboard</a></div>'
    
    content = f"""
    <div class="max-w-md mx-auto bg-slate-900 p-10 rounded-3xl border border-emerald-500 shadow-2xl text-center mt-10">
        <h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase italic tracking-tighter">Clone New Movie Site</h2>
        <form method="POST" class="space-y-6">
            <input name="name" placeholder="Enter Your Site Name" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-emerald-500 transition text-center font-bold" required>
            <button class="w-full bg-emerald-600 hover:bg-emerald-700 py-4 rounded-2xl font-black uppercase tracking-widest shadow-lg">Launch My Network</button>
        </form>
    </div>"""
    return render_full_page(main_site, content)

@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin_login(slug):
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'auth_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
        flash("❌ Invalid Admin Access!")
    
    content = f"""
    <div class="max-w-sm mx-auto bg-slate-900 p-10 rounded-3xl border border-white/5 shadow-2xl mt-10">
        <h2 class="text-2xl font-black mb-8 text-center uppercase tracking-widest text-blue-500">Admin Login</h2>
        <form method="POST" class="space-y-4">
            <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 transition">
            <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 transition">
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Authenticate</button>
        </form>
    </div>"""
    return render_full_page(site, content)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def dashboard(slug):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save_settings":
            new_pass = request.form.get('new_pass')
            upd = {
                "site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'),
                "header_notice": request.form.get('header_notice'), "admin_user": request.form.get('admin_user'),
                "tmdb_key": request.form.get('tmdb_key'), "bot_token": request.form.get('bot_token'),
                "channel_id": request.form.get('channel_id'), "channel_username": request.form.get('channel_username').replace('@',''),
                "categories": request.form.get('categories').split(',')
            }
            if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
            sites_col.update_one({"slug": slug}, {"$set": upd})
            flash("✅ All Settings Synchronized!")
        
        if action == "set_webhook":
            if not site['bot_token']: flash("❌ Token Missing!")
            else:
                webhook_url = f"https://clonemovie-six.vercel.app/telegram-webhook"
                r = requests.get(f"https://api.telegram.org/bot{site['bot_token']}/setWebhook?url={webhook_url}")
                flash(f"Webhook Notification: {r.json().get('description')}")
        return redirect(f'/s/{slug}/dashboard')

    movies = list(movies_col.find({"site_slug": slug}).sort('_id', -1))
    movies_list_html = ""
    for m in movies:
        movies_list_html += f"""
        <div class="flex items-center justify-between bg-black/30 p-4 rounded-2xl border border-white/5 mb-3">
            <div class="flex items-center gap-4">
                <img src="{m['poster']}" class="h-10 w-8 rounded object-cover">
                <span class="text-xs font-bold truncate w-32 md:w-60">{m['title']}</span>
            </div>
            <a href="/s/{slug}/delete/{m['_id']}" class="text-red-500 font-bold text-[10px] hover:bg-red-500/10 px-3 py-1 rounded-lg transition">DELETE</a>
        </div>"""

    content = f"""
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5 shadow-2xl">
            <h2 class="text-xl font-black mb-6 uppercase tracking-widest text-blue-500">Site Configuration</h2>
            <form method="POST" class="space-y-4 text-[11px] font-bold">
                <input type="hidden" name="action" value="save_settings">
                <div><label class="opacity-50">SITE NAME & LOGO URL</label>
                <div class="grid grid-cols-2 gap-4 mt-1">
                    <input name="site_name" value="{site['site_name']}" class="bg-black/40 p-3 rounded-xl border border-white/5">
                    <input name="logo_url" value="{site['logo_url']}" class="bg-black/40 p-3 rounded-xl border border-white/5">
                </div></div>
                <div><label class="opacity-50">HEADER NOTICE BAR</label>
                <input name="header_notice" value="{site['header_notice']}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5 mt-1"></div>
                <div><label class="opacity-50">TMDB API KEY & BOT TOKEN</label>
                <div class="grid grid-cols-2 gap-4 mt-1">
                    <input name="tmdb_key" value="{site['tmdb_key']}" placeholder="TMDB Key" class="bg-black/40 p-3 rounded-xl border border-white/5">
                    <input name="bot_token" value="{site['bot_token']}" placeholder="Bot Token" class="bg-black/40 p-3 rounded-xl border border-white/5">
                </div></div>
                <div><label class="opacity-50">TELEGRAM CHANNEL ID & USERNAME</label>
                <div class="grid grid-cols-2 gap-4 mt-1">
                    <input name="channel_id" value="{site['channel_id']}" placeholder="ID (-100...)" class="bg-black/40 p-3 rounded-xl border border-white/5">
                    <input name="channel_username" value="{site['channel_username']}" placeholder="Username (no @)" class="bg-black/40 p-3 rounded-xl border border-white/5">
                </div></div>
                <div><label class="opacity-50">MOVIE CATEGORIES (COMMA SEPARATED)</label>
                <input name="categories" value="{','.join(site['categories'])}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5 mt-1"></div>
                <div class="p-4 bg-blue-600/10 rounded-2xl border border-blue-600/20">
                    <label class="text-blue-400">ADMIN ACCESS CONTROL</label>
                    <input name="admin_user" value="{site['admin_user']}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5 mt-2">
                    <input name="new_pass" type="password" placeholder="Set New Secure Password" class="w-full bg-black/40 p-3 rounded-xl border border-white/5 mt-2">
                </div>
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase tracking-widest shadow-lg">Save Global Settings</button>
            </form>
            <form method="POST" class="mt-4">
                <input type="hidden" name="action" value="set_webhook">
                <button class="w-full bg-emerald-600 py-3 rounded-xl font-black uppercase text-[10px] tracking-widest shadow-lg">🛠️ Auto Set Telegram Webhook</button>
            </form>
        </div>
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5 shadow-2xl h-[850px] overflow-y-auto">
            <h2 class="text-xl font-black mb-6 uppercase tracking-widest text-emerald-500">Movie Inventory</h2>
            {movies_list_html}
        </div>
    </div>"""
    return render_full_page(site, content)

@app.route('/s/<slug>/delete/<id>')
def delete_movie(slug, id):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    flash("🗑️ Movie Permanently Removed!")
    return redirect(f'/s/{slug}/dashboard')

# --- Telegram Webhook Core ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        # মেইন সাইটের সেটিংস থেকে বট চালানো হচ্ছে
        site = sites_col.find_one({"slug": "main"})
        if not site or not site.get('bot_token'): return ''
        
        bot = telebot.TeleBot(site['bot_token'], threaded=False)
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)

        @bot.message_handler(commands=['post'])
        def post_cmd(m):
            args = m.text.split(' ', 2)
            if len(args) < 3: return bot.reply_to(m, "Format: `/post [slug] [movie_name]`")
            slug, name = args[1], args[2]
            target = sites_col.find_one({"slug": slug})
            if not target: return bot.reply_to(m, "❌ Site Not Found!")
            
            res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={target['tmdb_key']}&query={name}").json()
            results = res.get('results', [])[:5]
            markup = telebot.types.InlineKeyboardMarkup()
            for r in results: 
                markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{slug}_{r['id']}"))
            bot.reply_to(m, f"🎬 Results for {target['site_name']}:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
        def sel_movie(c):
            _, slug, tid = c.data.split('_')
            target = sites_col.find_one({"slug": slug})
            res = requests.get(f"https://api.themoviedb.org/3/movie/{tid}?api_key={target['tmdb_key']}&append_to_response=credits").json()
            cast = [x['name'] for x in res.get('credits', {}).get('cast', [])[:8]]
            director = next((x['name'] for x in res.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")
            
            info = {
                "title": res['title'], "year": res.get('release_date','0000')[:4], "plot": res.get('overview',''),
                "rating": res.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}",
                "banner": f"https://image.tmdb.org/t/p/original{res.get('backdrop_path')}",
                "cast": ", ".join(cast), "director": director
            }
            bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "slug": slug, "files": [], "step": "cat"}}, upsert=True)
            markup = telebot.types.InlineKeyboardMarkup()
            for cat in target['categories']: 
                markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{cat.strip()}"))
            bot.send_message(c.message.chat.id, "Select Movie Category:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
        def set_cat(c):
            cat = c.data.split('_')[1]
            bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"category": cat, "step": "file"}})
            bot.send_message(c.message.chat.id, f"✅ Category: {cat}. Now SEND Video/Files. Send /done when finished.")

        @bot.message_handler(content_types=['video', 'document'])
        def handle_docs(m):
            state = bot_states.find_one({"user_id": m.from_user.id})
            if not state or state.get('step') != 'file': return
            target = sites_col.find_one({"slug": state['slug']})
            fwd = bot.forward_message(target['channel_id'], m.chat.id, m.message_id)
            fname = m.video.file_name if m.video else m.document.file_name
            bot_states.update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": fname if fname else "Download", "msg_id": fwd.message_id}}})
            bot.reply_to(m, "📥 File Synchronized. Send more or /done.")

        @bot.message_handler(commands=['done'])
        def publish(m):
            state = bot_states.find_one({"user_id": m.from_user.id})
            if not state: return
            movies_col.insert_one({**state['info'], "category": state['category'], "files": state['files'], "site_slug": state['slug']})
            bot.send_message(m.chat.id, f"🚀 PUBLISHED SUCCESSFULLY ON /s/{state['slug']} !")
            bot_states.delete_one({"user_id": m.from_user.id})

        bot.process_new_updates([update])
        return ''
    return abort(403)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
