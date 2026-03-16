import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "master_cinema_absolute_v500"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['AbsoluteCinema_DB']
collection = db['media_hub']
settings_col = db['settings']

# --- UI Helpers (CSS & Tailwind) ---
BASE_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        body { background: #050505; color: white; font-family: 'Outfit', sans-serif; }
        .glass { background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .m-card:hover { transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 10px; }
        .card-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
        @media (min-width: 640px) { .card-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (min-width: 768px) { .card-grid { grid-template-columns: repeat(4, 1fr); } }
        @media (min-width: 1024px) { .card-grid { grid-template-columns: repeat(6, 1fr); } }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
        .scroll-hide::-webkit-scrollbar { display: none; }
    </style>
</head>
<body>
"""

NAV_HTML = """
<nav class="glass p-4 sticky top-0 z-50">
    <div class="container mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div class="flex items-center gap-6">
            <a href="/" class="text-2xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <div class="hidden md:flex gap-4 text-[10px] font-black uppercase tracking-widest text-zinc-400">
                <a href="/category/movie" class="hover:text-rose-500 transition">Movies</a>
                <a href="/category/tv" class="hover:text-rose-500 transition">TV Shows</a>
                <a href="/category/anime" class="hover:text-rose-500 transition">Anime</a>
            </div>
        </div>
        <div class="flex flex-1 max-w-md w-full gap-4">
            <form action="/" method="GET" class="flex flex-1 bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="মুভি বা টিভি খুঁজুন..." class="bg-transparent outline-none w-full text-xs text-white">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] flex items-center transition text-white shadow-lg">ADMIN</a>
        </div>
    </div>
</nav>
"""

CARD_TMPL = """
<a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 block group relative shadow-2xl">
    <div class="aspect-[2/3] overflow-hidden relative">
        <img src="{{ m.poster }}" class="w-full h-full object-cover" loading="lazy">
        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
            <i class="fa-solid fa-play-circle text-5xl"></i>
        </div>
        <div class="absolute top-2 right-2 bg-rose-600 text-[9px] font-black px-2 py-1 rounded-full shadow-lg text-white">⭐ {{ m.rating }}</div>
    </div>
    <div class="p-4">
        <h3 class="font-bold text-xs truncate uppercase text-zinc-200">{{ m.title }}</h3>
        <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase tracking-widest">{{ m.year }} | {{ m.type }}</p>
    </div>
</a>
"""

# --- ১. হোম পেজ (ক্যাটাগরি এবং এডস সহ) ---
@app.route('/')
def home():
    q = request.args.get('q')
    ads = settings_col.find_one({"name": "ads"}) or {}
    
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('release_date', -1))
        body = NAV_HTML + f'<main class="container mx-auto py-10 px-4"><h2 class="text-2xl font-black mb-8 italic border-l-4 border-rose-600 pl-4 uppercase tracking-tighter">Results: {q}</h2><div class="card-grid">'
        for m in items: body += render_template_string(CARD_TMPL, m=m)
        body += '</div></main>'
        return render_template_string(BASE_HEAD + body + "</body></html>")

    # Content Filtering
    anime = list(collection.find({"category": "Animation", "language": "ja"}).sort('release_date', -1).limit(12))
    movies = list(collection.find({"type": "movie", "category": {"$ne": "Animation"}}).sort('release_date', -1).limit(12))
    tv_shows = list(collection.find({"type": "tv", "category": {"$ne": "Animation"}}).sort('release_date', -1).limit(12))

    sections = [
        {"title": "Latest Movies", "items": movies, "link": "/category/movie"},
        {"title": "TV Series", "items": tv_shows, "link": "/category/tv"},
        {"title": "Latest Anime", "items": anime, "link": "/category/anime"}
    ]

    body = NAV_HTML 
    if ads.get('home_ad'): body += f'<div class="container mx-auto px-4 py-6 flex justify-center">{ads["home_ad"]}</div>'
        
    body += '<main class="container mx-auto py-10 px-4 space-y-20">'
    for sec in sections:
        if sec['items']:
            body += f'''<section><div class="flex justify-between items-end mb-8"><h2 class="text-2xl md:text-3xl font-black italic uppercase border-l-4 border-rose-600 pl-4 tracking-tighter">{sec['title']}</h2><a href="{sec['link']}" class="text-rose-600 font-bold text-xs hover:underline">SEE MORE <i class="fa fa-arrow-right ml-1"></i></a></div><div class="card-grid">'''
            for m in sec['items']: body += render_template_string(CARD_TMPL, m=m)
            body += '</div></section>'
    body += '</main>'
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ২. ক্যাটাগরি ভিউ (See More) ---
@app.route('/category/<ctype>')
def category_view(ctype):
    if ctype == "anime":
        items = list(collection.find({"category": "Animation", "language": "ja"}).sort('release_date', -1))
        title = "ALL ANIME SERIES"
    elif ctype == "movie":
        items = list(collection.find({"type": "movie", "category": {"$ne": "Animation"}}).sort('release_date', -1))
        title = "ALL MOVIES"
    else:
        items = list(collection.find({"type": "tv", "category": {"$ne": "Animation"}}).sort('release_date', -1))
        title = "ALL TV SHOWS"

    body = NAV_HTML + f'<main class="container mx-auto py-10 px-4"><h2 class="text-3xl font-black mb-10 italic uppercase border-l-4 border-rose-600 pl-4">{title}</h2><div class="card-grid">'
    for m in items: body += render_template_string(CARD_TMPL, m=m)
    body += '</div></main>'
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ৩. ডিটেইল পেজ (Trailer, OTT, Downloads, Gallery) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    ads = settings_col.find_one({"name": "ads"}) or {}
    dl_links = m.get('dl_links', [])
    
    body = NAV_HTML
    if ads.get('details_ad'): body += f'<div class="container mx-auto px-4 py-4 flex justify-center">{ads["details_ad"]}</div>'

    body += """
    <div class="relative min-h-screen pb-20">
        <div class="h-[50vh] md:h-[75vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[2px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>
        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-96 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3.5rem] border border-zinc-700 shadow-2xl">
                    <div class="mt-8 space-y-4">
                        <p class="text-center text-[10px] font-black text-rose-500 uppercase tracking-widest mb-2">Download Server</p>
                        {% for dl in dl_links %}
                        <a href="{{ dl.url }}" target="_blank" class="flex items-center justify-between bg-zinc-900 hover:bg-rose-600 p-5 rounded-3xl transition group border border-zinc-800">
                            <span class="font-bold text-xs uppercase">{{ dl.label }}</span>
                            <i class="fa fa-download text-rose-600 group-hover:text-white"></i>
                        </a>
                        {% endfor %}
                    </div>
                </div>
                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase text-[10px] font-bold tracking-widest">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-white">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>
                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center uppercase font-black text-[10px] mb-10">
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800"><p class="text-zinc-500 mb-1">Rating</p><p class="text-yellow-500 text-xl font-black">⭐ {{ m.rating }}</p></div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800"><p class="text-zinc-500 mb-1">Language</p><p class="text-lg text-white font-bold">{{ m.language | upper }}</p></div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800"><p class="text-zinc-500 mb-1">Director</p><p class="text-rose-500 truncate text-[11px]">{{ m.director.name }}</p></div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800"><p class="text-zinc-500 mb-1">Release</p><p class="text-white text-[11px]">{{ m.release_date }}</p></div>
                    </div>
                    {% if m.ott %}
                    <div class="p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-[9px] font-black uppercase text-rose-500 mb-6 tracking-[0.2em] italic">Where to Watch (OTT)</p>
                        <div class="flex flex-wrap gap-8">
                            {% for ott in m.ott %}
                            <div class="text-center"><img src="{{ ott.logo }}" class="w-12 h-12 rounded-xl border border-zinc-800 mb-2 mx-auto"><p class="text-[8px] font-bold">{{ ott.name }}</p></div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            {% if m.yt_id != "N/A" %}
            <div class="mt-20"><h3 class="text-3xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">Official Trailer</h3><div class="aspect-video w-full max-w-5xl mx-auto rounded-[3rem] overflow-hidden border border-zinc-800 shadow-2xl"><iframe class="w-full h-full" src="https://www.youtube.com/embed/{{ m.yt_id }}?rel=0" frameborder="0" allowfullscreen></iframe></div></div>
            {% endif %}

            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Cast & Crew</h3>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ m.director.id }}')">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl group-hover:scale-110 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ p.id }}')">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:scale-110 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ a.id }}')">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:scale-110 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 font-bold uppercase truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="mt-20"><h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Gallery</h3><div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">{% for img in m.gallery %}<div class="overflow-hidden rounded-3xl border border-zinc-800 shadow-xl"><img src="{{ img }}" class="w-full h-full object-cover hover:scale-110 transition duration-700"></div>{% endfor %}</div></div>
        </div>
    </div>

    <!-- Modal for Person Detail -->
    <div id="personModal" class="modal" onclick="this.style.display='none'">
        <div class="bg-zinc-900 border border-zinc-800 p-8 rounded-[3.5rem] max-w-3xl w-full max-h-[85vh] overflow-y-auto relative shadow-2xl" onclick="event.stopPropagation()">
            <div id="personContent" class="flex flex-col md:flex-row gap-8"></div>
        </div>
    </div>

    <script>
        async function showPersonDetail(id) {
            const m = document.getElementById('personModal');
            const c = document.getElementById('personContent');
            m.style.display = 'flex';
            c.innerHTML = '<div class="w-full text-center py-20 font-bold text-rose-600 tracking-widest">FETCHING DATA...</div>';
            try {
                const r = await fetch('/api/person/' + id);
                const d = await r.json();
                c.innerHTML = `
                    <img src="${d.photo}" class="w-64 h-80 object-cover rounded-[3rem] border border-zinc-700 shadow-2xl mx-auto">
                    <div class="flex-1">
                        <h2 class="text-4xl font-black text-rose-600 mb-2 tracking-tighter">${d.name}</h2>
                        <p class="text-[10px] font-black text-zinc-500 uppercase tracking-widest mb-6">${d.job}</p>
                        <div class="space-y-4 text-xs text-zinc-300">
                            <p><strong>BORN:</strong> ${d.birthday || 'Unknown'}</p>
                            <p><strong>FROM:</strong> ${d.place || 'Unknown'}</p>
                            <p class="leading-relaxed text-zinc-400 mt-6 pt-6 border-t border-zinc-800 italic">${d.bio || 'Bio not available.'}</p>
                        </div>
                    </div>`;
            } catch(e) { c.innerHTML = 'Error loading profile.'; }
        }
    </script>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", m=m, dl_links=dl_links)

# --- ৪. এডমিন ড্যাশবোর্ড (Stats, Bulk Sync, Manual Sync, Ads, Edit) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    body = '<div class="h-screen flex items-center justify-center bg-[#050505]"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm text-center shadow-2xl"><h2 class="text-3xl font-black mb-10 text-rose-600 italic tracking-widest uppercase">Admin Hub</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none text-white focus:border-rose-600 transition"><button class="w-full bg-rose-600 py-4 rounded-3xl font-black text-white shadow-xl shadow-rose-900/30">LOGIN</button></form></div>'
    return render_template_string(BASE_HEAD + body + "</body></html>")

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    stats = {
        "movies": collection.count_documents({"type": "movie", "category": {"$ne": "Animation"}}),
        "tv": collection.count_documents({"type": "tv", "category": {"$ne": "Animation"}}),
        "anime": collection.count_documents({"category": "Animation", "language": "ja"}),
        "drama": collection.count_documents({"category": "Drama"})
    }
    ads = settings_col.find_one({"name": "ads"}) or {}
    aq = request.args.get('aq')
    items = list(collection.find({"title": {"$regex": aq, "$options": "i"}}).sort('_id', -1)) if aq else list(collection.find().sort('_id', -1).limit(10))

    body = NAV_HTML + """
    <div class="container mx-auto py-10 px-4 max-w-6xl pb-40">
        <div class="flex justify-between items-center mb-16 border-b border-zinc-800 pb-10">
            <h1 class="text-5xl font-black italic tracking-tighter">CONTROL HUB</h1>
            <a href="/logout" class="text-rose-500 font-bold uppercase text-[10px] tracking-widest">Logout</a>
        </div>

        <div class="grid grid-cols-2 lg:grid-cols-4 gap-8 mb-20">
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 text-center"><p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Movies</p><h3 class="text-4xl font-black text-blue-500 tracking-tighter">{{ stats.movies }}</h3></div>
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 text-center"><p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Series</p><h3 class="text-4xl font-black text-rose-500 tracking-tighter">{{ stats.tv }}</h3></div>
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 text-center"><p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Anime</p><h3 class="text-4xl font-black text-purple-500 tracking-tighter">{{ stats.anime }}</h3></div>
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 text-center"><p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Drama</p><h3 class="text-4xl font-black text-yellow-500 tracking-tighter">{{ stats.drama }}</h3></div>
        </div>

        <div class="grid md:grid-cols-2 gap-10 mb-20">
            <!-- Bulk Auto Sync -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-black mb-8 italic text-blue-500 uppercase tracking-widest">Unlimited Bulk Sync</h3>
                <div class="space-y-4">
                    <input type="number" id="yr" placeholder="Year (e.g. 2024)" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none">
                    <input type="number" id="pg" placeholder="Total Pages" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none">
                    <select id="type" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none"><option value="movie">Movies</option><option value="tv">TV Shows</option></select>
                    <button onclick="startBulkSync()" id="bulk_btn" class="w-full bg-blue-600 py-4 rounded-3xl font-black text-white shadow-xl shadow-blue-900/30">START BULK SYNC</button>
                    <p id="bulk_stat" class="text-center text-[10px] font-mono text-zinc-500 uppercase mt-4"></p>
                </div>
            </div>
            <!-- Manual Sync -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-black mb-8 italic text-rose-600 uppercase tracking-widest">Manual Sync ID</h3>
                <div class="space-y-4">
                    <input type="text" id="m_id" placeholder="TMDB Content ID" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none">
                    <select id="m_type" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none"><option value="movie">Movie</option><option value="tv">TV Show</option></select>
                    <button onclick="manualSync()" class="w-full bg-rose-600 py-4 rounded-3xl font-black text-white shadow-xl shadow-rose-900/30">SYNC ID NOW</button>
                </div>
            </div>
        </div>

        <!-- Ads Configuration -->
        <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 mb-20 shadow-2xl">
            <h3 class="text-xl font-black mb-8 italic text-green-500 uppercase tracking-widest">Manage Advertisements</h3>
            <form action="/api/update_ads" method="POST" class="space-y-6">
                <textarea name="home_ad" placeholder="Home Page Ad Code" class="w-full bg-black border border-zinc-800 p-5 rounded-2xl h-24 text-zinc-400 font-mono text-[10px] outline-none">{ads.home_ad}</textarea>
                <textarea name="details_ad" placeholder="Details Page Ad Code" class="w-full bg-black border border-zinc-800 p-5 rounded-2xl h-24 text-zinc-400 font-mono text-[10px] outline-none">{ads.details_ad}</textarea>
                <button class="bg-green-600 px-10 py-4 rounded-full font-black text-white uppercase text-xs tracking-widest shadow-xl">Update Ads Config</button>
            </form>
        </div>

        <!-- Content Management List -->
        <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
            <div class="flex flex-col md:flex-row justify-between items-center mb-10 gap-4">
                <h3 class="text-xl font-black italic text-zinc-400 uppercase tracking-widest">Content Inventory</h3>
                <form method="GET" class="flex bg-black border border-zinc-800 rounded-full px-5 py-2 w-full md:max-w-xs">
                    <input type="text" name="aq" placeholder="Database search..." class="bg-transparent outline-none text-[11px] text-white w-full">
                    <button><i class="fa fa-search text-zinc-600"></i></button>
                </form>
            </div>
            <div class="overflow-x-auto">
                <table class="w-full text-left">
                    <thead class="text-zinc-500 font-black uppercase text-[10px] border-b border-zinc-800"><tr class="opacity-50 tracking-widest"><th class="py-4">Title</th><th class="py-4 text-center">Action</th></tr></thead>
                    <tbody class="divide-y divide-zinc-800">
                        {% for i in items %}
                        <tr>
                            <td class="py-6 font-bold text-xs uppercase">{{ i.title }} <span class="text-zinc-600 ml-2 font-normal">({{ i.year }})</span></td>
                            <td class="py-6 text-center space-x-6"><a href="/edit/{{ i.tmdb_id }}" class="text-blue-500 text-[10px] font-black hover:underline uppercase tracking-widest">EDIT / LINKS</a><a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete Content?')" class="text-rose-500 text-[10px] font-black hover:underline uppercase tracking-widest">DELETE</a></td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
    async function startBulkSync() {
        const yr = document.getElementById('yr').value;
        const pg = document.getElementById('pg').value || 1;
        const t = document.getElementById('type').value;
        const stat = document.getElementById('bulk_stat');
        if(!yr) return alert('Provide Year!');
        document.getElementById('bulk_btn').disabled = true;
        for(let p=1; p <= pg; p++) {
            stat.innerHTML = 'Status: Page ' + p + ' Fetching...';
            const res = await fetch(`/api/get_ids?year=${yr}&page=${p}&type=${t}`);
            const data = await res.json();
            for(let item of data.ids) {
                stat.innerHTML = 'Auto Syncing: ' + item.title;
                await fetch(`/api/sync_single?id=${item.id}&type=${t}`);
            }
        }
        stat.innerHTML = 'SYNC PROCESS FINISHED!'; location.reload();
    }
    async function manualSync() {
        const id = document.getElementById('m_id').value;
        const t = document.getElementById('m_type').value;
        if(!id) return alert('Provide Content ID!');
        await fetch(`/api/sync_single?id=${id}&type=${t}`);
        location.reload();
    }
    </script>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", stats=stats, ads=ads, items=items)

# --- ৫. এডিট এবং আনলিমিটেড ডাউনলোড লিঙ্ক সিস্টেম ---
@app.route('/edit/<tid>', methods=['GET', 'POST'])
def edit(tid):
    if not session.get('logged'): return redirect('/admin')
    m = collection.find_one({"tmdb_id": tid})
    if request.method == 'POST':
        links_raw = request.form.get('links').strip().split('\n')
        dl_links = [{"label": l.split('|')[0].strip(), "url": l.split('|')[1].strip()} for l in links_raw if '|' in l]
        collection.update_one({"tmdb_id": tid}, {"$set": {"title": request.form.get('t'), "story": request.form.get('s'), "dl_links": dl_links}})
        return redirect('/admin/dashboard')

    links_str = "\n".join([f"{l['label']} | {l['url']}" for l in m.get('dl_links', [])])
    body = f"""<div class="container mx-auto py-24 px-4 max-w-2xl"><form method="POST" class="bg-zinc-900 p-14 rounded-[4.5rem] border border-zinc-800 shadow-2xl"><h2 class="text-3xl font-black mb-12 italic uppercase text-rose-600 tracking-tighter border-l-4 border-rose-600 pl-4">Update Content</h2><div class="space-y-8"><div><label class="text-[10px] font-black text-zinc-500 uppercase tracking-widest block ml-4 mb-2">Display Title</label><input name="t" value="{m['title']}" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-white outline-none focus:border-blue-600 transition"></div><div><label class="text-[10px] font-black text-zinc-500 uppercase tracking-widest block ml-4 mb-2">Description / Story</label><textarea name="s" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-white h-44 outline-none focus:border-blue-600 transition">{m['story']}</textarea></div><div><label class="text-[10px] font-black text-zinc-500 uppercase tracking-widest block ml-4 mb-2">Download Links (Format: Label | URL)</label><textarea name="links" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-blue-400 font-mono text-[11px] h-48 outline-none focus:border-blue-600 transition" placeholder="720p HD | https://server.com/dl">{links_str}</textarea></div><button class="w-full bg-blue-600 py-5 rounded-[2.5rem] font-black text-white uppercase tracking-widest shadow-xl shadow-blue-900/30">Save Changes</button></div></form></div>"""
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ৬. ব্যাকএন্ড এপিআই লজিক (Sync Engine) ---

@app.route('/api/update_ads', methods=['POST'])
def update_ads():
    if session.get('logged'): 
        settings_col.update_one({"name": "ads"}, {"$set": {"home_ad": request.form.get('home_ad'), "details_ad": request.form.get('details_ad')}}, upsert=True)
    return redirect('/admin/dashboard')

@app.route('/api/person/<id>')
def api_person(id):
    url = f"https://api.themoviedb.org/3/person/{id}?api_key={TMDB_API_KEY}"
    d = requests.get(url).json()
    return jsonify({"name": d.get('name'), "photo": IMG_BASE + d.get('profile_path') if d.get('profile_path') else "https://via.placeholder.com/200", "bio": d.get('biography'), "birthday": d.get('birthday'), "place": d.get('place_of_birth'), "job": d.get('known_for_department')})

@app.route('/api/get_ids')
def get_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/api/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else ""} for p in crew if p['job'] == 'Director'), {"id": 0, "name": "N/A", "photo": ""})
    producers = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else ""} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:15]]
    
    # OTT & Providers
    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:12]]

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path') if d.get('poster_path') else "",
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')), "gallery": gallery
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/del/<tid>')
def delete(tid):
    if session.get('logged'): collection.delete_one({"tmdb_id": tid})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
