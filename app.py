import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_key_final"

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

# --- UI হেল্পার ফাংশন (যাতে Template Error না আসে) ---
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
        body {{ background: #050505; color: white; font-family: 'Inter', sans-serif; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #ef4444; transition: 0.4s; }}
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #ef4444; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="bg-zinc-900 border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-red-600 tracking-tighter italic">MOVIE AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-zinc-800 rounded-full px-5 py-1 w-1/3">
                <input type="text" name="q" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-red-600 px-5 py-2 rounded-full font-bold text-xs">ADMIN</a>
        </div>
    </nav>
    {body_content}
    <div id="tModal" class="modal" onclick="closePlayer()">
        <div class="w-full max-w-4xl p-4 aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl">
            <iframe id="vPlayer" class="w-full h-full" src="" frameborder="0" allowfullscreen allow="autoplay"></iframe>
        </div>
    </div>
    <script>
        function playTrailer(id) {{
            if(!id || id === 'N/A') return alert('Trailer not found');
            document.getElementById('vPlayer').src = `https://www.youtube.com/embed/${{id}}?autoplay=1`;
            document.getElementById('tModal').style.display = 'flex';
        }}
        function closePlayer() {{
            document.getElementById('tModal').style.display = 'none';
            document.getElementById('vPlayer').src = '';
        }}
    </script>
</body>
</html>
'''

# --- হোম পেজ রাউট ---
@app.route('/')
def home():
    q = request.args.get('q')
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {% for m in items %}
            <div class="m-card bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800 shadow-xl group cursor-pointer" onclick="playTrailer('{{ m.yt_id }}')">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <i class="fa-solid fa-play-circle text-5xl text-red-600"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-yellow-500 text-black text-[10px] font-black px-2 py-1 rounded">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-3">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500">{{ m.year }} | {{ m.type | upper }}</p>
                    <div class="mt-2 flex -space-x-2">
                        {% for actor in m.cast[:4] %}
                        <img src="{{ actor.photo }}" title="{{ actor.name }}" class="h-7 w-7 rounded-full border border-zinc-900 object-cover">
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(render_layout(body), items=items)

# --- এডমিন প্যানেল রাউট ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PW:
            session['logged'] = True
            return redirect('/admin/panel')
    if session.get('logged'): return redirect('/admin/panel')
    
    body = '''
    <div class="h-[80vh] flex items-center justify-center">
        <form method="POST" class="bg-zinc-900 p-8 rounded-3xl border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-xl font-bold mb-6 text-center text-red-600">ADMIN LOGIN</h2>
            <input type="password" name="pw" placeholder="Password" class="w-full bg-black border border-zinc-700 p-3 rounded-xl mb-4 text-center outline-none">
            <button class="w-full bg-red-600 py-3 rounded-xl font-bold">LOGIN</button>
        </form>
    </div>
    '''
    return render_template_string(render_layout(body))

@app.route('/admin/panel')
def admin_panel():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="flex justify-between items-center mb-10">
            <h1 class="text-2xl font-bold">Admin Panel</h1>
            <a href="/logout" class="text-red-500 font-bold">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-6 mb-12">
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-xl">
                <h3 class="font-bold mb-4 text-blue-500"><i class="fa fa-calendar-alt mr-2"></i>Bulk Sync by Year</h3>
                <div class="flex gap-2">
                    <input type="number" id="yInput" placeholder="2024" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <button onclick="bulkSync()" id="syncBtn" class="bg-blue-600 px-4 py-2 rounded font-bold text-sm">Start Sync</button>
                </div>
                <div id="status" class="mt-3 text-[10px] text-zinc-500 uppercase tracking-widest"></div>
            </div>
            
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800 shadow-xl">
                <h3 class="font-bold mb-4 text-red-500"><i class="fa fa-plus-circle mr-2"></i>Sync by TMDB ID</h3>
                <form action="/sync_id" method="POST" class="flex gap-2">
                    <input type="text" name="tid" placeholder="ID" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-2 rounded text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-red-600 px-4 py-2 rounded font-bold text-sm">Sync</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 uppercase text-[10px] tracking-widest text-zinc-400">
                    <tr><th class="p-4">Title</th><th class="p-4">Year</th><th class="p-4 text-center">Action</th></tr>
                </thead>
                <tbody>
                    {% for i in items %}
                    <tr class="border-b border-zinc-800">
                        <td class="p-4 font-bold">{{ i.title }}</td>
                        <td class="p-4 text-zinc-500">{{ i.year }}</td>
                        <td class="p-4 text-center"><a href="/del/{{ i.tmdb_id }}" class="text-red-500" onclick="return confirm('Delete?')"><i class="fa fa-trash"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function bulkSync() {
        const year = document.getElementById('yInput').value;
        const btn = document.getElementById('syncBtn');
        const status = document.getElementById('status');
        if(!year) return alert('Enter Year');
        
        btn.disabled = true; status.innerText = 'Fetching IDs...';
        const res = await fetch(`/get_bulk_ids?year=${year}`);
        const data = await res.json();
        const ids = data.results;

        for(let i=0; i<ids.length; i++) {
            status.innerText = `Syncing (${i+1}/${ids.length}): ${ids[i].title || ids[i].name}`;
            await fetch(`/sync_single?id=${ids[i].id}&type=${ids[i].media_type || 'movie'}`);
        }
        status.innerText = 'Sync Done! Reloading...';
        location.reload();
    }
    </script>
    '''
    return render_template_string(render_layout(body), items=items)

# --- ইন্টারনাল লজিক রাউটস ---

@app.route('/get_bulk_ids')
def get_bulk_ids():
    year = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"results": res[:20]})

@app.route('/sync_single')
def sync_single():
    tid = request.args.get('id')
    mtype = request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    cast = []
    for p in d.get('credits', {}).get('cast', [])[:15]:
        if p.get('profile_path'):
            cast.append({"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']})
    
    hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
    heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")
    director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")

    ytid = "N/A"
    for v in d.get('videos', {}).get('results', []):
        if v['type'] == 'Trailer' and v['site'] == 'YouTube':
            ytid = v['key']; break

    posters = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:10]]
    backdrops = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:10]]
    
    eps = []
    if mtype == 'tv':
        for s in d.get('seasons', [])[:1]: # টাইমআউট এড়াতে ১টি সিজন
            s_url = f"https://api.themoviedb.org/3/tv/{tid}/season/{s['season_number']}?api_key={TMDB_API_KEY}"
            s_data = requests.get(s_url).json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})

    data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "director": director, "hero": hero, "heroine": heroine,
        "poster": IMG_ORIG + d.get('poster_path') if d.get('poster_path') else None,
        "all_posters": posters, "all_backdrops": backdrops, "yt_id": ytid, "cast": cast, "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_single?id={request.form.get('tid')}&type={request.form.get('type')}")
    return redirect('/admin/panel')

@app.route('/del/<id>')
def delete(id):
    if session.get('logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/panel')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
