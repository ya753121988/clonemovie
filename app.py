import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_cinema_portal_v5"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_final']
collection = db['media_content']

# --- UI লেআউট (HTML/CSS) ---
def render_layout(body_content):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Movie Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{ background: #050505; color: white; font-family: 'Inter', sans-serif; scroll-behavior: smooth; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #ef4444; transition: 0.4s ease; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #ef4444; border-radius: 10px; }}
        .glass {{ background: rgba(10, 10, 10, 0.8); backdrop-filter: blur(20px); }}
    </style>
</head>
<body>
    <nav class="glass border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-red-600 italic tracking-tighter">MOVIE AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-zinc-900 border border-zinc-800 rounded-full px-5 py-1.5 w-1/3">
                <input type="text" name="q" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <div class="flex gap-4">
                <a href="/admin" class="bg-red-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-red-700 transition shadow-lg shadow-red-900/30">ADMIN PANEL</a>
            </div>
        </div>
    </nav>
    {body_content}
</body>
</html>
'''

# --- ১. হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({{"title": {{"$regex": q, "$options": "i"}}}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-12 px-4">
        <h2 class="text-2xl font-bold mb-8 border-l-4 border-red-600 pl-4">Discover Content</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 shadow-2xl block group">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-play-circle text-5xl text-white"></i>
                    </div>
                    <div class="absolute top-3 right-3 bg-red-600 text-white text-[10px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500 mt-1 uppercase tracking-widest font-bold">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(render_layout(body), items=items)

# --- ২. ডিটেইল পেজ (সব তথ্য এখানে) ---
@app.route('/details/<tmdb_id>')
def details(tmdb_id):
    m = collection.find_one({"tmdb_id": tmdb_id})
    if not m: return redirect('/')
    
    body = '''
    <div class="relative min-h-screen">
        <!-- Backdrop Header -->
        <div class="h-[70vh] relative">
            <img src="{{ m.backdrops[0] if m.backdrops else m.poster }}" class="w-full h-full object-cover opacity-20">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <!-- Side Poster -->
                <div class="w-72 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[2.5rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-4 rounded-2xl font-black shadow-xl shadow-red-900/40 hover:scale-105 transition">
                        <i class="fa fa-play"></i> WATCH TRAILER
                    </a>
                    {% endif %}
                </div>

                <!-- Content Info -->
                <div class="flex-1">
                    <h1 class="text-6xl font-black mb-6 leading-tight">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-6 text-sm text-zinc-400 mb-8 uppercase tracking-widest font-bold">
                        <span class="bg-zinc-800 px-3 py-1 rounded text-yellow-500">⭐ {{ m.rating }}</span>
                        <span class="bg-zinc-800 px-3 py-1 rounded">{{ m.language | upper }}</span>
                        <span class="bg-zinc-800 px-3 py-1 rounded">{{ m.year }}</span>
                        <span class="bg-zinc-800 px-3 py-1 rounded text-red-500">{{ m.type }}</span>
                    </div>
                    
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 max-w-4xl">{{ m.summary }}</p>

                    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 bg-zinc-900/40 p-8 rounded-[2.5rem] border border-zinc-800 shadow-xl">
                        <div><p class="text-zinc-500 text-xs font-bold uppercase mb-1">Director</p><p class="font-bold text-red-500">{{ m.director }}</p></div>
                        <div><p class="text-zinc-500 text-xs font-bold uppercase mb-1">Lead Hero</p><p class="font-bold text-white">{{ m.hero }}</p></div>
                        <div><p class="text-zinc-500 text-xs font-bold uppercase mb-1">Lead Heroine</p><p class="font-bold text-white">{{ m.heroine }}</p></div>
                    </div>
                </div>
            </div>

            <!-- Cast Section -->
            <div class="mt-24">
                <h3 class="text-3xl font-black mb-10 border-l-4 border-red-600 pl-4 uppercase tracking-tighter">Full Movie Cast</h3>
                <div class="flex gap-8 overflow-x-auto pb-8">
                    {% for actor in m.cast %}
                    <div class="min-w-[130px] text-center group">
                        <img src="{{ actor.photo }}" class="w-28 h-28 rounded-full mx-auto object-cover border-4 border-zinc-900 group-hover:border-red-600 transition duration-500 shadow-xl">
                        <p class="text-sm font-bold mt-4 truncate w-28 mx-auto">{{ actor.name }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Full Gallery Section -->
            <div class="mt-24">
                <h3 class="text-3xl font-black mb-10 border-l-4 border-red-600 pl-4 uppercase tracking-tighter">Media Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                    {% for img in m.all_posters[:15] %}
                    <img src="{{ img }}" class="w-full rounded-[1.5rem] border border-zinc-800 hover:scale-105 transition duration-500 shadow-lg">
                    {% endfor %}
                </div>
            </div>

            <!-- TV Seasons & Episodes -->
            {% if m.episodes %}
            <div class="mt-24 pb-32">
                <h3 class="text-3xl font-black mb-10 border-l-4 border-red-600 pl-4 uppercase tracking-tighter">TV Seasons & Episodes</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-[1.5rem] p-4 border border-zinc-800 flex flex-col gap-4">
                        <img src="{{ ep.img }}" class="w-full h-32 object-cover rounded-xl shadow-md">
                        <div>
                            <p class="text-[10px] text-red-600 font-black uppercase mb-1">S{{ ep.season }} | Episode {{ ep.num }}</p>
                            <p class="text-sm font-bold truncate">{{ ep.name }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    '''
    return render_template_string(render_layout(body), m=m)

# --- ৩. এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    
    body = '''
    <div class="h-[80vh] flex items-center justify-center">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[3rem] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-3xl font-black mb-8 text-center text-red-600 tracking-tighter">ADMIN LOGIN</h2>
            <input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-6 text-center outline-none focus:border-red-600">
            <button class="w-full bg-red-600 py-4 rounded-2xl font-black shadow-xl shadow-red-900/20 tracking-widest">LOGIN</button>
        </form>
    </div>
    '''
    return render_template_string(render_layout(body))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-4xl font-black tracking-tighter italic">DASHBOARD</h1>
            <a href="/logout" class="text-red-500 font-bold hover:underline">LOGOUT</a>
        </div>

        <div class="grid md:grid-cols-2 gap-10 mb-16">
            <!-- Advanced Bulk Sync by Year -->
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-6 text-blue-500 uppercase tracking-widest"><i class="fa fa-calendar-alt mr-2"></i> All Content Sync by Year</h3>
                <div class="flex gap-4 mb-4">
                    <input type="number" id="y" placeholder="Year (e.g. 2024)" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none">
                    <input type="number" id="pg" placeholder="Total Pages (1-500)" class="bg-black border border-zinc-700 p-4 rounded-2xl w-32 outline-none">
                </div>
                <button onclick="bulkSync()" id="bBtn" class="w-full bg-blue-600 py-4 rounded-2xl font-black shadow-lg">START FULL SYNC</button>
                <div id="stat" class="mt-6 text-xs text-zinc-500 font-mono"></div>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-6 text-red-500 uppercase tracking-widest"><i class="fa fa-plus-circle mr-2"></i> Specific TMDB ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <div class="flex gap-3">
                        <input type="text" name="tid" placeholder="Content ID" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none">
                        <select name="type" class="bg-black border border-zinc-700 p-4 rounded-2xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    </div>
                    <button class="w-full bg-red-600 py-4 rounded-2xl font-black shadow-lg">SYNC NOW</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-8 uppercase tracking-widest font-black">Content Name</th><th class="p-8 text-center uppercase tracking-widest font-black">Action</th></tr></thead>
                <tbody class="divide-y divide-zinc-800">
                    {% for i in items %}
                    <tr>
                        <td class="p-8 font-bold text-lg">{{ i.title }} <span class="text-zinc-600 font-normal ml-2">({{ i.year }})</span></td>
                        <td class="p-8 text-center"><a href="/del/{{ i.tmdb_id }}" class="text-red-600 text-xl hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function bulkSync() {
        const year = document.getElementById('y').value;
        const totalPages = document.getElementById('pg').value || 1;
        const btn = document.getElementById('bBtn');
        const stat = document.getElementById('stat');
        if(!year) return alert('Enter Year');
        
        btn.disabled = true; stat.innerText = 'Initializing Sync Process...';

        for(let p=1; p <= totalPages; p++) {
            stat.innerText = `Fetching IDs from Page ${{p}} of ${{totalPages}}...`;
            const res = await fetch(`/get_bulk_ids?year=${{year}}&page=${{p}}`);
            const data = await res.json();
            const list = data.ids;

            for(let i=0; i<list.length; i++) {
                stat.innerText = `Processing Page ${{p}}: Syncing (${{i+1}}/${{list.length}}) - ${{list[i].title}}`;
                await fetch(`/sync_single?id=${{list[i].id}}&type=${{list[i].type}}`);
            }
        }
        stat.innerText = 'FULL SYNC COMPLETED!';
        location.reload();
    }
    </script>
    '''
    return render_template_string(render_layout(body), items=items)

# --- ৪. ইন্টারনাল লজিক (The Scraper Engine) ---

@app.route('/get_bulk_ids')
def get_bulk_ids():
    year, page = request.args.get('year'), request.args.get('page', 1)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page={page}&sort_by=popularity.desc"
    res = requests.get(url).json().get('results', [])
    # মুভি এবং টিভি শো মিক্সিং ( Discover API এর লিমিটেশন অনুযায়ী মুভি আগে আনা হচ্ছে )
    return jsonify({"ids": [{"id": m['id'], "type": "movie", "title": m['title']} for m in res]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    # কাস্ট এবং ডিটেইলস (বিন্দু পরিমাণ মিসিং ছাড়া)
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', []) if p.get('profile_path')]
    director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")
    hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
    heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")

    # সব পোস্টার ও থাম্বনেইল গ্যালারি
    posters = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:20]]
    backdrops = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:15]]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")

    # ইপিসোডস (সব সিজন থেকে ডাটা সংগ্রহ)
    eps = []
    if mtype == 'tv':
        for s in d.get('seasons', [])[:3]: # প্রথম ৩ সিজন (বেশি দিলে টাইমআউট হতে পারে)
            s_url = f"https://api.themoviedb.org/3/tv/{tid}/season/{s['season_number']}?api_key={TMDB_API_KEY}"
            s_data = requests.get(s_url).json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "season": s['season_number'], "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "director": director, "hero": hero, "heroine": heroine, "yt_id": ytid,
        "poster": IMG_ORIG + d.get('poster_path'), "all_posters": posters, "backdrops": backdrops,
        "cast": cast[:25], "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'): 
        requests.get(f"{request.url_root}sync_single?id={request.form.get('tid')}&type={request.form.get('type')}")
    return redirect('/admin/dashboard')

@app.route('/del/<id>')
def delete(id):
    if session.get('logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
