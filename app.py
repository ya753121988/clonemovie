import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_mega_cinema_v25_final"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_v25']
collection = db['media_hub']

# --- UI লেআউট (HTML/CSS/JS) ---
def get_layout(body_content):
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
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;700;900&display=swap');
        body {{ background: #050505; color: white; font-family: 'Inter', sans-serif; scroll-behavior: smooth; }}
        .glass {{ background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(20px); border-bottom: 1px solid rgba(255,255,255,0.1); }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
        .poster-shadow {{ box-shadow: 0 25px 50px -12px rgba(225, 9, 20, 0.3); }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-lg bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="মুভি, টিভি শো বা এক্টর খুঁজুন..." class="bg-transparent outline-none w-full text-xs md:text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] md:text-xs transition">ADMIN</a>
        </div>
    </nav>
    {body_content}
    <footer class="bg-zinc-900 p-10 mt-20 text-center border-t border-zinc-800 text-zinc-500 text-sm">
        <p>&copy; 2024 MOVIE-AI Portal. All rights reserved.</p>
    </footer>
</body>
</html>
'''

# --- হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-10 px-4">
        <div class="flex items-center gap-3 mb-10">
            <div class="h-8 w-1.5 bg-rose-600 rounded-full"></div>
            <h2 class="text-2xl font-black uppercase tracking-widest italic">New Releases</h2>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6 md:gap-8">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2.5rem] overflow-hidden border border-zinc-800 shadow-2xl block group relative">
                <div class="relative aspect-[2/3] overflow-hidden">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover transition duration-500 group-hover:scale-110">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <div class="bg-rose-600 h-12 w-12 rounded-full flex items-center justify-center shadow-2xl scale-75 group-hover:scale-100 transition duration-300">
                            <i class="fa-solid fa-play text-white"></i>
                        </div>
                    </div>
                    <div class="absolute top-3 left-3 bg-black/70 backdrop-blur-md text-yellow-500 text-[10px] font-black px-2 py-1 rounded-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter text-zinc-200">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(get_layout("Home", body), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    body = '''
    <div class="relative">
        <!-- Hero Section -->
        <div class="h-[60vh] md:h-[80vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-30 scale-105 blur-[2px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-[#050505]/40 to-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-96 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12 items-start">
                <!-- Poster Column -->
                <div class="w-full max-w-[320px] mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3.5rem] poster-shadow border border-zinc-700 shadow-2xl">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-rose-600 py-5 rounded-3xl font-black shadow-xl hover:bg-rose-700 transition">
                        <i class="fa fa-play text-xl"></i> WATCH TRAILER
                    </a>
                    {% endif %}
                </div>

                <!-- Info Column -->
                <div class="flex-1">
                    <div class="flex items-center gap-3 text-rose-600 font-black text-xs uppercase tracking-[0.3em] mb-4">
                        <span>{{ m.type }}</span> • <span>{{ m.language | upper }}</span> • <span>{{ m.year }}</span>
                    </div>
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-none tracking-tighter">{{ m.title }}</h1>
                    
                    <div class="flex flex-wrap gap-2 mb-8">
                        {% for cat in m.category %}
                        <span class="bg-zinc-800 border border-zinc-700 px-4 py-1.5 rounded-full text-[10px] font-bold">{{ cat }}</span>
                        {% endfor %}
                    </div>

                    <p class="text-lg md:text-xl text-zinc-300 leading-relaxed mb-10 max-w-4xl">{{ m.story }}</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">TMDB Rating</p>
                            <p class="text-xl font-black text-yellow-500">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Release Date</p>
                            <p class="text-sm font-black">{{ m.release_date }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Main Title</p>
                            <p class="text-sm font-black truncate">{{ m.title }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Status</p>
                            <p class="text-sm font-black text-green-500">Released</p>
                        </div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase tracking-widest text-rose-500 mb-5">Available on OTT Platforms</p>
                        <div class="flex flex-wrap gap-6">
                            {% for ott in m.ott %}
                            <div class="flex flex-col items-center">
                                <img src="{{ ott.logo }}" class="w-14 h-14 rounded-2xl shadow-xl">
                                <span class="text-[10px] mt-2 font-bold text-zinc-400">{{ ott.name }}</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Crew (With Photos) -->
            <div class="mt-32">
                <div class="flex items-center gap-3 mb-12">
                    <div class="h-8 w-1.5 bg-rose-600 rounded-full"></div>
                    <h2 class="text-3xl font-black uppercase tracking-widest italic">Cast & Crew Profiles</h2>
                </div>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <!-- Director -->
                    <div class="min-w-[140px] text-center">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl ring-offset-4 ring-offset-black">
                        <p class="mt-4 font-black text-sm">{{ m.director.name }}</p>
                        <p class="text-[10px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    <!-- Producers -->
                    {% for p in m.producers %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ p.name }}</p>
                        <p class="text-[10px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    <!-- Actors -->
                    {% for a in m.cast %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm">{{ a.name }}</p>
                        <p class="text-[10px] text-zinc-500 font-bold uppercase truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-32">
                <div class="flex items-center gap-3 mb-12">
                    <div class="h-8 w-1.5 bg-rose-600 rounded-full"></div>
                    <h2 class="text-3xl font-black uppercase tracking-widest italic">Gallery & Thumbnails</h2>
                </div>
                <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
                    {% for img in m.gallery %}
                    <div class="overflow-hidden rounded-3xl border border-zinc-800 shadow-xl">
                        <img src="{{ img }}" class="w-full h-full object-cover hover:scale-110 transition duration-700">
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Episodes (If TV) -->
            {% if m.episodes %}
            <div class="mt-32 pb-32">
                <div class="flex items-center gap-3 mb-12">
                    <div class="h-8 w-1.5 bg-rose-600 rounded-full"></div>
                    <h2 class="text-3xl font-black uppercase tracking-widest italic">TV Episodes Details</h2>
                </div>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-[2.5rem] p-5 border border-zinc-800 flex flex-col gap-4 group">
                        <div class="overflow-hidden rounded-2xl aspect-video">
                            <img src="{{ ep.img }}" class="w-full h-full object-cover group-hover:scale-110 transition duration-500">
                        </div>
                        <div>
                            <p class="text-[10px] text-rose-600 font-black uppercase mb-1">S{{ ep.season }} | E{{ ep.num }}</p>
                            <p class="font-black text-sm truncate">{{ ep.name }}</p>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
    '''
    return render_template_string(get_layout(m['title'], body), m=m)

# --- এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    
    body = f'''
    <div class="h-[80vh] flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[3.5rem] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-3xl font-black mb-10 text-center text-rose-600 tracking-tighter uppercase">Admin Auth</h2>
            <input type="password" name="pw" placeholder="Password" class="w-full bg-black border border-zinc-700 p-5 rounded-2xl mb-6 text-center outline-none focus:border-rose-600 transition">
            <button class="w-full bg-rose-600 py-4 rounded-2xl font-black shadow-xl">LOG IN</button>
        </form>
    </div>
    '''
    return render_template_string(get_layout("Admin Login", body))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = '''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-4xl font-black tracking-tighter italic">ADMIN HUB</h1>
            <a href="/logout" class="text-rose-600 font-bold hover:underline">LOG OUT</a>
        </div>

        <div class="grid md:grid-cols-2 gap-10 mb-16">
            <!-- Advanced Sync Section -->
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-8 text-blue-500 uppercase tracking-widest"><i class="fa fa-sync-alt mr-2"></i>Bulk Year Sync</h3>
                <div class="flex gap-4 mb-4">
                    <input type="number" id="sy" placeholder="Year (2024)" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none">
                    <button onclick="startBulk()" id="sb" class="bg-blue-600 px-8 py-4 rounded-2xl font-black">START</button>
                </div>
                <div id="status" class="mt-6 text-[10px] text-zinc-500 font-mono uppercase"></div>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="text-xl font-bold mb-8 text-rose-600 uppercase tracking-widest"><i class="fa fa-id-card mr-2"></i>Single ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <div class="flex gap-3">
                        <input type="text" name="id" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none">
                        <select name="type" class="bg-black border border-zinc-700 p-4 rounded-2xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    </div>
                    <button class="bg-rose-600 py-4 rounded-2xl font-black">SYNC NOW</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm"><thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-8 font-black uppercase">Content Name</th><th class="p-8 text-center uppercase">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800">
                {% for i in items %}
                <tr><td class="p-8 font-black text-lg">{{ i.title }} <span class="text-zinc-600 ml-2">({{ i.year }})</span></td>
                <td class="p-8 text-center"><a href="/del/{{ i.tmdb_id }}" class="text-rose-600 text-xl"><i class="fa fa-trash-alt"></i></a></td></tr>
                {% endfor %}
            </tbody></table>
        </div>
    </div>
    <script>
    async function startBulk() {
        const yr = document.getElementById('sy').value;
        const btn = document.getElementById('sb');
        const st = document.getElementById('status');
        if(!yr) return alert('Enter Year');
        btn.disabled = true; st.innerText = 'Fetching IDs...';
        const r = await fetch(`/get_year_ids?year=${yr}`);
        const d = await r.json();
        for(let i=0; i<d.ids.length; i++) {
            st.innerText = `Syncing (${i+1}/${d.ids.length}): ${d.ids[i].title}`;
            await fetch(`/sync_single?id=${d.ids[i].id}&type=movie`);
        }
        st.innerText = 'SYNC COMPLETED!'; location.reload();
    }
    </script>
    '''
    return render_template_string(get_layout("Admin Dashboard", body), items=items)

# --- ইন্টারনাল স্ক্র্যাপিং লজিক ---

@app.route('/get_year_ids')
def get_year_ids():
    y = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={y}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m['title']} for m in res[:20]]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    # ১. ডিরেক্টর, প্রডিউসার ও কাস্ট (সব তথ্য ও ছবিসহ)
    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "Unknown", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    # ২. OTT তথ্য
    ott = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for prov in providers:
        ott.append({"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']})

    # ৩. ট্রেলার ও গ্যালারি
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]
    backdrops = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:8]]

    # ৪. ইপিসোডস (সব সিজন থেকে)
    eps = []
    if mtype == 'tv':
        for s in d.get('seasons', [])[:2]:
            s_url = f"https://api.themoviedb.org/3/tv/{tid}/season/{s['season_number']}?api_key={TMDB_API_KEY}"
            s_data = requests.get(s_url).json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "season": s['season_number'], "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])],
        "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')), "gallery": gallery, "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_single?id={request.form.get('id')}&type={request.form.get('type')}")
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
