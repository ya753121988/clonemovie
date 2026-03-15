import os, requests, telebot, re, time, threading
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask Initial Setup ---
app = Flask(__name__)
app.secret_key = "ultimate_premium_standalone_standalone_v1000"

# --- MongoDB Connection ---
# মূল ডাটাবেস যা থেকে মেইন সাইট চলে
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['movie_standalone_mega_db']
settings_col = db['settings']
movies_col = db['movies']
files_col = db['stored_files']
bot_states = db['bot_states']

# --- Initialize Default Settings (সব ফিচার সহ) ---
def init_settings():
    if settings_col.count_documents({}) == 0:
        settings_col.insert_one({
            "site_name": "Premium Movie Hub 🍿",
            "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
            "header_notice": "🔥 স্বাগতম! সরাসরি টেলিগ্রাম ফাইল স্টোর বটের মাধ্যমে মুভি ডাউনলোড করুন। 🔥",
            "admin_user": "admin",
            "admin_pass": generate_password_hash("admin123"),
            "categories": ["Action 💥", "Hindi 🍿", "English 🇺🇸", "Bangla 🇧🇩", "Dual Audio 🔊"],
            "tmdb_key": "275aff9f1c570308fa10d14c6f49f998",
            "bot_token": "",
            "bot_username": "",
            "auto_delete_min": 0,
            "restrict_forward": False,
            "ads": {
                "banner_ad": "", "popunder": "", "social_bar": "", 
                "header_ad": "", "footer_ad": "", "native_banner": ""
            }
        })
init_settings()

# --- Helper: কোয়ালিটি ডিটেকশন ---
def extract_quality(filename):
    qualities = ['2160p', '1440p', '1080p', '720p', '480p', '360p', '4K', 'BluRay', 'WEB-DL', 'HDRip']
    for q in qualities:
        if q.lower() in filename.lower():
            return q.upper()
    return "Download"

# --- Premium Layout Engine (Auto Responsive) ---
def render_site(body_html, settings):
    ads = settings.get('ads', {})
    cats = settings.get('categories', [])
    cat_links = "".join([f'<a href="/?cat={c.strip()}" class="hover:text-blue-500 transition whitespace-nowrap">{c.strip()}</a>' for c in cats])
    
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
            .glass {{ background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: 0.4s; }}
            .card:hover {{ transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 0 30px rgba(59, 130, 246, 0.4); }}
            .swiper-slide img {{ height: 500px; width: 100%; object-fit: cover; border-radius: 30px; filter: brightness(0.4); }}
            @media (max-width: 768px) {{ .swiper-slide img {{ height: 320px; }} }}
            .copy-box {{ background: rgba(0,0,0,0.5); padding: 15px; border-radius: 15px; border: 1px dashed #10b981; margin-bottom: 15px; cursor: pointer; position: relative; }}
            .copy-box:active {{ transform: scale(0.98); }}
        </style>
        {ads.get('popunder', '')} {ads.get('social_bar', '')}
    </head>
    <body>
        {ads.get('header_ad', '')}
        <div class="bg-blue-700 text-white text-center py-2 text-[10px] md:text-sm font-black uppercase px-4 shadow-lg">{settings['header_notice']}</div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-3 flex justify-between items-center text-white">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-gradient-to-r from-emerald-600 to-green-500 px-3 py-1.5 rounded-lg text-[10px] font-black uppercase shadow-lg">🚀 CLONE</a>
                    <a href="/" class="flex items-center gap-2">
                        <img src="{settings['logo_url']}" class="h-8 md:h-10 rounded">
                        <span class="text-xl md:text-2xl font-black tracking-tighter hidden sm:block">{settings['site_name']}</span>
                    </a>
                </div>
                <div class="flex items-center gap-4">
                    <form action="/search" method="GET" class="hidden md:flex bg-black/50 rounded-full px-4 py-1 border border-white/10">
                        <input name="q" placeholder="Search movies..." class="bg-transparent outline-none text-xs text-white w-40">
                    </form>
                    <div class="hidden lg:flex gap-6 text-[11px] font-black uppercase tracking-widest">{cat_links}</div>
                    <a href="/admin" class="bg-slate-800 hover:bg-blue-600 px-4 py-1.5 rounded-full text-[10px] font-bold transition border border-white/10">ADMIN ⚙️</a>
                </div>
            </div>
        </nav>

        <div class="container mx-auto px-4 py-8">
            <div class="flex justify-center mb-8">{ads.get('banner_ad', '')}</div>
            {body_html}
            <div class="mt-12 flex justify-center">{ads.get('footer_ad', '')}</div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>
            const swiper = new Swiper('.swiper', {{ autoplay: {{ delay: 4000 }}, loop: true, pagination: {{ el: '.swiper-pagination', clickable: true }} }});
            function copyToClipboard(id) {{
                var text = document.getElementById(id).innerText;
                navigator.clipboard.writeText(text);
                alert("Copied to Clipboard! ✅");
            }}
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
    q, cat = request.args.get('q'), request.args.get('cat')
    query = {"category": cat} if cat else {}
    if q: query["title"] = {"$regex": q, "$options": "i"}
    
    movies = list(movies_col.find(query).sort('_id', -1))
    sliders = movies[:6]

    slider_html = ""
    if sliders and not cat and not q:
        slider_html = '<div class="swiper mb-12 overflow-hidden rounded-[40px] shadow-2xl relative border border-white/5"><div class="swiper-wrapper">'
        for s in sliders:
            slider_html += f"""
            <div class="swiper-slide relative">
                <img src="{s['banner']}">
                <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div>
                <div class="absolute bottom-10 left-6 md:left-12 text-left">
                    <h2 class="text-3xl md:text-7xl font-black text-white uppercase tracking-tighter mb-4">{s['title']}</h2>
                    <a href="/movie/{s['_id']}" class="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-full font-black text-xs md:text-sm inline-block shadow-lg transition">VIEW DETAILS</a>
                </div>
            </div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'

    title = q if q else (cat if cat else "Latest Movies 🍿")
    grid_html = f'<h2 class="text-2xl md:text-3xl font-black mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest text-blue-500">{title}</h2><div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-8">'
    for m in movies:
        grid_html += f"""
        <a href="/movie/{m['_id']}" class="card rounded-3xl overflow-hidden group">
            <div class="relative overflow-hidden">
                <img src="{m['poster']}" class="h-64 md:h-80 w-full object-cover group-hover:scale-110 transition duration-500">
                <div class="absolute top-2 right-2 bg-black/80 px-2 py-1 rounded-lg text-[9px] font-black uppercase">⭐ {m.get('rating', '0.0')}</div>
            </div>
            <div class="p-4 text-center">
                <h3 class="text-[11px] font-black truncate uppercase text-slate-100 group-hover:text-blue-500 transition">{m['title']}</h3>
                <p class="text-[10px] text-slate-500 mt-1 font-bold uppercase">{m['year']} | {m['category']}</p>
            </div>
        </a>"""
    grid_html += '</div>'
    return render_site(slider_html + grid_html, settings)

@app.route('/movie/<id>')
def movie_page(id):
    settings = settings_col.find_one({})
    m = movies_col.find_one({"_id": ObjectId(id)})
    if not m: return "Movie Not Found", 404
    
    links_html = "".join([f'<a href="https://t.me/{settings["bot_username"]}?start={f["file_ref"]}" target="_blank" class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-black transition shadow-2xl group border-b-4 border-blue-900 active:border-0 uppercase tracking-tighter mb-4"><span>📥 DOWNLOAD {f["quality"]}</span><span class="text-[10px] bg-black/20 px-3 py-1 rounded-full font-black">Secure Bot</span></a>' for f in m['files']])

    content = f"""
    <div class="flex flex-col lg:flex-row gap-12 mt-4">
        <div class="w-full lg:w-1/3 shrink-0"><img src="{m['poster']}" class="rounded-[40px] shadow-2xl w-full border border-white/10 sticky top-24"></div>
        <div class="flex-1">
            <h1 class="text-4xl md:text-8xl font-black text-white leading-tight uppercase tracking-tighter">{m['title']}</h1>
            <div class="flex flex-wrap gap-4 mt-8">
                <span class="bg-blue-600 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['category']}</span>
                <span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-yellow-500 shadow-xl">⭐ {m['rating']}</span>
                <span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['year']}</span>
            </div>
            <div class="mt-10 p-8 bg-slate-900/50 rounded-3xl border border-white/5 shadow-inner">
                <h3 class="text-blue-500 font-black text-xs uppercase mb-4 tracking-widest text-white">Full Storyline 📖</h3>
                <p class="text-slate-400 text-lg md:text-xl leading-relaxed italic font-medium">"{m['plot']}"</p>
            </div>
            <div class="mt-8 grid md:grid-cols-2 gap-6 text-[13px] text-slate-400">
                <div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🎬 Director</b> {m.get('director', 'Unknown')}</div>
                <div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🌟 Starring Cast</b> {m.get('cast', 'Unknown')}</div>
            </div>
            <div class="mt-12 space-y-4">
                <h2 class="text-3xl font-black uppercase tracking-tighter mb-6 flex items-center gap-3">📥 DOWNLOAD OPTIONS:</h2>
                <div class="grid gap-4">{links_html}</div>
            </div>
        </div>
    </div>"""
    return render_site(content, settings)

# --- Routes: Admin Dashboard ---

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    settings = settings_col.find_one({})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == settings['admin_user'] and check_password_hash(settings['admin_pass'], p):
            session['is_admin'] = True
            return redirect('/dashboard')
        flash("❌ Authentication Failed!")
    return render_site("""<div class="max-w-sm mx-auto bg-slate-900 p-10 rounded-[40px] border border-blue-500 shadow-2xl mt-10 text-center"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">Admin Login ⚙️</h2><form method="POST" class="space-y-4"><input name="user" placeholder="Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white"><input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white"><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Authenticate</button></form></div>""", settings)

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
                "auto_delete_min": int(request.form.get('auto_delete_min', 0)),
                "restrict_forward": request.form.get('restrict_forward') == "on",
                "ads": {
                    "banner_ad": request.form.get('banner_ad'), "popunder": request.form.get('popunder'),
                    "social_bar": request.form.get('social_bar'), "header_ad": request.form.get('header_ad'), 
                    "footer_ad": request.form.get('footer_ad'), "native_banner": request.form.get('native_banner')
                }
            }
            if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
            settings_col.update_one({}, {"$set": upd})
            flash("✅ Settings Saved Successfully!")
        elif action == "set_webhook":
            webhook_url = f"https://{request.host}/telegram-webhook"
            r = requests.get(f"https://api.telegram.org/bot{settings['bot_token']}/setWebhook?url={webhook_url}")
            flash(f"Webhook Status: {r.json().get('description')}")
        return redirect('/dashboard')

    dq = request.args.get('dq')
    mq = {"title": {"$regex": dq, "$options": "i"}} if dq else {}
    movies = list(movies_col.find(mq).sort('_id', -1))
    movies_list_html = "".join([f'<div class="flex items-center justify-between bg-black/40 p-4 rounded-2xl border border-white/5 mb-3 shadow-lg"><div class="flex items-center gap-4"><img src="{m["poster"]}" class="h-10 w-8 rounded-lg object-cover"><span class="text-xs font-black truncate w-32 md:w-60 uppercase">{m["title"]}</span></div><div class="flex gap-2"><a href="/edit-movie/{m["_id"]}" class="bg-blue-600 px-3 py-1 rounded text-[9px] font-black uppercase">Edit</a><a href="/delete/{m["_id"]}" class="bg-red-600 px-3 py-1 rounded text-[9px] font-black uppercase" onclick="return confirm(\'Delete?\')">Delete</a></div></div>' for m in movies])

    content = f"""<div class="grid lg:grid-cols-2 gap-10"><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl"><h2 class="text-xl font-bold mb-6 uppercase text-blue-500 text-white">⚙️ Master Configuration</h2><form method="POST" class="space-y-4 text-[10px] font-black uppercase tracking-widest"><input type="hidden" name="action" value="save"><div class="grid grid-cols-2 gap-4"><input name="site_name" value="{settings['site_name']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="logo_url" value="{settings['logo_url']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><input name="header_notice" value="{settings['header_notice']}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><div class="grid grid-cols-2 gap-4"><input name="tmdb_key" value="{settings['tmdb_key']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="bot_token" value="{settings['bot_token']}" placeholder="Bot Token" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><div class="grid grid-cols-2 gap-4"><input name="bot_username" value="{settings['bot_username']}" placeholder="Bot Username" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="categories" value="{','.join(settings['categories'])}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><div class="grid grid-cols-2 gap-4 bg-blue-600/10 p-4 rounded-2xl border border-blue-500/20"><div class="text-blue-400">Auto Delete (Min):<br><input name="auto_delete_min" type="number" value="{settings.get('auto_delete_min', 0)}" class="bg-black/50 p-2 rounded-xl mt-1 w-full text-white"></div><div class="text-blue-400">Restrict Forward:<br><input name="restrict_forward" type="checkbox" {"checked" if settings.get("restrict_forward") else ""} class="mt-3"></div></div><h3 class="text-emerald-500 underline mt-4">💰 Ad Management</h3><div class="grid grid-cols-2 gap-4"><textarea name="banner_ad" placeholder="Banner Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20 text-white">{settings.get('ads',{}).get('banner_ad','')}</textarea><textarea name="popunder" placeholder="Popunder" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20 text-white">{settings.get('ads',{}).get('popunder','')}</textarea><textarea name="header_ad" placeholder="Header Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20 text-white">{settings.get('ads',{}).get('header_ad','')}</textarea><textarea name="footer_ad" placeholder="Footer Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20 text-white">{settings.get('ads',{}).get('footer_ad','')}</textarea></div><div class="p-6 bg-blue-600/10 rounded-[30px] border border-blue-600/20 mt-4"><input name="admin_user" value="{settings['admin_user']}" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 mb-2 outline-none text-white"><input name="new_pass" type="password" placeholder="New Admin Password" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 outline-none text-white"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Save Master Settings</button></form><form method="POST" class="mt-4"><input type="hidden" name="action" value="set_webhook"><button class="w-full bg-emerald-600 py-3 rounded-xl font-black uppercase text-[10px] shadow-lg">🛠️ Auto Set Bot Webhook</button></form></div><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl h-[1000px] overflow-y-auto"><h2 class="text-xl font-bold mb-6 uppercase text-emerald-500 text-white">🎬 Movie Management</h2><form action="/dashboard" method="GET" class="mb-4 flex gap-2"><input name="dq" placeholder="Search title..." class="w-full bg-black/40 p-3 rounded-xl border border-white/10 outline-none text-xs text-white"><button class="bg-blue-600 px-4 rounded-xl font-black text-xs uppercase shadow-lg">Filter</button></form>{movies_list_html}</div></div>"""
    return render_site(content, settings)

@app.route('/edit-movie/<id>', methods=['GET', 'POST'])
def edit_movie(id):
    if not session.get('is_admin'): return redirect('/admin')
    settings = settings_col.find_one({})
    m = movies_col.find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        new_files = []
        labels, refs = request.form.getlist('f_label'), request.form.getlist('f_ref')
        for l, r in zip(labels, refs):
            if l and r: new_files.append({"quality": l, "file_ref": r})
        upd = {"title": request.form.get('title'), "year": request.form.get('year'), "rating": request.form.get('rating'), "plot": request.form.get('plot'), "category": request.form.get('category'), "files": new_files}
        movies_col.update_one({"_id": ObjectId(id)}, {"$set": upd})
        flash("✅ Movie Updated Successfully!")
        return redirect('/dashboard')
    
    file_inputs_html = "".join([f'<div class="flex gap-2 mb-2"><input name="f_label" value="{f["quality"]}" class="bg-black/50 p-2 rounded-xl border border-white/10 w-1/3 text-white"><input name="f_ref" value="{f["file_ref"]}" class="bg-black/50 p-2 rounded-xl border border-white/10 w-2/3 text-white"></div>' for f in m['files']])
    
    content = f"""<div class="max-w-2xl mx-auto bg-slate-900 p-10 rounded-[40px] border border-white/5 shadow-2xl mt-4"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500 text-center">Edit Movie Info 🎬</h2><form method="POST" class="space-y-4 uppercase text-[11px] font-black text-white"><input name="title" value="{m['title']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none"><div class="grid grid-cols-2 gap-4"><input name="year" value="{m['year']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"><input name="rating" value="{m['rating']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"></div><input name="category" value="{m['category']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10"><textarea name="plot" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 h-48">{m['plot']}</textarea><h3 class="text-emerald-500 underline mt-6 mb-2 uppercase">Edit Download Buttons</h3>{file_inputs_html}<div class="flex gap-2"><input name="f_label" placeholder="New Quality" class="bg-black/50 p-2 rounded-xl border border-white/10 w-1/3"><input name="f_ref" placeholder="New File Ref" class="bg-black/50 p-2 rounded-xl border border-white/10 w-2/3"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg mt-8">Save All Updates</button></form></div>"""
    return render_site(content, settings)

@app.route('/delete/<id>')
def delete_movie(id):
    if not session.get('is_admin'): return redirect('/admin')
    movies_col.delete_one({"_id": ObjectId(id)})
    flash("🗑️ Movie Deleted!")
    return redirect('/dashboard')

# --- Clone System: লিং কপি এবং স্বতন্ত্র ডাটাবেস ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    settings = settings_col.find_one({})
    if request.method == 'POST':
        name, db_uri = request.form.get('name'), request.form.get('db_uri')
        site_url = f"https://{request.host}"
        admin_url = f"{site_url}/admin"
        content = f"""
        <div class="max-w-xl mx-auto bg-slate-900 p-10 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-6 text-white uppercase font-black">
            <h2 class="text-3xl text-emerald-400 mb-6 italic tracking-tighter">🎉 CLONE SUCCESSFUL! 🎉</h2>
            <div class="space-y-4 text-left">
                <div class="copy-box"><p class="text-[9px] text-blue-400 font-black">USER SITE URL</p><p id="s_url" class="font-mono text-sm truncate">{site_url}</p><button onclick="copyToClipboard('s_url')" class="bg-blue-600 px-4 py-1 rounded-full text-[10px] mt-2 shadow-xl">COPY URL</button></div>
                <div class="copy-box"><p class="text-[9px] text-emerald-400 font-black">ADMIN PANEL URL</p><p id="a_url" class="font-mono text-sm truncate">{admin_url}</p><button onclick="copyToClipboard('a_url')" class="bg-emerald-600 px-4 py-1 rounded-full text-[10px] mt-2 shadow-xl">COPY ADMIN</button></div>
            </div>
            <p class="mt-6 text-[10px] opacity-60 tracking-widest">Now use the new MongoDB URI in your GitHub Environment variables.</p>
            <a href="/admin" class="mt-8 inline-block bg-white text-black px-10 py-3 rounded-full text-xs font-bold shadow-2xl">BACK TO HOME</a>
        </div>"""
        return render_site(content, settings)
    
    content = f"""<div class="max-w-md mx-auto bg-slate-900 p-12 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-10 text-white"><h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase tracking-tighter italic">Network Cloner 🚀</h2><p class="text-slate-500 text-[10px] mb-8 uppercase font-bold tracking-widest">Generate your dedicated movie network instance.</p><form method="POST" class="space-y-6"><input name="name" placeholder="Desired Site Name" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 font-bold text-white outline-none text-center shadow-inner"><input name="db_uri" placeholder="Paste NEW MongoDB Atlas URI" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 text-xs text-white outline-none text-center shadow-inner" required><button class="w-full bg-emerald-600 hover:bg-emerald-700 py-5 rounded-3xl font-black uppercase tracking-widest shadow-2xl">Deploy Standalone Network</button></form></div>"""
    return render_site(content, settings)

# --- Telegram Bot Webhook Implementation ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    settings = settings_col.find_one({})
    if not settings or not settings.get('bot_token'): return ''
    bot = telebot.TeleBot(settings['bot_token'], threaded=False)
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))

    @bot.message_handler(commands=['start'])
    def handle_start(m):
        args = m.text.split()
        if len(args) > 1:
            file_data = files_col.find_one({"_id": ObjectId(args[1])})
            if file_data:
                protect = settings.get('restrict_forward', False)
                # ফাইল পাঠানো
                sent_msg = bot.send_document(m.chat.id, file_data['file_id'], caption=f"🎬 মুভি: *{file_data['file_name']}*\n\n🔥 Enjoy Your Movie! 🔥", parse_mode="Markdown", protect_content=protect)
                # অটো ডিলিট টাইমার
                del_min = settings.get('auto_delete_min', 0)
                if del_min > 0:
                    threading.Timer(del_min * 60, lambda: (bot.delete_message(m.chat.id, sent_msg.message_id) if bot else None)).start()
                    bot.send_message(m.chat.id, f"⚠️ ফাইলটি {del_min} মিনিট পর অটো ডিলিট হয়ে যাবে।")
            else: bot.send_message(m.chat.id, "❌ Error: File Not Found!")
        else: bot.send_message(m.chat.id, f"🎬 Welcome! Official File Store for {settings['site_name']}.")

    @bot.message_handler(commands=['post'])
    def handle_post(m):
        query = m.text.replace('/post', '').strip()
        if not query: return bot.reply_to(m, "Format: `/post Avatar`")
        try:
            res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={settings['tmdb_key']}&query={query}").json()
            results = res.get('results', [])[:5]
            markup = telebot.types.InlineKeyboardMarkup()
            for r in results: markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{r['id']}"))
            bot.reply_to(m, "🎬 Select Correct Movie:", reply_markup=markup)
        except Exception as e: bot.reply_to(m, f"Error: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_sel(c):
        tid = c.data.split('_')[1]
        try:
            r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}?api_key={settings['tmdb_key']}&append_to_response=credits").json()
            cast = ", ".join([x['name'] for x in r.get('credits', {}).get('cast', [])[:8]])
            director = next((x['name'] for x in r.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")
            info = {"title": r['title'], "year": r.get('release_date','0000')[:4], "plot": r.get('overview',''), "rating": r.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": cast, "director": director}
            bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "files": [], "step": "cat"}}, upsert=True)
            markup = telebot.types.InlineKeyboardMarkup()
            for cat in settings['categories']: markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{cat.strip()}"))
            bot.send_message(c.message.chat.id, "✅ Details Fetched! Select Category:", reply_markup=markup)
        except Exception as e: bot.send_message(c.message.chat.id, f"Error: {e}")

    @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
    def handle_cat(c):
        bot_states.update_one({"user_id": c.from_user.id}, {"$set": {"category": c.data.split('_')[1], "step": "file"}})
        bot.send_message(c.message.chat.id, "✅ Send Movie Files now. Send /done when finished.")

    @bot.message_handler(content_types=['video', 'document', 'audio'])
    def handle_files(m):
        state = bot_states.find_one({"user_id": m.from_user.id})
        if not state or state.get('step') != 'file': return
        fid = m.video.file_id if m.video else (m.document.file_id if m.document else m.audio.file_id)
        fname = m.video.file_name if m.video else (m.document.file_name if m.document else "Download")
        quality = extract_quality(fname)
        ref_id = files_col.insert_one({"file_id": fid, "file_name": fname}).inserted_id
        bot_states.update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": quality, "file_ref": str(ref_id)}}})
        bot.reply_to(m, f"📥 {quality} Recorded! Send more or /done.")

    @bot.message_handler(commands=['done'])
    def handle_done(m):
        state = bot_states.find_one({"user_id": m.from_user.id})
        if not state: return
        movies_col.insert_one({**state['info'], "category": state['category'], "files": state['files']})
        bot.send_message(m.chat.id, "🚀 PUBLISHED LIVE ON WEBSITE! ✅")
        bot_states.delete_one({"user_id": m.from_user.id})

    bot.process_new_updates([update])
    return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
