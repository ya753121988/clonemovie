import os, threading, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ultimate_movie_cloner_v3_99"

# --- MongoDB Connection ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['movie_business_db']
    sites_col = db['sites']
    movies_col = db['movies']
    client.server_info()
except Exception as e:
    print(f"MongoDB Error: {e}")

# --- Initialize Main Site ---
def init_main_site():
    if sites_col.count_documents({"slug": "main"}) == 0:
        sites_col.insert_one({
            "slug": "main",
            "site_name": "Movie Master",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome to our Multi-Site Movie Cloud!",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "Bangla", "Dual Audio"],
            "tmdb_key": "",
            "bot_token": "",
            "channel_id": "",
            "channel_username": ""
        })

init_main_site()

# --- Helper: Render Logic (Fixing TemplateNotFound) ---
BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background: #0b0f19; color: #f8fafc; font-family: sans-serif; }
        .glass { background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .card { background: #111827; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: #3b82f6; }
    </style>
</head>
<body>
    <div class="bg-blue-600 text-white text-center py-2 text-[10px] md:text-sm font-bold">{{ site.header_notice }}</div>
    <nav class="glass sticky top-0 z-50">
        <div class="container mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-4">
                <a href="/clone-site" class="bg-emerald-600 px-3 py-1 rounded text-[10px] font-bold">➕ CLONE</a>
                <a href="/s/{{site.slug}}" class="flex items-center gap-2">
                    <img src="{{ site.logo_url }}" class="h-8">
                    <span class="text-xl font-black">{{ site.site_name }}</span>
                </a>
            </div>
            <div class="flex items-center gap-4">
                <div class="hidden lg:flex gap-4 text-sm font-medium">
                    {% for c in site.categories %}
                    <a href="/s/{{site.slug}}?cat={{c.strip()}}" class="hover:text-blue-500">{{c.strip()}}</a>
                    {% endfor %}
                </div>
                <a href="/s/{{site.slug}}/admin" class="bg-slate-800 px-3 py-1 rounded text-[10px] font-bold">ADMIN</a>
            </div>
        </div>
    </nav>
    <div class="container mx-auto px-4 py-8">
        {% with messages = get_flashed_messages() %}{% if messages %}{% for m in messages %}
        <div class="bg-blue-600 text-white p-3 rounded-lg mb-6 text-sm">{{ m }}</div>
        {% endfor %}{% endif %}{% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

def render_with_base(content_html, **kwargs):
    # This manually combines the base and content to avoid Jinja TemplateNotFound
    full_html = BASE_LAYOUT.replace('{% block content %}{% endblock %}', content_html)
    return render_template_string(full_html, **kwargs)

# --- Routes ---

@app.route('/')
def index_root():
    return redirect('/s/main')

@app.route('/s/<slug>')
def site_home(slug):
    site = sites_col.find_one({"slug": slug})
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    
    content = """
    <h2 class="text-2xl font-bold mb-8 border-l-4 border-blue-600 pl-4">{{ request.args.get('cat', 'Latest') }}</h2>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
        {% for m in movies %}
        <a href="/s/{{site.slug}}/movie/{{m._id}}" class="card rounded-2xl overflow-hidden group">
            <img src="{{m.poster}}" class="h-64 w-full object-cover">
            <div class="p-3 text-center">
                <h3 class="text-xs font-bold truncate">{{m.title}}</h3>
            </div>
        </a>
        {% endfor %}
    </div>
    """
    return render_with_base(content, site=site, movies=movies)

@app.route('/s/<slug>/movie/<id>')
def movie_page(slug, id):
    site = sites_col.find_one({"slug": slug})
    m = movies_col.find_one({"_id": ObjectId(id)})
    content = """
    <div class="flex flex-col lg:flex-row gap-12 mt-4">
        <img src="{{m.poster}}" class="w-full lg:w-1/3 rounded-3xl shadow-2xl">
        <div class="flex-1">
            <h1 class="text-4xl md:text-6xl font-black">{{m.title}}</h1>
            <p class="mt-6 text-slate-400 text-lg italic">{{m.description}}</p>
            <div class="mt-10 space-y-4">
                {% for f in m.files %}
                <a href="https://t.me/{{site.channel_username}}/{{f.msg_id}}" target="_blank" 
                   class="block bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl text-center font-bold">📥 Download {{f.quality}}</a>
                {% endfor %}
            </div>
        </div>
    </div>
    """
    return render_with_base(content, site=site, m=m)

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    site = sites_col.find_one({"slug": "main"})
    if request.method == 'POST':
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if sites_col.find_one({"slug": slug}):
            flash("❌ Name already exists!")
        else:
            sites_col.insert_one({
                "slug": slug, "site_name": name, "logo_url": site['logo_url'],
                "header_notice": "Welcome to " + name,
                "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
                "categories": ["Action", "Hindi"], "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            return f"Site Created! URL: /s/{slug} | Admin: admin | Pass: admin123"
            
    content = """
    <div class="max-w-md mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5 shadow-2xl">
        <h2 class="text-3xl font-black mb-4 text-center">Clone Site</h2>
        <form method="POST" class="space-y-4">
            <input name="name" placeholder="Enter Site Name" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none" required>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Start Cloning</button>
        </form>
    </div>
    """
    return render_with_base(content, site=site)

@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin_login(slug):
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'auth_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
        flash("❌ Wrong Credentials!")
        
    content = """
    <div class="max-w-sm mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
        <h2 class="text-2xl font-black mb-6 text-center">Login</h2>
        <form method="POST" class="space-y-4">
            <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10">
            <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10">
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Login</button>
        </form>
    </div>
    """
    return render_with_base(content, site=site)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def dashboard(slug):
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
        flash("✅ Updated!")
        return redirect(f'/s/{slug}/dashboard')

    movies = list(movies_col.find({"site_slug": slug}))
    content = """
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-xl font-bold mb-6">Settings</h2>
            <form method="POST" class="space-y-4">
                <input name="site_name" value="{{site.site_name}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="logo_url" value="{{site.logo_url}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="header_notice" value="{{site.header_notice}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="tmdb_key" value="{{site.tmdb_key}}" placeholder="TMDB Key" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="bot_token" value="{{site.bot_token}}" placeholder="Bot Token" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="channel_id" value="{{site.channel_id}}" placeholder="Channel ID" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="channel_username" value="{{site.channel_username}}" placeholder="Channel Username" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="categories" value="{{site.categories|join(',')}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <hr class="border-white/5">
                <input name="admin_user" value="{{site.admin_user}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <input name="new_pass" type="password" placeholder="New Password (Leave blank to keep)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <button class="w-full bg-blue-600 py-3 rounded-xl font-bold">SAVE</button>
            </form>
        </div>
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5 h-[600px] overflow-y-auto">
            <h2 class="text-xl font-bold mb-6">Movies</h2>
            {% for m in movies %}
            <div class="flex justify-between items-center p-3 bg-black/20 rounded-xl mb-2">
                <span class="text-sm truncate w-40">{{m.title}}</span>
                <a href="/s/{{site.slug}}/delete/{{m._id}}" class="text-red-500 text-xs">DELETE</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return render_with_base(content, site=site, movies=movies)

@app.route('/s/<slug>/delete/<id>')
def delete_movie(slug, id):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    flash("Deleted!")
    return redirect(f'/s/{slug}/dashboard')

# --- Bot Helper (Vercel has issues with threads, but keeping simple) ---
def start_bot_polling():
    main_site = sites_col.find_one({"slug": "main"})
    if not main_site or not main_site.get('bot_token'): return
    try:
        bot = telebot.TeleBot(main_site['bot_token'])
        # Simple Logic to avoid crash
        @bot.message_handler(commands=['start'])
        def welcome(message):
            bot.reply_to(message, "Universal Movie Bot Active. Use Admin to Post.")
        bot.infinity_polling()
    except: pass

if __name__ == '__main__':
    # Vercel-এ থ্রেড মাঝেমধ্যে ঝামেলা করে, তবুও ট্রাই করা হচ্ছে
    threading.Thread(target=start_bot_polling, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
