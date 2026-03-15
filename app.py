import os, threading, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask Configuration ---
app = Flask(__name__)
app.secret_key = "ultimate_movie_cloner_secret_99"

# --- MongoDB Connection ---
# আপনার দেওয়া URI এখানে সেট করা হয়েছে।
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['movie_business_db']
    sites_col = db['sites']
    movies_col = db['movies']
    # কানেকশন চেক
    client.server_info()
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# --- System Initialization (Create Main Site) ---
def init_main_site():
    if sites_col.count_documents({"slug": "main"}) == 0:
        sites_col.insert_one({
            "slug": "main",
            "site_name": "Movie Hub",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome to our Multi-Site Movie Store!",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "English", "Dual Audio"],
            "tmdb_key": "",
            "bot_token": "",
            "channel_id": "",
            "channel_username": ""
        })

init_main_site()

# --- Utility: Fetch TMDB Data ---
def fetch_tmdb(tmdb_id, api_key):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&append_to_response=credits"
        res = requests.get(url).json()
        if 'title' not in res: return None
        cast = [c['name'] for c in res.get('credits', {}).get('cast', [])[:5]]
        director = next((c['name'] for c in res.get('credits', {}).get('crew', []) if c['job'] == 'Director'), "Unknown")
        return {
            "title": res.get('title'),
            "year": res.get('release_date', '0000')[:4],
            "plot": res.get('overview'),
            "rating": res.get('vote_average'),
            "poster": f"https://image.tmdb.org/t/p/w500{res.get('poster_path')}",
            "banner": f"https://image.tmdb.org/t/p/original{res.get('backdrop_path')}",
            "cast": ", ".join(cast),
            "director": director
        }
    except: return None

# --- Responsive HTML Layout ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0f172a; color: #f1f5f9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass { background: rgba(30, 41, 59, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .movie-card { background: #1e293b; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .movie-card:hover { transform: translateY(-5px); border-color: #3b82f6; }
    </style>
</head>
<body>
    <div class="bg-blue-600 text-white text-center py-2 text-[10px] md:text-sm font-bold px-4">{{ site.header_notice }}</div>
    <nav class="glass sticky top-0 z-50">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <div class="flex items-center gap-4 md:gap-8">
                <a href="/clone-site" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-[10px] md:text-xs font-black uppercase tracking-wider">➕ Clone Site</a>
                <a href="/s/{{site.slug}}" class="flex items-center gap-2">
                    <img src="{{ site.logo_url }}" class="h-7 md:h-9">
                    <span class="text-lg md:text-xl font-black tracking-tighter">{{ site.site_name }}</span>
                </a>
            </div>
            <div class="flex items-center gap-4">
                <div class="hidden lg:flex gap-6 text-sm font-semibold">
                    {% for c in site.categories %}
                    <a href="/s/{{site.slug}}?cat={{c.strip()}}" class="hover:text-blue-400">{{c.strip()}}</a>
                    {% endfor %}
                </div>
                <a href="/s/{{site.slug}}/admin" class="bg-slate-800 px-3 py-1.5 rounded-xl text-[10px] font-bold border border-white/10">ADMIN</a>
            </div>
        </div>
    </nav>
    <div class="container mx-auto px-4 py-8">
        {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}
        <div class="bg-blue-600 text-white p-4 rounded-xl mb-6 text-sm shadow-lg">{{ m }}</div>
        {% endfor %}{% endif %}{% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- Routes: Frontend ---

@app.route('/')
def root_redirect():
    return redirect('/s/main')

@app.route('/s/<slug>')
def site_home(slug):
    site = sites_col.find_one({"slug": slug})
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <h2 class="text-xl md:text-2xl font-bold mb-8 flex items-center gap-3">
            <span class="w-1.5 h-8 bg-blue-600 rounded-full"></span>
            {{ request.args.get('cat', 'Recently Added') }}
        </h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-6">
            {% for m in movies %}
            <a href="/s/{{site.slug}}/movie/{{m._id}}" class="movie-card rounded-2xl overflow-hidden group">
                <div class="relative">
                    <img src="{{m.poster}}" class="h-60 md:h-80 w-full object-cover">
                    <div class="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-[10px] font-bold">{{m.year}}</div>
                </div>
                <div class="p-3">
                    <h3 class="text-xs md:text-sm font-bold truncate group-hover:text-blue-400 transition">{{m.title}}</h3>
                    <p class="text-[10px] text-slate-500 mt-1">{{m.category}}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endblock %}
    """, base=LAYOUT, site=site, movies=movies)

@app.route('/s/<slug>/movie/<id>')
def movie_detail(slug, id):
    site = sites_col.find_one({"slug": slug})
    m = movies_col.find_one({"_id": ObjectId(id)})
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="flex flex-col lg:flex-row gap-10 mt-4">
            <div class="w-full lg:w-1/3 shrink-0">
                <img src="{{m.poster}}" class="rounded-3xl shadow-2xl w-full border border-white/5">
            </div>
            <div class="flex-1">
                <h1 class="text-3xl md:text-5xl font-black leading-tight">{{m.title}} ({{m.year}})</h1>
                <div class="flex gap-3 mt-4">
                    <span class="bg-blue-600 px-3 py-1 rounded-lg text-[10px] font-bold">⭐ {{m.rating}}</span>
                    <span class="bg-slate-800 px-3 py-1 rounded-lg text-[10px] font-bold uppercase">{{m.category}}</span>
                </div>
                <p class="mt-6 text-slate-400 text-base md:text-lg leading-relaxed">{{m.description}}</p>
                <div class="mt-6 text-sm text-slate-500 space-y-1">
                    <p><b>Director:</b> {{m.director}}</p>
                    <p><b>Cast:</b> {{m.cast}}</p>
                </div>
                <div class="mt-10">
                    <h3 class="text-xl font-bold mb-4">Direct Telegram Files</h3>
                    <div class="grid gap-3">
                        {% for f in m.files %}
                        <a href="https://t.me/{{site.channel_username}}/{{f.msg_id}}" target="_blank" 
                           class="flex justify-between items-center bg-slate-800 hover:bg-blue-600 p-4 rounded-xl border border-white/5 transition">
                            <span class="font-bold text-sm">📥 Download {{f.quality}}</span>
                            <span class="text-[10px] opacity-60">Telegram File</span>
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {% endblock %}
    """, base=LAYOUT, site=site, m=m)

# --- Route: Clone Site ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    main_site = sites_col.find_one({"slug": "main"})
    if request.method == 'POST':
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if sites_col.find_one({"slug": slug}):
            flash("❌ This site name already exists!")
        else:
            sites_col.insert_one({
                "slug": slug, "site_name": name, "logo_url": main_site['logo_url'],
                "header_notice": "Welcome to " + name,
                "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
                "categories": ["Action", "Hindi"], "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            flash(f"✅ Success! Site URL: /s/{slug} | Admin Pass: admin123")
            return redirect(f'/s/{slug}/admin')
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="max-w-md mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5 shadow-2xl">
            <h2 class="text-3xl font-black mb-4">Clone New Site</h2>
            <p class="text-slate-500 text-sm mb-6">Enter a name to create your own instant movie store.</p>
            <form method="POST" class="space-y-4">
                <input name="name" placeholder="Site Name (e.g. BongoTV)" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 transition" required>
                <button class="w-full bg-blue-600 hover:bg-blue-700 py-4 rounded-2xl font-black">START CLONING</button>
            </form>
        </div>
        {% endblock %}
    """, base=LAYOUT, site=main_site)

# --- Routes: Admin Panel ---

@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin_login(slug):
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        u = request.form.get('user')
        p = request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'auth_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
        flash("❌ Invalid Username or Password")
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="max-w-sm mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-2xl font-black mb-6 text-center">Admin Login</h2>
            <form method="POST" class="space-y-4">
                <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10">
                <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10">
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-black">LOGIN</button>
            </form>
        </div>
        {% endblock %}
    """, base=LAYOUT, site=site)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def admin_dashboard(slug):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    site = sites_col.find_one({"slug": slug})
    
    if request.method == 'POST':
        new_pass = request.form.get('new_pass')
        upd = {
            "site_name": request.form.get('site_name'),
            "logo_url": request.form.get('logo_url'),
            "header_notice": request.form.get('header_notice'),
            "admin_user": request.form.get('admin_user'),
            "tmdb_key": request.form.get('tmdb_key'),
            "bot_token": request.form.get('bot_token'),
            "channel_id": request.form.get('channel_id'),
            "channel_username": request.form.get('channel_username').replace('@',''),
            "categories": request.form.get('categories').split(',')
        }
        if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
        sites_col.update_one({"slug": slug}, {"$set": upd})
        flash("✅ Settings Updated Successfully!")
        return redirect(f'/s/{slug}/dashboard')

    movies = list(movies_col.find({"site_slug": slug}).sort('_id', -1))
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="grid lg:grid-cols-2 gap-10">
            <div class="bg-slate-900 p-6 md:p-8 rounded-3xl border border-white/5">
                <h2 class="text-2xl font-black mb-6">Site Configuration</h2>
                <form method="POST" class="space-y-4">
                    <input name="site_name" value="{{site.site_name}}" placeholder="Site Name" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <input name="logo_url" value="{{site.logo_url}}" placeholder="Logo URL" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <textarea name="header_notice" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">{{site.header_notice}}</textarea>
                    <input name="tmdb_key" value="{{site.tmdb_key}}" placeholder="TMDB API Key" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <input name="bot_token" value="{{site.bot_token}}" placeholder="Telegram Bot Token" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <input name="channel_id" value="{{site.channel_id}}" placeholder="Channel ID" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <input name="channel_username" value="{{site.channel_username}}" placeholder="Channel Username" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <input name="categories" value="{{site.categories|join(',')}}" placeholder="Categories (Comma Separated)" class="w-full bg-black/40 p-3 rounded-xl border border-white/10">
                    <div class="p-4 bg-blue-600/10 rounded-2xl border border-blue-600/20">
                        <h4 class="text-blue-400 font-bold text-sm mb-2">Change Admin Credentials</h4>
                        <input name="admin_user" value="{{site.admin_user}}" class="w-full bg-black/40 p-2 rounded-lg border border-white/10 mb-2">
                        <input name="new_pass" type="password" placeholder="New Password (Blank to keep)" class="w-full bg-black/40 p-2 rounded-lg border border-white/10">
                    </div>
                    <button class="w-full bg-blue-600 py-4 rounded-2xl font-black">SAVE SETTINGS</button>
                </form>
            </div>
            <div class="bg-slate-900 p-6 md:p-8 rounded-3xl border border-white/5 h-[800px] overflow-y-auto">
                <h2 class="text-2xl font-black mb-6">Manage Movies</h2>
                {% for m in movies %}
                <div class="flex items-center justify-between bg-black/30 p-4 rounded-2xl mb-3 border border-white/5">
                    <div class="flex items-center gap-4">
                        <img src="{{m.poster}}" class="h-12 w-10 rounded object-cover">
                        <div>
                            <p class="text-sm font-bold truncate w-32 md:w-48">{{m.title}}</p>
                            <p class="text-[10px] text-slate-500 uppercase">{{m.category}}</p>
                        </div>
                    </div>
                    <a href="/s/{{site.slug}}/delete/{{m._id}}" class="text-red-500 font-bold text-xs p-2">DELETE</a>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endblock %}
    """, base=LAYOUT, site=site, movies=movies)

@app.route('/s/<slug>/delete/<id>')
def delete_movie(slug, id):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    flash("🗑️ Movie deleted successfully!")
    return redirect(f'/s/{slug}/dashboard')

# --- Telegram Bot Engine ---

def start_bot_polling():
    # মেইন সাইটের টোকেন দিয়ে বট শুরু হবে
    main_site = sites_col.find_one({"slug": "main"})
    if not main_site or not main_site.get('bot_token'): 
        print("Bot Token not set in main site. Bot disabled.")
        return

    bot = telebot.TeleBot(main_site['bot_token'])
    bot_states = {}

    @bot.message_handler(commands=['start'])
    def send_welcome(message):
        bot.reply_to(message, "🎬 *Universal Movie Bot*\n\nUsage: `/post [site_slug] [movie_name]`\nExample: `/post main Avatar`", parse_mode="Markdown")

    @bot.message_handler(commands=['post'])
    def init_post(message):
        parts = message.text.split(' ', 2)
        if len(parts) < 3:
            bot.reply_to(message, "❌ Format: `/post [slug] [name]`")
            return
        slug, query = parts[1], parts[2]
        site = sites_col.find_one({"slug": slug})
        if not site:
            bot.reply_to(message, f"❌ Site slug '{slug}' not found!")
            return
        
        # Search TMDB
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={site['tmdb_key']}&query={query}").json()
        results = res.get('results', [])[:5]
        if not results:
            bot.reply_to(message, "❌ No movie found on TMDB!")
            return

        markup = telebot.types.InlineKeyboardMarkup()
        for m in results:
            markup.add(telebot.types.InlineKeyboardButton(f"{m['title']} ({m.get('release_date','0000')[:4]})", callback_data=f"sel_{slug}_{m['id']}"))
        bot.reply_to(message, f"[{site['site_name']}] Select Movie:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sel_'))
    def select_movie(call):
        _, slug, tmdb_id = call.data.split('_')
        site = sites_col.find_one({"slug": slug})
        details = fetch_tmdb(tmdb_id, site['tmdb_key'])
        if not details: return
        
        bot_states[call.from_user.id] = {"details": details, "slug": slug, "files": [], "step": "cat"}
        markup = telebot.types.InlineKeyboardMarkup()
        for c in site['categories']:
            markup.add(telebot.types.InlineKeyboardButton(c, callback_data=f"cat_{slug}_{c.strip()}"))
        bot.send_message(call.message.chat.id, "Select Category:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
    def select_category(call):
        _, slug, cat = call.data.split('_')
        bot_states[call.from_user.id]['category'] = cat
        bot_states[call.from_user.id]['step'] = 'file'
        bot.send_message(call.message.chat.id, f"Category: {cat}\nNow SEND Movie Files (Video/Document). Send /done when finished.")

    @bot.message_handler(content_types=['video', 'document'], func=lambda m: bot_states.get(m.from_user.id, {}).get('step') == 'file')
    def collect_files(message):
        state = bot_states[message.from_user.id]
        site = sites_col.find_one({"slug": state['slug']})
        # Forward to channel
        try:
            fwd = bot.forward_message(site['channel_id'], message.chat.id, message.message_id)
            name = message.video.file_name if message.video else message.document.file_name
            state['files'].append({"quality": name if name else "Download", "msg_id": fwd.message_id})
            bot.reply_to(message, "✅ File Saved. Send more or /done.")
        except Exception as e:
            bot.reply_to(message, f"❌ Forward Error: {e}")

    @bot.message_handler(commands=['done'], func=lambda m: bot_states.get(m.from_user.id, {}).get('step') == 'file')
    def final_publish(message):
        state = bot_states[message.from_user.id]
        movie_doc = {**state['details'], "category": state['category'], "files": state['files'], "site_slug": state['slug']}
        movies_col.insert_one(movie_doc)
        bot.send_message(message.chat.id, f"🚀 Movie Published to '{state['slug']}' site!")
        del bot_states[message.from_user.id]

    bot.infinity_polling()

# --- App Runner ---

if __name__ == '__main__':
    # টেলিগ্রাম বট থ্রেড চালু করুন
    threading.Thread(target=start_bot_polling, daemon=True).start()
    # ফ্ল্যাস্ক ওয়েবসাইট চালু করুন
    app.run(host='0.0.0.0', port=5000, debug=False)
