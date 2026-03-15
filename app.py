import os, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "dynamic_cloner_master_key_99"

# --- ডাটাবেস কানেকশন (শুধুমাত্র এটি কোডে থাকবে) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['pro_movie_v11']
sites_col = db['sites']
movies_col = db['movies']
bot_states = db['bot_states']

# --- সিস্টেম ইনিশিয়াল (ফাঁকা সেটিংস দিয়ে মেইন সাইট তৈরি) ---
def init_system():
    if sites_col.count_documents({"slug": "main"}) == 0:
        sites_col.insert_one({
            "slug": "main", "site_name": "My Movie Site",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome! Go to Admin to setup TMDB and Bot.",
            "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "English"],
            "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
        })
init_system()

# --- মাস্টার লেআউট (Responsive) ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
    <style>
        body { background: #0b0f19; color: #f1f5f9; font-family: sans-serif; }
        .glass { background: rgba(17, 24, 39, 0.9); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .card { background: #111827; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: #3b82f6; }
        .swiper-slide img { height: 400px; width: 100%; object-fit: cover; border-radius: 20px; filter: brightness(0.5); }
    </style>
</head>
<body>
    <div class="bg-blue-600 text-center py-2 text-[10px] md:text-sm font-bold px-4">{{ site.header_notice }}</div>
    <nav class="glass sticky top-0 z-50">
        <div class="container mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <a href="/clone-site" class="bg-emerald-600 text-white px-3 py-1 rounded-lg text-[10px] font-black uppercase tracking-tighter">➕ CLONE</a>
                <a href="/s/{{site.slug}}" class="flex items-center gap-2">
                    <img src="{{ site.logo_url }}" class="h-8 md:h-10">
                    <span class="text-xl font-black tracking-tighter">{{ site.site_name }}</span>
                </a>
            </div>
            <div class="flex items-center gap-4">
                <div class="hidden lg:flex gap-6 text-sm font-semibold uppercase">
                    {% for c in site.categories %}<a href="/s/{{site.slug}}?cat={{c.strip()}}" class="hover:text-blue-400">{{c.strip()}}</a>{% endfor %}
                </div>
                <a href="/s/{{site.slug}}/admin" class="bg-slate-800 px-4 py-1.5 rounded-full text-xs font-bold">Admin</a>
            </div>
        </div>
    </nav>
    <div class="container mx-auto px-4 py-8">
        {% block content %}{% endblock %}
    </div>
    <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
    <script>const swiper = new Swiper('.swiper', { autoplay: { delay: 3000 }, loop: true });</script>
</body>
</html>
"""

def render_pro(content, site, **kwargs):
    full_html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', content)
    return render_template_string(full_html, site=site, **kwargs)

# --- রুটস ---

@app.route('/')
def root(): return redirect('/s/main')

@app.route('/s/<slug>')
def home(slug):
    site = sites_col.find_one({"slug": slug})
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    sliders = movies[:5]
    content = """
    {% if sliders %}
    <div class="swiper mb-10 overflow-hidden">
        <div class="swiper-wrapper">
            {% for s in sliders %}
            <div class="swiper-slide relative">
                <img src="{{ s.banner }}">
                <div class="absolute bottom-10 left-10"><h2 class="text-3xl md:text-5xl font-black">{{ s.title }}</h2><a href="/s/{{site.slug}}/movie/{{s._id}}" class="mt-4 inline-block bg-blue-600 px-6 py-2 rounded-full font-bold text-sm">Details</a></div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}
    <h2 class="text-2xl font-bold mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest">{{ request.args.get('cat', 'Latest Movies') }}</h2>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
        {% for m in movies %}
        <a href="/s/{{site.slug}}/movie/{{m._id}}" class="card rounded-2xl overflow-hidden group text-center p-2">
            <img src="{{m.poster}}" class="h-60 md:h-80 w-full object-cover rounded-xl mb-2">
            <h3 class="text-xs font-bold truncate uppercase">{{m.title}}</h3>
            <p class="text-[10px] text-slate-500 mt-1">{{m.year}} | ⭐ {{m.rating}}</p>
        </a>
        {% endfor %}
    </div>
    """
    return render_pro(content, site, sliders=sliders, movies=movies)

@app.route('/s/<slug>/movie/<id>')
def movie(slug, id):
    site = sites_col.find_one({"slug": slug})
    m = movies_col.find_one({"_id": ObjectId(id)})
    content = """
    <div class="flex flex-col lg:flex-row gap-10">
        <img src="{{m.poster}}" class="w-full lg:w-1/3 rounded-3xl shadow-2xl border border-white/5">
        <div class="flex-1">
            <h1 class="text-4xl md:text-5xl font-black">{{m.title}}</h1>
            <div class="flex gap-4 mt-6">
                <span class="bg-blue-600 px-4 py-1 rounded-full text-xs font-bold uppercase">{{m.category}}</span>
                <span class="bg-slate-800 px-4 py-1 rounded-full text-xs font-bold uppercase">⭐ {{m.rating}}</span>
            </div>
            <p class="mt-6 text-slate-400 text-lg italic">"{{m.plot}}"</p>
            <div class="mt-6 text-sm text-slate-500"><p><b>Director:</b> {{m.director}}</p><p><b>Cast:</b> {{m.cast}}</p></div>
            <div class="mt-10 space-y-4">
                <h3 class="text-2xl font-bold uppercase tracking-tighter">📥 Download Links:</h3>
                {% for f in m.files %}
                <a href="https://t.me/{{site.channel_username}}/{{f.msg_id}}" target="_blank" class="block bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-bold text-center">Download {{f.quality}} (Telegram)</a>
                {% endfor %}
            </div>
        </div>
    </div>
    """
    return render_pro(content, site, m=m)

# --- ক্লোন সেন্টার ---
@app.route('/clone-site', methods=['GET', 'POST'])
def clone():
    main_site = sites_col.find_one({"slug": "main"})
    if request.method == 'POST':
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if sites_col.find_one({"slug": slug}): flash("❌ Name Already Exists!")
        else:
            sites_col.insert_one({
                "slug": slug, "site_name": name, "logo_url": main_site['logo_url'], "header_notice": "Welcome to " + name,
                "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
                "categories": ["Action", "Hindi"], "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            return f"<h1>Site Created! URL: /s/{slug} | Admin: admin | Pass: admin123</h1>"
    content = """
    <div class="max-w-md mx-auto bg-slate-900 p-10 rounded-3xl border border-emerald-500 shadow-2xl text-center">
        <h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase">Clone Movie Site</h2>
        <form method="POST" class="space-y-6">
            <input name="name" placeholder="Enter Site Name" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none" required>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Create My Site</button>
        </form>
    </div>
    """
    return render_pro(content, main_site)

# --- অ্যাডমিন প্যানেল (WEB CONTROL) ---
@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin(slug):
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'auth_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
        flash("❌ Wrong Credentials!")
    content = """
    <div class="max-w-sm mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
        <h2 class="text-2xl font-black mb-6 text-center uppercase tracking-widest">Login</h2>
        <form method="POST" class="space-y-4">
            <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
            <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Login</button>
        </form>
    </div>
    """
    return render_pro(content, site)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def dashboard(slug):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save":
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
            flash("✅ Settings Saved!")
        
        if action == "set_webhook":
            if not site['bot_token']: flash("❌ First Save Bot Token!")
            else:
                webhook_url = f"https://clonemovie-six.vercel.app/telegram-webhook"
                r = requests.get(f"https://api.telegram.org/bot{site['bot_token']}/setWebhook?url={webhook_url}")
                flash(f"Webhook Status: {r.json().get('description')}")
        
        return redirect(f'/s/{slug}/dashboard')
    
    movies = list(movies_col.find({"site_slug": slug}))
    content = """
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-xl font-bold mb-6">⚙️ Configuration</h2>
            <form method="POST" class="space-y-4 text-xs">
                <input type="hidden" name="action" value="save">
                <label>Site Name & Logo</label>
                <input name="site_name" value="{{site.site_name}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="logo_url" value="{{site.logo_url}}" placeholder="Logo URL" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <label>Header Notice</label>
                <input name="header_notice" value="{{site.header_notice}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <label>API Keys (TMDB & Telegram Bot)</label>
                <input name="tmdb_key" value="{{site.tmdb_key}}" placeholder="TMDB API Key" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="bot_token" value="{{site.bot_token}}" placeholder="Telegram Bot Token" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <label>Channel Info</label>
                <input name="channel_id" value="{{site.channel_id}}" placeholder="Channel ID (-100...)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="channel_username" value="{{site.channel_username}}" placeholder="Channel Username (without @)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <label>Categories (Comma Separated)</label>
                <input name="categories" value="{{site.categories|join(',')}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <hr class="border-white/5">
                <label>Admin Access</label>
                <input name="admin_user" value="{{site.admin_user}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="new_pass" type="password" placeholder="Set New Password" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <button class="w-full bg-blue-600 py-3 rounded-xl font-bold">SAVE ALL SETTINGS</button>
            </form>
            <form method="POST" class="mt-4">
                <input type="hidden" name="action" value="set_webhook">
                <button class="w-full bg-emerald-600 py-3 rounded-xl font-bold">🛠️ AUTO SET WEBHOOK</button>
            </form>
        </div>
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5 h-[800px] overflow-y-auto">
            <h2 class="text-xl font-bold mb-6 uppercase">Manage Movies</h2>
            {% for m in movies %}
            <div class="flex justify-between items-center p-3 bg-black/20 rounded-xl mb-2">
                <span class="text-xs truncate w-40 font-bold text-slate-400">{{m.title}}</span>
                <a href="/s/{{site.slug}}/delete/{{m._id}}" class="text-red-500 font-bold text-xs uppercase">Delete</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_pro(content, site, movies=movies)

@app.route('/s/<slug>/delete/<id>')
def movie_delete(slug, id):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    return redirect(f'/s/{slug}/dashboard')

# --- টেলিগ্রাম ওয়েবহুক লজিক (DYNAMIC BOT) ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        # এখানে মেইন সাইটের সেটিংস থেকে বটের টোকেন নেওয়া হচ্ছে
        site = sites_col.find_one({"slug": "main"})
        if not site or not site.get('bot_token'): return ''
        
        bot = telebot.TeleBot(site['bot_token'], threaded=False)
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        
        # --- বটের কমান্ড হ্যান্ডলারগুলো এখানে থাকবে ---
        @bot.message_handler(commands=['post'])
        def bot_post(message):
            args = message.text.split(' ', 2)
            if len(args) < 3: return bot.reply_to(message, "Use: `/post [slug] [movie_name]`")
            slug, name = args[1], args[2]
            target_site = sites_col.find_one({"slug": slug})
            if not target_site: return bot.reply_to(message, "Site Not Found!")
            
            res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={target_site['tmdb_key']}&query={name}").json()
            results = res.get('results', [])[:5]
            markup = telebot.types.InlineKeyboardMarkup()
            for r in results: markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{slug}_{r['id']}"))
            bot.reply_to(message, "Select Movie:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('sel_'))
        def bot_select(call):
            _, slug, tid = call.data.split('_')
            target_site = sites_col.find_one({"slug": slug})
            url = f"https://api.themoviedb.org/3/movie/{tid}?api_key={target_site['tmdb_key']}&append_to_response=credits"
            r = requests.get(url).json()
            cast = [c['name'] for c in r.get('credits', {}).get('cast', [])[:5]]
            director = next((c['name'] for c in r.get('credits', {}).get('crew', []) if c['job'] == 'Director'), "Unknown")
            info = {"title": r.get('title'), "year": r.get('release_date', '0000')[:4], "plot": r.get('overview'), "rating": r.get('vote_average'), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": ", ".join(cast), "director": director}
            bot_states.update_one({"user_id": call.from_user.id}, {"$set": {"info": info, "slug": slug, "files": [], "step": "cat"}}, upsert=True)
            markup = telebot.types.InlineKeyboardMarkup()
            for c in target_site['categories']: markup.add(telebot.types.InlineKeyboardButton(c, callback_data=f"cat_{c.strip()}"))
            bot.send_message(call.message.chat.id, "Select Category:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
        def bot_cat(call):
            cat = call.data.split('_')[1]
            bot_states.update_one({"user_id": call.from_user.id}, {"$set": {"category": cat, "step": "file"}})
            bot.send_message(call.message.chat.id, f"Now SEND Video/Files. Send /done when finished.")

        @bot.message_handler(content_types=['video', 'document'])
        def bot_file(m):
            state = bot_states.find_one({"user_id": m.from_user.id})
            if not state or state.get('step') != 'file': return
            target_site = sites_col.find_one({"slug": state['slug']})
            fwd = bot.forward_message(target_site['channel_id'], m.chat.id, m.message_id)
            name = m.video.file_name if m.video else m.document.file_name
            bot_states.update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": name if name else "Download", "msg_id": fwd.message_id}}})
            bot.reply_to(m, "File saved. /done to publish.")

        @bot.message_handler(commands=['done'])
        def bot_done(m):
            state = bot_states.find_one({"user_id": m.from_user.id})
            if not state: return
            movies_col.insert_one({**state['info'], "category": state['category'], "files": state['files'], "site_slug": state['slug']})
            bot.send_message(m.chat.id, "🚀 Published!")
            bot_states.delete_one({"user_id": m.from_user.id})

        bot.process_new_updates([update])
        return ''
    else:
        abort(403)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
