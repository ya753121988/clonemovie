import os, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "ultimate_premium_movie_standalone_v30"

# --- ডাটাবেস কানেকশন (এডমিন প্যানেল থেকে চেঞ্জ করা যাবে) ---
# প্রথমবার রান করার জন্য ডিফল্ট মংগোডিবি
DEFAULT_MONGO = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(DEFAULT_MONGO)
db = client['movie_standalone_db']
settings_col = db['settings']
movies_col = db['movies']
files_col = db['stored_files']
bot_states = db['bot_states']

# --- সিস্টেম ইনিশিয়াল সেটিংস (ডিফল্ট) ---
def init_settings():
    if settings_col.count_documents({}) == 0:
        settings_col.insert_one({
            "site_name": "Premium Movie Hub 🎥",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "🔥 স্বাগতম! সরাসরি টেলিগ্রাম বটের মাধ্যমে মুভি ডাউনলোড করুন। 🔥",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action 💥", "Hindi 🍿", "English 🇺🇸", "Bangla 🇧🇩"],
            "tmdb_key": "275aff9f1c570308fa10d14c6f49f998",
            "bot_token": "",
            "bot_username": "",
            "ads": {
                "banner_ad": "", "popunder": "", "native_banner": "",
                "social_bar": "", "header_ad": "", "footer_ad": ""
            }
        })
init_settings()

# --- প্রিমিয়াম ডাইনামিক লেআউট (রেসপন্সিভ মোড অটো) ---
def render_premium(content, settings, movies=None):
    ads = settings.get('ads', {})
    cats = settings.get('categories', [])
    cat_html = "".join([f'<a href="/?cat={c.strip()}" class="hover:text-blue-400 transition whitespace-nowrap">{c.strip()}</a>' for c in cats])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{settings['site_name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body {{ background: #080a10; color: #f1f5f9; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
            .glass {{ background: rgba(15, 23, 42, 0.9); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: 0.4s cubic-bezier(0.4, 0, 0.2, 1); }}
            .card:hover {{ transform: scale(1.05); border-color: #3b82f6; box-shadow: 0 10px 40px -10px rgba(59, 130, 246, 0.5); }}
            .swiper-slide img {{ height: 50vh; width: 100%; object-fit: cover; border-radius: 20px; filter: brightness(0.4); }}
            @media (max-width: 768px) {{ .swiper-slide img {{ height: 35vh; }} }}
            .search-box {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); }}
        </style>
        {ads.get('popunder', '')}
        {ads.get('social_bar', '')}
    </head>
    <body>
        {ads.get('header_ad', '')}
        <div class="bg-blue-700 text-white text-center py-2 text-[10px] md:text-sm font-black uppercase tracking-tighter px-4 shadow-lg">{settings['header_notice']}</div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-3 flex justify-between items-center">
                <div class="flex items-center gap-3 md:gap-6">
                    <a href="/clone-site" class="bg-gradient-to-r from-emerald-600 to-green-500 text-white px-3 py-1.5 rounded-lg text-[10px] font-black shadow-lg">🚀 CLONE</a>
                    <a href="/" class="flex items-center gap-2">
                        <img src="{settings['logo_url']}" class="h-8 md:h-10">
                        <span class="text-xl md:text-2xl font-black text-white tracking-tighter hidden sm:block">{settings['site_name']}</span>
                    </a>
                </div>

                <div class="flex items-center gap-2 md:gap-5">
                    <form action="/search" method="GET" class="flex items-center search-box rounded-full px-4 py-1.5">
                        <input name="q" placeholder="Search..." class="bg-transparent outline-none text-xs w-24 md:w-48 text-white">
                        <button type="submit">🔍</button>
                    </form>
                    <div class="hidden lg:flex gap-6 text-[11px] font-black uppercase tracking-widest">{cat_html}</div>
                    <a href="/admin" class="bg-slate-800 hover:bg-blue-600 px-4 py-1.5 rounded-full text-[10px] font-black border border-white/10 transition-all shadow-xl">ADMIN ⚙️</a>
                </div>
            </div>
        </nav>

        <div class="container mx-auto px-4 py-8">
            <div class="flex justify-center mb-6">{ads.get('banner_ad', '')}</div>
            {content}
            <div class="mt-12 flex justify-center">{ads.get('footer_ad', '')}</div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>
            const swiper = new Swiper('.swiper', {{ autoplay: {{ delay: 4000 }}, loop: true, pagination: {{ el: '.swiper-pagination', clickable: true }} }});
        </script>
        {ads.get('native_banner', '')}
    </body>
    </html>
    """
    return render_template_string(html)

# --- Routes: Frontend ---

@app.route('/')
@app.route('/search')
def home():
    settings = settings_col.find_one({})
    q = request.args.get('q')
    cat = request.args.get('cat')
    query = {"category": cat} if cat else {}
    if q: query["title"] = {"$regex": q, "$options": "i"}
    
    movies = list(movies_col.find(query).sort('_id', -1))
    sliders = movies[:6]

    slider_html = ""
    if sliders and not cat and not q:
        slider_html = '<div class="swiper mb-12 overflow-hidden rounded-[30px] shadow-2xl relative border border-white/5"><div class="swiper-wrapper">'
        for s in sliders:
            slider_html += f"""
            <div class="swiper-slide relative">
                <img src="{s['banner']}">
                <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                <div class="absolute bottom-6 md:bottom-12 left-6 md:left-12 text-left">
                    <h2 class="text-3xl md:text-7xl font-black text-white uppercase tracking-tighter mb-4 shadow-black">{s['title']}</h2>
                    <a href="/movie/{s['_id']}" class="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-full font-black text-xs md:text-sm inline-block shadow-2xl transition">⚡ WATCH DETAILS</a>
                </div>
            </div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'

    grid_title = q if q else (cat if cat else "Recently Uploaded 🍿")
    grid_html = f'<h2 class="text-2xl md:text-3xl font-black mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest text-blue-500">{grid_title}</h2>'
    grid_html += '<div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-8">'
    for m in movies:
        grid_html += f"""
        <a href="/movie/{m['_id']}" class="card rounded-3xl overflow-hidden group">
            <div class="relative overflow-hidden">
                <img src="{m['poster']}" class="h-64 md:h-80 w-full object-cover group-hover:scale-110 transition duration-500">
                <div class="absolute top-2 right-2 bg-black/80 px-2 py-1 rounded-lg text-[9px] font-black tracking-widest">⭐ {m.get('rating', '0.0')}</div>
            </div>
            <div class="p-4 text-center">
                <h3 class="text-[11px] font-black truncate uppercase text-slate-100 group-hover:text-blue-500 transition">{m['title']}</h3>
                <p class="text-[10px] text-slate-500 mt-1 font-bold uppercase">{m['year']} | {m['category']}</p>
            </div>
        </a>"""
    grid_html += '</div>'
    return render_premium(slider_html + grid_html, settings)

@app.route('/movie/<id>')
def movie_details(id):
    settings = settings_col.find_one({})
    m = movies_col.find_one({"_id": ObjectId(id)})
    if not m: return "Movie Not Found", 404
    
    links = "".join([f'<a href="https://t.me/{settings["bot_username"]}?start={f["file_ref"]}" target="_blank" class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-black transition shadow-2xl group border-b-4 border-blue-900 active:border-0 uppercase tracking-tighter"><span>📥 DOWNLOAD {f["quality"]}</span><span class="text-[10px] bg-black/20 px-3 py-1 rounded-full">Bot Server</span></a>' for f in m['files']])

    content = f"""
    <div class="flex flex-col lg:flex-row gap-12 mt-4">
        <div class="w-full lg:w-1/3 shrink-0"><img src="{m['poster']}" class="rounded-[40px] shadow-2xl w-full border border-white/10 sticky top-24"></div>
        <div class="flex-1">
            <h1 class="text-4xl md:text-8xl font-black text-white leading-tight uppercase tracking-tighter">{m['title']}</h1>
            <div class="flex flex-wrap gap-4 mt-8">
                <span class="bg-blue-600 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">📂 {m['category']}</span>
                <span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-yellow-500 shadow-xl">⭐ {m['rating']} / 10</span>
                <span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['year']}</span>
            </div>
            <div class="mt-10 p-8 bg-slate-900/50 rounded-3xl border border-white/5 shadow-inner">
                <h3 class="text-blue-500 font-black text-xs uppercase mb-4 tracking-widest">Full Storyline 📖</h3>
                <p class="text-slate-400 text-lg md:text-xl leading-relaxed italic font-medium">"{m['plot']}"</p>
            </div>
            <div class="mt-8 grid md:grid-cols-2 gap-6 text-[13px]">
                <div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🎬 Director</b> {m.get('director', 'Unknown')}</div>
                <div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🌟 Starring Cast</b> {m.get('cast', 'Unknown')}</div>
            </div>
            <div class="mt-12 space-y-4">
                <h2 class="text-3xl font-black uppercase tracking-tighter mb-6 flex items-center gap-3">📥 Download Options 📥</h2>
                <div class="grid gap-4">{links}</div>
            </div>
        </div>
    </div>"""
    return render_premium(content, settings)

# --- Routes: Admin Panel ---

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    settings = settings_col.find_one({})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == settings['admin_user'] and check_password_hash(settings['admin_pass'], p):
            session['is_admin'] = True
            return redirect('/dashboard')
        flash("❌ পাসওয়ার্ড ভুল!")
    return render_premium("""<div class="max-w-sm mx-auto bg-slate-900 p-10 rounded-[40px] border border-blue-500 shadow-2xl mt-10 text-center"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">Admin Area ⚙️</h2><form method="POST" class="space-y-4"><input name="user" placeholder="Admin Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white"><input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white"><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Authenticate</button></form></div>""", settings)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if not session.get('is_admin'): return redirect('/admin')
    settings = settings_col.find_one({})
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save":
            new_pass = request.form.get('new_pass')
            upd = {
                "site_name": request.form.get('site_name'), "logo_url": request.form.get('logo_url'),
                "header_notice": request.form.get('header_notice'), "admin_user": request.form.get('admin_user'),
                "tmdb_key": request.form.get('tmdb_key'), "bot_token": request.form.get('bot_token'),
                "bot_username": request.form.get('bot_username').replace('@',''),
                "categories": request.form.get('categories').split(','),
                "ads": {
                    "banner_ad": request.form.get('banner_ad'), "popunder": request.form.get('popunder'),
                    "native_banner": request.form.get('native_banner'), "social_bar": request.form.get('social_bar'),
                    "header_ad": request.form.get('header_ad'), "footer_ad": request.form.get('footer_ad')
                }
            }
            if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
            settings_col.update_one({}, {"$set": upd})
            flash("✅ সব সেটিংস সেভ হয়েছে!")
        elif action == "set_webhook":
            webhook_url = f"https://{request.host}/telegram-webhook"
            r = requests.get(f"https://api.telegram.org/bot{settings['bot_token']}/setWebhook?url={webhook_url}")
            flash(f"বট স্ট্যাটাস: {r.json().get('description')}")
        return redirect('/dashboard')

    q = request.args.get('dq')
    mq = {"title": {"$regex": q, "$options": "i"}} if q else {}
    movies = list(movies_col.find(mq).sort('_id', -1))
    movies_list = "".join([f'<div class="flex items-center justify-between bg-black/40 p-4 rounded-2xl border border-white/5 mb-3 shadow-lg"><div class="flex items-center gap-4"><img src="{m["poster"]}" class="h-10 w-8 rounded-lg object-cover"><span class="text-xs font-black truncate w-32 md:w-60 uppercase">{m["title"]}</span></div><div class="flex gap-2"><a href="/edit-movie/{m["_id"]}" class="bg-blue-600 px-3 py-1 rounded text-[9px] font-black uppercase">Edit</a><a href="/delete/{m["_id"]}" class="bg-red-600 px-3 py-1 rounded text-[9px] font-black uppercase" onclick="return confirm(\'Delete?\')">Delete</a></div></div>' for m in movies])

    content = f"""
    <div class="grid lg:grid-cols-2 gap-10">
        <div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl">
            <h2 class="text-xl font-black mb-6 uppercase text-blue-500 flex items-center gap-2">🛠️ System Configuration</h2>
            <form method="POST" class="space-y-4 text-[10px] font-black uppercase tracking-widest">
                <input type="hidden" name="action" value="save">
                <div class="grid grid-cols-2 gap-4"><input name="site_name" value="{settings['site_name']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none">
                <input name="logo_url" value="{settings['logo_url']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none"></div>
                <input name="header_notice" value="{settings['header_notice']}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none">
                <div class="grid grid-cols-2 gap-4"><input name="tmdb_key" value="{settings['tmdb_key']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none">
                <input name="bot_token" value="{settings['bot_token']}" placeholder="Bot Token" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none"></div>
                <div class="grid grid-cols-2 gap-4"><input name="bot_username" value="{settings['bot_username']}" placeholder="Bot Username" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none">
                <input name="categories" value="{','.join(settings['categories'])}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none"></div>
                <h3 class="text-emerald-500 mt-4 underline">Ad Management 💰</h3>
                <div class="grid grid-cols-2 gap-4">
                    <textarea name="banner_ad" placeholder="Banner Ad Code" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{settings.get('ads',{}).get('banner_ad','')}</textarea>
                    <textarea name="popunder" placeholder="Popunder Ad Code" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{settings.get('ads',{}).get('popunder','')}</textarea>
                    <textarea name="header_ad" placeholder="Header Ad Code" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{settings.get('ads',{}).get('header_ad','')}</textarea>
                    <textarea name="footer_ad" placeholder="Footer Ad Code" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{settings.get('ads',{}).get('footer_ad','')}</textarea>
                </div>
                <div class="p-6 bg-blue-600/10 rounded-[30px] border border-blue-600/20 mt-4">
                    <label class="text-blue-400 block mb-2">Admin Security Panel</label>
                    <input name="admin_user" value="{settings['admin_user']}" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 mb-2">
                    <input name="new_pass" type="password" placeholder="Set New Password" class="w-full bg-black/60 p-4 rounded-xl border border-white/10">
                </div>
                <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Save Master Settings</button>
            </form>
            <form method="POST" class="mt-4"><input type="hidden" name="action" value="set_webhook"><button class="w-full bg-emerald-600 py-3 rounded-xl font-black uppercase text-[10px] shadow-lg">🛠️ Auto Connect Bot Webhook</button></form>
        </div>
        <div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl h-[950px] overflow-y-auto">
            <h2 class="text-xl font-black mb-6 uppercase text-emerald-500">🎬 Manage Movies</h2>
            <form action="/dashboard" method="GET" class="mb-4 flex gap-2"><input name="dq" placeholder="Search by title..." class="w-full bg-black/40 p-3 rounded-xl border border-white/10 outline-none text-xs text-white"><button class="bg-blue-600 px-4 rounded-xl font-black text-xs uppercase">Filter</button></form>
            {movies_list}
        </div>
    </div>"""
    return render_premium(content, settings)

@app.route('/edit-movie/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('is_admin'): return redirect('/admin')
    settings = settings_col.find_one({})
    m = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        upd = {"title": request.form.get('title'), "year": request.form.get('year'), "rating": request.form.get('rating'), "plot": request.form.get('plot'), "category": request.form.get('category')}
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": upd})
        flash("✅ মুভি আপডেট হয়েছে!")
        return redirect('/dashboard')
    
    content = f"""
    <div class="max-w-2xl mx-auto bg-slate-900 p-10 rounded-[40px] border border-white/5 shadow-2xl mt-4">
        <h2 class="text-2xl font-black mb-8 uppercase text-blue-500">Edit Movie Entry 🎬</h2>
        <form method="POST" class="space-y-4 font-black uppercase text-[11px]">
            <input name="title" value="{m['title']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white">
            <div class="grid grid-cols-2 gap-4">
                <input name="year" value="{m['year']}" class="bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white">
                <input name="rating" value="{m['rating']}" class="bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white">
            </div>
            <input name="category" value="{m['category']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white">
            <textarea name="plot" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 h-48 text-white">{m['plot']}</textarea>
            <button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Save Changes</button>
        </form>
    </div>"""
    return render_premium(content, settings)

@app.route('/delete/<id>')
def delete_movie(id):
    if not session.get('is_admin'): return redirect('/admin')
    movies_col.delete_one({"_id": ObjectId(id)})
    flash("🗑️ মুভি মুছে ফেলা হয়েছে!")
    return redirect('/dashboard')

# --- Standalone Cloning (নিজেস্ব ডাটাবেস সাপোর্ট) ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    settings = settings_col.find_one({})
    if request.method == 'POST':
        name = request.form.get('name')
        db_uri = request.form.get('db_uri')
        return f'<div style="background:#000;color:#fff;padding:50px;text-align:center;font-family:sans-serif;"><h1>✅ সাইট রেডি!</h1><p>আপনার নাম: {name}</p><p>মংগোডিবি: {db_uri}</p><p>এখন আপনার গিটহাবে এই URI দিয়ে নতুন একটি ডেপ্লয়মেন্ট করুন।</p></div>'
    
    content = f"""
    <div class="max-w-md mx-auto bg-slate-900 p-12 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-10">
        <h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase tracking-tighter italic">Network Cloner 🚀</h2>
        <p class="text-slate-500 text-xs mb-8 uppercase font-bold tracking-widest">নতুন সাইট খুলতে আপনার নাম ও নিজস্ব MongoDB URI দিন।</p>
        <form method="POST" class="space-y-6">
            <input name="name" placeholder="আপনার মুভি সাইটের নাম" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 outline-none text-center font-bold text-white" required>
            <input name="db_uri" placeholder="নতুন MongoDB URI দিন" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 outline-none text-center text-xs text-white" required>
            <button class="w-full bg-emerald-600 hover:bg-emerald-700 py-5 rounded-3xl font-black uppercase tracking-widest shadow-xl transition-all">Launch Independent Site</button>
        </form>
    </div>"""
    return render_premium(content, settings)

# --- টেলিগ্রাম ওয়েবহুক লজিক (নিখুঁত ফাইল ডেলিভারি) ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    settings = settings_col.find_one({})
    if not settings or not settings.get('bot_token'): return ''
    bot = telebot.TeleBot(settings['bot_token'], threaded=False)
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))

    # ১. ইউজারকে ফাইল পাঠানো
    @bot.message_handler(commands=['start'])
    def handle_start(m):
        params = m.text.split()
        if len(params) > 1:
            file_ref = params[1]
            stored = files_col.find_one({"_id": ObjectId(file_ref)})
            if stored:
                bot.send_document(m.chat.id, stored['file_id'], caption=f"🎥 মুভি: *{stored['file_name']}*\n\n🔥 Enjoy your movie! 🔥", parse_mode="Markdown")
            else:
                bot.send_message(m.chat.id, "❌ দুঃখিত! ফাইলটি ডাটাবেসে পাওয়া যায়নি।")
        else:
            bot.send_message(m.chat.id, f"🎬 স্বাগতম! আমি {settings['site_name']} এর অফিশিয়াল ফাইল স্টোর বট। ওয়েবসাইটে মুভি খুঁজে ডাউনলোড বাটনে ক্লিক করুন।", parse_mode="Markdown")

    # ২. অ্যাডমিন মুভি পোস্ট করা
    @bot.message_handler(commands=['post'])
    def handle_post(m):
        query = m.text.replace('/post', '').strip()
        if not query: return bot.reply_to(m, "ব্যবহার: `/post Avatar`", parse_mode="Markdown")
        try:
            res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={settings['tmdb_key']}&query={query}").json()
            results = res.get('results', [])[:5]
            if not results: return bot.reply_to(m, "❌ TMDB-তে কোনো মুভি পাওয়া যায়নি।")
            markup = telebot.types.InlineKeyboardMarkup()
            for r in results:
                markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{r['id']}"))
            bot.reply_to(m, "🎬 নিচের তালিকা থেকে সঠিক মুভিটি সিলেক্ট করুন:", reply_markup=markup)
        except Exception as e: bot.reply_to(m, f"Error: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_selection(c):
        tid = c.data.split('_')[1]
        try:
            url = f"https://api.themoviedb.org/3/movie/{tid}?api_key={settings['tmdb_key']}&append_to_response=credits"
            r = requests.get(url).json()
            cast = ", ".join([x['name'] for x in r.get('credits', {}).get('cast', [])[:8]])
            director = next((x['name'] for x in r.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")
            info = {"title": r['title'], "year": r.get('release_date','0000')[:4], "plot": r.get('overview',''), "rating": r.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": cast, "director": director}
            bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "files": [], "step": "cat"}}, upsert=True)
            markup = telebot.types.InlineKeyboardMarkup()
            for cat in settings['categories']:
                markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{cat.strip()}"))
            bot.send_message(c.message.chat.id, "✅ মুভি ডিটেইলস পাওয়া গেছে। ক্যাটাগরি সিলেক্ট করুন:", reply_markup=markup)
        except Exception as e: bot.send_message(c.message.chat.id, f"Error: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
    def handle_cat(c):
        cat = c.data.split('_')[1]
        bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"category": cat, "step": "file"}})
        bot.send_message(c.message.chat.id, f"✅ ক্যাটাগরি: {cat}।\n\nএখন আপনার মুভি ফাইলটি (Video/File) এখানে পাঠান। শেষ হলে /done লিখুন।")

    @bot.message_handler(content_types=['video', 'document', 'audio'])
    def handle_files(m):
        state = bot_states.find_one({"user_id": m.from_user.id})
        if not state or state.get('step') != 'file': return
        fid = m.video.file_id if m.video else (m.document.file_id if m.document else m.audio.file_id)
        fname = m.video.file_name if m.video else (m.document.file_name if m.document else "Download")
        ref_id = files_col.insert_one({"file_id": fid, "file_name": fname}).inserted_id
        bot_states.update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": fname, "file_ref": str(ref_id)}}})
        bot.reply_to(m, "📥 ফাইলটি ডাটাবেসে সেভ হয়েছে! আরও পাঠান অথবা /done লিখে সাইটে পাবলিশ করুন।")

    @bot.message_handler(commands=['done'])
    def handle_publish(m):
        state = bot_states.find_one({"user_id": m.from_user.id})
        if not state: return
        movies_col.insert_one({**state['info'], "category": state['category'], "files": state['files']})
        bot.send_message(m.chat.id, "🚀 অভিনন্দন! মুভিটি সরাসরি ওয়েবসাইটে পাবলিশ হয়েছে।")
        bot_states.delete_one({"user_id": m.from_user.id})

    bot.process_new_updates([update])
    return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
