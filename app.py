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

# --- UI Helpers (CSS & HTML) ---
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
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
        .card-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
        @media (min-width: 640px) { .card-grid { grid-template-columns: repeat(3, 1fr); } }
        @media (min-width: 768px) { .card-grid { grid-template-columns: repeat(4, 1fr); } }
        @media (min-width: 1024px) { .card-grid { grid-template-columns: repeat(6, 1fr); } }
        .scroll-hide::-webkit-scrollbar { display: none; }
    </style>
</head>
<body>
"""

NAV_HTML = """
<nav class="glass p-4 sticky top-0 z-50">
    <div class="container mx-auto flex justify-between items-center gap-4">
        <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
        <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
            <input type="text" name="q" placeholder="মুভি, টিভি বা এক্টর..." class="bg-transparent outline-none w-full text-xs md:text-sm text-white">
            <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
        </form>
        <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] md:text-xs transition text-white">ADMIN</a>
    </div>
</nav>
"""

CARD_HTML = """
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

# --- ১. হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    ads = settings_col.find_one({"name": "ads"}) or {}
    
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('release_date', -1))
        body = NAV_HTML + f'<main class="container mx-auto py-10 px-4"><h2 class="text-2xl font-black mb-6 italic border-l-4 border-rose-600 pl-4">SEARCH RESULTS: {q}</h2><div class="card-grid">'
        for m in items: body += render_template_string(CARD_HTML, m=m)
        body += '</div></main>'
        return render_template_string(BASE_HEAD + body + "</body></html>")

    # Categories Logic
    anime = list(collection.find({"category": "Animation", "language": "ja"}).sort('release_date', -1).limit(10))
    movies = list(collection.find({"type": "movie", "category": {"$ne": "Animation"}}).sort('release_date', -1).limit(10))
    tv_shows = list(collection.find({"type": "tv", "category": {"$ne": "Animation"}}).sort('release_date', -1).limit(10))

    sections = [
        {"title": "Latest Movies", "items": movies, "link": "/category/movie"},
        {"title": "TV Series", "items": tv_shows, "link": "/category/tv"},
        {"title": "Latest Anime", "items": anime, "link": "/category/anime"}
    ]

    body = NAV_HTML 
    if ads.get('home_ad'):
        body += f'<div class="container mx-auto px-4 py-4 flex justify-center overflow-hidden">{ads["home_ad"]}</div>'
        
    body += '<main class="container mx-auto py-10 px-4 space-y-16">'
    for sec in sections:
        if sec['items']:
            body += f'''<section><div class="flex justify-between items-end mb-8"><h2 class="text-2xl md:text-3xl font-black italic uppercase border-l-4 border-rose-600 pl-4 tracking-tighter">{sec['title']}</h2><a href="{sec['link']}" class="text-rose-600 font-bold text-xs hover:underline">SEE ALL <i class="fa fa-arrow-right ml-1"></i></a></div><div class="card-grid">'''
            for m in sec['items']: body += render_template_string(CARD_HTML, m=m)
            body += '</div></section>'
    body += '</main>'
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ২. ক্যাটাগরি ভিউ ---
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
    for m in items: body += render_template_string(CARD_HTML, m=m)
    body += '</div></main>'
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ৩. ডিটেইল পেজ ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    ads = settings_col.find_one({"name": "ads"}) or {}
    dl_links = m.get('dl_links', [])
    
    body = NAV_HTML
    if ads.get('details_ad'):
        body += f'<div class="container mx-auto px-4 py-4 flex justify-center overflow-hidden">{ads["details_ad"]}</div>'

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
                    
                    <!-- Download Section -->
                    <div class="mt-8 space-y-4">
                        <p class="text-center text-[10px] font-black text-rose-500 uppercase tracking-[0.3em] mb-2">Download Links</p>
                        {% for dl in dl_links %}
                        <a href="{{ dl.url }}" target="_blank" class="flex items-center justify-between bg-zinc-900 hover:bg-rose-600 p-5 rounded-3xl transition group border border-zinc-800">
                            <span class="font-bold text-xs uppercase tracking-widest">{{ dl.label }}</span>
                            <i class="fa fa-download text-rose-600 group-hover:text-white"></i>
                        </a>
                        {% endfor %}
                        {% if not dl_links %}<p class="text-center text-zinc-500 text-xs italic">No links available yet.</p>{% endif %}
                    </div>
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase text-[10px] font-bold tracking-widest">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-white">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 text-center uppercase font-black text-[10px]">
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Rating</p><p class="text-yellow-500 text-xl font-black">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Language</p><p class="text-lg text-white font-bold">{{ m.language | upper }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Director</p><p class="text-rose-500 truncate text-[11px]">{{ m.director.name }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Release</p><p class="text-white text-[11px]">{{ m.release_date }}</p>
                        </div>
                    </div>
                </div>
            </div>

            {% if m.yt_id != "N/A" %}
            <div class="mt-20">
                <h3 class="text-3xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">Official Trailer</h3>
                <div class="aspect-video w-full max-w-5xl mx-auto rounded-[3rem] overflow-hidden border border-zinc-800 shadow-2xl">
                    <iframe class="w-full h-full" src="https://www.youtube.com/embed/{{ m.yt_id }}?rel=0" frameborder="0" allowfullscreen></iframe>
                </div>
            </div>
            {% endif %}

            <!-- Cast & Gallery Section -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Media Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for img in m.gallery %}
                    <div class="overflow-hidden rounded-3xl border border-zinc-800 shadow-xl"><img src="{{ img }}" class="w-full h-full object-cover hover:scale-110 transition duration-700"></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", m=m, dl_links=dl_links)

# --- ৪. এডমিন ড্যাশবোর্ড ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    body = '<div class="h-screen flex items-center justify-center"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm text-center shadow-2xl"><h2 class="text-2xl font-black mb-10 text-rose-600 italic tracking-widest">ADMIN HUB</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none text-white focus:border-rose-600"><button class="w-full bg-rose-600 py-4 rounded-3xl font-black text-white shadow-lg">LOGIN</button></form></div>'
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
    items = list(collection.find({"title": {"$regex": aq, "$options": "i"}}).sort('_id', -1)) if aq else list(collection.find().sort('_id', -1).limit(15))

    body = NAV_HTML + """
    <div class="container mx-auto py-10 px-4 max-w-6xl pb-32">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-4xl font-black italic tracking-tighter">DASHBOARD</h1>
            <a href="/logout" class="text-rose-500 font-bold hover:underline uppercase text-xs">Logout</a>
        </div>

        <!-- Stats -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-6 mb-16">
            <div class="bg-zinc-900 p-8 rounded-[2.5rem] border border-zinc-800 text-center shadow-xl">
                <p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Movies</p>
                <h3 class="text-4xl font-black text-blue-500">{{ stats.movies }}</h3>
            </div>
            <div class="bg-zinc-900 p-8 rounded-[2.5rem] border border-zinc-800 text-center shadow-xl">
                <p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">TV Series</p>
                <h3 class="text-4xl font-black text-rose-500">{{ stats.tv }}</h3>
            </div>
            <div class="bg-zinc-900 p-8 rounded-[2.5rem] border border-zinc-800 text-center shadow-xl">
                <p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Anime</p>
                <h3 class="text-4xl font-black text-purple-500">{{ stats.anime }}</h3>
            </div>
            <div class="bg-zinc-900 p-8 rounded-[2.5rem] border border-zinc-800 text-center shadow-xl">
                <p class="text-zinc-500 text-[10px] font-black uppercase mb-3 tracking-widest">Drama</p>
                <h3 class="text-4xl font-black text-yellow-500">{{ stats.drama }}</h3>
            </div>
        </div>

        <!-- Ads & Sync -->
        <div class="grid md:grid-cols-2 gap-10 mb-16">
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-black mb-8 italic text-rose-600 uppercase tracking-widest">Ads Manager</h3>
                <form action="/api/update_ads" method="POST" class="space-y-6">
                    <textarea name="home_ad" placeholder="Home Ad Code" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl h-24 text-zinc-400 font-mono text-[10px]">{{ ads.home_ad }}</textarea>
                    <textarea name="details_ad" placeholder="Details Ad Code" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl h-24 text-zinc-400 font-mono text-[10px]">{{ ads.details_ad }}</textarea>
                    <button class="w-full bg-rose-600 py-4 rounded-3xl font-black text-white shadow-xl shadow-rose-900/20">SAVE ADS</button>
                </form>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-black mb-8 italic text-blue-500 uppercase tracking-widest">Sync Content</h3>
                <div class="space-y-4">
                    <input type="text" id="m_id" placeholder="TMDB ID (e.g. 12345)" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white outline-none">
                    <select id="m_type" class="w-full bg-black border border-zinc-800 p-4 rounded-2xl text-white">
                        <option value="movie">Movie</option><option value="tv">TV Show</option>
                    </select>
                    <button onclick="manualSync()" class="w-full bg-blue-600 py-4 rounded-3xl font-black text-white shadow-xl shadow-blue-900/20">SYNC NOW</button>
                </div>
            </div>
        </div>

        <!-- Content Search & List -->
        <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
            <div class="flex justify-between items-center mb-8">
                <h3 class="text-xl font-black italic text-green-500 uppercase tracking-widest">Manage Content</h3>
                <form method="GET" class="flex bg-black border border-zinc-800 rounded-full px-4 py-2">
                    <input type="text" name="aq" placeholder="Search to edit..." class="bg-transparent outline-none text-xs text-white">
                    <button><i class="fa fa-search text-zinc-600"></i></button>
                </form>
            </div>
            <div class="overflow-hidden">
                <table class="w-full text-left">
                    <thead class="text-zinc-500 font-black uppercase text-[10px] border-b border-zinc-800">
                        <tr><th class="py-4">Title</th><th class="py-4 text-center">Action</th></tr>
                    </thead>
                    <tbody class="divide-y divide-zinc-800">
                        {% for i in items %}
                        <tr>
                            <td class="py-6 font-bold text-xs">{{ i.title }} <span class="text-zinc-600 ml-2 font-normal">({{ i.year }})</span></td>
                            <td class="py-6 text-center space-x-6">
                                <a href="/edit/{{ i.tmdb_id }}" class="text-blue-500 text-sm font-black hover:underline">EDIT/LINKS</a>
                                <a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete?')" class="text-rose-500 text-sm font-black hover:underline">DELETE</a>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    <script>
    async function manualSync() {
        const id = document.getElementById('m_id').value;
        const t = document.getElementById('m_type').value;
        if(!id) return alert('Enter ID!');
        const btn = event.target; btn.disabled = true; btn.innerHTML = "Syncing...";
        await fetch(`/api/sync_single?id=${id}&type=${t}`);
        location.reload();
    }
    </script>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", stats=stats, ads=ads, items=items)

# --- ৫. এডিট ও লিঙ্কস সিস্টেম ---
@app.route('/edit/<tid>', methods=['GET', 'POST'])
def edit(tid):
    if not session.get('logged'): return redirect('/admin')
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/admin/dashboard')
    
    if request.method == 'POST':
        title = request.form.get('t')
        story = request.form.get('s')
        links_raw = request.form.get('links').strip().split('\n')
        dl_links = []
        for line in links_raw:
            if '|' in line:
                lbl, url = line.split('|')
                dl_links.append({"label": lbl.strip(), "url": url.strip()})
        
        collection.update_one({"tmdb_id": tid}, {"$set": {"title": title, "story": story, "dl_links": dl_links}})
        return redirect('/admin/dashboard')

    links_str = "\n".join([f"{l['label']} | {l['url']}" for l in m.get('dl_links', [])])
    body = f"""
    <div class="container mx-auto py-20 px-4 max-w-2xl">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 shadow-2xl">
            <h2 class="text-2xl font-black mb-10 italic uppercase text-rose-600 border-l-4 border-rose-600 pl-4">Edit Content</h2>
            <div class="space-y-8">
                <div><label class="text-[10px] font-black text-zinc-500 uppercase mb-2 block ml-4">Title</label>
                <input name="t" value="{m['title']}" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-white outline-none focus:border-blue-600"></div>
                
                <div><label class="text-[10px] font-black text-zinc-500 uppercase mb-2 block ml-4">Story</label>
                <textarea name="s" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-white h-40 outline-none focus:border-blue-600 leading-relaxed">{m['story']}</textarea></div>
                
                <div><label class="text-[10px] font-black text-zinc-500 uppercase mb-2 block ml-4">Download Links (Format: Label | Link)</label>
                <textarea name="links" class="w-full bg-black border border-zinc-800 p-5 rounded-3xl text-blue-400 font-mono text-xs h-48 outline-none focus:border-blue-600" placeholder="720p Bluray | https://link.com">{links_str}</textarea></div>
                
                <button class="w-full bg-blue-600 py-5 rounded-[2.5rem] font-black text-white shadow-xl shadow-blue-900/20 uppercase tracking-widest">Update Now</button>
            </div>
        </form>
    </div>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>")

# --- ৬. API ও ব্যাকএন্ড লজিক ---

@app.route('/api/update_ads', methods=['POST'])
def update_ads():
    if not session.get('logged'): return redirect('/admin')
    settings_col.update_one({"name": "ads"}, {"$set": {"home_ad": request.form.get('home_ad'), "details_ad": request.form.get('details_ad')}}, upsert=True)
    return redirect('/admin/dashboard')

@app.route('/api/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else ""} for p in crew if p['job'] == 'Director'), {"id": 0, "name": "N/A", "photo": ""})
    cast = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:15]]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:12]]

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "cast": cast,
        "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path') if d.get('poster_path') else "",
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
