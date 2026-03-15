import os, requests, telebot, re, time, threading
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- Flask Initial Setup ---
app = Flask(__name__)
app.secret_key = "STANDALONE_STANDALONE_MASTER_V100"

# --- মাস্টার মংগোডিবি (কানেকশন চেক সহ) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
try:
    master_client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    master_db = master_client['network_engine_standalone']
    sites_col = master_db['sites_list']
    master_client.server_info()
except Exception as e:
    print(f"MongoDB Connection Error: {e}")

# --- ডাটাবেস সুইচ মেকানিজম ---
def get_site_db(site_name):
    site_cfg = sites_col.find_one({"name": site_name})
    if not site_cfg: return None, None
    try:
        client = MongoClient(site_cfg['db_uri'])
        db = client['movie_data_store']
        return db, site_cfg
    except: return None, None

# --- মেইন সাইট ডিফল্ট এন্ট্রি ---
if not sites_col.find_one({"name": "Main"}):
    sites_col.insert_one({
        "name": "Main", "display_name": "Premium Movie Duplex 🍿",
        "db_uri": MONGO_URI, "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
        "header_notice": "🔥 স্বাগতম! আমাদের প্রিমিয়াম নেটওয়ার্কে আপনাকে স্বাগতম। 🔥",
        "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
        "categories": ["Action 💥", "Hindi 🍿", "English 🇺🇸", "Bangla 🇧🇩"],
        "tmdb_key": "275aff9f1c570308fa10d14c6f49f998", "bot_token": "", "bot_username": "",
        "channel_id": "", "auto_delete_min": 0, "restrict_forward": False,
        "ads": {"banner_ad": "", "popunder": "", "social_bar": "", "header_ad": "", "footer_ad": "", "native_banner": ""}
    })

# --- প্রিমিয়াম ডুপ্লে থিম ডিজাইন ---
def render_duplex(content, config):
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
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;900&display=swap');
            body {{ background: #080a10; color: #f1f5f9; font-family: 'Inter', sans-serif; overflow-x: hidden; }}
            .glass {{ background: rgba(15, 23, 42, 0.95); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: 0.4s; }}
            .card:hover {{ transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 0 30px rgba(59, 130, 246, 0.3); }}
            .swiper-slide img {{ height: 500px; width: 100%; object-fit: cover; border-radius: 30px; filter: brightness(0.4); }}
            @media (max-width: 768px) {{ .swiper-slide img {{ height: 320px; }} }}
            .copy-btn {{ background: #10b981; padding: 10px; border-radius: 10px; cursor: pointer; text-align: center; font-weight: 900; }}
        </style>
        {ads.get('popunder', '')} {ads.get('social_bar', '')}
    </head>
    <body>
        {ads.get('header_ad', '')}
        <div class="bg-blue-700 text-white text-center py-2 text-[10px] md:text-sm font-black uppercase px-4 shadow-xl">{config['header_notice']}</div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-4 flex justify-between items-center text-white">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-emerald-600 hover:bg-emerald-500 text-white px-3 py-1.5 rounded-lg text-[10px] font-black uppercase shadow-lg">🚀 CLONE</a>
                    <a href="/{sn}/" class="flex items-center gap-2">
                        <img src="{config['logo_url']}" class="h-8 md:h-10 rounded shadow-lg">
                        <span class="text-xl md:text-2xl font-black tracking-tighter hidden sm:block">{config['display_name']}</span>
                    </a>
                </div>
                <div class="flex items-center gap-4">
                    <form action="/{sn}/search" method="GET" class="hidden md:flex bg-black/50 rounded-full px-4 py-1 border border-white/10">
                        <input name="q" placeholder="Search..." class="bg-transparent outline-none text-xs text-white w-32">
                    </form>
                    <div class="hidden lg:flex gap-5 text-[11px] font-bold uppercase tracking-widest">{cats}</div>
                    <a href="/{sn}/admin" class="bg-slate-800 hover:bg-blue-600 px-4 py-1.5 rounded-full text-[10px] font-bold transition border border-white/10">ADMIN</a>
                </div>
            </div>
        </nav>

        <div class="container mx-auto px-4 py-8">
            <div class="flex justify-center mb-8">{ads.get('banner_ad', '')}</div>
            {content}
            <div class="mt-12 flex justify-center">{ads.get('footer_ad', '')}</div>
        </div>
        <script src="https://cdn.jsdelivr.net/npm/swiper@10/swiper-bundle.min.js"></script>
        <script>
            const swiper = new Swiper('.swiper', {{ autoplay: {{ delay: 4000 }}, loop: true, pagination: {{ el: '.swiper-pagination', clickable: true }} }});
            function copyToClipboard(id) {{ var t = document.getElementById(id).innerText; navigator.clipboard.writeText(t); alert("Copied! ✅"); }}
        </script>
        {ads.get('native_banner', '')}
    </body>
    </html>
    """
    return render_template_string(html)

# --- Routes: Frontend ---

@app.route('/')
def global_root(): return redirect('/Main/')

@app.route('/<site_name>/')
@app.route('/<site_name>/search')
def site_home(site_name):
    db, config = get_site_db(site_name)
    if not db: return "<h1>Error: Site Not Found</h1>", 404
    q, cat = request.args.get('q'), request.args.get('cat')
    query = {"category": cat} if cat else {}
    if q: query["title"] = {"$regex": q, "$options": "i"}
    movies = list(db['movies'].find(query).sort('_id', -1))
    sliders = movies[:6]
    
    slider_html = ""
    if sliders and not cat and not q:
        slider_html = '<div class="swiper mb-12 overflow-hidden rounded-[40px] shadow-2xl relative border border-white/5"><div class="swiper-wrapper">'
        for s in sliders:
            slider_html += f"""<div class="swiper-slide relative"><img src="{s['banner']}"><div class="absolute inset-0 bg-gradient-to-t from-black via-transparent to-transparent"></div><div class="absolute bottom-10 left-6 md:left-12 text-left"><h2 class="text-3xl md:text-7xl font-black text-white uppercase tracking-tighter mb-4">{s['title']}</h2><a href="/{site_name}/movie/{s["_id"]}" class="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-full font-black text-sm inline-block shadow-lg transition">VIEW DETAILS</a></div></div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'
    
    grid = f'<h2 class="text-2xl font-black mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest text-blue-500">{q if q else (cat if cat else "Recently Uploaded 🍿")}</h2><div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-8">'
    for m in movies:
        grid += f"""<a href="/{site_name}/movie/{m["_id"]}" class="card rounded-3xl overflow-hidden group text-center p-2"><div class="relative overflow-hidden"><img src="{m["poster"]}" class="h-64 md:h-80 w-full object-cover rounded-xl mb-2 group-hover:scale-110 transition duration-500"><div class="absolute top-2 right-2 bg-black/80 px-2 py-1 rounded-lg text-[9px] font-black uppercase">⭐ {m.get("rating", "0.0")}</div></div><h3 class="text-[11px] font-black truncate uppercase text-slate-100 group-hover:text-blue-500 transition">{m["title"]}</h3><p class="text-[10px] text-slate-500 mt-1 uppercase font-bold">{m["year"]} | {m["category"]}</p></a>"""
    grid += '</div>'
    return render_duplex(slider_html + grid, config)

@app.route('/<site_name>/movie/<id>')
def movie_page(site_name, id):
    db, config = get_site_db(site_name)
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if not m: return "404 Not Found", 404
    links = "".join([f'<a href="https://t.me/{config["bot_username"]}?start={f["file_ref"]}" target="_blank" class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-black transition shadow-2xl mb-4 border-b-4 border-blue-900 uppercase tracking-tighter"><span>📥 DOWNLOAD {f["quality"]}</span><span class="text-[10px] bg-black/20 px-3 py-1 rounded-full font-black">Bot Server</span></a>' for f in m['files']])
    content = f"""<div class="flex flex-col lg:flex-row gap-12 mt-4"><div class="w-full lg:w-1/3 shrink-0"><img src="{m['poster']}" class="rounded-[40px] shadow-2xl w-full border border-white/10 sticky top-24"></div><div class="flex-1"><h1 class="text-4xl md:text-8xl font-black text-white leading-tight uppercase tracking-tighter">{m['title']}</h1><div class="flex flex-wrap gap-4 mt-8"><span class="bg-blue-600 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['category']}</span><span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase text-yellow-500 shadow-xl">⭐ {m['rating']}</span><span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase">{m['year']}</span></div><div class="mt-10 p-8 bg-slate-900/50 rounded-3xl border border-white/5 shadow-inner"><h3 class="text-blue-500 font-black text-xs uppercase mb-4 tracking-widest text-white">The Synopsis</h3><p class="text-slate-400 text-lg md:text-xl leading-relaxed italic font-medium">"{m['plot']}"</p></div><div class="mt-8 grid md:grid-cols-2 gap-6 text-[13px]"><div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🎬 Director</b> {m.get('director', 'Unknown')}</div><div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🌟 Starring</b> {m.get('cast', 'Unknown')}</div></div><div class="mt-12 space-y-4"><h2 class="text-3xl font-black uppercase tracking-tighter mb-6 flex items-center gap-3">📥 DOWNLOAD OPTIONS:</h2>{links}</div></div></div>"""
    return render_duplex(content, config)

# --- Admin Panel: Full Configuration & Movie Management ---

@app.route('/<site_name>/admin', methods=['GET', 'POST'])
def admin_login(site_name):
    _, config = get_site_db(site_name)
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == config['admin_user'] and check_password_hash(config['admin_pass'], p):
            session[f'auth_{site_name}'] = True
            return redirect(f'/{site_name}/dashboard')
        flash("❌ Authentication Failed!")
    return render_duplex(f"""<div class="max-w-sm mx-auto bg-slate-900 p-10 rounded-[40px] border border-blue-500 shadow-2xl mt-10 text-center"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">{site_name} Admin</h2><form method="POST" class="space-y-4"><input name="user" placeholder="Admin Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white"><input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white"><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Authenticate</button></form></div>""", config)

@app.route('/<site_name>/dashboard', methods=['GET', 'POST'])
def dashboard(site_name):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, config = get_site_db(site_name)
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save_config":
            upd = {"display_name": request.form.get('display_name'), "logo_url": request.form.get('logo_url'), "header_notice": request.form.get('header_notice'), "admin_user": request.form.get('admin_user'), "tmdb_key": request.form.get('tmdb_key'), "bot_token": request.form.get('bot_token'), "bot_username": request.form.get('bot_username').replace('@',''), "channel_id": request.form.get('channel_id'), "auto_delete_min": int(request.form.get('auto_delete_min', 0)), "restrict_forward": request.form.get('restrict_forward') == "on", "categories": request.form.get('categories').split(','), "ads": {"banner_ad": request.form.get('banner_ad'), "popunder": request.form.get('popunder'), "social_bar": request.form.get('social_bar'), "header_ad": request.form.get('header_ad'), "footer_ad": request.form.get('footer_ad'), "native_banner": request.form.get('native_banner')}}
            if request.form.get('new_pass'): upd["admin_pass"] = generate_password_hash(request.form.get('new_pass'))
            sites_col.update_one({"name": site_name}, {"$set": upd}); flash("✅ Settings Saved!")
        elif action == "set_webhook":
            requests.get(f"https://api.telegram.org/bot{config['bot_token']}/setWebhook?url=https://{request.host}/telegram-webhook"); flash("✅ Webhook Connected!")
        return redirect(f'/{site_name}/dashboard')
    
    dq = request.args.get('dq')
    mq = {"title": {"$regex": dq, "$options": "i"}} if dq else {}
    movies = list(db['movies'].find(mq).sort('_id', -1))
    movies_html = "".join([f'<div class="flex items-center justify-between bg-black/40 p-4 rounded-2xl border border-white/5 mb-3 shadow-lg"><div class="flex items-center gap-4"><img src="{m["poster"]}" class="h-10 w-8 rounded-lg object-cover"><span class="text-xs font-black truncate w-32 md:w-60 uppercase text-white font-bold">{m["title"]}</span></div><div class="flex gap-2"><a href="/{site_name}/edit-movie/{m["_id"]}" class="bg-blue-600 px-3 py-1 rounded text-[9px] font-black uppercase">Edit</a><a href="/{site_name}/delete/{m["_id"]}" class="bg-red-600 px-3 py-1 rounded text-[9px] font-black uppercase" onclick="return confirm(\'Delete?\')">Delete</a></div></div>' for m in movies])
    
    content = f"""<div class="grid lg:grid-cols-2 gap-10"><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl"><h2 class="text-xl font-bold mb-6 uppercase text-blue-500">⚙️ Configuration</h2><form method="POST" class="space-y-4 text-[10px] font-black uppercase tracking-widest text-white"><input type="hidden" name="action" value="save_config"><div class="grid grid-cols-2 gap-4"><input name="display_name" value="{config['display_name']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="logo_url" value="{config['logo_url']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><input name="header_notice" value="{config['header_notice']}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><div class="grid grid-cols-2 gap-4"><input name="tmdb_key" value="{config['tmdb_key']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="bot_token" value="{config['bot_token']}" placeholder="Bot Token" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><div class="grid grid-cols-2 gap-4"><input name="bot_username" value="{config.get('bot_username','')}" placeholder="Bot Username" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="channel_id" value="{config.get('channel_id','')}" placeholder="Channel ID (-100...)" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><div class="grid grid-cols-2 gap-4 bg-blue-600/10 p-4 rounded-[30px] border border-blue-600/20"><div class="text-blue-400">Auto Delete (Min):<input name="auto_delete_min" type="number" value="{config.get('auto_delete_min', 0)}" class="bg-black/50 p-2 rounded-xl mt-1 w-full text-white"></div><div>Forward Off:<br><input name="restrict_forward" type="checkbox" {"checked" if config.get("restrict_forward") else ""} class="mt-3 scale-125"></div></div><input name="categories" value="{','.join(config['categories'])}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><h3 class="text-emerald-500 underline mt-4 tracking-widest font-black">💰 Ad Manager (HTML)</h3><div class="grid grid-cols-2 gap-4"><textarea name="banner_ad" placeholder="Banner Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('banner_ad','')}</textarea><textarea name="popunder" placeholder="Popunder Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('popunder','')}</textarea></div><div class="p-6 bg-blue-600/10 rounded-[30px] border border-blue-600/20 mt-4"><input name="admin_user" value="{config['admin_user']}" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 mb-2 outline-none text-white"><input name="new_pass" type="password" placeholder="New Password" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 outline-none text-white"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Save Master Settings</button></form><form method="POST" class="mt-4"><input type="hidden" name="action" value="set_webhook"><button class="w-full bg-emerald-600 py-3 rounded-xl font-black uppercase text-[10px] shadow-lg">🛠️ Auto Connect Webhook</button></form></div><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl h-[1000px] overflow-y-auto"><h2 class="text-xl font-bold mb-6 uppercase text-emerald-500">🎬 Manage Movies</h2><form action="/{site_name}/dashboard" method="GET" class="mb-4 flex gap-2"><input name="dq" placeholder="Search title..." class="w-full bg-black/40 p-3 rounded-xl border border-white/10 outline-none text-xs text-white"><button class="bg-blue-600 px-4 rounded-xl font-black text-xs uppercase shadow-lg">Filter</button></form>{movies_html}</div></div>"""
    return render_duplex(content, config)

@app.route('/<site_name>/edit-movie/<id>', methods=['GET', 'POST'])
def edit_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, config = get_site_db(site_name)
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        ls, rs = request.form.getlist('f_label'), request.form.getlist('f_ref')
        upd = {"title": request.form.get('title'), "year": request.form.get('year'), "rating": request.form.get('rating'), "plot": request.form.get('plot'), "category": request.form.get('category'), "files": [{"quality": l, "file_ref": r} for l, r in zip(ls, rs) if l and r]}
        db['movies'].update_one({"_id": ObjectId(id)}, {"$set": upd}); flash("✅ Movie Updated!"); return redirect(f'/{site_name}/dashboard')
    f_in = "".join([f'<div class="flex gap-4 mb-3"><input name="f_label" value="{f["quality"]}" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-1/3 text-white"><input name="f_ref" value="{f["file_ref"]}" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-2/3 text-white"></div>' for f in m['files']])
    content = f"""<div class="max-w-2xl mx-auto bg-slate-900 p-10 rounded-[40px] border border-white/5 shadow-2xl mt-4"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500 text-center">Edit Movie 🎬</h2><form method="POST" class="space-y-4 font-black uppercase text-[11px] text-white"><input name="title" value="{m['title']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none"><div class="grid grid-cols-2 gap-4"><input name="year" value="{m['year']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"><input name="rating" value="{m['rating']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"></div><input name="category" value="{m['category']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 text-white"><textarea name="plot" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 h-40 text-white">{m['plot']}</textarea><h3 class="text-emerald-500 underline uppercase tracking-widest mt-6 mb-2">Edit Download Buttons</h3>{f_in}<div class="flex gap-4"><input name="f_label" placeholder="Quality" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-1/3 text-white"><input name="f_ref" placeholder="Ref ID" class="bg-black/50 p-4 rounded-2xl border border-white/10 w-2/3 text-white"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg mt-8">Save Changes</button></form></div>"""
    return render_duplex(content, config)

@app.route('/<site_name>/delete/<id>')
def delete_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db, _ = get_site_db(site_name)
    db['movies'].delete_one({"_id": ObjectId(id)})
    flash("🗑️ Deleted!"); return redirect(f'/{site_name}/dashboard')

# --- Mega Clone System ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    db_m, config_m = get_site_db("Main")
    if request.method == 'POST':
        name, uri = request.form.get('name').strip(), request.form.get('db_uri').strip()
        if sites_col.find_one({"name": name}): flash("❌ Name Already Exists!")
        else:
            sites_col.insert_one({"name": name, "display_name": name + " Hub", "db_uri": uri, "logo_url": config_m['logo_url'], "header_notice": "Welcome to your Hub!", "admin_user": "admin", "admin_pass": generate_password_hash("admin123"), "categories": ["Action", "Hindi"], "tmdb_key": config_m['tmdb_key'], "bot_token": "", "bot_username": "", "ads": {}})
            s_u, a_u = f"https://{request.host}/{name}/", f"https://{request.host}/{name}/admin"
            content = f"""<div class="max-w-xl mx-auto bg-slate-900 p-10 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-6 text-white uppercase font-black"><h2 class="text-3xl text-emerald-400 mb-6 italic tracking-tighter">🎉 CLONE SUCCESSFUL! 🎉</h2><div class="space-y-4 text-left"><div class="copy-card p-5 bg-black/40 rounded-3xl border border-blue-500"><p class="text-[9px] text-blue-400">USER SITE URL</p><p id="s_url" class="font-mono text-sm truncate">{s_u}</p><button onclick="copyToClipboard('s_url')" class="bg-blue-600 px-4 py-1 rounded-full text-[10px] mt-2 shadow-xl">COPY URL</button></div><div class="copy-card p-5 bg-black/40 rounded-3xl border border-emerald-500"><p class="text-[9px] text-emerald-400">ADMIN PANEL URL</p><p id="a_url" class="font-mono text-sm truncate">{a_u}</p><button onclick="copyToClipboard('a_url')" class="bg-emerald-600 px-4 py-1 rounded-full text-[10px] mt-2 shadow-xl">COPY ADMIN</button></div></div><a href="/" class="mt-8 inline-block bg-white text-black px-10 py-3 rounded-full text-xs font-bold">BACK HOME</a></div>"""
            return render_duplex(content, config_m)
    return render_duplex("""<div class="max-w-md mx-auto bg-slate-900 p-12 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-10 text-white"><h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase italic tracking-tighter">Clone Premium Network 🚀</h2><form method="POST" class="space-y-6"><input name="name" placeholder="Network Name (No Spaces)" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 font-bold text-white outline-none text-center shadow-inner"><input name="db_uri" placeholder="Paste NEW MongoDB URI" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 text-[10px] text-white outline-none text-center shadow-inner" required><button class="w-full bg-emerald-600 hover:bg-emerald-700 py-5 rounded-3xl font-black uppercase tracking-widest text-white shadow-xl">Launch New Hub</button></form></div>""", config_m)

# --- Telegram Bot Webhook Engine ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    _, main_config = get_site_db("Main")
    if not main_config['bot_token']: return ''
    bot = telebot.TeleBot(main_config['bot_token'], threaded=False)
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))

    @bot.message_handler(commands=['start'])
    def handle_start(m):
        p = m.text.split()
        if len(p) > 1:
            for s in list(sites_col.find({})):
                db_s = MongoClient(s['db_uri'])['standalone_movie_db']
                f = db_s['stored_files'].find_one({"_id": ObjectId(p[1])})
                if f:
                    sent = bot.send_document(m.chat.id, f['file_id'], caption=f"🎥 মুভি: {f['file_name']}", protect_content=s.get('restrict_forward', False))
                    if s.get('auto_delete_min', 0) > 0: threading.Timer(s['auto_delete_min']*60, lambda: bot.delete_message(m.chat.id, sent.message_id)).start()
                    return
            bot.send_message(m.chat.id, "❌ Error: Link Expired!")
        else: bot.send_message(m.chat.id, "🎬 Movie Network Bot Connected.")

    @bot.message_handler(commands=['post'])
    def handle_post(m):
        parts = m.text.split(' ', 2)
        if len(parts) < 3: return bot.reply_to(m, "Format: `/post SiteName MovieQuery`")
        sn, mq = parts[1], parts[2]; db_s, c_s = get_site_db(sn)
        if not db_s: return bot.reply_to(m, "❌ HUB Not Found!")
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={c_s['tmdb_key']}&query={mq}").json()
        markup = telebot.types.InlineKeyboardMarkup()
        for r in res.get('results', [])[:5]: markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{sn}_{r['id']}"))
        bot.reply_to(m, f"🎬 Choose for {sn}:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_sel(c):
        _, sn, tid = c.data.split('_'); db_s, c_s = get_site_db(sn)
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}?api_key={c_s['tmdb_key']}&append_to_response=credits").json()
        cast = ", ".join([x['name'] for x in r.get('credits', {}).get('cast', [])[:8]])
        info = {"title": r['title'], "year": r.get('release_date','0000')[:4], "plot": r.get('overview',''), "rating": r.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": cast, "director": next((x['name'] for x in r.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")}
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "sn": sn, "files": [], "step": "cat"}}, upsert=True)
        markup = telebot.types.InlineKeyboardMarkup()
        for cat in c_s['categories']: markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{sn}_{cat.strip()}"))
        bot.send_message(c.message.chat.id, "Select Category:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
    def handle_cat(c):
        _, sn, cat = c.data.split('_'); db_s, _ = get_site_db(sn)
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"category": cat, "step": "file"}})
        bot.send_message(c.message.chat.id, f"✅ Category Set. Send Files for {sn}. Send /done when finished.")

    @bot.message_handler(content_types=['video', 'document', 'audio'])
    def handle_files(m):
        all_s = list(sites_col.find({}))
        for s in all_s:
            db_s = MongoClient(s['db_uri'])['movie_data_store']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st and st.get('step') == 'file':
                fwd = bot.forward_message(s['channel_id'], m.chat.id, m.message_id)
                fname = m.video.file_name if m.video else (m.document.file_name if m.document else "Download")
                ref_id = db_s['stored_files'].insert_one({"file_id": fwd.document.file_id if hasattr(fwd, 'document') else fwd.video.file_id, "file_name": fname, "msg_id": fwd.message_id}).inserted_id
                db_s['bot_states'].update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": fname[:8], "file_ref": str(ref_id)}}})
                return bot.reply_to(m, f"📥 File Recorded!")

    @bot.message_handler(commands=['done'])
    def handle_done(m):
        all_s = list(sites_col.find({}))
        for s in all_s:
            db_s = MongoClient(s['db_uri'])['movie_data_store']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st:
                db_s['movies'].insert_one({**st['info'], "category": st['category'], "files": st['files']})
                bot.send_message(m.chat.id, f"🚀 Published LIVE on {st['sn']}! ✅")
                db_s['bot_states'].delete_one({"user_id": m.from_user.id}); return

    bot.process_new_updates([update]); return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
