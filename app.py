import os, threading, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "ultimate_movie_system_fixed_v5"

# --- MongoDB Connection ---
# আপনার দেওয়া লিঙ্কটি এখানে সরাসরি বসানো হয়েছে
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['movie_vault_final']
    sites_col = db['sites']
    movies_col = db['movies']
    client.server_info() # Check connection
except Exception as e:
    print(f"MongoDB Connection Failed: {e}")

# --- Initialize Main Site (If not exists) ---
def init_system():
    if sites_col.count_documents({"slug": "main"}) == 0:
        sites_col.insert_one({
            "slug": "main",
            "site_name": "Movie Master",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "Welcome to the world of unlimited movies!",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action", "Hindi", "English", "Bangla"],
            "tmdb_key": "",
            "bot_token": "",
            "channel_id": "",
            "channel_username": ""
        })

init_system()

# --- Movie Data Fetcher (TMDB) ---
def get_tmdb_data(tmdb_id, api_key):
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}?api_key={api_key}&append_to_response=credits"
        res = requests.get(url).json()
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

# --- Master UI Function (To avoid TemplateNotFound Error) ---
def master_render(content_html, site, **kwargs):
    master_html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{{{ site.site_name }}}}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <style>
            body {{ background: #0b0f19; color: #f8fafc; font-family: sans-serif; }}
            .glass {{ background: rgba(17, 24, 39, 0.8); backdrop-filter: blur(12px); border-bottom: 1px solid rgba(255,255,255,0.1); }}
            .card {{ background: #111827; border: 1px solid rgba(255,255,255,0.05); transition: 0.3s; }}
            .card:hover {{ transform: translateY(-5px); border-color: #3b82f6; }}
        </style>
    </head>
    <body>
        <div class="bg-blue-600 text-white text-center py-2 text-[10px] md:text-sm font-bold px-4">
            {{{{ site.header_notice }}}}
        </div>
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-3 flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-emerald-600 hover:bg-emerald-700 text-white px-3 py-1.5 rounded-lg text-[10px] font-black uppercase">➕ Clone</a>
                    <a href="/s/{{{{site.slug}}}}" class="flex items-center gap-2">
                        <img src="{{{{ site.logo_url }}}}" class="h-7 md:h-9">
                        <span class="text-lg md:text-xl font-black tracking-tighter">{{{{ site.site_name }}}}</span>
                    </a>
                </div>
                <div class="flex items-center gap-4">
                    <div class="hidden lg:flex gap-6 text-sm font-semibold">
                        {{% for c in site.categories %}}
                        <a href="/s/{{{{site.slug}}}}?cat={{{{c.strip()}}}}" class="hover:text-blue-400">{{{{c.strip()}}}}</a>
                        {{% endfor %}}
                    </div>
                    <a href="/s/{{{{site.slug}}}}/admin" class="bg-slate-800 px-3 py-1.5 rounded-xl text-[10px] font-bold border border-white/10">ADMIN</a>
                </div>
            </div>
        </nav>
        <div class="container mx-auto px-4 py-8">
            {content_html}
        </div>
    </body>
    </html>
    """
    return render_template_string(master_html, site=site, **kwargs)

# --- Routes ---

@app.route('/')
def go_home():
    return redirect('/s/main')

@app.route('/s/<slug>')
def home_page(slug):
    site = sites_col.find_one({"slug": slug})
    if not site: return "Site Not Found", 404
    cat = request.args.get('cat')
    query = {"site_slug": slug}
    if cat: query["category"] = cat
    movies = list(movies_col.find(query).sort('_id', -1))
    
    html = """
    <h2 class="text-2xl font-bold mb-8 flex items-center gap-3"><span class="w-1.5 h-8 bg-blue-600 rounded-full"></span> {{ request.args.get('cat', 'Latest Movies') }}</h2>
    <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
        {% for m in movies %}
        <a href="/s/{{site.slug}}/movie/{{m._id}}" class="card rounded-2xl overflow-hidden group">
            <img src="{{m.poster}}" class="h-64 w-full object-cover group-hover:scale-105 transition duration-500">
            <div class="p-3 text-center">
                <h3 class="text-xs font-bold truncate group-hover:text-blue-400">{{m.title}}</h3>
                <p class="text-[10px] text-slate-500 mt-1 uppercase">{{m.category}}</p>
            </div>
        </a>
        {% endfor %}
    </div>
    """
    return master_render(html, site, movies=movies)

@app.route('/s/<slug>/movie/<id>')
def movie_details(slug, id):
    site = sites_col.find_one({"slug": slug})
    m = movies_col.find_one({"_id": ObjectId(id)})
    html = """
    <div class="flex flex-col lg:flex-row gap-10">
        <div class="w-full lg:w-1/3 shrink-0"><img src="{{m.poster}}" class="rounded-3xl shadow-2xl w-full"></div>
        <div class="flex-1">
            <h1 class="text-4xl md:text-6xl font-black">{{m.title}} ({{m.year}})</h1>
            <p class="mt-4 text-slate-400 text-lg leading-relaxed">{{m.description}}</p>
            <div class="mt-10 grid gap-3">
                <h3 class="text-xl font-bold">Download Now:</h3>
                {% for f in m.files %}
                <a href="https://t.me/{{site.channel_username}}/{{f.msg_id}}" target="_blank" class="bg-blue-600 hover:bg-blue-700 p-4 rounded-2xl font-bold text-center">📥 {{f.quality}}</a>
                {% endfor %}
            </div>
        </div>
    </div>
    """
    return master_render(html, site, m=m)

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_center():
    site = sites_col.find_one({"slug": "main"})
    if request.method == 'POST':
        name = request.form.get('name')
        slug = re.sub(r'[^a-z0-9]', '-', name.lower())
        if sites_col.find_one({"slug": slug}):
            flash("Name already taken!")
        else:
            sites_col.insert_one({
                "slug": slug, "site_name": name, "logo_url": site['logo_url'],
                "header_notice": "Welcome to " + name,
                "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
                "categories": ["Action", "Hindi"], "tmdb_key": "", "bot_token": "", "channel_id": "", "channel_username": ""
            })
            return f"<h1>Success! Site: /s/{slug} | Admin: admin | Pass: admin123</h1><a href='/s/{slug}/admin'>Go to Login</a>"
            
    html = """
    <div class="max-w-md mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5 shadow-2xl">
        <h2 class="text-3xl font-black mb-6 text-center text-emerald-500">Clone Movie Site</h2>
        <form method="POST" class="space-y-4">
            <input name="name" placeholder="Enter Site Name" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none" required>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Start My Site</button>
        </form>
    </div>
    """
    return master_render(html, site)

@app.route('/s/<slug>/admin', methods=['GET', 'POST'])
def admin_login(slug):
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == site['admin_user'] and check_password_hash(site['admin_pass'], p):
            session[f'admin_{slug}'] = True
            return redirect(f'/s/{slug}/dashboard')
    html = """
    <div class="max-w-sm mx-auto bg-slate-900 p-8 rounded-3xl border border-white/5">
        <h2 class="text-2xl font-black mb-6 text-center">Admin Login</h2>
        <form method="POST" class="space-y-4">
            <input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
            <input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none">
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase">Login</button>
        </form>
    </div>
    """
    return master_render(html, site)

@app.route('/s/<slug>/dashboard', methods=['GET', 'POST'])
def admin_dashboard(slug):
    if not session.get(f'admin_{slug}'): return redirect(f'/s/{slug}/admin')
    site = sites_col.find_one({"slug": slug})
    if request.method == 'POST':
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
        return redirect(f'/s/{slug}/dashboard')

    movies = list(movies_col.find({"site_slug": slug}))
    html = """
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-xl font-bold mb-6">Settings</h2>
            <form method="POST" class="space-y-3 text-sm">
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
                <input name="new_pass" type="password" placeholder="New Password (Keep blank to skip)" class="w-full bg-black/40 p-3 rounded-xl border border-white/5">
                <button class="w-full bg-blue-600 py-3 rounded-xl font-bold uppercase">Update Site</button>
            </form>
        </div>
        <div class="bg-slate-900 p-8 rounded-3xl border border-white/5">
            <h2 class="text-xl font-bold mb-6">Manage Movies</h2>
            {% for m in movies %}
            <div class="flex justify-between items-center p-3 bg-black/20 rounded-xl mb-2">
                <span class="text-xs truncate w-48 font-bold text-slate-400">{{m.title}}</span>
                <a href="/s/{{site.slug}}/delete/{{m._id}}" class="text-red-500 text-[10px] font-bold">DELETE</a>
            </div>
            {% endfor %}
        </div>
    </div>
    """
    return master_render(html, site, movies=movies)

@app.route('/s/<slug>/delete/<id>')
def delete_movie(slug, id):
    if not session.get(f'admin_{slug}'): return redirect(f'/s/{slug}/admin')
    movies_col.delete_one({"_id": ObjectId(id), "site_slug": slug})
    return redirect(f'/s/{slug}/dashboard')

# --- Telegram Bot Logic ---
def start_bot():
    main_site = sites_col.find_one({"slug": "main"})
    if not main_site or not main_site.get('bot_token'): return
    try:
        bot = telebot.TeleBot(main_site['bot_token'])
        bot_states = {}

        @bot.message_handler(commands=['post'])
        def handle_post(message):
            args = message.text.split(' ', 2)
            if len(args) < 3:
                bot.reply_to(message, "Use: `/post [slug] [name]`")
                return
            slug, query = args[1], args[2]
            site = sites_col.find_one({"slug": slug})
            if not site: return
            res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={site['tmdb_key']}&query={query}").json()
            results = res.get('results', [])[:5]
            markup = telebot.types.InlineKeyboardMarkup()
            for m in results:
                markup.add(telebot.types.InlineKeyboardButton(m['title'], callback_data=f"sl_{slug}_{m['id']}"))
            bot.reply_to(message, "Select:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('sl_'))
        def sel_movie(call):
            _, slug, tmdb_id = call.data.split('_')
            site = sites_col.find_one({"slug": slug})
            data = get_tmdb_data(tmdb_id, site['tmdb_key'])
            bot_states[call.from_user.id] = {"data": data, "slug": slug, "files": [], "step": "cat"}
            markup = telebot.types.InlineKeyboardMarkup()
            for c in site['categories']:
                markup.add(telebot.types.InlineKeyboardButton(c, callback_data=f"ct_{slug}_{c.strip()}"))
            bot.send_message(call.message.chat.id, "Category:", reply_markup=markup)

        @bot.callback_query_handler(func=lambda call: call.data.startswith('ct_'))
        def sel_cat(call):
            _, slug, cat = call.data.split('_')
            bot_states[call.from_user.id]['category'] = cat
            bot_states[call.from_user.id]['step'] = 'file'
            bot.send_message(call.message.chat.id, "Send Video/File. Then send /done")

        @bot.message_handler(content_types=['video', 'document'], func=lambda m: bot_states.get(m.from_user.id, {}).get('step') == 'file')
        def get_file(message):
            state = bot_states[message.from_user.id]
            site = sites_col.find_one({"slug": state['slug']})
            fwd = bot.forward_message(site['channel_id'], message.chat.id, message.message_id)
            name = message.video.file_name if message.video else message.document.file_name
            state['files'].append({"quality": name if name else "Download", "msg_id": fwd.message_id})
            bot.reply_to(message, "Saved. /done to finish.")

        @bot.message_handler(commands=['done'], func=lambda m: bot_states.get(m.from_user.id, {}).get('step') == 'file')
        def finish(message):
            state = bot_states[message.from_user.id]
            movies_col.insert_one({**state['data'], "category": state['category'], "files": state['files'], "site_slug": state['slug']})
            bot.send_message(message.chat.id, "🚀 Published!")
            del bot_states[message.from_user.id]

        bot.infinity_polling()
    except: pass

if __name__ == '__main__':
    threading.Thread(target=start_bot, daemon=True).start()
    app.run(host='0.0.0.0', port=5000)
