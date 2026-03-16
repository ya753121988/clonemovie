import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_ultimate_pro_v101"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন (Fixed Name to avoid 100 DB Limit)
client = MongoClient(MONGO_URI)
db = client['MoviePortal_DB']
collection = db['media_content']

# --- HTML Layout ---
def get_layout(title, body):
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
        body {{ background: #050505; color: white; font-family: 'Outfit', sans-serif; }}
        .glass {{ background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(20px); border-bottom: 1px solid #222; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic">MOVIE-AI</a>
            <form action="/" method="GET" class="flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="Search..." class="bg-transparent outline-none w-full text-xs md:text-sm">
            </form>
            <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px]">ADMIN</a>
        </div>
    </nav>
    {body}
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
            <i class="fa fa-film text-6xl text-zinc-800 mb-4"></i>
            <h2 class="text-xl font-bold text-zinc-500 uppercase">ডাটাবেস খালি!</h2>
            <p class="text-zinc-600 mt-2">এডমিন প্যানেল থেকে মুভি সিঙ্ক করুন।</p>
        </div>
        {% else %}
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 block group relative">
                <div class="aspect-[2/3] overflow-hidden relative">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition"><i class="fa-solid fa-play text-5xl"></i></div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </main>
    '''
    return render_template_string(get_layout("Explore", content), items=items)

# --- ডিটেইল পেজ (বিন্দু পরিমাণ ফিচার মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative min-h-screen pb-20">
        <div class="h-[60vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[1px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-4 rounded-2xl font-black shadow-xl"><i class="fa fa-play"></i> Watch Trailer</a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-6xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase tracking-widest text-[10px] font-bold">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2rem] border border-zinc-800">
                        <div><p class="text-[10px] text-zinc-500 uppercase">Rating</p><p class="font-bold text-yellow-500">⭐ {{ m.rating }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">Language</p><p class="font-bold uppercase">{{ m.language }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">Director</p><p class="font-bold text-[10px] truncate">{{ m.director.name }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">OTT</p><p class="text-green-500 font-bold uppercase text-[10px]">{{ m.ott[0].name if m.ott else 'THEATER' }}</p></div>
                    </div>

                    {% if m.ott %}
                    <div class="p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem] mb-10">
                        <p class="text-xs font-black uppercase text-rose-500 mb-6 tracking-widest italic">Released On (OTT)</p>
                        <div class="flex flex-wrap gap-8">
                            {% for ott in m.ott %}
                            <div class="text-center"><img src="{{ ott.logo }}" class="w-14 h-14 rounded-2xl shadow-xl"><p class="text-[9px] mt-2 font-bold">{{ ott.name }}</p></div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Producers Profiles -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase">এক্টর, ডিরেক্টর ও প্রডিউসার</h3>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <div class="min-w-[150px] text-center">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl">
                        <p class="mt-4 font-black text-sm text-white">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[150px] text-center">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm text-white">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[150px] text-center group">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:border-white transition">
                        <p class="mt-4 font-black text-sm text-white">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 font-bold uppercase truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase"> Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}<img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 hover:scale-105 transition">{% endfor %}
                </div>
            </div>
            
            <!-- Episodes if TV -->
            {% if m.episodes %}
            <div class="mt-32 pb-20"><h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic text-rose-500">Episodes List</h3>
                <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
                    {% for ep in m.episodes %}
                    <div class="bg-zinc-900 rounded-[2rem] p-4 border border-zinc-800 flex flex-col gap-4">
                        <img src="{{ ep.img }}" class="w-full h-32 object-cover rounded-2xl shadow-lg">
                        <div><p class="text-[10px] text-rose-600 font-black uppercase">E{{ ep.num }} | S{{ ep.season }}</p><p class="font-black text-sm truncate">{{ ep.name }}</p></div>
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
    return render_template_string(get_layout("Admin Login", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-3xl font-black mb-10 text-center text-rose-600 uppercase">Admin</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none"><button class="w-full bg-rose-600 py-4 rounded-2xl font-black shadow-xl">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-3xl font-black">Admin Panel</h1>
            <a href="/logout" class="text-rose-500 font-bold uppercase text-xs">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-blue-500 uppercase tracking-widest text-center italic">Unlimited Auto Sync</h3>
                <div class="flex flex-col gap-4 mb-6">
                    <input type="number" id="yr" placeholder="Year" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-white text-center">
                    <input type="number" id="pg" placeholder="Total Pages (1-50)" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-white text-center">
                    <select id="type" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-center"><option value="movie">Movies</option><option value="tv">TV Shows</option></select>
                </div>
                <button onclick="startSync()" id="btn" class="w-full bg-blue-600 py-4 rounded-xl font-black">START AUTO SYNC</button>
                <div id="stat" class="mt-4 text-[10px] text-zinc-500 font-mono tracking-widest text-center max-h-32 overflow-y-auto hidden"></div>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-rose-500 uppercase tracking-widest text-center italic">Single ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <input type="text" name="id" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none text-white text-center">
                    <button class="bg-rose-600 py-4 rounded-xl font-black">SYNC NOW</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3.5rem] border border-zinc-800 overflow-hidden">
            <table class="w-full text-left text-xs font-black uppercase"><thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-8">Name</th><th class="p-8 text-center">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800 uppercase font-black text-[11px]">
                {{% for i in items %}}
                <tr><td class="p-8 text-zinc-200">{{{{ i.title }}}} ({{{{ i.year }}}})</td>
                <td class="p-8 text-center flex justify-center gap-6"><a href="/edit/{{{{ i.tmdb_id }}}}" class="text-blue-500"><i class="fa fa-edit text-xl"></i></a><a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-500"><i class="fa fa-trash-alt text-xl"></i></a></td></tr>
                {{% endfor %}}
            </tbody></table>
        </div>
    </div>
    <script>
    async function startSync() {{
        const yr = document.getElementById('yr').value;
        const pg = document.getElementById('pg').value || 1;
        const t = document.getElementById('type').value;
        const b = document.getElementById('btn');
        const s = document.getElementById('stat');
        if(!yr) return alert('সাল দিন!');
        b.disabled = true; s.classList.remove('hidden');
        for(let p=1; p <= pg; p++) {{
            s.innerHTML += `<div>Fetching Page ${{p}}...</div>`;
            const r = await fetch(`/get_ids?year=${{yr}}&page=${{p}}&type=${{t}}`);
            const d = await r.json();
            for(let item of d.ids) {{
                s.innerHTML += `<div>Saving: ${{item.title}}</div>`;
                s.scrollTop = s.scrollHeight;
                await fetch(`/sync_single?id=${{item.id}}&type=${{t}}`);
            }}
        }}
        s.innerHTML += `<div class="text-green-500 mt-4 underline font-black">SUCCESS! REFRESHING...</div>`;
        setTimeout(() => location.reload(), 2000);
    }}
    </script>
    '''
    return render_template_string(get_layout("Admin Panel", content), items=items)

# --- স্ক্র্যাপিং ইঞ্জিন রাউটস ---

@app.route('/get_ids')
def get_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "Unknown", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")

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
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')),
        "gallery": [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]], "episodes": eps
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
    body = f'''<div class="h-screen flex items-center justify-center"><form method="POST" class="bg-zinc-900 p-10 rounded-3xl w-full max-w-sm"><input name="t" value="{item['title']}" class="w-full bg-black p-4 mb-4"><input name="y" value="{item['year']}" class="w-full bg-black p-4 mb-4"><textarea name="s" class="w-full bg-black p-4 mb-4">{item['story']}</textarea><button class="w-full bg-blue-600 p-4">UPDATE</button></form></div>'''
    return render_template_string(get_layout("Edit", body))

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'): requests.get(f"{request.url_root}sync_single?id={request.form.get('id')}")
    return redirect('/admin/dashboard')

@app.route('/del/<tid>')
def delete(tid):
    if session.get('logged'): collection.delete_one({"tmdb_id": str(tid)})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
