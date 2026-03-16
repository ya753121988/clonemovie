import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_final_fixed"

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

# --- UI লেআউট হেল্পার ---
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
        .glass {{ background: rgba(20, 20, 20, 0.8); backdrop-filter: blur(15px); }}
        .m-card:hover {{ transform: scale(1.05); border-color: #ef4444; transition: 0.4s; }}
        ::-webkit-scrollbar {{ width: 6px; }}
        ::-webkit-scrollbar-thumb {{ background: #ef4444; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="bg-black/90 border-b border-zinc-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-red-600 italic tracking-tighter">MOVIE AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-zinc-900 border border-zinc-800 rounded-full px-5 py-1.5 w-1/3">
                <input type="text" name="q" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-red-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-red-700 transition">ADMIN</a>
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
        <h2 class="text-2xl font-bold mb-8 border-l-4 border-red-600 pl-4">Recently Added</h2>
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 shadow-2xl block group">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-circle-info text-5xl text-white"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-yellow-500 text-black text-[10px] font-black px-2 py-1 rounded">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500 mt-1">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(render_layout(body), items=items)

# --- ২. ডিটেইল পেজ (নতুন অ্যাড করা হয়েছে) ---
@app.route('/details/<tmdb_id>')
def details(tmdb_id):
    m = collection.find_one({"tmdb_id": tmdb_id})
    if not m: return redirect('/')
    
    body = '''
    <div class="relative min-h-screen">
        <!-- Backdrop Header -->
        <div class="h-[60vh] relative">
            <img src="{{ m.backdrops[0] if m.backdrops else m.poster }}" class="w-full h-full object-cover opacity-30">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-64 relative z-10">
            <div class="flex flex-col md:flex-row gap-10">
                <!-- Poster -->
                <div class="w-64 flex-shrink-0 mx-auto md:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[2rem] shadow-2xl border border-zinc-700">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-6 flex items-center justify-center gap-2 bg-red-600 py-3 rounded-xl font-bold hover:bg-red-700 transition">
                        <i class="fa fa-play"></i> Watch Trailer
                    </a>
                    {% endif %}
                </div>

                <!-- Info -->
                <div class="flex-1">
                    <h1 class="text-5xl font-black mb-4">{{ m.title }} <span class="text-zinc-500 font-light">({{ m.year }})</span></h1>
                    <div class="flex flex-wrap gap-4 text-sm text-zinc-400 mb-6">
                        <span>Rating: <strong class="text-yellow-500">⭐ {{ m.rating }}</strong></span>
                        <span>Language: <strong>{{ m.language | upper }}</strong></span>
                        <span>Release Date: <strong>{{ m.release_date }}</strong></span>
                    </div>
                    
                    <p class="text-lg text-zinc-300 leading-relaxed mb-8">{{ m.summary }}</p>

                    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 bg-zinc-900/50 p-6 rounded-3xl border border-zinc-800">
                        <p><strong>Director:</strong> <span class="text-red-500">{{ m.director }}</span></p>
                        <p><strong>Lead Hero:</strong> <span class="text-red-500">{{ m.hero }}</span></p>
                        <p><strong>Lead Heroine:</strong> <span class="text-red-500">{{ m.heroine }}</span></p>
                    </div>
                </div>
            </div>

            <!-- Cast Section -->
            <div class="mt-20">
                <h3 class="text-2xl font-bold mb-8">Full Cast & Actors</h3>
                <div class="flex gap-6 overflow-x-auto pb-6">
                    {% for actor in m.cast %}
                    <div class="min-w-[120px] text-center">
                        <img src="{{ actor.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-2 border-zinc-800 mb-2">
                        <p class="text-xs font-bold truncate w-24 mx-auto">{{ actor.name }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery Section -->
            <div class="mt-20">
                <h3 class="text-2xl font-bold mb-8">Image Gallery (Posters & Wallpapers)</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {% for img in m.all_posters[:8] %}
                    <img src="{{ img }}" class="w-full rounded-2xl border border-zinc-800 hover:scale-105 transition">
                    {% endfor %}
                </div>
            </div>

            <!-- Episodes Section (If TV) -->
            {% if m.episodes %}
            <div class="mt-20 pb-20">
                <h3 class="text-2xl font-bold mb-8">Episodes List</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-2xl p-4 flex gap-4 items-center border border-zinc-800">
                        <img src="{{ ep.img }}" class="w-24 h-16 object-cover rounded-lg">
                        <div>
                            <p class="text-xs text-red-500 font-bold tracking-widest">EPISODE {{ ep.num }}</p>
                            <p class="text-sm font-bold truncate w-40">{{ ep.name }}</p>
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
        <form method="POST" class="bg-zinc-900 p-10 rounded-[40px] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-2xl font-black mb-8 text-center text-red-600">ADMIN ACCESS</h2>
            <input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-4 text-center outline-none">
            <button class="w-full bg-red-600 py-4 rounded-2xl font-bold shadow-lg">LOGIN</button>
        </form>
    </div>
    '''
    return render_template_string(render_layout(body))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="flex justify-between items-center mb-10">
            <h1 class="text-3xl font-bold">Dashboard</h1>
            <a href="/logout" class="text-red-500">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <div class="bg-zinc-900 p-8 rounded-[35px] border border-zinc-800">
                <h3 class="font-bold mb-4 text-blue-500">Bulk Sync by Year</h3>
                <div class="flex gap-3">
                    <input type="number" id="y" placeholder="2024" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <button onclick="bulk()" id="bBtn" class="bg-blue-600 px-6 py-3 rounded-xl font-bold">Bulk Sync</button>
                </div>
                <div id="stat" class="mt-4 text-xs text-zinc-500"></div>
            </div>
            
            <div class="bg-zinc-900 p-8 rounded-[35px] border border-zinc-800">
                <h3 class="font-bold mb-4 text-red-500">Sync by TMDB ID</h3>
                <form action="/sync_id" method="POST" class="flex gap-3">
                    <input type="text" name="tid" placeholder="ID" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-3 rounded-xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-red-600 px-6 py-3 rounded-xl font-bold">Sync</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-3xl border border-zinc-800 overflow-hidden">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 text-zinc-400"><tr><th class="p-6">Title</th><th class="p-6 text-center">Action</th></tr></thead>
                <tbody>
                    {% for i in items %}
                    <tr class="border-b border-zinc-800">
                        <td class="p-6 font-bold">{{ i.title }} ({{ i.year }})</td>
                        <td class="p-6 text-center"><a href="/del/{{ i.tmdb_id }}" class="text-red-500"><i class="fa fa-trash"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function bulk() {
        const y = document.getElementById('y').value;
        const b = document.getElementById('bBtn');
        const s = document.getElementById('stat');
        if(!y) return alert('Enter Year');
        b.disabled = true; s.innerText = 'Syncing...';
        const res = await fetch(`/get_bulk?year=${y}`);
        const data = await res.json();
        for(let i=0; i<data.ids.length; i++) {
            s.innerText = `Syncing (${i+1}/${data.ids.length}): ${data.ids[i].title}`;
            await fetch(`/sync_one?id=${data.ids[i].id}&type=${data.ids[i].type}`);
        }
        location.reload();
    }
    </script>
    '''
    return render_template_string(render_layout(body), items=items)

# --- ৪. ইন্টারনাল সিঙ্ক লজিক (সব তথ্য সংগ্রহের মূল জায়গা) ---

@app.route('/get_bulk')
def get_bulk():
    year = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "type": "movie", "title": m['title']} for m in res[:20]]})

@app.route('/sync_one')
def sync_one():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    # কাস্ট এবং হিরো/হিরোইন
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', []) if p.get('profile_path')]
    director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")
    hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
    heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")

    # ইমেজ ও ট্রেলার
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    posters = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]
    backdrops = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:8]]

    # ইপিসোড
    eps = []
    if mtype == 'tv':
        s_data = requests.get(f"https://api.themoviedb.org/3/tv/{tid}/season/1?api_key={TMDB_API_KEY}").json()
        for ep in s_data.get('episodes', []):
            eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})

    data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "director": director, "hero": hero, "heroine": heroine, "yt_id": ytid,
        "poster": IMG_ORIG + d.get('poster_path'), "all_posters": posters, "backdrops": backdrops,
        "cast": cast[:15], "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'): 
        tid, mtype = request.form.get('tid'), request.form.get('type')
        requests.get(f"{request.url_root}sync_one?id={tid}&type={mtype}")
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
