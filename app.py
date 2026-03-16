import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_mega_cinema_v20"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_v20']
collection = db['all_data']

# --- UI টেমপ্লেট ফাংশন ---
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
        body {{ background: #050505; color: white; font-family: 'Inter', sans-serif; }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
        .glass {{ background: rgba(10, 10, 10, 0.8); backdrop-filter: blur(20px); }}
    </style>
</head>
<body>
    <nav class="glass border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-4 py-1.5">
                <input type="text" name="q" placeholder="মুভি বা টিভি শো খুঁজুন..." class="bg-transparent outline-none w-full text-xs md:text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="hidden md:block bg-rose-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-rose-700 transition">ADMIN</a>
        </div>
    </nav>
    {body}
</body>
</html>
'''

# --- হোম পেজ রাউট ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({{"title": {{"$regex": q, "$options": "i"}}}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    content = '''
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 shadow-2xl block group">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-play-circle text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-[10px] font-black px-2 py-1 rounded-full shadow-lg">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-sm truncate uppercase tracking-tighter">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold tracking-widest">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
    </main>
    '''
    return render_template_string(get_layout("Explore Movies", content), items=items)

# --- ডিটেইল পেজ রাউট (বিন্দু পরিমাণ ফিচার মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative min-h-screen">
        <div class="h-[50vh] md:h-[70vh] relative">
            <img src="{{ m.backdrop if m.backdrop else m.poster }}" class="w-full h-full object-cover opacity-20">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-64 relative z-10">
            <div class="flex flex-col lg:flex-row gap-10">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-6 flex items-center justify-center gap-3 bg-rose-600 py-4 rounded-2xl font-black shadow-xl">
                        <i class="fa fa-play"></i> ট্রেলার দেখুন
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-6xl font-black mb-6 leading-tight">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-3 mb-8">
                        {% for genre in m.category %}
                        <span class="bg-zinc-800 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">{{ genre }}</span>
                        {% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-[10px] font-bold tracking-widest">{{ m.year }}</span>
                    </div>
                    
                    <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800 mb-8">
                        <h3 class="text-rose-500 font-bold text-sm uppercase mb-3">মুভির গল্প</h3>
                        <p class="text-zinc-300 leading-relaxed">{{ m.summary }}</p>
                    </div>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Rating</p>
                            <p class="font-bold text-yellow-500">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Language</p>
                            <p class="font-bold">{{ m.language | upper }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Director</p>
                            <p class="font-bold truncate">{{ m.director.name }}</p>
                        </div>
                        <div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase">Released</p>
                            <p class="font-bold">{{ m.release_date }}</p>
                        </div>
                    </div>

                    {% if m.ott_info %}
                    <div class="mb-10">
                        <h3 class="font-bold text-xs uppercase text-zinc-500 mb-4">মুভিটি যেখানে পাবেন (OTT)</h3>
                        <div class="flex gap-4">
                            {% for ott in m.ott_info %}
                            <div class="flex flex-col items-center">
                                <img src="{{ ott.logo }}" class="w-12 h-12 rounded-xl shadow-lg border border-zinc-800">
                                <p class="text-[9px] mt-1 text-zinc-400">{{ ott.name }}</p>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Crew -->
            <div class="mt-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase">এক্টর ও ডিরেক্টর প্রোফাইল</h3>
                <div class="flex gap-8 overflow-x-auto pb-8">
                    <!-- Director -->
                    <div class="min-w-[120px] text-center">
                        <img src="{{ m.director.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-xl">
                        <p class="text-xs font-bold mt-4">{{ m.director.name }}</p>
                        <p class="text-[9px] text-zinc-500">DIRECTOR</p>
                    </div>
                    <!-- Producers -->
                    {% for p in m.producers %}
                    <div class="min-w-[120px] text-center">
                        <img src="{{ p.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-2 border-zinc-800">
                        <p class="text-xs font-bold mt-4">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500">PRODUCER</p>
                    </div>
                    {% endfor %}
                    <!-- Cast -->
                    {% for a in m.cast %}
                    <div class="min-w-[120px] text-center">
                        <img src="{{ a.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-2 border-zinc-800">
                        <p class="text-xs font-bold mt-4">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-500">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-20 pb-32"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase">পোস্টার ও থাম্বনেইল গ্যালারি</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}
                    <img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 shadow-xl hover:scale-105 transition">
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(get_layout(m['title'], content), m=m)

# --- এডমিন কন্ট্রোল রাউটস ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    return render_template_string(get_layout("Admin Login", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-2xl font-black mb-8 text-center text-rose-600 uppercase">Admin Access</h2><input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-4 text-center outline-none"><button class="w-full bg-rose-600 py-4 rounded-2xl font-bold shadow-lg">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-6xl">
        <div class="flex justify-between items-center mb-10 border-b border-zinc-800 pb-6">
            <h1 class="text-2xl font-bold">Admin Dashboard</h1>
            <a href="/logout" class="text-rose-500 font-bold">LOGOUT</a>
        </div>
        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800">
                <h3 class="font-bold mb-6 text-blue-500 uppercase tracking-widest"><i class="fa fa-sync-alt mr-2"></i>Bulk Year Sync</h3>
                <div class="flex gap-2">
                    <input type="number" id="sy" placeholder="2024" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <button onclick="startBulk()" id="sb" class="bg-blue-600 px-6 py-3 rounded-xl font-bold">START SYNC</button>
                </div>
                <div id="st" class="mt-4 text-[10px] text-zinc-500 font-mono"></div>
            </div>
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800">
                <h3 class="font-bold mb-6 text-rose-500 uppercase tracking-widest"><i class="fa fa-id-card mr-2"></i>Single ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex gap-2">
                    <input type="text" name="id" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-3 rounded-xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-rose-600 px-6 py-3 rounded-xl font-bold">SYNC</button>
                </form>
            </div>
        </div>
        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden">
            <table class="w-full text-left text-sm"><thead class="bg-zinc-800 text-zinc-500"><tr><th class="p-6 uppercase">Title</th><th class="p-6 text-center">Action</th></tr></thead>
            <tbody>{{% for i in items %}}<tr><td class="p-6 font-bold">{{{{ i.title }}}} ({{{{ i.year }}}})</td><td class="p-6 text-center"><a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-500"><i class="fa fa-trash"></i></a></td></tr>{{% endfor %}}</tbody></table>
        </div>
    </div>
    <script>
    async function startBulk() {{
        const yr = document.getElementById('sy').value;
        const btn = document.getElementById('sb');
        const st = document.getElementById('st');
        if(!yr) return alert('Enter Year');
        btn.disabled = true;
        const r = await fetch(`/get_year_ids?year=${{yr}}`);
        const d = await r.json();
        for(let i=0; i<d.ids.length; i++) {{
            st.innerText = `Syncing (${{i+1}}/${{d.ids.length}}): ${{d.ids[i].title}}`;
            await fetch(`/sync_single?id=${{d.ids[i].id}}&type=${{d.ids[i].type}}`);
        }}
        location.reload();
    }}
    </script>
    '''
    return render_template_string(get_layout("Dashboard", content), items=items)

# --- ইন্টারনাল এপিআই রাউটস (The Heart of System) ---

@app.route('/get_year_ids')
def get_year_ids():
    y = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={y}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m['title'], "type": "movie"} for m in res[:20]]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    # ১. ডিরেক্টর ও প্রডিউসার তথ্য (সব তথ্য ও ছবিসহ)
    crew = d.get('credits', {}).get('crew', [])
    director_data = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:3]

    # ২. সব অভিনেতা (অ্যাক্টর)
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:15]]

    # ৩. OTT তথ্য (Watch Providers)
    ott_info = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for provider in providers:
        ott_info.append({"name": provider['provider_name'], "logo": IMG_BASE + provider['logo_path']})

    # ৪. ট্রেলার ও গ্যালারি
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]

    save_data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])],
        "director": director_data, "producers": producers, "cast": cast,
        "ott_info": ott_info, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + d.get('backdrop_path'), "gallery": gallery
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
