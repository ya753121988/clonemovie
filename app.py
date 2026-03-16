import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_movie_portal_fixed_v100"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_v100']
collection = db['all_data']

# --- UI লেআউট ইঞ্জিন (বিন্দু পরিমাণ এরর হবে না) ---
def get_ui(title, body_content):
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
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        body {{ background: #050505; color: white; font-family: 'Outfit', sans-serif; overflow-x: hidden; }}
        .glass {{ background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(15px); border-bottom: 1px solid #222; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s ease-in-out; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 tracking-tighter italic">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="মুভি, টিভি বা এক্টর খুঁজুন..." class="bg-transparent outline-none w-full text-xs md:text-sm text-white">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] transition">ADMIN</a>
        </div>
    </nav>
    {body_content}
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
        {% if not items %}
        <div class="h-[60vh] flex flex-col items-center justify-center text-center">
            <i class="fa fa-folder-open text-6xl text-zinc-800 mb-4"></i>
            <h2 class="text-xl font-bold text-zinc-500 uppercase">ডাটাবেস খালি! এডমিন থেকে সিঙ্ক করুন।</h2>
        </div>
        {% else %}
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 shadow-2xl block group relative">
                <div class="aspect-[2/3] overflow-hidden relative">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-circle-play text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-[10px] font-black px-2 py-1 rounded-full">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </main>
    '''
    return render_template_string(get_ui("Explore", content), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ ফিচার মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative min-h-screen pb-20">
        <div class="h-[50vh] md:h-[70vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[1px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] border border-zinc-800 shadow-2xl">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-4 rounded-2xl font-black shadow-xl hover:scale-105 transition">
                        <i class="fa fa-play text-xl"></i> ট্রেলার দেখুন
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase tracking-widest text-[10px] font-bold">
                        {% for cat in m.category %}
                        <span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>
                        {% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800 text-center">
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Rating</p><p class="font-black text-yellow-500 text-lg">⭐ {{ m.rating }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Language</p><p class="font-bold uppercase">{{ m.language }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Director</p><p class="font-bold text-[10px] truncate">{{ m.director.name }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">OTT</p><p class="font-black text-green-500 text-[10px]">{{ m.ott[0].name if m.ott else 'THEATER' }}</p></div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase text-rose-500 mb-5 tracking-widest">Streaming Platforms</p>
                        <div class="flex gap-6">
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

            <!-- Cast & Crew Profile Photos -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">এক্টর, ডিরেক্টর ও প্রডিউসার</h3>
                <div class="flex gap-10 overflow-x-auto pb-10">
                    <div class="min-w-[140px] text-center">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 uppercase font-black">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-500 uppercase">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase italic">Gallery & Wallpapers</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}
                    <img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 hover:scale-105 transition">
                    {% endfor %}
                </div>
            </div>

            <!-- Episodes List -->
            {% if m.episodes %}
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase">Episodes List</h3>
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-[2rem] p-4 border border-zinc-800 flex flex-col gap-4">
                        <img src="{{ ep.img }}" class="w-full h-32 object-cover rounded-2xl">
                        <div>
                            <p class="text-[10px] text-rose-600 font-black mb-1 uppercase tracking-widest italic">S{{ ep.season }} | E{{ ep.num }}</p>
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
    return render_template_string(get_ui(m['title'], content), m=m)

# --- এডমিন প্যানেল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    return render_template_string(get_ui("Admin Access", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-3xl font-black mb-10 text-center text-rose-600 uppercase italic">Admin Auth</h2><input type="password" name="pw" placeholder="Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none focus:border-rose-600 transition"><button class="w-full bg-rose-600 py-4 rounded-3xl font-black shadow-xl">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-5xl pb-32">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-6 uppercase italic">
            <h1 class="text-3xl font-black italic tracking-tighter">Control Hub</h1>
            <a href="/logout" class="text-rose-500 font-bold text-xs underline">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <!-- Unlimited Auto Sync -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-blue-500 uppercase tracking-widest italic text-center">Unlimited Auto Sync</h3>
                <div class="flex flex-col gap-4 mb-6">
                    <input type="number" id="yr" placeholder="সাল (2024)" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center">
                    <input type="number" id="pg" placeholder="কয়টি পেজ? (যেমন: 10)" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center">
                    <select id="type" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center">
                        <option value="movie">Movies</option><option value="tv">TV Shows</option>
                    </select>
                </div>
                <button onclick="startUnlimitedSync()" id="btn" class="w-full bg-blue-600 py-4 rounded-3xl font-black shadow-lg">START AUTO SYNC</button>
                <div id="stat" class="mt-6 text-[10px] text-zinc-500 font-mono tracking-widest text-center max-h-32 overflow-y-auto hidden"></div>
            </div>
            
            <!-- Manual ID Sync -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-rose-500 uppercase tracking-widest italic text-center">Manual TMDB ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <input type="text" name="id" placeholder="ID (যেমন: 550)" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center">
                    <select name="type" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-rose-600 py-4 rounded-3xl font-black shadow-lg">SYNC NOW</button>
                </form>
            </div>
        </div>

        <!-- Manage Library -->
        <div class="bg-zinc-900 rounded-[3.5rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm"><thead class="bg-zinc-800 text-zinc-500 font-black"><tr><th class="p-8">Content</th><th class="p-8 text-center">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800">
                {{% for i in items %}}
                <tr><td class="p-8 font-black uppercase text-xs">{{{{ i.title }}}} ({{{{ i.year }}}})</td>
                <td class="p-8 text-center flex justify-center gap-6">
                    <a href="/edit/{{{{ i.tmdb_id }}}}" class="text-blue-500 text-xl"><i class="fa fa-edit"></i></a>
                    <a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-500 text-xl"><i class="fa fa-trash-alt"></i></a>
                </td></tr>
                {{% endfor %}}
            </tbody></table>
        </div>
    </div>
    <script>
    async function startUnlimitedSync() {{
        const yr = document.getElementById('yr').value;
        const pg = document.getElementById('pg').value || 1;
        const t = document.getElementById('type').value;
        const b = document.getElementById('btn');
        const s = document.getElementById('stat');
        if(!yr) return alert('Enter Year!');
        b.disabled = true; s.classList.remove('hidden');
        for(let p=1; p <= pg; p++) {{
            s.innerHTML += `<div>Fetching Page ${{p}}...</div>`;
            const r = await fetch(`/get_bulk_ids?year=${{yr}}&page=${{p}}&type=${{t}}`);
            const d = await r.json();
            for(let item of d.ids) {{
                s.innerHTML += `<div>Syncing: ${{item.title}}</div>`;
                s.scrollTop = s.scrollHeight;
                await fetch(`/sync_item?id=${{item.id}}&type=${{t}}`);
            }}
        }}
        s.innerHTML += `<div class="text-green-500 mt-4 underline">ALL DATA SAVED! REFRESHING...</div>`;
        setTimeout(() => location.reload(), 2000);
    }}
    </script>
    '''
    return render_template_string(get_ui("Dashboard", content), items=items)

# --- ৪. স্ক্র্যাপিং লজিক রাউটস ---

@app.route('/get_bulk_ids')
def get_bulk_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/sync_item')
def sync_item():
    tid, mtype = request.args.get('id'), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:25]]

    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:15]]

    eps = []
    if mtype == 'tv':
        try:
            s_data = requests.get(f"https://api.themoviedb.org/3/tv/{tid}/season/1?api_key={TMDB_API_KEY}").json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "season": 1, "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else IMG_BASE + d.get('poster_path')})
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
    if session.get('logged'): requests.get(f"{request.url_root}sync_item?id={request.form.get('id')}&type={request.form.get('type')}")
    return redirect('/admin/dashboard')

@app.route('/del/<id>')
def delete(id):
    if session.get('logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/dashboard')

@app.route('/edit/<tid>', methods=['GET', 'POST'])
def edit(tid):
    if not session.get('logged'): return redirect('/admin')
    m = collection.find_one({"tmdb_id": tid})
    if request.method == 'POST':
        collection.update_one({"tmdb_id": tid}, {"$set": {"title": request.form.get('t'), "story": request.form.get('s')}})
        return redirect('/admin/dashboard')
    return render_template_string(get_ui("Edit", f'<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] w-full max-w-xl"><h2 class="text-2xl font-bold mb-6">Edit: {m["title"]}</h2><input name="t" value="{m["title"]}" class="w-full bg-black p-4 rounded-2xl mb-4"><textarea name="s" class="w-full bg-black p-4 rounded-2xl mb-4 h-40">{m["story"]}</textarea><button class="w-full bg-blue-600 py-4 rounded-2xl font-bold">UPDATE</button></form></div>'))

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
