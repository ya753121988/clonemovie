import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_pro_v50"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_portal_v50']
collection = db['all_data']

# --- লেআউট ইঞ্জিন ---
def get_layout(title, content):
    return f'''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body {{ background: #050505; color: white; font-family: sans-serif; overflow-x: hidden; }}
        .glass {{ background: rgba(20, 20, 20, 0.8); backdrop-filter: blur(15px); border-bottom: 1px solid #333; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-4 py-1.5">
                <input type="text" name="q" placeholder="মুভি বা টিভি শো খুঁজুন..." class="bg-transparent outline-none w-full text-xs md:text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-rose-600 px-4 py-1.5 rounded-full font-bold text-xs">ADMIN</a>
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
    
    content = '''
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 shadow-2xl block group relative">
                <div class="aspect-[2/3] overflow-hidden">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-play-circle text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-white text-[10px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 tracking-widest">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(get_layout("Explore Movies", content), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative min-h-screen">
        <div class="h-[50vh] md:h-[70vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[1px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-64 relative z-10 pb-20">
            <div class="flex flex-col lg:flex-row gap-12 items-start">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0 text-center">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-4 rounded-2xl font-black shadow-xl">
                        <i class="fa fa-play"></i> WATCH TRAILER
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-6xl font-black mb-6 leading-tight">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-3 mb-8">
                        {% for cat in m.category %}
                        <span class="bg-zinc-800 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">{{ cat }}</span>
                        {% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-[10px] font-bold">{{ m.year }}</span>
                    </div>
                    
                    <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800 mb-8">
                        <h3 class="text-rose-500 font-bold text-sm uppercase mb-3">মুভির গল্প</h3>
                        <p class="text-zinc-300 leading-relaxed text-lg">{{ m.story }}</p>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800 text-center">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Rating</p>
                            <p class="font-bold text-yellow-500 text-xl">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800 text-center">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Language</p>
                            <p class="font-bold text-lg">{{ m.language | upper }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800 text-center">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Release Date</p>
                            <p class="font-bold text-xs">{{ m.release_date }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800 text-center">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">OTT</p>
                            <p class="font-black text-xs text-green-500 uppercase">{{ m.ott[0].name if m.ott else 'THEATER' }}</p>
                        </div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase text-rose-500 mb-5 tracking-widest italic">Streaming On (OTT)</p>
                        <div class="flex flex-wrap gap-6">
                            {% for ott in m.ott %}
                            <div class="flex flex-col items-center">
                                <img src="{{ ott.logo }}" class="w-14 h-14 rounded-2xl shadow-xl">
                                <span class="text-[9px] mt-2 font-bold text-zinc-400">{{ ott.name }}</span>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Crew -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">Cast, Director & Producers</h3>
                <div class="flex gap-10 overflow-x-auto pb-10">
                    <div class="min-w-[140px] text-center">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl">
                        <p class="mt-4 font-black text-sm">{{ m.director.name }}</p>
                        <p class="text-[10px] text-rose-500 font-black uppercase tracking-widest">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ p.name }}</p>
                        <p class="text-[10px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 font-bold uppercase tracking-tighter truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Image Gallery -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase">Posters & Wallpapers Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}
                    <img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 shadow-xl hover:scale-105 transition">
                    {% endfor %}
                </div>
            </div>

            <!-- TV Episode List -->
            {% if m.episodes %}
            <div class="mt-20 pb-32"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">Episodes List</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-[2rem] p-4 border border-zinc-800 flex flex-col gap-4">
                        <img src="{{ ep.img }}" class="w-full h-32 object-cover rounded-2xl shadow-md">
                        <div>
                            <p class="text-[10px] text-rose-600 font-black mb-1 uppercase tracking-widest">Episode {{ ep.num }}</p>
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
    return render_template_string(get_layout(m['title'], content), m=m)

# --- এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    return render_template_string(get_layout("Admin Auth", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-2xl font-black mb-8 text-center text-rose-600 uppercase">Admin</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-6 text-center outline-none"><button class="w-full bg-rose-600 py-4 rounded-2xl font-bold shadow-lg shadow-rose-900/20">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-5xl pb-32">
        <div class="flex justify-between items-center mb-10 border-b border-zinc-800 pb-6">
            <h1 class="text-2xl font-black italic">CONTROL CENTER</h1>
            <a href="/logout" class="text-rose-500 font-bold text-xs uppercase">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <!-- Yearly Bulk Sync -->
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-blue-500 uppercase tracking-widest"><i class="fa fa-sync-alt mr-2"></i>Bulk Year Sync (Auto Save)</h3>
                <div class="flex flex-col gap-3">
                    <input type="number" id="yr" placeholder="Year (2024)" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-white">
                    <select id="type" class="bg-black border border-zinc-700 p-4 rounded-xl text-xs"><option value="movie">Movies</option><option value="tv">TV Shows</option></select>
                    <button onclick="bulkSync()" id="bs" class="bg-blue-600 py-4 rounded-xl font-bold">START AUTO SYNC</button>
                </div>
                <div id="stat" class="mt-4 text-[10px] text-zinc-500 font-mono tracking-widest uppercase">Status: Ready</div>
            </div>
            
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-rose-500 uppercase tracking-widest"><i class="fa fa-id-card mr-2"></i>Single TMDB ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-3">
                    <input type="text" name="id" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-white">
                    <select name="type" class="bg-black border border-zinc-700 p-4 rounded-xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-rose-600 py-4 rounded-xl font-bold">SYNC NOW</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm"><thead class="bg-zinc-800 text-zinc-500 uppercase text-[10px] font-black"><tr><th class="p-6">Content List</th><th class="p-6 text-center">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800">
                {{% for i in items %}}
                <tr><td class="p-6 font-bold text-white uppercase text-xs">{{{{ i.title }}}} ({{{{ i.year }}}})</td>
                <td class="p-6 text-center"><a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-500 text-lg hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td></tr>
                {{% endfor %}}
            </tbody></table>
        </div>
    </div>
    <script>
    async function bulkSync() {{
        const y = document.getElementById('yr').value;
        const t = document.getElementById('type').value;
        const b = document.getElementById('bs');
        const s = document.getElementById('stat');
        if(!y) return alert('Enter Year!');
        b.disabled = true; s.innerText = 'Fetching ID list...';
        const r = await fetch(`/get_bulk_ids?year=${{y}}&type=${{t}}`);
        const d = await r.json();
        for(let i=0; i<d.ids.length; i++) {{
            s.innerText = `Auto Saving (${{i+1}}/${{d.ids.length}}): ${{d.ids[i].title}}`;
            await fetch(`/sync_item?id=${{d.ids[i].id}}&type=${{t}}`);
        }}
        s.innerText = 'All Data Saved Successfully!'; location.reload();
    }}
    </script>
    '''
    return render_template_string(get_layout("Admin Panel", content), items=items)

# --- ৪. ইন্টারনাল স্ক্র্যাপিং ইঞ্জিন ---

@app.route('/get_bulk_ids')
def get_bulk_ids():
    y, t = request.args.get('year'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res[:20]]})

@app.route('/sync_item')
def sync_item():
    tid = request.args.get('id')
    mtype = request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    ott = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for prov in providers: ott.append({"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']})

    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]

    eps = []
    if mtype == 'tv':
        try:
            s_data = requests.get(f"https://api.themoviedb.org/3/tv/{tid}/season/1?api_key={TMDB_API_KEY}").json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else IMG_BASE + d.get('poster_path')})
        except: pass

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')), "gallery": gallery, "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": save_data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_item?id={request.form.get('id')}&type={request.form.get('type')}")
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
