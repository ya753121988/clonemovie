import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "master_cinema_ultra_v100_secure"

# --- কনফিগারেশন (আপনার তথ্য) ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন (Fixed Database Name)
client = MongoClient(MONGO_URI)
db = client['MasterCinema_DB']
collection = db['media_content']

# --- UI লেআউট ইঞ্জিন ---
def get_ui(title, content):
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
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }}
        .person-card:hover img {{ border-color: #e11d48; transform: translateY(-5px); transition: 0.3s; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
        .modal {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="hidden md:flex flex-1 max-w-sm mx-4 bg-zinc-900 border border-zinc-800 rounded-full px-5 py-1.5">
                <input type="text" name="q" placeholder="Search movies, tv, actors..." class="bg-transparent outline-none w-full text-xs text-white">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <div class="flex gap-3">
                <a href="/admin" class="bg-rose-600 px-4 py-1.5 rounded-full font-bold text-xs shadow-lg shadow-rose-900/40 transition">ADMIN</a>
            </div>
        </div>
    </nav>
    {content}
    
    <!-- Person Detail Modal -->
    <div id="pModal" class="modal" onclick="this.style.display='none'">
        <div class="bg-zinc-900 border border-zinc-800 p-8 rounded-[3rem] max-w-2xl w-full max-h-[85vh] overflow-y-auto relative" onclick="event.stopPropagation()">
            <button class="absolute top-6 right-6 text-2xl" onclick="document.getElementById('pModal').style.display='none'">&times;</button>
            <div id="pContent" class="flex flex-col md:flex-row gap-8 text-center md:text-left">
                <!-- Ajax Data -->
            </div>
        </div>
    </div>

    <script>
        async function showPerson(id) {{
            const modal = document.getElementById('pModal');
            const content = document.getElementById('pContent');
            modal.style.display = 'flex';
            content.innerHTML = '<div class="w-full text-center py-20"><i class="fa fa-spinner fa-spin text-4xl text-rose-600"></i></div>';
            try {{
                const res = await fetch(`/api/person/${{id}}`);
                const p = await res.json();
                content.innerHTML = `
                    <img src="${{p.photo}}" class="w-56 h-72 object-cover rounded-[2rem] border border-zinc-700 shadow-2xl mx-auto">
                    <div class="flex-1">
                        <h2 class="text-3xl font-black text-rose-600 mb-2">${{p.name}}</h2>
                        <p class="text-xs font-bold text-zinc-500 mb-6 uppercase tracking-widest">${{p.job}}</p>
                        <div class="space-y-4 text-sm text-zinc-300">
                            <p><strong>Birthday:</strong> ${{p.birthday || 'Unknown'}}</p>
                            <p><strong>Place:</strong> ${{p.place || 'Unknown'}}</p>
                            <p class="leading-relaxed text-zinc-400 mt-6">${{p.bio || 'Biography not available.'}}</p>
                        </div>
                    </div>`;
            }} catch(e) {{ content.innerHTML = '<p class="text-red-500">Error loading profile.</p>'; }}
        }}
    </script>
</body>
</html>
'''

# --- হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    body = '''
    <main class="container mx-auto py-12 px-4">
        {% if not items %}
        <div class="h-[60vh] flex flex-col items-center justify-center text-center">
            <i class="fa fa-database text-6xl text-zinc-800 mb-4"></i>
            <h2 class="text-xl font-bold text-zinc-500 uppercase italic">Database Empty</h2>
            <p class="text-zinc-600 text-xs mt-2">Go to admin and sync data now.</p>
        </div>
        {% else %}
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6 md:gap-8">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2.5rem] overflow-hidden border border-zinc-800 block shadow-2xl group relative transition duration-500">
                <div class="aspect-[2/3] overflow-hidden relative">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-circle-play text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-[9px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter text-zinc-100">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </main>
    '''
    return render_template_string(get_ui("Explore", body), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    body = '''
    <div class="relative min-h-screen pb-20">
        <!-- Banner Backdrop (Thumbnail) -->
        <div class="h-[50vh] md:h-[80vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-30">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <!-- Poster & Trailer -->
                <div class="w-64 md:w-96 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3.5rem] border border-zinc-700 shadow-2xl">
                    {% if m.yt_id != "N/A" %}
                    <button onclick="document.getElementById('tModal').style.display='flex'" class="w-full mt-8 flex items-center justify-center gap-3 bg-red-600 py-5 rounded-3xl font-black shadow-xl shadow-red-900/40 hover:scale-105 transition">
                        <i class="fa fa-play"></i> ট্রেলার দেখুন
                    </button>
                    {% endif %}
                </div>

                <!-- Content Info -->
                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase text-[10px] font-bold tracking-widest">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full">{{ m.year }}</span>
                    </div>
                    
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800 text-center uppercase font-black text-[10px]">
                        <div><p class="text-zinc-500 mb-1">Rating</p><p class="text-yellow-500 text-xl font-black">⭐ {{ m.rating }}</p></div>
                        <div><p class="text-zinc-500 mb-1">Language</p><p class="text-lg">{{ m.language }}</p></div>
                        <div><p class="text-zinc-500 mb-1">Director</p><p class="text-rose-500 text-[11px] truncate">{{ m.director.name }}</p></div>
                        <div><p class="text-zinc-500 mb-1">Status</p><p class="text-green-500">{{ m.type | upper }}</p></div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase text-rose-500 mb-6 tracking-widest italic">Streaming On</p>
                        <div class="flex flex-wrap gap-8">
                            {% for ott in m.ott %}
                            <div class="text-center"><img src="{{ ott.logo }}" class="w-14 h-14 rounded-2xl shadow-xl"><p class="text-[9px] mt-2 font-bold">{{ ott.name }}</p></div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Crew Profile Photos -->
            <div class="mt-20"><h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase">এক্টর ও ডিরেক্টর প্রোফাইল</h3>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <div class="min-w-[150px] text-center person-card cursor-pointer" onclick="showPerson('{{ m.director.id }}')">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl transition duration-300">
                        <p class="mt-4 font-black text-sm">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[150px] text-center person-card cursor-pointer" onclick="showPerson('{{ p.id }}')">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl transition duration-300">
                        <p class="mt-4 font-black text-sm">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[150px] text-center person-card cursor-pointer" onclick="showPerson('{{ a.id }}')">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-lg transition duration-300">
                        <p class="mt-4 font-black text-sm">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-bold uppercase truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery Wallpapers -->
            <div class="mt-20 pb-32"><h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}<img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 hover:scale-110 transition duration-500">{% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Trailer Modal -->
    <div id="tModal" class="modal" onclick="this.style.display='none'">
        <div class="w-full max-w-5xl aspect-video bg-black rounded-[3rem] overflow-hidden shadow-2xl border border-zinc-800">
            <iframe src="https://www.youtube.com/embed/{{ m.yt_id }}?autoplay=1" class="w-full h-full" frameborder="0" allowfullscreen allow="autoplay"></iframe>
        </div>
    </div>
    '''
    return render_template_string(get_ui(m['title'], content), m=m)

# --- এডমিন কন্ট্রোল (লগইন, সিঙ্ক, ডিলিট, এডিট) ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    return render_template_string(get_ui("Admin", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm shadow-2xl"><h2 class="text-3xl font-black mb-10 text-center text-rose-600 uppercase">Admin Hub</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none focus:border-rose-600 transition"><button class="w-full bg-rose-600 py-4 rounded-3xl font-black shadow-xl">LOG IN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8 uppercase italic">
            <h1 class="text-3xl font-black tracking-tighter italic">ADMIN DASHBOARD</h1>
            <a href="/logout" class="text-rose-500 font-bold text-xs underline">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16 text-center">
            <!-- Unlimited Auto Bulk Sync -->
            <div class="bg-zinc-900 p-10 rounded-[4rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-blue-500 uppercase tracking-widest italic">Unlimited Auto Sync</h3>
                <div class="flex flex-col gap-3 mb-8">
                    <input type="number" id="yr" placeholder="Year (e.g. 2024)" class="bg-black border border-zinc-700 p-5 rounded-3xl outline-none text-white text-center">
                    <input type="number" id="pg" placeholder="Total Pages (1-100)" class="bg-black border border-zinc-700 p-5 rounded-3xl outline-none text-white text-center">
                    <select id="type" class="bg-black border border-zinc-700 p-5 rounded-3xl outline-none text-center"><option value="movie">Movies</option><option value="tv">TV Shows</option></select>
                </div>
                <button onclick="startAutoSync()" id="btn" class="w-full bg-blue-600 py-5 rounded-[2.5rem] font-black text-xl shadow-xl shadow-blue-900/30">START AUTO SYNC</button>
                <div id="stat" class="mt-8 p-6 bg-black/50 rounded-[2rem] border border-zinc-800 text-[10px] font-mono text-zinc-500 uppercase text-left max-h-48 overflow-y-auto hidden"></div>
            </div>
            
            <!-- Manual TMDB ID Sync (Manual Add System) -->
            <div class="bg-zinc-900 p-10 rounded-[4rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-rose-500 uppercase tracking-widest italic">Manual ID Sync</h3>
                <div class="flex flex-col gap-3 mb-8">
                    <input type="text" id="m_id" placeholder="TMDB ID (e.g. 550)" class="bg-black border border-zinc-700 p-5 rounded-3xl outline-none text-white text-center">
                    <select id="m_type" class="bg-black border border-zinc-700 p-5 rounded-3xl outline-none text-center"><option value="movie">Movie</option><option value="tv">TV</option></select>
                </div>
                <button onclick="manualSync()" id="m_btn" class="w-full bg-rose-600 py-5 rounded-[2.5rem] font-black text-white uppercase">Sync ID Now</button>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3.5rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-xs uppercase font-black tracking-widest">
                <thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-8">Content Name</th><th class="p-8 text-center">Action</th></tr></thead>
                <tbody class="divide-y divide-zinc-800 uppercase font-black text-[11px]">
                    {% for i in items %}
                    <tr><td class="p-8 text-zinc-200 text-sm font-black">{{ i.title }} ({{ i.year }})</td>
                    <td class="p-8 text-center flex justify-center gap-8">
                        <a href="/edit/{{ i.tmdb_id }}" class="text-blue-500 text-2xl hover:scale-125 transition"><i class="fa fa-edit"></i></a>
                        <a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete?')" class="text-rose-500 text-2xl hover:scale-125 transition"><i class="fa fa-trash-alt"></i></a>
                    </td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function startAutoSync() {{
        const yr = document.getElementById('yr').value;
        const pg = document.getElementById('pg').value || 1;
        const t = document.getElementById('type').value;
        const b = document.getElementById('btn');
        const s = document.getElementById('stat');
        if(!yr) return alert('Enter Year!');
        b.disabled = true; s.classList.remove('hidden');
        for(let p=1; p <= pg; p++) {{
            s.innerHTML += `<div>Fetching IDs: Page ${{p}}...</div>`;
            const r = await fetch(`/get_ids?year=${{yr}}&page=${{p}}&type=${{t}}`);
            const d = await r.json();
            for(let item of d.ids) {{
                s.innerHTML += `<div>Auto Saving: ${{item.title}}</div>`;
                s.scrollTop = s.scrollHeight;
                await fetch(`/sync_single?id=${{item.id}}&type=${{t}}`);
            }}
        }}
        s.innerHTML += `<div class="text-green-500 mt-4 underline font-black">ALL DATA SAVED! REFRESHING...</div>`;
        setTimeout(() => location.reload(), 2000);
    }}
    async function manualSync() {{
        const id = document.getElementById('m_id').value;
        const t = document.getElementById('m_type').value;
        if(!id) return alert('ID Required!');
        await fetch(`/sync_single?id=${{id}}&type=${{t}}`);
        location.reload();
    }}
    </script>
    '''
    return render_template_string(get_ui("Dashboard", content), items=items)

# --- ইন্টারনাল এপিআই রাউটস ---

@app.route('/api/person/<id>')
def api_person(id):
    url = f"https://api.themoviedb.org/3/person/{id}?api_key={TMDB_API_KEY}"
    d = requests.get(url).json()
    return jsonify({
        "name": d.get('name'), "photo": IMG_BASE + d.get('profile_path') if d.get('profile_path') else "https://via.placeholder.com/200",
        "bio": d.get('biography'), "birthday": d.get('birthday'), "place": d.get('place_of_birth'), "job": d.get('known_for_department')
    })

@app.route('/get_ids')
def get_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()
    crew = d.get('credits', {}).get('crew', [])
    director = next(({"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"id": 0, "name": "N/A", "photo": ""})
    producers = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]
    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:10]] + [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:10]]

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

@app.route('/edit/<tid>', methods=['GET', 'POST'])
def edit_item(tid):
    if not session.get('logged'): return redirect('/admin')
    item = collection.find_one({"tmdb_id": tid})
    if request.method == 'POST':
        collection.update_one({"tmdb_id": tid}, {"$set": {"title": request.form.get('t'), "story": request.form.get('s'), "year": request.form.get('y')}})
        return redirect('/admin/dashboard')
    body = f'''<div class="h-screen flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] w-full max-w-sm"><h2 class="text-2xl font-black mb-8">Edit: {item['title']}</h2><input name="t" value="{item['title']}" class="w-full bg-black p-4 mb-4 rounded-xl outline-none"><input name="y" value="{item['year']}" class="w-full bg-black p-4 mb-4 rounded-xl outline-none"><textarea name="s" class="w-full bg-black p-4 mb-4 rounded-xl h-32 outline-none">{item['story']}</textarea><button class="w-full bg-blue-600 p-4 rounded-xl font-bold uppercase tracking-widest">Update</button></form></div>'''
    return render_template_string(get_ui("Edit Content", body))

@app.route('/del/<tid>')
def delete(tid):
    if session.get('logged'): collection.delete_one({"tmdb_id": tid})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
