import os, requests, telebot, re
from flask import Flask, render_template_string, request, redirect, url_for, session, flash, abort
from pymongo import MongoClient
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash

# --- অ্যাপ কনফিগারেশন ---
app = Flask(__name__)
app.secret_key = "STANDALONE_ULTIMATE_PREMIUM_V99"

# --- মাস্টার কানেকশন (শুধুমাত্র সাইট নেটওয়ার্ক ম্যানেজ করার জন্য) ---
MASTER_MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
master_client = MongoClient(MASTER_MONGO_URI)
master_db = master_client['network_engine_db']
sites_col = master_db['registered_sites']

# --- ডাটাবেস কানেকশন ক্যাশ (পারফরম্যান্সের জন্য) ---
db_cache = {}

def get_db(site_name):
    if site_name in db_cache:
        return db_cache[site_name]
    site_cfg = sites_col.find_one({"name": site_name})
    if not site_cfg: return None
    try:
        client = MongoClient(site_cfg['db_uri'])
        db = client['standalone_movie_db']
        db_cache[site_name] = db
        return db
    except: return None

# --- ডিফল্ট মেইন সাইট ইনিশিয়াল ---
if not sites_col.find_one({"name": "Main"}):
    sites_col.insert_one({
        "name": "Main", "display_name": "Premium Movie Hub 🍿",
        "db_uri": MASTER_MONGO_URI, "logo_url": "https://i.ibb.co/V9XmN8p/logo.png",
        "header_notice": "🔥 স্বাগতম! সরাসরি বটের মাধ্যমে হাই-স্পিড মুভি ডাউনলোড করুন। 🔥",
        "admin_user": "admin", "admin_pass": generate_password_hash("admin123"),
        "categories": ["Action 💥", "Hindi 🍿", "English 🇺🇸", "Bangla 🇧🇩"],
        "tmdb_key": "275aff9f1c570308fa10d14c6f49f998", "bot_token": "", "bot_username": "",
        "ads": {"banner_ad": "", "popunder": "", "social_bar": "", "header_ad": "", "footer_ad": "", "negative_banner": ""}
    })

# --- প্রিমিয়াম ডাইনামিক রেন্ডার ইঞ্জিন (Auto Responsive) ---
def render_pro_ui(content, config):
    ads = config.get('ads', {})
    cats = config.get('categories', [])
    sn = config['name']
    cat_links = "".join([f'<a href="/{sn}/?cat={c.strip()}" class="hover:text-blue-500 transition">{c.strip()}</a>' for c in cats])
    
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
            .glass {{ background: rgba(15, 23, 42, 0.92); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
            .card {{ background: #0f172a; border: 1px solid rgba(255,255,255,0.05); transition: 0.4s; }}
            .card:hover {{ transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 0 30px rgba(59, 130, 246, 0.3); }}
            .swiper-slide img {{ height: 550px; width: 100%; object-fit: cover; border-radius: 30px; filter: brightness(0.4); }}
            @media (max-width: 768px) {{ .swiper-slide img {{ height: 320px; }} }}
            .copy-btn {{ background: #10b981; padding: 10px; border-radius: 10px; cursor: pointer; text-align: center; font-weight: 900; }}
        </style>
        {ads.get('popunder', '')} {ads.get('social_bar', '')}
    </head>
    <body>
        {ads.get('header_ad', '')}
        <div class="bg-blue-700 text-white text-center py-2 text-[10px] md:text-xs font-black uppercase tracking-widest px-4">{config['header_notice']}</div>
        
        <nav class="glass sticky top-0 z-50">
            <div class="container mx-auto px-4 py-4 flex justify-between items-center">
                <div class="flex items-center gap-4">
                    <a href="/clone-site" class="bg-emerald-600 text-white px-3 py-1 rounded text-[10px] font-black uppercase shadow-lg">🚀 CLONE</a>
                    <a href="/{sn}/" class="flex items-center gap-2">
                        <img src="{config['logo_url']}" class="h-8 md:h-10">
                        <span class="text-xl md:text-2xl font-black text-white tracking-tighter hidden sm:block">{config['display_name']}</span>
                    </a>
                </div>
                <div class="flex items-center gap-4">
                    <form action="/{sn}/search" method="GET" class="hidden md:flex bg-black/50 rounded-full px-4 py-1 border border-white/10">
                        <input name="q" placeholder="Search..." class="bg-transparent outline-none text-xs text-white w-32">
                    </form>
                    <div class="hidden lg:flex gap-5 text-[11px] font-bold uppercase tracking-tighter">{cat_links}</div>
                    <a href="/{sn}/admin" class="bg-slate-800 hover:bg-blue-600 px-4 py-1.5 rounded-full text-[10px] font-bold transition">ADMIN ⚙️</a>
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
            function copyTo(id) {{ var t = document.getElementById(id).innerText; navigator.clipboard.writeText(t); alert("URL Copied! ✅"); }}
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
    db = get_db(site_name)
    config = sites_col.find_one({"name": site_name})
    if not db: return "Site Not Found", 404
    
    q, cat = request.args.get('q'), request.args.get('cat')
    query = {"category": cat} if cat else {}
    if q: query["title"] = {"$regex": q, "$options": "i"}
    
    movies = list(db['movies'].find(query).sort('_id', -1))
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
                    <a href="/{site_name}/movie/{s["_id"]}" class="bg-blue-600 hover:bg-blue-700 px-8 py-3 rounded-full font-black text-sm inline-block shadow-lg transition">VIEW DETAILS</a>
                </div>
            </div>"""
        slider_html += '</div><div class="swiper-pagination"></div></div>'

    grid_title = q if q else (cat if cat else "Latest Uploads 🍿")
    grid_html = f'<h2 class="text-2xl font-black mb-8 border-l-4 border-blue-600 pl-4 uppercase tracking-widest text-blue-500">{grid_title}</h2><div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4 md:gap-8">'
    for m in movies:
        grid_html += f"""
        <a href="/{site_name}/movie/{m["_id"]}" class="card rounded-3xl overflow-hidden group text-center p-2">
            <div class="relative overflow-hidden">
                <img src="{m["poster"]}" class="h-64 md:h-80 w-full object-cover rounded-xl mb-2 group-hover:scale-110 transition duration-500">
                <div class="absolute top-2 right-2 bg-black/80 px-2 py-1 rounded-lg text-[9px] font-black uppercase">⭐ {m.get("rating", "0.0")}</div>
            </div>
            <h3 class="text-[11px] font-black truncate uppercase text-slate-100 group-hover:text-blue-500 transition">{m["title"]}</h3>
            <p class="text-[10px] text-slate-500 mt-1">{m["year"]} | {m["category"]}</p>
        </a>"""
    grid_html += '</div>'
    
    return render_pro_ui(slider_html + grid_html, config)

@app.route('/<site_name>/movie/<id>')
def movie_page(site_name, id):
    db = get_db(site_name)
    config = sites_col.find_one({"name": site_name})
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if not m: return "Movie Not Found", 404
    
    links = "".join([f'<a href="https://t.me/{config["bot_username"]}?start={f["file_ref"]}" target="_blank" class="flex justify-between items-center bg-blue-600 hover:bg-blue-700 p-5 rounded-2xl font-black transition shadow-2xl mb-4 border-b-4 border-blue-900 uppercase tracking-tighter"><span>📥 DOWNLOAD {f["quality"]}</span><span class="text-[10px] bg-black/20 px-3 py-1 rounded-full font-black">Secure Bot</span></a>' for f in m['files']])

    content = f"""<div class="flex flex-col lg:flex-row gap-12 mt-4"><div class="w-full lg:w-1/3 shrink-0"><img src="{m['poster']}" class="rounded-[40px] shadow-2xl w-full border border-white/5 sticky top-24"></div><div class="flex-1"><h1 class="text-4xl md:text-8xl font-black text-white leading-tight uppercase tracking-tighter">{m['title']}</h1><div class="flex flex-wrap gap-4 mt-8"><span class="bg-blue-600 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['category']}</span><span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest text-yellow-500 shadow-xl">⭐ {m['rating']}</span><span class="bg-slate-800 px-6 py-2 rounded-xl text-xs font-black uppercase tracking-widest">{m['year']}</span></div><div class="mt-10 p-8 bg-slate-900/50 rounded-3xl border border-white/5 shadow-inner"><h3 class="text-blue-500 font-black text-xs uppercase mb-4 tracking-widest text-white">Full Storyline 📖</h3><p class="text-slate-400 text-lg md:text-xl leading-relaxed italic font-medium">"{m['plot']}"</p></div><div class="mt-8 grid md:grid-cols-2 gap-6 text-[13px]"><div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🎬 Director</b> {m.get('director', 'Unknown')}</div><div class="bg-black/40 p-5 rounded-2xl border border-white/5"><b class="text-blue-500 uppercase block mb-1">🌟 Starring Cast</b> {m.get('cast', 'Unknown')}</div></div><div class="mt-12 space-y-4"><h2 class="text-3xl font-black uppercase tracking-tighter mb-6 flex items-center gap-3"><span class="w-2 h-8 bg-emerald-500 rounded-full"></span> Download From Telegram</h2>{links}</div></div></div>"""
    return render_pro_ui(content, config)

# --- Admin Panel: Full Search/Edit/Delete/Ads ---

@app.route('/<site_name>/admin', methods=['GET', 'POST'])
def admin_login(site_name):
    config = sites_col.find_one({"name": site_name})
    if request.method == 'POST':
        u, p = request.form.get('user'), request.form.get('pass')
        if u == config['admin_user'] and check_password_hash(config['admin_pass'], p):
            session[f'auth_{site_name}'] = True
            return redirect(f'/{site_name}/dashboard')
        flash("❌ Authentication Failed!")
    return render_pro_ui(f"""<div class="max-w-sm mx-auto bg-slate-900 p-10 rounded-[40px] border border-blue-500 shadow-2xl mt-10 text-center"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">{site_name} Admin</h2><form method="POST" class="space-y-4"><input name="user" placeholder="Admin Username" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white"><input name="pass" type="password" placeholder="Password" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none text-white"><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Authenticate</button></form></div>""", config)

@app.route('/<site_name>/dashboard', methods=['GET', 'POST'])
def dashboard(site_name):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db = get_db(site_name)
    config = sites_col.find_one({"name": site_name})
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == "save_config":
            new_pass = request.form.get('new_pass')
            upd = {
                "display_name": request.form.get('display_name'), "logo_url": request.form.get('logo_url'),
                "header_notice": request.form.get('header_notice'), "admin_user": request.form.get('admin_user'),
                "tmdb_key": request.form.get('tmdb_key'), "bot_token": request.form.get('bot_token'),
                "bot_username": request.form.get('bot_username').replace('@',''),
                "categories": request.form.get('categories').split(','),
                "ads": {"banner_ad": request.form.get('banner_ad'), "popunder": request.form.get('popunder'), "social_bar": request.form.get('social_bar'), "header_ad": request.form.get('header_ad'), "footer_ad": request.form.get('footer_ad'), "native_banner": request.form.get('native_banner')}
            }
            if new_pass: upd["admin_pass"] = generate_password_hash(new_pass)
            sites_col.update_one({"name": site_name}, {"$set": upd})
            flash("✅ Settings Saved!")
        elif action == "set_webhook":
            requests.get(f"https://api.telegram.org/bot{config['bot_token']}/setWebhook?url=https://{request.host}/telegram-webhook")
            flash("✅ Webhook Connected!")
        return redirect(f'/{site_name}/dashboard')

    dq = request.args.get('dq')
    mq = {"title": {"$regex": dq, "$options": "i"}} if dq else {}
    movies = list(db['movies'].find(mq).sort('_id', -1))
    movies_list = "".join([f'<div class="flex items-center justify-between bg-black/40 p-4 rounded-2xl border border-white/5 mb-3 shadow-lg"><div class="flex items-center gap-4"><img src="{m["poster"]}" class="h-10 w-8 rounded-lg object-cover"><span class="text-xs font-black truncate w-32 md:w-60 uppercase">{m["title"]}</span></div><div class="flex gap-2"><a href="/{site_name}/edit-movie/{m["_id"]}" class="bg-blue-600 px-3 py-1 rounded text-[9px] font-black uppercase">Edit</a><a href="/{site_name}/delete/{m["_id"]}" class="bg-red-600 px-3 py-1 rounded text-[9px] font-black uppercase" onclick="return confirm(\'Delete?\')">Delete</a></div></div>' for m in movies])

    content = f"""<div class="grid lg:grid-cols-2 gap-10"><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl"><h2 class="text-xl font-bold mb-6 uppercase text-blue-500">⚙️ Master Configuration</h2><form method="POST" class="space-y-4 text-[10px] font-black uppercase tracking-widest"><input type="hidden" name="action" value="save_config"><div class="grid grid-cols-2 gap-4"><input name="display_name" value="{config['display_name']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="logo_url" value="{config['logo_url']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><input name="header_notice" value="{config['header_notice']}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><div class="grid grid-cols-2 gap-4"><input name="tmdb_key" value="{config['tmdb_key']}" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="bot_token" value="{config['bot_token']}" placeholder="Bot Token" class="bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"></div><input name="bot_username" value="{config.get('bot_username','')}" placeholder="Bot Username (no @)" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><input name="categories" value="{','.join(config['categories'])}" class="w-full bg-black/50 p-4 rounded-xl border border-white/10 outline-none text-white"><h3 class="text-emerald-500 underline mt-4 tracking-widest">💰 Ad Management (HTML)</h3><div class="grid grid-cols-2 gap-4"><textarea name="banner_ad" placeholder="Banner Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('banner_ad','')}</textarea><textarea name="popunder" placeholder="Popunder Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('popunder','')}</textarea><textarea name="header_ad" placeholder="Header Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('header_ad','')}</textarea><textarea name="footer_ad" placeholder="Footer Ad" class="bg-black/50 p-3 rounded-xl border border-white/10 h-20">{config.get('ads',{}).get('footer_ad','')}</textarea></div><div class="p-6 bg-blue-600/10 rounded-[30px] border border-blue-600/20 mt-4"><input name="admin_user" value="{config['admin_user']}" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 mb-2 outline-none text-white"><input name="new_pass" type="password" placeholder="New Password" class="w-full bg-black/60 p-4 rounded-xl border border-white/10 outline-none text-white"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg">Save Master Settings</button></form><form method="POST" class="mt-4"><input type="hidden" name="action" value="set_webhook"><button class="w-full bg-emerald-600 py-3 rounded-xl font-black uppercase text-[10px] shadow-lg">🛠️ Auto Connect Telegram Webhook</button></form></div><div class="bg-slate-900 p-8 rounded-[40px] border border-white/5 shadow-2xl h-[1000px] overflow-y-auto"><h2 class="text-xl font-bold mb-6 uppercase text-emerald-500">🎬 Manage Movies</h2><form action="/{site_name}/dashboard" method="GET" class="mb-4 flex gap-2"><input name="dq" placeholder="Search by title..." class="w-full bg-black/40 p-3 rounded-xl border border-white/10 outline-none text-xs text-white"><button class="bg-blue-600 px-4 rounded-xl font-black text-xs uppercase shadow-lg">Filter</button></form>{movies_list}</div></div>"""
    return render_pro_ui(content, config)

@app.route('/<site_name>/edit-movie/<id>', methods=['GET', 'POST'])
def edit_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db = get_db(site_name)
    config = sites_col.find_one({"name": site_name})
    m = db['movies'].find_one({"_id": ObjectId(id)})
    if request.method == 'POST':
        labels = request.form.getlist('file_label')
        refs = request.form.getlist('file_ref')
        new_files = [{"quality": l, "file_ref": r} for l, r in zip(labels, refs) if l and r]
        upd = {"title": request.form.get('title'), "year": request.form.get('year'), "rating": request.form.get('rating'), "plot": request.form.get('plot'), "category": request.form.get('category'), "files": new_files}
        db['movies'].update_one({"_id": ObjectId(id)}, {"$set": upd})
        flash("✅ Movie Updated!")
        return redirect(f'/{site_name}/dashboard')
    
    file_inputs = "".join([f'<div class="flex gap-2 mb-2"><input name="file_label" value="{f["quality"]}" class="bg-black/50 p-2 rounded-xl border border-white/10 w-1/3 text-white"><input name="file_ref" value="{f["file_ref"]}" class="bg-black/50 p-2 rounded-xl border border-white/10 w-2/3 text-white"></div>' for f in m['files']])
    
    content = f"""<div class="max-w-2xl mx-auto bg-slate-900 p-10 rounded-[40px] border border-white/5 shadow-2xl mt-4"><h2 class="text-2xl font-black mb-8 uppercase text-blue-500">Edit Complete Info 🎬</h2><form method="POST" class="space-y-4 font-black uppercase text-[11px] text-white"><input name="title" value="{m['title']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 outline-none"><div class="grid grid-cols-2 gap-4"><input name="year" value="{m['year']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"><input name="rating" value="{m['rating']}" class="bg-black/50 p-4 rounded-2xl border border-white/10"></div><input name="category" value="{m['category']}" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10"><textarea name="plot" class="w-full bg-black/50 p-4 rounded-2xl border border-white/10 h-40">{m['plot']}</textarea><h3 class="text-emerald-500 underline uppercase tracking-widest mt-6 mb-2">Edit Download Buttons (Labels & Refs)</h3>{file_inputs}<div class="text-blue-400 text-[10px] mb-2">Add New Button (Empty fields to ignore):</div><div class="flex gap-2"><input name="file_label" placeholder="Quality" class="bg-black/50 p-2 rounded-xl border border-white/10 w-1/3"><input name="file_ref" placeholder="File Ref ID" class="bg-black/50 p-2 rounded-xl border border-white/10 w-2/3"></div><button class="w-full bg-blue-600 py-4 rounded-2xl font-black uppercase shadow-lg mt-8">Save Everything</button></form></div>"""
    return render_pro_ui(content, config)

@app.route('/<site_name>/delete/<id>')
def delete_movie(site_name, id):
    if not session.get(f'auth_{site_name}'): return redirect(f'/{site_name}/admin')
    db = get_db(site_name)
    db['movies'].delete_one({"_id": ObjectId(id)})
    flash("🗑️ Movie Deleted!")
    return redirect(f'/{site_name}/dashboard')

# --- Network Clone System ---

@app.route('/clone-site', methods=['GET', 'POST'])
def clone_page():
    config = sites_col.find_one({"name": "Main"})
    if request.method == 'POST':
        name, uri = request.form.get('name').strip(), request.form.get('db_uri').strip()
        if sites_col.find_one({"name": name}): flash("❌ Name Already In Use!")
        else:
            sites_col.insert_one({"name": name, "display_name": name + " Hub", "db_uri": uri, "logo_url": config['logo_url'], "header_notice": "Welcome to your new site!", "admin_user": "admin", "admin_pass": generate_password_hash("admin123"), "categories": ["Action", "Hindi"], "tmdb_key": config['tmdb_key'], "bot_token": "", "bot_username": "", "ads": {}})
            site_url = f"https://{request.host}/{name}/"
            admin_url = f"https://{request.host}/{name}/admin"
            return f"""<div style="background:#000;color:#fff;padding:40px;text-align:center;font-family:sans-serif;height:100vh;"><h1>🎉 Network Cloned! 🎉</h1><div style="background:#111;padding:20px;border-radius:20px;display:inline-block;text-align:left;border:1px solid cyan;"><p id='s'><b>Main URL:</b> {site_url}</p><p id='a'><b>Admin Panel:</b> {admin_url}</p><p><b>Password:</b> admin123</p></div><br><button onclick="navigator.clipboard.writeText('{site_url}');alert('Copied!')" style="margin-top:20px;background:blue;color:#fff;padding:10px 20px;border:none;border-radius:10px;cursor:pointer;">Copy Site URL</button></div>"""
    return render_pro_ui("""<div class="max-w-md mx-auto bg-slate-900 p-12 rounded-[50px] border border-emerald-500 shadow-2xl text-center mt-10"><h2 class="text-3xl font-black mb-6 text-emerald-500 uppercase italic tracking-tighter">Clone Premium Network 🚀</h2><form method="POST" class="space-y-6"><input name="name" placeholder="Unique Site Name (No Spaces)" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 font-bold text-white outline-none text-center shadow-inner"><input name="db_uri" placeholder="Enter Your Dedicated MongoDB Atlas URI" class="w-full bg-black/50 p-5 rounded-3xl border border-white/10 text-xs text-white outline-none text-center shadow-inner" required><button class="w-full bg-emerald-600 hover:bg-emerald-700 py-5 rounded-3xl font-black uppercase tracking-widest text-white shadow-2xl transition-all">Launch Standalone Site</button></form></div>""", config)

# --- Bot Webhook: All-in-One Engine ---

@app.route('/telegram-webhook', methods=['POST'])
def webhook():
    m_cfg = sites_col.find_one({"name": "Main"})
    if not m_cfg or not m_cfg['bot_token']: return ''
    bot = telebot.TeleBot(m_cfg['bot_token'], threaded=False)
    update = telebot.types.Update.de_json(request.get_data().decode('utf-8'))

    @bot.message_handler(commands=['start'])
    def handle_start(m):
        p = m.text.split()
        if len(p) > 1:
            all_s = list(sites_col.find({}))
            for s in all_s:
                db_s = MongoClient(s['db_uri'])['standalone_movie_db']
                f = db_s['stored_files'].find_one({"_id": ObjectId(p[1])})
                if f: return bot.send_document(m.chat.id, f['file_id'], caption=f"🎬 Movie: *{f['file_name']}*\n\n🔥 Enjoy High Speed Download! 🔥", parse_mode="Markdown")
            bot.send_message(m.chat.id, "❌ Error: File Not Found or Site Inactive!")
        else: bot.send_message(m.chat.id, "🎬 Welcome to Movie Master Bot! Find movies on the website.")

    @bot.message_handler(commands=['post'])
    def handle_post(m):
        parts = m.text.split(' ', 2)
        if len(parts) < 3: return bot.reply_to(m, "Usage: `/post SiteName MovieQuery`")
        sn, mq = parts[1], parts[2]
        db_s = get_db(sn)
        site_cfg = sites_col.find_one({"name": sn})
        if not db_s: return bot.reply_to(m, "❌ Site Not Found!")
        res = requests.get(f"https://api.themoviedb.org/3/search/movie?api_key={site_cfg['tmdb_key']}&query={mq}").json()
        markup = telebot.types.InlineKeyboardMarkup()
        for r in res.get('results', [])[:5]:
            markup.add(telebot.types.InlineKeyboardButton(f"{r['title']} ({r.get('release_date','')[:4]})", callback_data=f"sel_{sn}_{r['id']}"))
        bot.reply_to(m, f"🎬 Results for {sn}:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('sel_'))
    def handle_sel(c):
        _, sn, tid = c.data.split('_')
        site_cfg = sites_col.find_one({"name": sn})
        db_s = get_db(sn)
        r = requests.get(f"https://api.themoviedb.org/3/movie/{tid}?api_key={site_cfg['tmdb_key']}&append_to_response=credits").json()
        cast = ", ".join([x['name'] for x in r.get('credits', {}).get('cast', [])[:8]])
        info = {"title": r['title'], "year": r.get('release_date','0000')[:4], "plot": r.get('overview',''), "rating": r.get('vote_average',0), "poster": f"https://image.tmdb.org/t/p/w500{r.get('poster_path')}", "banner": f"https://image.tmdb.org/t/p/original{r.get('backdrop_path')}", "cast": cast, "director": next((x['name'] for x in r.get('credits', {}).get('crew', []) if x['job'] == 'Director'), "Unknown")}
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"info": info, "sn": sn, "files": [], "step": "cat"}}, upsert=True)
        markup = telebot.types.InlineKeyboardMarkup()
        for cat in site_cfg['categories']: markup.add(telebot.types.InlineKeyboardButton(cat, callback_data=f"cat_{sn}_{cat.strip()}"))
        bot.send_message(c.message.chat.id, "✅ Details Fetched. Select Category:", reply_markup=markup)

    @bot.callback_query_handler(func=lambda c: c.data.startswith('cat_'))
    def handle_cat(c):
        _, sn, cat = c.data.split('_')
        db_s = get_db(sn)
        db_s['bot_states'].update_one({"user_id": c.from_user.id}, {"$set": {"category": cat, "step": "file"}})
        bot.send_message(c.message.chat.id, f"✅ Category Set. Now Send Files for {sn}. Send /done when finished.")

    @bot.message_handler(content_types=['video', 'document', 'audio'])
    def handle_files(m):
        all_s = list(sites_col.find({}))
        for s in all_s:
            db_s = MongoClient(s['db_uri'])['standalone_movie_db']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st and st.get('step') == 'file':
                fid = m.video.file_id if m.video else (m.document.file_id if m.document else m.audio.file_id)
                fname = m.video.file_name if m.video else (m.document.file_name if m.document else "Download")
                qual = "1080P" if "1080" in fname else ("720P" if "720" in fname else ("480P" if "480" in fname else "HD"))
                ref_id = db_s['stored_files'].insert_one({"file_id": fid, "file_name": fname}).inserted_id
                db_s['bot_states'].update_one({"user_id": m.from_user.id}, {"$push": {"files": {"quality": qual, "file_ref": str(ref_id)}}})
                return bot.reply_to(m, f"📥 {qual} Added!")

    @bot.message_handler(commands=['done'])
    def handle_done(m):
        all_s = list(sites_col.find({}))
        for s in all_s:
            db_s = MongoClient(s['db_uri'])['standalone_movie_db']
            st = db_s['bot_states'].find_one({"user_id": m.from_user.id})
            if st:
                db_s['movies'].insert_one({**st['info'], "category": st['category'], "files": st['files']})
                bot.send_message(m.chat.id, f"🚀 Movie Live on {st['sn']} HUB! ✅")
                db_s['bot_states'].delete_one({"user_id": m.from_user.id})
                return

    bot.process_new_updates([update])
    return ''

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
