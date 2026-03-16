import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_ultimate_movie_system_v30"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_portal_v30']
collection = db['media_content']

# --- UI লেআউট ইঞ্জিন (যাতে এরর না আসে) ---
def render_full_layout(content):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MOVIE AI - Pro Entertainment Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        body {{ background: #050505; color: white; font-family: 'Outfit', sans-serif; }}
        .glass {{ background: rgba(10, 10, 10, 0.8); backdrop-filter: blur(20px); }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body class="overflow-x-hidden">
    <nav class="glass border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-lg bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="Search movies, tv, actors..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <div class="flex gap-4">
                <a href="/admin" class="bg-rose-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-rose-700 transition shadow-lg shadow-rose-900/40">ADMIN</a>
            </div>
        </div>
    </nav>
    {content}
</body>
</html>
'''

# --- হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({{"title": {{"$regex": q, "$options": "i"}}}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-12 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 md:gap-10">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2.5rem] overflow-hidden border border-zinc-800 shadow-2xl block group relative">
                <div class="relative aspect-[2/3] overflow-hidden">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover transition duration-500 group-hover:scale-110">
                    <div class="absolute top-3 right-3 bg-rose-600 text-white text-[10px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter text-zinc-200">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(render_full_layout(body), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    body = '''
    <div class="relative min-h-screen">
        <div class="h-[50vh] md:h-[75vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 scale-105 blur-[2px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/60 to-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10 pb-20">
            <div class="flex flex-col lg:flex-row gap-12 items-start">
                <!-- Poster -->
                <div class="w-72 md:w-96 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3.5rem] border border-zinc-700 shadow-2xl shadow-rose-900/20">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-rose-600 py-5 rounded-3xl font-black shadow-xl hover:scale-105 transition">
                        <i class="fa fa-play text-xl"></i> WATCH TRAILER
                    </a>
                    {% endif %}
                </div>

                <!-- Main Info -->
                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8">
                        {% for cat in m.category %}
                        <span class="bg-zinc-800 border border-zinc-700 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">{{ cat }}</span>
                        {% endfor %}
                    </div>
                    
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 max-w-4xl italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800 shadow-xl">
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Rating</p><p class="text-xl font-black text-yellow-500">⭐ {{ m.rating }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Language</p><p class="text-sm font-black">{{ m.language | upper }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Released</p><p class="text-sm font-black">{{ m.release_date }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Main Title</p><p class="text-[10px] font-black truncate">{{ m.title }}</p></div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-8 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem] shadow-inner">
                        <p class="text-xs font-black uppercase text-rose-500 mb-6 tracking-widest">Released On (OTT Info)</p>
                        <div class="flex flex-wrap gap-8">
                            {% for ott in m.ott %}
                            <div class="flex flex-col items-center">
                                <img src="{{ ott.logo }}" class="w-16 h-16 rounded-2xl shadow-xl border border-zinc-800">
                                <span class="text-[10px] mt-2 font-bold text-zinc-400">{{ ott.name }}</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast, Director, Producer Profiles -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Cast, Director & Producers</h3>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <!-- Director -->
                    <div class="min-w-[150px] text-center">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl">
                        <p class="mt-4 font-black text-sm text-white">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    <!-- Producers -->
                    {% for p in m.producers %}
                    <div class="min-w-[150px] text-center">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm text-white">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    <!-- Actors -->
                    {% for a in m.cast %}
                    <div class="min-w-[150px] text-center group">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:border-white transition duration-500">
                        <p class="mt-4 font-black text-sm text-white">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 uppercase font-bold truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Full Gallery (Wallpapers & Thumbnails) -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">All Posters & Wallpapers</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for img in m.gallery %}
                    <div class="overflow-hidden rounded-3xl border border-zinc-800 shadow-xl group">
                        <img src="{{ img }}" class="w-full h-full object-cover group-hover:scale-110 transition duration-700">
                    </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(render_full_layout(body), m=m)

# --- এডমিন প্যানেল (লগইন, ডিলিট, বাল্ক সিঙ্ক) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    
    body = '''
    <div class="h-[80vh] flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-3xl font-black mb-10 text-center text-rose-600 uppercase tracking-tighter italic">Admin Access</h2>
            <input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none focus:border-rose-600 transition">
            <button class="w-full bg-rose-600 py-4 rounded-3xl font-black shadow-xl text-lg">LOGIN</button>
        </form>
    </div>
    '''
    return render_template_string(render_full_layout(body))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-4xl font-black italic tracking-tighter">CONTROL HUB</h1>
            <a href="/logout" class="text-rose-500 font-bold hover:underline">LOGOUT</a>
        </div>

        <div class="grid md:grid-cols-2 gap-10 mb-16 text-center">
            <!-- Ultimate Bulk Sync by Year -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-8 text-blue-500 uppercase tracking-widest italic">All-Content Sync by Year</h3>
                <div class="flex gap-4 mb-4">
                    <input type="number" id="yYear" placeholder="Year" class="bg-black border border-zinc-700 p-4 rounded-3xl flex-1 outline-none">
                    <input type="number" id="pCount" placeholder="Pages" class="bg-black border border-zinc-700 p-4 rounded-3xl w-24 outline-none">
                </div>
                <button onclick="runBulk()" id="bBtn" class="w-full bg-blue-600 py-4 rounded-3xl font-black shadow-lg">START BULK SYNC</button>
                <div id="status" class="mt-6 text-[10px] text-zinc-500 font-mono uppercase tracking-widest"></div>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-8 text-rose-500 uppercase tracking-widest italic text-center">Manual TMDB ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <div class="flex gap-4">
                        <input type="text" name="tid" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-4 rounded-3xl flex-1 outline-none">
                        <select name="type" class="bg-black border border-zinc-700 p-4 rounded-3xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    </div>
                    <button class="w-full bg-rose-600 py-4 rounded-3xl font-black shadow-lg">SYNC NOW</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3.5rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 text-zinc-400"><tr><th class="p-8 uppercase font-black">Content Info</th><th class="p-8 text-center uppercase font-black">Action</th></tr></thead>
                <tbody class="divide-y divide-zinc-800">
                    {% for i in items %}
                    <tr>
                        <td class="p-8"><p class="font-black text-lg">{{ i.title }}</p><p class="text-zinc-500">{{ i.year }} | {{ i.type | upper }}</p></td>
                        <td class="p-8 text-center"><a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete?')" class="text-rose-500 text-2xl hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function runBulk() {
        const year = document.getElementById('yYear').value;
        const pages = document.getElementById('pCount').value || 1;
        const btn = document.getElementById('bBtn');
        const status = document.getElementById('status');
        if(!year) return alert('Enter Year');
        btn.disabled = true;
        for(let p=1; p <= pages; p++) {
            status.innerText = `Fetching Page ${{p}}...`;
            const r = await fetch(`/get_bulk?year=${year}&page=${p}`);
            const d = await r.json();
            for(let item of d.results) {
                status.innerText = `Syncing (${p}): ${item.title || item.name}`;
                await fetch(`/sync_item?id=${item.id}&type=${item.media_type || 'movie'}`);
            }
        }
        status.innerText = 'All Contents Synced!'; location.reload();
    }
    </script>
    '''
    return render_template_string(render_full_layout(body), items=items)

# --- ইন্টারনাল ডেটা ফেচিং এপিআই ---

@app.route('/get_bulk')
def get_bulk():
    year, page = request.args.get('year'), request.args.get('page', 1)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page={page}&sort_by=popularity.desc"
    return jsonify({"results": requests.get(url).json().get('results', [])})

@app.route('/sync_item')
def sync_item():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    # কাস্ট, ডিরেক্টর ও প্রডিউসার (সব তথ্য ও ছবিসহ)
    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', [])[:20]]

    # OTT তথ্য (Providers)
    ott = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for prov in providers: ott.append({"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']})

    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:15]]

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')), "gallery": gallery
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_item?id={request.form.get('tid')}&type={request.form.get('type')}")
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
