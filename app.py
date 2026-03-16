import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_key_v4"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['full_media_db']
collection = db['content_library']

# --- এইচটিএমএল ডিজাইন (পুরো পোর্টাল) ---
def get_ui_layout(content_body):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cinema Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{ background: #050505; color: white; font-family: 'Inter', sans-serif; }}
        .glass {{ background: rgba(20, 20, 20, 0.9); backdrop-filter: blur(10px); }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; }}
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="glass border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-rose-600 tracking-tighter italic">MOVIE AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-zinc-900 border border-zinc-700 rounded-full px-5 py-1.5 w-1/3">
                <input type="text" name="q" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <div class="flex gap-4">
                <a href="/admin" class="bg-rose-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-rose-700 transition shadow-lg shadow-rose-900/20">ADMIN</a>
            </div>
        </div>
    </nav>

    {content_body}

    <!-- Trailer Modal -->
    <div id="tModal" class="modal" onclick="closePlayer()">
        <div class="w-full max-w-5xl p-4">
            <div class="aspect-video bg-black rounded-3xl overflow-hidden border border-zinc-800 shadow-2xl">
                <iframe id="vPlayer" class="w-full h-full" src="" frameborder="0" allowfullscreen allow="autoplay"></iframe>
            </div>
        </div>
    </div>

    <script>
        function playTrailer(id) {{
            if(!id || id === 'N/A') return alert('Trailer not available');
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

# --- হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}) if q else collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-12 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
            {% for m in items %}
            <div class="m-card bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 transition duration-500 cursor-pointer group" onclick="playTrailer('{{ m.yt_id }}')">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition duration-300">
                        <i class="fa-solid fa-play-circle text-6xl text-rose-600"></i>
                    </div>
                    <div class="absolute top-3 right-3 bg-yellow-500 text-black text-[10px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500 mt-1">{{ m.year }} | {{ m.language | upper }}</p>
                    
                    <div class="mt-3 flex -space-x-2">
                        {% for actor in m.cast[:5] %}
                        <img src="{{ actor.photo }}" title="{{ actor.name }}" class="h-8 w-8 rounded-full border-2 border-zinc-900 object-cover">
                        {% endfor %}
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(get_ui_layout(body), items=items)

# --- এডমিন প্যানেল (Bulk Year Sync & Delete) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PW:
            session['admin_logged'] = True
            return redirect('/admin/dashboard')
    if session.get('admin_logged'): return redirect('/admin/dashboard')
    
    body = '''
    <div class="h-[80vh] flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-10 rounded-[40px] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-2xl font-black mb-8 text-center text-rose-600 tracking-tighter">SECURE ACCESS</h2>
            <input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-4 text-center outline-none focus:border-rose-600">
            <button class="w-full bg-rose-600 py-4 rounded-2xl font-bold shadow-lg shadow-rose-900/20">LOGIN</button>
        </form>
    </div>
    '''
    return render_template_string(get_ui_layout(body))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('admin_logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-6">
            <h1 class="text-3xl font-black">Control Panel</h1>
            <a href="/logout" class="text-rose-500 font-bold hover:underline">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <!-- Sync by Year (Bulk) -->
            <div class="bg-zinc-900 p-8 rounded-[35px] border border-zinc-800 shadow-xl">
                <h3 class="font-bold mb-6 text-blue-500 flex items-center gap-2"><i class="fa fa-calendar-day"></i> Yearly Bulk Sync</h3>
                <div class="flex gap-3">
                    <input type="number" id="yYear" placeholder="2024" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <button onclick="startBulk()" id="bBtn" class="bg-blue-600 px-6 py-3 rounded-xl font-bold">Start Sync</button>
                </div>
                <div id="stat" class="mt-4 text-xs text-zinc-500"></div>
            </div>

            <!-- Sync by ID -->
            <div class="bg-zinc-900 p-8 rounded-[35px] border border-zinc-800 shadow-xl">
                <h3 class="font-bold mb-6 text-rose-500 flex items-center gap-2"><i class="fa fa-plus-circle"></i> Sync by TMDB ID</h3>
                <form action="/sync_id" method="POST" class="flex gap-3">
                    <input type="text" name="tid" placeholder="e.g. 550" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-3 rounded-xl text-xs">
                        <option value="movie">Movie</option><option value="tv">TV Show</option>
                    </select>
                    <button class="bg-rose-600 px-6 py-3 rounded-xl font-bold">Sync</button>
                </form>
            </div>
        </div>

        <!-- Manage List -->
        <div class="bg-zinc-900 rounded-[35px] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 text-zinc-400 uppercase text-[10px] tracking-widest">
                    <tr><th class="p-6">Content Details</th><th class="p-6">Type</th><th class="p-6 text-center">Action</th></tr>
                </thead>
                <tbody class="divide-y divide-zinc-800">
                    {% for i in items %}
                    <tr>
                        <td class="p-6 flex items-center gap-4">
                            <img src="{{ i.poster }}" class="w-12 h-16 object-cover rounded-lg shadow-md">
                            <div><p class="font-bold text-base">{{ i.title }}</p><p class="text-zinc-500">{{ i.year }}</p></div>
                        </td>
                        <td class="p-6 font-medium text-zinc-400">{{ i.type | upper }}</td>
                        <td class="p-6 text-center"><a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete?')" class="text-rose-500 text-xl"><i class="fa fa-trash-alt"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <script>
    async function startBulk() {
        const year = document.getElementById('yYear').value;
        const btn = document.getElementById('bBtn');
        const stat = document.getElementById('stat');
        if(!year) return alert('Enter Year');
        
        btn.disabled = true; stat.innerText = 'Fetching IDs...';
        const res = await fetch(`/get_year_data?year=${{year}}`);
        const data = await res.json();
        const list = data.results;

        for(let i=0; i<list.length; i++) {
            stat.innerText = `Syncing (${{i+1}}/${{list.length}}): ${{list[i].title || list[i].name}}`;
            await fetch(`/sync_single?id=${{list[i].id}}&type=${{list[i].media_type || 'movie'}}`);
        }
        stat.innerText = 'All items synced successfully!';
        location.reload();
    }
    </script>
    '''
    return render_template_string(get_ui_layout(body), items=items)

# --- ইন্টারনাল এপিআই লজিক ---

@app.route('/get_year_data')
def get_year_data():
    year = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"results": res[:20]}) # ২০টি করে সিঙ্ক হবে টাইমআউট এড়াতে

@app.route('/sync_single')
def sync_single():
    tid = request.args.get('id')
    mtype = request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    # কাস্ট ও হিরো-হিরোইন
    cast = []
    for p in d.get('credits', {}).get('cast', [])[:15]:
        if p.get('profile_path'):
            cast.append({"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']})
    
    hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
    heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")
    director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")

    # ইমেজ ও ট্রেলার
    ytid = "N/A"
    for v in d.get('videos', {}).get('results', []):
        if v['type'] == 'Trailer' and v['site'] == 'YouTube':
            ytid = v['key']; break

    posters = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:10]]
    backdrops = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:10]]

    # টিভি এপিসোড তথ্য
    episodes = []
    if mtype == 'tv':
        for s in d.get('seasons', [])[:2]: # প্রথম ২ সিজন (যাতে টাইমআউট না হয়)
            s_url = f"https://api.themoviedb.org/3/tv/{tid}/season/{s['season_number']}?api_key={TMDB_API_KEY}"
            s_data = requests.get(s_url).json()
            for ep in s_data.get('episodes', []):
                episodes.append({"name": ep.get('name'), "num": ep.get('episode_number'), "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "director": director, "hero": hero, "heroine": heroine, "yt_id": ytid,
        "poster": IMG_ORIG + d.get('poster_path'), "all_posters": posters, "backdrops": backdrops,
        "cast": cast, "episodes": episodes
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('admin_logged'):
        requests.get(f"{request.url_root}sync_single?id={request.form.get('tid')}&type={request.form.get('type')}")
    return redirect('/admin/dashboard')

@app.route('/del/<id>')
def delete(id):
    if session.get('admin_logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('admin_logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
