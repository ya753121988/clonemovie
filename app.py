import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_pro_fixed_v35"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['movie_portal_final']
collection = db['content_data']

# --- UI ইঞ্জিন (HTML/CSS) ---
def get_layout(title, body_content):
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
        .glass {{ background: rgba(15, 15, 15, 0.8); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.05); }}
        .m-card:hover {{ transform: scale(1.05); border-color: #e11d48; transition: 0.4s ease; }}
        ::-webkit-scrollbar {{ width: 5px; }}
        ::-webkit-scrollbar-thumb {{ background: #e11d48; border-radius: 10px; }}
    </style>
</head>
<body>
    <nav class="glass p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center gap-4">
            <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
                <input type="text" name="q" placeholder="Search..." class="bg-transparent outline-none w-full text-xs md:text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-xs transition">ADMIN</a>
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
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    if not items:
        content = '''
        <div class="h-[70vh] flex flex-col items-center justify-center text-center px-4">
            <i class="fa fa-film text-6xl text-zinc-800 mb-4"></i>
            <h2 class="text-2xl font-bold text-zinc-500">ডাটাবেসে কোনো মুভি নেই!</h2>
            <p class="text-zinc-600 mt-2">প্রথমে এডমিন প্যানেলে গিয়ে মুভি সিঙ্ক (Sync) করুন।</p>
            <a href="/admin" class="mt-6 bg-rose-600 px-8 py-3 rounded-full font-bold shadow-lg shadow-rose-900/40">এডমিন প্যানেলে যান</a>
        </div>
        '''
    else:
        content = '''
        <main class="container mx-auto py-10 px-4">
            <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6 md:gap-8">
                {% for m in items %}
                <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2.5rem] overflow-hidden border border-zinc-800 block group relative">
                    <div class="aspect-[2/3] overflow-hidden">
                        <img src="{{ m.poster }}" class="w-full h-full object-cover">
                        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                            <i class="fa-solid fa-play-circle text-5xl"></i>
                        </div>
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
    return render_template_string(get_layout("Home", content), items=items)

# --- ২. ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    content = '''
    <div class="relative min-h-screen pb-20">
        <div class="h-[50vh] md:h-[70vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-30 blur-[1px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3rem] shadow-2xl border border-zinc-800">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-rose-600 py-4 rounded-2xl font-black shadow-xl">
                        <i class="fa fa-play"></i> ট্রেলার দেখুন
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-6xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-3 mb-8">
                        {% for cat in m.category %}
                        <span class="bg-zinc-800 px-4 py-1.5 rounded-full text-[10px] font-bold uppercase tracking-widest">{{ cat }}</span>
                        {% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-[10px] font-bold">{{ m.year }}</span>
                    </div>
                    
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10">{{ m.story }}</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10">
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Rating</p>
                            <p class="text-xl font-black text-yellow-500">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Language</p>
                            <p class="font-bold">{{ m.language | upper }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Released</p>
                            <p class="text-sm font-black">{{ m.release_date }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-5 rounded-3xl border border-zinc-800">
                            <p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">OTT</p>
                            <p class="text-[10px] font-black uppercase text-green-500">{{ m.ott[0].name if m.ott else 'N/A' }}</p>
                        </div>
                    </div>

                    {% if m.ott %}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase text-rose-500 mb-5 tracking-widest italic">Streaming On</p>
                        <div class="flex gap-6">
                            {% for ott in m.ott %}
                            <div class="flex flex-col items-center">
                                <img src="{{ ott.logo }}" class="w-12 h-12 rounded-xl shadow-lg">
                                <span class="text-[9px] mt-2 font-bold text-zinc-500">{{ ott.name }}</span>
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
                    <div class="min-w-[140px] text-center">
                        <img src="{{ m.director.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl">
                        <p class="mt-4 font-black text-sm">{{ m.director.name }}</p>
                        <p class="text-[10px] text-rose-500 font-black uppercase tracking-widest">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ p.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ p.name }}</p>
                        <p class="text-[10px] text-zinc-500 font-black uppercase tracking-widest">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[140px] text-center">
                        <img src="{{ a.photo }}" class="w-24 h-24 rounded-full mx-auto object-cover border-4 border-zinc-800 shadow-xl">
                        <p class="mt-4 font-black text-sm">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 uppercase tracking-tighter truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-20 pb-20"><h3 class="text-2xl font-black mb-10 border-l-4 border-rose-600 pl-4 uppercase">পোস্টার ও থাম্বনেইল গ্যালারি</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for p in m.gallery %}
                    <img src="{{ p }}" class="w-full rounded-3xl border border-zinc-800 shadow-xl hover:scale-110 transition">
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(get_layout(m['title'], content), m=m)

# --- ৩. এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    return render_template_string(get_layout("Admin Auth", '<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 w-full max-w-sm"><h2 class="text-2xl font-black mb-8 text-center text-rose-600 uppercase">Admin</h2><input type="password" name="pw" placeholder="Password" class="w-full bg-black border border-zinc-700 p-4 rounded-2xl mb-6 text-center outline-none"><button class="w-full bg-rose-600 py-4 rounded-2xl font-bold shadow-lg shadow-rose-900/20">LOGIN</button></form></div>'))

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    content = f'''
    <div class="container mx-auto py-10 px-4 max-w-5xl pb-32">
        <div class="flex justify-between items-center mb-10 border-b border-zinc-800 pb-6">
            <h1 class="text-2xl font-black italic tracking-tighter">DASHBOARD</h1>
            <a href="/logout" class="text-rose-500 font-bold text-xs">LOGOUT</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-16">
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-blue-500 uppercase tracking-widest"><i class="fa fa-sync-alt mr-2"></i>Yearly Bulk Sync</h3>
                <div class="flex gap-2">
                    <input type="number" id="yr" placeholder="2024" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none text-white">
                    <button onclick="bulkSync()" id="bs" class="bg-blue-600 px-6 py-3 rounded-xl font-bold">START</button>
                </div>
                <div id="stat" class="mt-4 text-[10px] text-zinc-500 font-mono tracking-widest uppercase"></div>
            </div>
            
            <div class="bg-zinc-900 p-8 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-6 text-rose-500 uppercase tracking-widest"><i class="fa fa-id-card mr-2"></i>Single ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex gap-2">
                    <input type="text" name="id" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-3 rounded-xl flex-1 outline-none text-white">
                    <button class="bg-rose-600 px-6 py-3 rounded-xl font-bold">SYNC</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800 text-zinc-500 uppercase text-[10px] font-black"><tr><th class="p-6">Content</th><th class="p-6 text-center">Action</th></tr></thead>
                <tbody class="divide-y divide-zinc-800">
                    {{% for i in items %}}
                    <tr><td class="p-6 font-bold text-white">{{{{ i.title }}}} ({{{{ i.year }}}})</td>
                    <td class="p-6 text-center"><a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-500 text-lg hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td></tr>
                    {{% endfor %}}
                </tbody>
            </table>
        </div>
    </div>
    <script>
    async function bulkSync() {{
        const y = document.getElementById('yr').value;
        const b = document.getElementById('bs');
        const s = document.getElementById('stat');
        if(!y) return alert('সাল দিন!');
        b.disabled = true; s.innerText = 'Fetching IDs...';
        const r = await fetch(`/get_year_ids?year=${{y}}`);
        const d = await r.json();
        for(let i=0; i<d.ids.length; i++) {{
            s.innerText = `Syncing (${{i+1}}/${{d.ids.length}}): ${{d.ids[i].title}}`;
            await fetch(`/sync_item?id=${{d.ids[i].id}}&type=movie`);
        }}
        s.innerText = 'Sync Done! Refreshing...'; location.reload();
    }}
    </script>
    '''
    return render_template_string(get_layout("Admin Panel", content), items=items)

# --- ৪. স্ক্র্যাপিং লজিক রাউটস ---

@app.route('/get_year_ids')
def get_year_ids():
    y = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={y}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m['title']} for m in res[:20]]})

@app.route('/sync_item')
def sync_item():
    tid = request.args.get('id')
    mtype = request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "Unknown", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    ott = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for prov in providers: ott.append({"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']})

    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:12]]

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
        requests.get(f"{request.url_root}sync_item?id={request.form.get('id')}")
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
