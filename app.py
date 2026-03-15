import os, requests, telebot, re, time, threading
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

# --- Flask Initial Setup ---
app = Flask(__name__)
app.secret_key = "ULTIMATE_MEGA_MOVIE_ENGINE_V10_FULL"

# --- Master MongoDB (নেটওয়ার্ক কন্ট্রোলার) ---
MASTER_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
master_client = MongoClient(MASTER_URI)
master_db = master_client['mega_network_engine']
sites_col = master_db['sites_registry']

# --- ডাটাবেস কানেকশন ম্যানেজার ---
def get_site_db(site_name):
    cfg = sites_col.find_one({"name": site_name})
    if not cfg: return None, None
    try:
        client = MongoClient(cfg['db_uri'])
        db = client['independent_movie_db']
        return db, cfg
    except: return None, None

# --- মেইন সাইট ইনিশিয়াল (যদি না থাকে) ---
if not sites_col.find_one({"name": "Main"}):
    sites_col.insert_one({
        "name": "Main", "display_name": "Premium Movie Duplex 🍿",
        "db_uri": MASTER_URI, "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
        "header_notice": "🔥 স্বাগতম! আমাদের প্রিমিয়াম মুভি নেটওয়ার্কে আপনাকে স্বাগতম। 🔥",
        "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
        "categories": ["Action 💥", "Hindi 🍿", "English 🇺🇸", "Bangla 🇧🇩", "Dual Audio 🔊", "Horror 👻"],
        "tmdb_key": "275aff9f1c570308fa10d14c6f49f998", "bot_token": "", "bot_username": "",
        "channel_id": "", "auto_delete_min": 0, "restrict_forward": False,
        "ads": {"banner_ad": "", "popunder": "", "social_bar": "", "header_ad": "", "footer_ad": "", "native_banner": ""}
    })

# --- প্রিমিয়াম ডুপ্লে থিম ডিজাইন ইঞ্জিন (Auto Responsive Desktop/Mobile) ---
def render_duplex_ui(content, config):
    ads = config.get('ads', {})
    sn = config['name']
    cats = "".join([f'<a href="/{sn}/?cat={c.strip()}" class="hover:text-blue-500 transition px-3 py-1 bg-white/5 rounded-full">{c.strip()}</a>' for c in config.get('categories', [])])
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{config['display_name']}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.css" />
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" />
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
            body {{ background: #06080c; color: #f1f5f9; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
            .glass {{ background: rgba(10, 15, 25, 0.95); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.08); }}
            .movie-card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); position: relative; overflow: hidden; }}
            .movie-card:hover {{ transform: scale(1.06); border-color: #3b82f6; box-shadow: 0 10px 40px -10px rgba(59, 130, 246, 0.5); }}
            .swiper-slide img {{ height: 550px; width: 100%; object-fit: cover; border-radius: 40px; filter: brightness(0.4); }}
            @media (max-width: 768px) {{ .swiper-slide img {{ height: 320px; border-radius: 20px; }} .mobile-hide {{ display: none; }} }}
            .ad-slot {{ display: flex; justify-content: center; margin: 15px 0; overflow: hidden; }}
            .btn-premium {{ background: linear-gradient(90deg, #2563eb, #7c3aed); transition: 0.3s; }}
            .btn-premium:hover {{ transform: translateY(-2px); box-shadow: 0 10px 20px rgba(37, 99, 235, 0.4); }}
        </style>
        {ads.get('popunder', '')} {ads.get('social_bar', '')}
    </head>
    <body>
        {ads.get('header_ad', '')}
        <div class="bg-gradient-to-r from-blue-700 to-indigo-900 text-white text-center py-2 text-[10px] md:text-xs font-bold uppercase px-4 tracking-widest shadow-2xl">
            <marquee scrollamount="5">{config['header_notice']}</marquee>
        </div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-emerald-600 hover:bg-emerald-500 text-white px-4 py-1.5 rounded-xl text-[10px] font-black uppercase shadow-lg transition">🚀 CLONE SITE</a>
                    <a href="/{sn}/" class="flex items-center gap-3">
                        <img src="{config['logo_url']}" class="h-8 md:h-11 rounded-lg shadow-lg">
                        <span class="text-xl md:text-3xl font-black text-white tracking-tighter mobile-hide">{config['display_name']}</span>
                    </a>
                </div>
                <div class="flex items-center gap-4">
                    <form action="/{sn}/search" method="GET" class="flex bg-white/5 rounded-full px-4 py-1.5 border border-white/10 focus-within:border-blue-500 transition">
                        <input name="q" placeholder="Search..." class="bg-transparent outline-none text-xs text-white w-24 md:w-56">
                        <button type="submit" class="text-slate-400 hover:text-white"><i class="fa fa-search"></i></button>
                    </form>
                    <div class="hidden xl:flex gap-3 text-[11px] font-bold uppercase tracking-tighter">{cats}</div>
                    <a href="/{sn}/admin" class="bg-white/10 hover:bg-blue-600 px-5 py-2 rounded-full text-[10px] font-black transition border border-white/10 shadow-xl">ADMIN</a>
                </div>
            </div>
        </nav>

        <div class="container mx-auto px-4 py-8">
            <div class="ad-slot">{ads.get('banner_ad', '')}</div>
            {content}
            <div class="ad-slot">{ads.get('footer_ad', '')}</div>
        </div>

        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>
            const swiper = new Swiper('.swiper', {{ autoplay: {{ delay: 4000 }}, loop: true, pagination: {{ el: '.swiper-pagination', clickable: true }} }});
            function copyToClipboard(id) {{
                var text = document.getElementById(id).innerText;
                navigator.clipboard.writeText(text);
                alert("Copied Successfully! ✅");
            }}
        </script>
        {ads.get('native_banner', '')}
    </body>
    </html>
    """
    return render_template_string(html)

# --- Routes: Frontend (Stand-alone Logic) ---

@app.route('/')
def global_entry(): return redirect('/Main/')

@app.route('/<site_name>/')
@app.route('/<site_name>/search')
def site_home(site_name):
    db, config = get_site_db(site_name)
    if not db: return f"<h1>Site '{site_name}' Not Found</h1>", 404
    q, cat = request.args.get('q'), request.args.get('cat')
    query = {"category": cat} if cat else {}
    if q: query["title"] = {"$regex": q, "$options": "i"}
    movies = list(db['movies'].find(query).sort('_id', -1))
    sliders = movies[:6]
    
    slider_html = ""
    if sliders and not cat and not q:
        slider_html = '<div class="swiper mb-12 overflow-hidden rounded-[40px] shadow-2xl relative border border-white/5"><div class="swiper-wrapper">'
        for s in sliders:
            slider_html += f"""<div class="swiper-slide relative"><img src="{s['banner']}"><div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div><div class="absolute bottom-10 left-6 md:left-12 text-left"><h2 class="text-3xl md:text-7xl font-black text-white uppercase tracking-tighter mb-4 shadow-2xl">{s['title']}</h2><a href="/{site_name}/movie/{s["_id"]}" class="btn-premium px-10 py-4 rounded-full font-black text-sm inline-block shadow-2xl uppercase">View Details</a></div></div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'

    title = q if q else (cat if cat else "Latest Uploads 🍿")
    grid = f'<h2 class="text-2xl md:text-4xl font-black mb-10 border-l-8 border-blue-600 pl-6 uppercase tracking-widest text-white">{title}</h2><div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-5 md:gap-10">'
    for m in movies:
        grid += f"""<a href="/{site_name}/movie/{m["_id"]}" class="movie-card rounded-[30px] overflow-hidden group text-center p-2"><div class="relative overflow-hidden rounded-[25px]"><img src="{m["poster"]}" class="h-64 md:h-80 w-full object-cover group-hover:scale-110 transition duration-700"><div class="absolute top-3 right-3 bg-blue-600 px-3 py-1 rounded-lg text-[10px] font-black shadow-2xl">⭐ {m.get("rating", "0.0")}</div></div><div class="p-4"><h3 class="text-xs md:text-sm font-black truncate uppercase text-slate-100 group-hover:text-blue-500 transition">{m["title"]}</h3><p class="text-[10px] text-slate-500 mt-1 font-bold">{m["year"]} | {m["category"]}</p></div></a>"""
    grid += '</div>'
    return render_duplex_ui(slider_html + grid, config)

@app.route('/<site_name>/movie/<id>')
def movie_page(site_name, id):
    db, config = get_site_db(site_name)
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if not m: return "404 Not Found", 404
    links = "".join([f'<a href="https://t.me/{config["bot_username"]}?start={f["file_ref"]}" target="_blank" class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-6 rounded-3xl font-black transition shadow-2xl mb-4 border-b-8 border-blue-900 uppercase tracking-tighter group"><span><i class="fa fa-download mr-3"></i> DOWNLOAD {f["quality"]}</span><span class="text-[10px] bg-black/30 px-4 py-1 rounded-full group-hover:bg-blue-500 transition">Telegram Server</span></a>' for f in m['files']])
    content = f"""<div class="flex flex-col lg:flex-row gap-12 mt-4"><div class="w-full lg:w-1/3 shrink-0"><img src="{m['poster']}" class="rounded-[50px] shadow-2xl w-full border-4 border-white/5 sticky top-24"></div><div class="flex-1"><h1 class="text-4xl md:text-8xl font-black text-white leading-tight tracking-tighter uppercase">{m['title']}</h1><div class="flex flex-wrap gap-4 mt-8"><span class="bg-blue-600 px-6 py-2 rounded-2xl text-xs font-black uppercase">📂 {m['category']}</span><span class="bg-slate-800 px-6 py-2 rounded-2xl text-xs font-black uppercase text-yellow-500 shadow-xl font-black">⭐ {m['rating']} / 10</span><span class="bg-slate-800 px-6 py-2 rounded-2xl text-xs font-black uppercase">{m['year']}</span></div><div class="mt-12 p-10 bg-white/5 rounded-[40px] border border-white/5 shadow-inner"><h3 class="text-blue-500 font-black text-xs uppercase mb-4 tracking-[0.3em] font-black">Story Synopsis</h3><p class="text-slate-300 text-lg md:text-2xl leading-relaxed italic font-medium">"{m['plot']}"</p></div><div class="mt-8 grid md:grid-cols-2 gap-8 text-sm"><div class="bg-black/40 p-6 rounded-[30px] border border-white/5 shadow-xl"><b class="text-blue-500 uppercase block mb-2 tracking-widest text-xs">🎬 Directed By</b> {m.get('director', 'Unknown')}</div><div class="bg-black/40 p-6 rounded-[30px] border border-white/5 shadow-xl"><b class="text-blue-500 uppercase block mb-2 tracking-widest text-xs">🌟 Main Cast</b> {m.get('cast', 'Unknown')}</div></div><div class="mt-16 space-y-4"><h2 class="text-4xl font-black uppercase tracking-tighter mb-8 flex items-center gap-4"><span class="w-3 h-12 bg-emerald-500 rounded-full"></span> Get Download Links</h2>{links}</div></div></div>"""
    return render_duplex_ui(content, config)

# --- Admin Panel: Full Network & Ad Control ---

@app.route('/<site_name>/admin', methods=['GET', 'POST'])
def admin_login(site_name):
    _, config = get_site_db(site_name)
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == config['admin_user'] and check_password_hash(config['admin_pass'], p):
            session[f'auth_{site_name}'] = True
            return redirect(f'/{site_name}/dashboard')
        flash("❌ Invalid Admin Access!")
    return render_duplex_ui(f"""<div class="max-w-sm mx-auto bg-slate-900 p-12 rounded-[50px] border-2 border-blue-600 shadow-2xl mt-10 text-center"><h2 class="text-3xl font-black mb-10 uppercase text-blue-500">Admin Area ⚙️</h2><form method="POST" class="space-y-5"><input name="user" placeholder="Username" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white font-bold"><input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 outline-none focus:border-blue-500 text-white font-bold"><button class="w-full btn-premium py-5 rounded-2xl font-black uppercase shadow-lg text-white">Authenticate</button></form></div>""", config)

@app.route('/<site_name>/dashboard', methods=['GET', 'POST'])
def dashboard(site_name):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, config = get_site_db(site_name)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save_config":
            new_pass = request.form.get('new_pass')
            upd = {"display_name": request.form.get('display_name'), "logo_url": request.form.get('logo_url'), "header_notice": request.form.get('header_notice'), "admin_user": request.form.get('admin_user'), "tmdb_key": request.form.get('tmdb_key'), "bot_token": request.form.get('bot_token'), "bot_username": request.form.get('bot_username').replace('@',''), "channel_id": request.form.get('channel_id'), "auto_delete_min": int(request.form.get('auto_delete_min', 0)), "restrict_forward": request.form.get('restrict_forward') == "on", "categories": request.form.get('categories').split(','), "ads": {"banner_ad": request.form.get('banner_ad'), "popunder": request.form.get('popunder'), "social_bar": request.form.get('social_bar'), "header_ad": request.form.get('header_ad'), "footer_ad": request.form.get('footer_ad'), "native_banner": request.form.get('native_banner')}}
            if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
            sites_col.update_one({"name": site_name}, {"$set": upd}); flash("✅ Network Updated!")
        elif action == "set_webhook":
            requests.get(f"https://api.telegram.org/bot{config['bot_token']}/setWebhook?url=https://{request.host}/telegram-webhook"); flash("✅ Bot Linked!")
        return redirect(f'/{site_name}/dashboard')

    dq = request.args.get('dq')
    mq = {"title": {"$regex": dq, "$options": "i"}} if dq else {}
    movies = list(db['movies'].find(mq).sort('_id', -1))
    movies_list = "".join([f'<div class="flex items-center justify-between bg-black/40 p-5 rounded-[25px] border border-white/5 mb-4 shadow-xl"><div class="flex items-center gap-5"><img src="{m["poster"]}" class="h-12 w-10 rounded-lg shadow-lg object-cover"><span class="text-xs font-black truncate w-32 md:w-80 uppercase text-white">{m["title"]}</span></div><div class="flex gap-3"><a href="/{site_name}/edit-movie/{m["_id"]}" class="bg-blue-600 px-4 py-2 rounded-xl text-[10px] font-black uppercase">Edit</a><a href="/{site_name}/delete/{m["_id"]}" class="bg-red-600 px-4 py-2 rounded-xl text-[10px] font-black uppercase" onclick="return confirm(\'Delete?\')">Del</a></div></div>' for m in movies])

    content = f"""<div class="grid lg:grid-cols-2 gap-12"><div class="bg-slate-900 p-10 rounded-[50px] border border-white/5 shadow-2xl"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">⚙️ Global Network Settings</h2><form method="POST" class="space-y-5 text-[10px] font-black uppercase tracking-widest text-white"><input type="hidden" name="action" value="save_config"><div class="grid grid-cols-2 gap-5"><input name="display_name" value="{config['display_name']}" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"><input name="logo_url" value="{config['logo_url']}" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"></div><input name="header_notice" value="{config['header_notice']}" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"><div class="grid grid-cols-2 gap-5"><input name="tmdb_key" value="{config['tmdb_key']}" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"><input name="bot_token" value="{config['bot_token']}" placeholder="Bot Token" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"></div><div class="grid grid-cols-2 gap-5"><input name="bot_username" value="{config.get('bot_username','')}" placeholder="Bot Username" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"><input name="channel_id" value="{config.get('channel_id','')}" placeholder="Channel ID (-100...)" class="bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"></div><div class="grid grid-cols-2 gap-5 bg-blue-600/10 p-5 rounded-[30px] border border-blue-600/20"><div class="text-blue-400">Auto Delete (Min):<input name="auto_delete_min" type="number" value="{config.get('auto_delete_min', 0)}" class="bg-black/50 p-3 rounded-xl mt-1 w-full"></div><div class="text-blue-400">Forward Lock:<br><input name="restrict_forward" type="checkbox" {"checked" if config.get("restrict_forward") else ""} class="mt-4 scale-150"></div></div><input name="categories" value="{','.join(config['categories'])}" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 outline-none"><h3 class="text-emerald-500 underline mt-6 tracking-widest font-black">💰 Premium Ads Management</h3><div class="grid grid-cols-2 gap-5"><textarea name="banner_ad" placeholder="Banner Ad" class="bg-black/50 p-4 rounded-2xl h-24">{config.get('ads',{}).get('banner_ad','')}</textarea><textarea name="popunder" placeholder="Popunder" class="bg-black/50 p-4 rounded-2xl h-24">{config.get('ads',{}).get('popunder','')}</textarea><textarea name="header_ad" placeholder="Header Ad" class="bg-black/50 p-4 rounded-2xl h-24">{config.get('ads',{}).get('header_ad','')}</textarea><textarea name="footer_ad" placeholder="Footer Ad" class="bg-black/50 p-4 rounded-2xl h-24">{config.get('ads',{}).get('footer_ad','')}</textarea></div><div class="p-8 bg-blue-600/10 rounded-[40px] border border-blue-600/20 mt-8"><input name="admin_user" value="{config['admin_user']}" class="w-full bg-black/60 p-5 rounded-2xl border border-white/10 mb-4 outline-none"><input name="new_pass" type="password" placeholder="Change Password" class="w-full bg-black/60 p-5 rounded-2xl border border-white/10 outline-none"></div><button class="w-full bg-blue-600 py-5 rounded-[30px] font-black uppercase shadow-2xl">Sync Site Data</button></form><form method="POST" class="mt-6"><input type="hidden" name="action" value="set_webhook"><button class="w-full bg-emerald-600 py-4 rounded-[30px] font-black uppercase text-[11px] shadow-2xl tracking-widest">🛠️ Set Telegram Webhook</button></form></div><div class="bg-slate-900 p-10 rounded-[50px] border border-white/5 shadow-2xl h-[1200px] overflow-y-auto"><h2 class="text-2xl font-black mb-8 uppercase text-emerald-500">🎬 Global Movie Inventory</h2><form action="/{site_name}/dashboard" method="GET" class="mb-6 flex gap-4"><input name="dq" placeholder="Quick Movie Search..." class="w-full bg-black/40 p-5 rounded-2xl border border-white/10 outline-none text-xs text-white"><button class="bg-blue-600 px-6 rounded-2xl font-black uppercase shadow-lg">Search</button></form>{movies_list}</div></div>"""
    return render_ui(content, config)

@app.route('/<site_name>/edit-movie/<id>', methods=['GET', 'POST'])
def edit_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, config = get_site_db(site_name)
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        l, r = request.form.getlist('f_label'), request.form.getlist('f_ref')
        upd = {"title": request.form.get('title'), "year": request.form.get('year'), "rating": request.form.get('rating'), "plot": request.form.get('plot'), "category": request.form.get('category'), "files": [{"quality": q, "file_ref": ref} for q, ref in zip(l, r) if q and ref]}
        db['movies'].update_one({"_id": ObjectId(id)}, {"$set": upd}); flash("✅ Movie Synced!"); return redirect(f'/{site_name}/dashboard')
    f_in = "".join([f'<div class="flex gap-4 mb-3"><input name="f_label" value="{f["quality"]}" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-1/3 text-white"><input name="f_ref" value="{f["file_ref"]}" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-2/3 text-white"></div>' for f in m['files']])
    content = f"""<div class="max-w-3xl mx-auto bg-slate-900 p-12 rounded-[50px] border border-white/5 shadow-2xl mt-4"><h2 class="text-3xl font-black mb-10 uppercase text-blue-500 text-center">Edit Global Data 🎬</h2><form method="POST" class="space-y-5 font-black uppercase text-[11px] text-white"><input name="title" value="{m['title']}" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 outline-none focus:border-blue-500"><div class="grid grid-cols-2 gap-5"><input name="year" value="{m['year']}" class="bg-black/50 p-5 rounded-2xl border border-white/10"><input name="rating" value="{m['rating']}" class="bg-black/50 p-5 rounded-2xl border border-white/10"></div><input name="category" value="{m['category']}" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10"><textarea name="plot" class="w-full bg-black/50 p-5 rounded-2xl border border-white/10 h-48">{m['plot']}</textarea><h3 class="text-emerald-500 underline uppercase tracking-widest mt-8 mb-4">Edit Download Nodes</h3>{f_in}<div class="text-blue-400 text-[10px] mb-3">Add New Resource:</div><div class="flex gap-4"><input name="f_label" placeholder="Quality" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-1/3 text-white"><input name="f_ref" placeholder="Reference ID" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-2/3 text-white"></div><button class="w-full btn-premium py-5 rounded-[30px] font-black uppercase shadow-2xl mt-10">Commit Changes</button></form></div>"""
    return render_ui(content, config)

@app.route('/<site_name>/delete/<id>')
def delete_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, _ = get_site_db(site_name); db['movies'].delete_one({"_id": ObjectId(id)}); flash("🗑️ Deleted!"); return redirect(f'/{site_name}/dashboard')

# --- Mega Clone System ---

@app.route('/clone-site', methods=['GET', 'POST'])
def mega_clone():
    db_m, config_m = get_site_db("Main")
    if request.method == 'POST':
        name, uri = request.form.get('name').strip(), request.form.get('db_uri').strip()
        if sites_col.find_one({"name": name}): flash("❌ Global Name Taken!")
        else:
            sites_col.insert_one({"name": name, "display_name": name + " Hub", "db_uri": uri, "logo_url": config_m['logo_url'], "header_notice": "Welcome to your Hub!", "admin_user": "admin", "admin_pass": generate_password_hash("admin123"), "categories": ["Action", "Hindi"], "tmdb_key": config_m['tmdb_key'], "bot_token": "", "bot_username": "", "ads": {}})
            s_u, a_u = f"https://{request.host}/{name}/", f"https://{request.host}/{name}/admin"
            return f"""<div style="background:#000;color:#fff;padding:80px;text-align:center;font-family:sans-serif;height:100vh;"><h1 style="color:#10b981;font-size:3em;">🎉 NETWORK DEPLOYED!</h1><div style="background:#111;padding:40px;border-radius:40px;display:inline-block;text-align:left;border:2px solid #10b981;box-shadow:0 0 50px #10b98133;"><p id='s'><b>Main Link:</b> {s_u}</p><p id='a'><b>Admin Control:</b> {a_u}</p><p><b>Password:</b> admin123</p></div><br><button onclick="navigator.clipboard.writeText('{s_u}');alert('Copied!')" style="margin-top:30px;background:#2563eb;color:#fff;padding:20px 40px;border:none;border-radius:20px;font-weight:900;cursor:pointer;text-transform:uppercase;">Copy User Link</button></div>"""
    return render_ui("""<div class="max-w-md mx-auto bg-slate-900 p-12 rounded-[60px] border-2 border-emerald-500 shadow-2xl text-center mt-10 text-white"><h2 class="text-4xl font-black mb-8 text-emerald-500 uppercase italic tracking-tighter">Clone Premium Network 🚀</h2><form method="POST" class="space-y-6"><input name="name" placeholder="Unique Network Name" class="w-full bg-black/50 p-6 rounded-3xl border-2 border-white/10 font-black text-white text-center shadow-2xl"><input name="db_uri" placeholder="Paste New MongoDB Atlas URI" class="w-full bg-black/50 p-6 rounded-3xl border-2 border-white/10 text-[10px] text-white text-center shadow-2xl" required><button class="w-full bg-emerald-600 hover:bg-emerald-700 py-6 rounded-3xl font-black uppercase tracking-widest text-white shadow-2xl transition-all transform hover:scale-105">Launch New Standalone HUB</button></form></div>""", config_m)

# --- Telegram Bot Webhook Engine ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    db_m, m_cfg = get_site_db("Main")
    if not m_cfg['bot_token']: return ''
    bot = telebot.TeleBot(m_cfg['bot_token'], threaded=False)
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))

    @bot.message_handler(commands=['start'])
    def handle_start(m):
        p = m.text.split()
        if len(p) > 1:
            for s in list(sites_col.find({})):
                db_s = MongoClient(s['db_uri'])['standalone_movie_db']
                f = db_s['stored_files'].find_one({"_id": ObjectId(p[1])})
                if f:
                    sent = bot.send_document(m.chat.id, f['file_id'], caption=f"🍿 মুভি: {f['file_name']}", protect_content=s.get('restrict_forward', False))
                    if s.get('auto_delete_min', 0) > 0: threading.Timer(s['auto_delete_min']*60, lambda: bot.delete_message(m.chat.id, sent.message_id)).start()
                    return
            bot.send_message(m.chat.id, "❌ Error: Link Expired!")
        else: bot.send_message(m.chat.id, "🎬 Global Hub Bot Connected.")

    @bot.message_handler(commands=['post'])
    def handle_post(m):
        parts = m.text.split(' ', 2)
        if len(parts) < 3: return bot.reply_to(m, "Format: `/post SiteName MovieQuery`")
        sn, mq = parts[1], parts[2]; db_s, c_s = get_site_db(sn)
        if not db_s: return bot.reply_to(m, "❌ HUB Not Found!")
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={c_s['tmdb_key']}&query={mq}").json()
        markup = telebot.types.InlineKeyboardMarkup()
        for r in res.get('results', [])[:5]: markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{sn}_{r['id']}"))
        bot.reply_to(m, f"🎬 Results for {sn}:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_sel(c):
        _, sn, tid = c.data.split('_'); db_s, c_s = get_site_db(sn)
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}?api_key={c_s['tmdb_key']}&append_to_response=credits").json()
        info = {"title": r['title'], "year": r.get('release_date','0000')[:4], "plot": r.get('overview',''), "rating": r.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": ", ".join([x['name'] for x in r.get('credits', {}).get('cast', [])[:8]]), "director": next((x['name'] for x in r.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")}
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "sn": sn, "files": [], "step": "cat"}}, upsert=True)
        markup = telebot.types.InlineKeyboardMarkup()
        for cat in c_s['categories']: markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{sn}_{cat.strip()}"))
        bot.send_message(c.message.chat.id, "Select Category:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
    def handle_cat(c):
        _, sn, cat = c.data.split('_'); db_s, _ = get_site_db(sn)
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"category": cat, "step": "file"}})
        bot.send_message(c.message.chat.id, f"✅ Send Files for {sn}. Send /done when finished.")

    @bot.message_handler(content_types=['video', 'document', 'audio'])
    def handle_files(m):
        for s in list(sites_col.find({})):
            db_s = MongoClient(s['db_uri'])['standalone_movie_db']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st and st.get('step') == 'file':
                fwd = bot.forward_message(s['channel_id'], m.chat.id, m.message_id)
                fn = m.video.file_name if m.video else (m.document.file_name if m.document else "Download")
                qual = "1080P" if "1080" in fn else ("720P" if "720" in fn else ("480P" if "480" in fn else "HD"))
                ref_id = db_s['stored_files'].insert_one({"file_id": fwd.document.file_id if hasattr(fwd, 'document') else fwd.video.file_id, "file_name": fn}).inserted_id
                db_s['bot_states'].update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": qual, "file_ref": str(ref_id)}}})
                return bot.reply_to(m, f"📥 {qual} Stored in {s['name']} HUB!")

    @bot.message_handler(commands=['done'])
    def handle_done(m):
        for s in list(sites_col.find({})):
            db_s = MongoClient(s['db_uri'])['standalone_movie_db']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st:
                db_s['movies'].insert_one({**st['info'], "category": st['category'], "files": st['files']})
                bot.send_message(m.chat.id, f"🚀 Published on {st['sn']}! ✅")
                db_s['bot_states'].delete_one({"user_id": m.from_user.id}); return

    bot.process_new_updates([update]); return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
