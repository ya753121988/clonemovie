import os, threading, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask App Configuration ---
app = Flask(__name__)
app.secret_key = "universal_movie_cloner_key"

# --- MongoDB Setup ---
# সরাসরি আপনার MONGO_URI এখানে বসান অথবা Environment Variable হিসেবে দিন
MONGO_URI = "আপনার_মংগোডিবি_ইউআরএল_এখানে_দিন" 
client = MongoClient(MONGO_URI)
db = client['multisite_movie_vault']
sites_col = db['sites']
movies_col = db['movies']

# --- Helper: Initial Main Site ---
def init_system():
    if not sites_col.find_one({"slug": "main"}):
        sites_col.insert_one({
            "slug": "main",
            "site_name": "Movie Master",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome to the world of unlimited movies!",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "English"],
            "tmdb_key": "",
            "bot_token": "",
            "channel_id": "",
            "channel_username": ""
        })

init_system()

# --- Utility Functions ---
def get_site(slug):
    return sites_col.find_one({"slug": slug})

def fetch_tmdb_data(tmdb_id, api_key):
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

# --- Telegram Bot Logic (Multi-Site Support) ---
# প্রতিটি সাইটের জন্য আলাদা বটের পরিবর্তে একটি মাস্টার বট দিয়ে সব চালানো যাবে।
# তবে এখানে আমরা একটি গ্লোবাল বটের লজিক দিচ্ছি যা এডমিন প্যানেলে দেওয়া টোকেন অনুযায়ী কাজ করবে।

user_states = {}

def setup_bot():
    config = get_site("main") # ডিফল্টভাবে মেইন সাইটের বট টোকেন চেক করবে
    if not config or not config.get('bot_token'): return None
    return telebot.TeleBot(config['bot_token'])

bot = setup_bot()

if bot:
    @bot.message_handler(commands=['start'])
    def welcome(message):
        bot.reply_to(message, "🎬 মুভি পোস্ট করতে আপনার সাইটের স্ল্যাগ (Slug) দিন।\nউদাহরণ: `/post main Avatar` (এখানে main হলো আপনার সাইটের নাম)")

    @bot.message_handler(commands=['post'])
    def start_post(message):
        args = message.text.split(' ', 2)
        if len(args) < 3:
            return bot.reply_to(message, "ব্যবহার: `/post [slug] [movie_name]`\nউদাহরণ: `/post main Avatar`")
        
        slug, query = args[1], args[2]
        site = get_site(slug)
        if not site: return bot.reply_to(message, "❌ এই স্ল্যাগে কোনো সাইট পাওয়া যায়নি!")
        
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={site['tmdb_key']}&query={query}").json()
        results = res.get('results', [])[:5]
        
        markup = telebot.types.InlineKeyboardMarkup()
        for m in results:
            markup.add(telebot.types.InlineKeyboardButton(f"{m['title']} ({m['release_date'][:4]})", callback_data=f"sel_{slug}_{m['id']}"))
        bot.reply_to(message, f"[{site['site_name']}] মুভি সিলেক্ট করুন:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('sel_'))
    def handle_selection(call):
        _, slug, tmdb_id = call.data.split('_')
        site = get_site(slug)
        details = fetch_tmdb_data(tmdb_id, site['tmdb_key'])
        user_states[call.from_user.id] = {"details": details, "slug": slug, "files": [], "step": "cat"}
        
        markup = telebot.types.InlineKeyboardMarkup()
        for c in site['categories']:
            markup.add(telebot.types.InlineKeyboardButton(c, callback_data=f"cat_{slug}_{c}"))
        bot.send_message(call.message.chat.id, "ক্যাটাগরি সিলেক্ট করুন:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda call: call.data.startswith('cat_'))
    def handle_cat(call):
        _, slug, cat = call.data.split('_')
        user_states[call.from_user.id]['category'] = cat
        user_states[call.from_user.id]['step'] = 'upload'
        bot.send_message(call.message.chat.id, f"এখন [{cat}] ক্যাটাগরির জন্য মুভি ফাইল (Video/File) পাঠান। শেষ হলে /done লিখুন।")

    @bot.message_handler(content_types=['video', 'document'], func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'upload')
    def handle_files(message):
        state = user_states[message.from_user.id]
        site = get_site(state['slug'])
        fwd = bot.forward_message(site['channel_id'], message.chat.id, message.message_id)
        name = message.video.file_name if message.video else message.document.file_name
        state['files'].append({"quality": name if name else "Download", "msg_id": fwd.message_id})
        bot.reply_to(message, "✅ ফাইল চ্যানেলে সেভ হয়েছে। আরও থাকলে পাঠান নতুবা /done লিখুন।")

    @bot.message_handler(commands=['done'], func=lambda m: user_states.get(m.from_user.id, {}).get('step') == 'upload')
    def save_movie(message):
        state = user_states[message.from_user.id]
        movie_doc = {**state['details'], "category": state['category'], "files": state['files'], "site_slug": state['slug']}
        movies_col.insert_one(movie_doc)
        bot.send_message(message.chat.id, f"🚀 মুভিটি '{state['slug']}' সাইটে পাবলিশ করা হয়েছে!")
        del user_states[message.from_user.id]

# --- Templates ---

BASE_LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ site.site_name }}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        body { background-color: #0b0f19; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .glass { background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .card { background: #111827; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }
        .card:hover { transform: translateY(-5px); border-color: #3b82f6; }
    </style>
</head>
<body>
    <div class="bg-blue-600 text-white text-center py-2 text-xs font-bold">{{ site.header_notice }}</div>
    <nav class="glass sticky top-0 z-50">
        <div class="container mx-auto px-4 py-4 flex justify-between items-center">
            <div class="flex items-center gap-6">
                <a href="/clone-center" class="bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-1.5 rounded-lg text-sm font-bold flex items-center gap-2">
                    ➕ <span class="hidden md:inline">Clone Site</span>
                </a>
                <a href="/s/{{site.slug}}" class="flex items-center gap-3">
                    <img src="{{ site.logo_url }}" class="h-8 md:h-10 rounded">
                    <span class="text-xl md:text-2xl font-black tracking-tighter">{{ site.site_name }}</span>
                </a>
            </div>
            <div class="flex items-center gap-4">
                <div class="hidden lg:flex gap-6 text-sm font-medium">
                    {% for c in site.categories %}
                    <a href="/s/{{site.slug}}?cat={{c}}" class="hover:text-blue-500">{{c}}</a>
                    {% endfor %}
                </div>
                <a href="/s/{{site.slug}}/admin" class="bg-slate-800 hover:bg-slate-700 px-4 py-2 rounded-xl text-xs font-bold">Admin</a>
            </div>
        </div>
    </nav>
    <div class="container mx-auto px-4 py-8">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for msg in messages %}
                <div class="bg-blue-600/20 border border-blue-600 text-blue-400 p-4 rounded-xl mb-6 text-sm">{{ msg }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- Website Routes ---

@app.route('/')
def main_root():
    return redirect('/s/main')

@app.route('/s/<slug>')
def home(slug):
    site = get_site(slug)
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <h2 class="text-2xl font-bold mb-8 border-l-4 border-blue-600 pl-4">{{ request.args.get('cat', 'Latest Uploads') }}</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {% for m in movies %}
            <a href="/s/{{site.slug}}/movie/{{m._id}}" class="card rounded-2xl overflow-hidden group">
                <div class="relative">
                    <img src="{{m.poster}}" class="h-64 md:h-80 w-full object-cover group-hover:scale-105 transition duration-500">
                    <div class="absolute top-2 right-2 bg-black/60 px-2 py-1 rounded text-[10px] font-bold">{{m.year}}</div>
                </div>
                <div class="p-3">
                    <h3 class="text-sm font-bold truncate">{{m.title}}</h3>
                    <p class="text-[10px] text-slate-500 mt-1 uppercase">{{m.category}}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endblock %}
    """, base=BASE_LAYOUT, site=site, movies=movies)

@app.route('/s/<slug>/movie/<id>')
def movie_page(slug, id):
    site = get_site(slug)
    m = movies_col.find_one({"_id": ObjectId(id)})
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="flex flex-col lg:flex-row gap-12 mt-4">
            <div class="w-full lg:w-1/3">
                <img src="{{m.poster}}" class="rounded-3xl shadow-2xl w-full border border-white/5">
            </div>
            <div class="flex-1">
                <h1 class="text-4xl md:text-6xl font-black">{{m.title}}</h1>
                <div class="flex gap-4 mt-6">
                    <span class="bg-blue-600 px-3 py-1 rounded-lg text-xs font-bold">⭐ {{m.rating}}</span>
                    <span class="bg-slate-800 px-3 py-1 rounded-lg text-xs font-bold">{{m.year}}</span>
                    <span class="bg-slate-800 px-3 py-1 rounded-lg text-xs font-bold uppercase">{{m.category}}</span>
                </div>
                <p class="mt-8 text-slate-400 text-lg leading-relaxed italic">{{m.description}}</p>
                <div class="mt-12">
                    <h3 class="text-xl font-bold mb-6 flex items-center gap-2">📂 Available Files:</h3>
                    <div class="grid gap-4">
                        {% for f in m.files %}
                        <a href="https://t.me/{{site.channel_username}}/{{f.msg_id}}" target="_blank" class="flex justify-between items-center bg-slate-900 hover:bg-blue-600 p-5 rounded-2xl border border-white/5 transition group">
                            <span class="font-bold tracking-wide">📥 {{f.quality}}</span>
                            <span class="text-[10px] bg-black/30 px-3 py-1 rounded-full group-hover:bg-white/20 uppercase font-black">Telegram File</span>
                        </a>
                        {% endfor %}
                    </div>
                </div>
            </div>
        </div>
        {% endblock %}
    """, base=BASE_LAYOUT, site=site, m=m)

# --- Clone System ---

@app.route('/clone-center', methods=['GET', 'POST'])
def clone_center():
    site = get_site("main")
    if request.method == 'POST':
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if get_site(slug):
            flash("❌ এই নামে ইতিমধ্যে একটি সাইট আছে!")
        else:
            sites_col.insert_one({
                "slug": slug, "site_name": name, "logo_url": site['logo_url'],
                "header_notice": "Welcome to " + name,
                "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
                "categories": ["Action", "Hindi"], "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            return render_template_string("""
                {% extends "base" %}
                {% block content %}
                <div class="max-w-xl mx-auto bg-slate-900 border border-emerald-500/50 p-10 rounded-3xl text-center">
                    <div class="text-5xl mb-4">🎉</div>
                    <h2 class="text-3xl font-black text-emerald-400">আপনার সাইট তৈরি!</h2>
                    <p class="mt-4 text-slate-400">সাইট ইউআরএল: <br><a href="/s/{{slug}}" class="text-blue-500 font-mono">{{url}}s/{{slug}}</a></p>
                    <div class="mt-8 p-6 bg-black/40 rounded-2xl text-left text-sm space-y-2">
                        <p>🔐 <b>Admin Login:</b> /s/{{slug}}/admin</p>
                        <p>👤 <b>User:</b> admin</p>
                        <p>🔑 <b>Pass:</b> admin123</p>
                    </div>
                    <p class="mt-6 text-xs text-slate-500 italic">এডমিন প্যানেলে ঢুকে আপনার TMDB API Key এবং বট টোকেন সেট করে নিন।</p>
                </div>
                {% endblock %}
            """, base=BASE_LAYOUT, site=site, slug=slug, url=request.host_url)
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="max-w-md mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-3xl font-black mb-2">Create Clone</h2>
            <p class="text-slate-500 mb-8 text-sm">নতুন মুভি সাইট তৈরি করতে নাম দিন।</p>
            <form method="POST" class="space-y-6">
                <input name="name" placeholder="Enter Site Name (e.g. BongoTV)" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 transition" required>
                <button class="w-full bg-blue-600 hover:bg-blue-700 py-4 rounded-2xl font-black tracking-widest uppercase">Start My Site</button>
            </form>
        </div>
        {% endblock %}
    """, base=BASE_LAYOUT, site=site)

# --- Admin Panel ---

@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin_login(slug):
    site = get_site(slug)
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'auth_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
        flash("❌ ভুল ইউজারনেম বা পাসওয়ার্ড!")
    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="max-w-sm mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-2xl font-black mb-6 text-center">{{site.site_name}} Admin</h2>
            <form method="POST" class="space-y-4">
                <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
                <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-black">LOGIN</button>
            </form>
        </div>
        {% endblock %}
    """, base=BASE_LAYOUT, site=site)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def dashboard(slug):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    site = get_site(slug)
    movies = list(movies_col.find({"site_slug": slug}))
    
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
        flash("✅ সেটিংস আপডেট করা হয়েছে!")
        return redirect(f'/s/{slug}/dashboard')

    return render_template_string("""
        {% extends "base" %}
        {% block content %}
        <div class="grid lg:grid-cols-2 gap-10">
            <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
                <h2 class="text-2xl font-black mb-6">Site Configuration</h2>
                <form method="POST" class="space-y-4">
                    <div class="grid grid-cols-2 gap-4">
                        <input name="site_name" value="{{site.site_name}}" placeholder="Site Name" class="bg-black/40 p-3 rounded-xl border border-white/5">
                        <input name="logo_url" value="{{site.logo_url}}" placeholder="Logo URL" class="bg-black/40 p-3 rounded-xl border border-white/5">
                    </div>
                    <textarea name="header_notice" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">{{site.header_notice}}</textarea>
                    <input name="tmdb_key" value="{{site.tmdb_key}}" placeholder="TMDB API KEY" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                    <input name="bot_token" value="{{site.bot_token}}" placeholder="Telegram Bot Token" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                    <div class="grid grid-cols-2 gap-4">
                        <input name="channel_id" value="{{site.channel_id}}" placeholder="Channel ID" class="bg-black/40 p-3 rounded-xl border border-white/5">
                        <input name="channel_username" value="{{site.channel_username}}" placeholder="Channel Username" class="bg-black/40 p-3 rounded-xl border border-white/5">
                    </div>
                    <input name="categories" value="{{site.categories|join(',')}}" placeholder="Categories (Comma Separated)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                    <hr class="border-white/5">
                    <h3 class="font-bold text-blue-500">Security</h3>
                    <input name="admin_user" value="{{site.admin_user}}" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                    <input name="new_pass" type="password" placeholder="New Password (Leave blank to keep current)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                    <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Save All Settings</button>
                </form>
            </div>
            <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
                <h2 class="text-2xl font-black mb-6">Movies List</h2>
                <div class="space-y-3 h-[600px] overflow-y-auto pr-2">
                    {% for m in movies %}
                    <div class="bg-black/40 p-4 rounded-2xl flex justify-between items-center">
                        <div class="flex items-center gap-4">
                            <img src="{{m.poster}}" class="h-12 w-10 rounded object-cover">
                            <div>
                                <p class="text-sm font-bold">{{m.title}}</p>
                                <p class="text-[10px] text-slate-500">{{m.category}}</p>
                            </div>
                        </div>
                        <a href="/s/{{site.slug}}/delete/{{m._id}}" class="text-red-500 hover:bg-red-500/10 p-2 rounded-lg">🗑️</a>
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endblock %}
    """, base=BASE_LAYOUT, site=site, movies=movies)

@app.route('/s/<slug>/delete/<id>')
def delete_movie(slug, id):
    if not session.get(f'auth_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    flash("🗑️ মুভি ডিলিট করা হয়েছে!")
    return redirect(f'/s/{slug}/dashboard')

# --- Bot Thread ---
def run_bot():
    if bot:
        print("Bot is starting...")
        bot.infinity_polling()

if __name__ == '__main__':
    threading.Thread(target=run_bot).start()
    app.run(host='0.0.0.0', port=5000)
