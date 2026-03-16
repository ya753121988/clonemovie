import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "final_mega_cinema_v100"

# --- আপনার দেওয়া তথ্য (Fixed) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন (Consistent Name: my_cinema_db)
client = MongoClient(MONGO_URI)
db = client['my_cinema_db']
collection = db['all_data']

# --- UI টেমপ্লেট ---
def get_ui(title, body):
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
        body {{ background: #050505; color: white; font-family: sans-serif; }}
        .glass {{ background: rgba(15, 15, 15, 0.9); backdrop-filter: blur(15px); border-bottom: 1px solid #333; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl font-black text-rose-600">MOVIE-AI</a>
            <form action="/" method="GET" class="flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-4 py-1.5">
                <input type="text" name="q" placeholder="Search..." class="bg-transparent outline-none w-full text-sm">
            </form>
            <a href="/admin" class="bg-zinc-800 px-4 py-1.5 rounded-full font-bold text-xs">ADMIN</a>
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
            <i class="fa fa-database text-6xl text-zinc-800 mb-4"></i>
            <h2 class="text-xl font-bold text-zinc-500 uppercase">কোনো মুভি পাওয়া যায়নি!</h2>
            <p class="text-zinc-600 mt-2">এডমিন প্যানেল থেকে সিঙ্ক করুন।</p>
        </div>
        {% else %}
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 block group relative">
                <div class="aspect-[2/3] relative overflow-hidden">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-circle-info text-5xl"></i>
                    </div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </main>
    '''
    return render_template_string(get_ui("Explore", content), items=items)

# --- ডিটেইল পেজ ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative pb-20">
        <div class="h-[60vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[2px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-4 rounded-2xl font-black">
                        <i class="fa fa-play"></i> TRAILER
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 text-[10px] font-bold uppercase">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 mb-10">{{ m.story }}</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2rem] border border-zinc-800">
                        <div><p class="text-[10px] text-zinc-500 uppercase">Rating</p><p class="font-bold text-yellow-500">⭐ {{ m.rating }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">Language</p><p class="font-bold uppercase">{{ m.language }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">Director</p><p class="font-bold text-xs">{{ m.director.name }}</p></div>
                        <div><p class="text-[10px] text-zinc-500 uppercase">OTT</p><p class="text-green-500 font-bold uppercase text-[10px]">{{ m.ott[0].name if m.ott else 'N/A' }}</p></div>
                    </div>
                </div>
            </div>

            <!-- Cast Section -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 uppercase">Full Cast</h3>
                <div class="flex gap-10 overflow-x-auto pb-8">
                    <div class="min-w-[120px] text-center">
                        <img src="{{ m.director.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-rose-600">
                        <p class="mt-4 font-bold text-xs">{{ m.director.name }}</p>
                        <p class="text-[9px] text-zinc-500 uppercase">Director</p>
                    </div>
                    {% for a in m.cast %}
                    <div class="min-w-[120px] text-center">
                        <img src="{{ a.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-bold text-xs">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-500 uppercase">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>
            
            <!-- Gallery -->
            <div class="mt-20 pb-32"><h3 class="text-2xl font-black mb-10 uppercase">Gallery</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}
                    <img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800">
                    {% endfor %}
                </div>
            </div>
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
    return render_template_string(get_ui("Admin", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-2xl font-bold mb-8 text-center text-rose-600">Admin Access</h2><input type="password" name="pw" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-6 text-center outline-none"><button class="w-full bg-rose-600 py-3 rounded-2xl font-bold">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="flex justify-between items-center mb-12">
            <h1 class="text-3xl font-black">Dashboard</h1>
            <a href="/logout" class="text-rose-500 font-bold uppercase text-xs">Logout</a>
        </div>

        <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 shadow-2xl mb-12">
            <h3 class="font-bold mb-6 text-blue-500 uppercase tracking-widest text-center">Unlimited Auto Sync</h3>
            <div class="flex flex-col md:flex-row gap-4 mb-6">
                <input type="number" id="yr" placeholder="Year" class="bg-black border border-zinc-700 p-4 rounded-xl flex-1 outline-none">
                <input type="number" id="pg" placeholder="Pages" class="bg-black border border-zinc-700 p-4 rounded-xl w-full md:w-32 outline-none">
                <select id="type" class="bg-black border border-zinc-700 p-4 rounded-xl outline-none"><option value="movie">Movie</option><option value="tv">TV</option></select>
            </div>
            <button onclick="startAutoSync()" id="btn" class="w-full bg-blue-600 py-4 rounded-xl font-black">START UNLIMITED SYNC</button>
            <div id="stat" class="mt-6 p-4 bg-black/50 rounded-xl text-[10px] font-mono text-zinc-500 hidden"></div>
        </div>

        <div class="bg-zinc-900 rounded-[2.5rem] border border-zinc-800 overflow-hidden">
            <table class="w-full text-left text-xs uppercase font-bold">
                <thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-6">Content</th><th class="p-6 text-center">Action</th></tr></thead>
                <tbody>
                    {% for i in items %}
                    <tr class="border-b border-zinc-800"><td class="p-6">{{ i.title }} ({{ i.year }})</td>
                    <td class="p-6 text-center flex justify-center gap-4"><a href="/edit/{{ i.tmdb_id }}" class="text-blue-500"><i class="fa fa-edit"></i></a><a href="/del/{{ i.tmdb_id }}" class="text-rose-500"><i class="fa fa-trash"></i></a></td></tr>
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
            s.innerHTML += `<div>Fetching Page ${{p}}...</div>`;
            const r = await fetch(`/get_ids?year=${{yr}}&page=${{p}}&type=${{t}}`);
            const d = await r.json();
            for(let item of d.ids) {{
                s.innerHTML += `<div>Saving: ${{item.title}}</div>`;
                s.scrollTop = s.scrollHeight;
                await fetch(`/sync_single?id=${{item.id}}&type=${{t}}`);
            }}
        }}
        s.innerHTML += `<div class="text-green-500 font-black mt-2">DONE! REFRESHING...</div>`;
        setTimeout(() => location.reload(), 2000);
    }}
    </script>
    '''
    return render_template_string(get_ui("Dashboard", content), items=items)

# --- সিঙ্ক ইঞ্জিন রাউটস ---

@app.route('/get_ids')
def get_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")

    data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')),
        "gallery": [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/del/<tid>')
def delete(tid):
    if session.get('logged'): collection.delete_one({"tmdb_id": tid})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
