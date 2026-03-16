import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "master_cinema_absolute_v500"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন (Fixed DB Name to avoid 100 DB limit)
client = MongoClient(MONGO_URI)
db = client['AbsoluteCinema_DB']
collection = db['media_hub']

# --- UI Layout Helpers ---
NAV_HTML = """
<nav class="glass p-4 sticky top-0 z-50">
    <div class="container mx-auto flex justify-between items-center gap-4">
        <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
        <form action="/" method="GET" class="flex flex-1 max-w-md bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
            <input type="text" name="q" placeholder="মুভি, টিভি বা এক্টর..." class="bg-transparent outline-none w-full text-xs md:text-sm text-white">
            <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
        </form>
        <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] md:text-xs transition text-white">ADMIN</a>
    </div>
</nav>
"""

BASE_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;700;900&display=swap');
        body { background: #050505; color: white; font-family: 'Outfit', sans-serif; }
        .glass { background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(15px); border-bottom: 1px solid rgba(255,255,255,0.1); }
        .m-card:hover { transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 10px; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; padding: 20px; }
    </style>
</head>
<body>
"""

# --- ১. হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    body = NAV_HTML + """
    <main class="container mx-auto py-10 px-4">
        {% if not items %}
        <div class="h-[60vh] flex flex-col items-center justify-center text-zinc-500">
            <i class="fa fa-database text-6xl mb-4 text-zinc-800"></i>
            <h2 class="text-2xl font-bold uppercase">ডাটাবেস খালি!</h2>
            <p class="mt-2">এডমিন প্যানেলে গিয়ে 'Bulk Sync' বাটনে ক্লিক করুন।</p>
        </div>
        {% else %}
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
            {% for m in items %}
            <a href="/details/{{ m.tmdb_id }}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 block group relative shadow-2xl">
                <div class="aspect-[2/3] overflow-hidden relative">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-play-circle text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-[9px] font-black px-2 py-1 rounded-full shadow-lg text-white">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase text-zinc-200">{{ m.title }}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1 uppercase tracking-widest">{{ m.year }} | {{ m.type }}</p>
                </div>
            </a>
            {% endfor %}
        </div>
        {% endif %}
    </main>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", items=items)

# --- ২. ডিটেইল পেজ (বিন্দু পরিমাণ মিসিং ছাড়া) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    body = NAV_HTML + """
    <div class="relative min-h-screen pb-20">
        <!-- Backdrop Banner (Fixed Thumbnail) -->
        <div class="h-[50vh] md:h-[75vh] relative overflow-hidden">
            <img src="{{ m.backdrop }}" class="w-full h-full object-cover opacity-20 blur-[2px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div>
        </div>

        <div class="container mx-auto px-4 -mt-80 relative z-10">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-96 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{ m.poster }}" class="w-full rounded-[3.5rem] border border-zinc-700 shadow-2xl">
                    {% if m.yt_id != "N/A" %}
                    <a href="https://www.youtube.com/watch?v={{ m.yt_id }}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-red-600 py-5 rounded-3xl font-black shadow-xl hover:scale-105 transition text-white">
                        <i class="fa fa-play text-xl"></i> WATCH TRAILER
                    </a>
                    {% endif %}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight tracking-tighter">{{ m.title }}</h1>
                    <div class="flex flex-wrap gap-2 mb-8 uppercase text-[10px] font-bold tracking-widest">
                        {% for cat in m.category %}<span class="bg-zinc-800 px-4 py-1.5 rounded-full border border-zinc-700">{{ cat }}</span>{% endfor %}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-white">{{ m.year }}</span>
                    </div>
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10 italic">"{{ m.story }}"</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 text-center uppercase font-black text-[10px]">
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Rating</p><p class="text-yellow-500 text-xl font-black">⭐ {{ m.rating }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Language</p><p class="text-lg text-white font-bold">{{ m.language | upper }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Director</p><p class="text-rose-500 truncate text-[11px]">{{ m.director.name }}</p>
                        </div>
                        <div class="bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                            <p class="text-zinc-500 mb-1">Release</p><p class="text-white text-[11px]">{{ m.release_date }}</p>
                        </div>
                    </div>

                    {% if m.ott %}
                    <div class="p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem] mb-10">
                        <p class="text-xs font-black uppercase text-rose-500 mb-6 tracking-widest italic">Streaming Platforms (OTT)</p>
                        <div class="flex flex-wrap gap-8">
                            {% for ott in m.ott %}
                            <div class="text-center"><img src="{{ ott.logo }}" class="w-14 h-14 rounded-2xl shadow-xl border border-zinc-800"><p class="text-[9px] mt-2 font-bold">{{ ott.name }}</p></div>
                            {% endfor %}
                        </div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Cast & Profiles (With Photo Click Detail) -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Cast, Director & Producers</h3>
                <div class="flex gap-10 overflow-x-auto pb-10 scroll-hide">
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ m.director.id }}')">
                        <img src="{{ m.director.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl group-hover:scale-105 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ m.director.name }}</p>
                        <p class="text-[9px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    {% for p in m.producers %}
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ p.id }}')">
                        <img src="{{ p.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:scale-105 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ p.name }}</p>
                        <p class="text-[9px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {% endfor %}
                    {% for a in m.cast %}
                    <div class="min-w-[150px] text-center cursor-pointer group" onclick="showPersonDetail('{{ a.id }}')">
                        <img src="{{ a.photo }}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800 group-hover:scale-105 transition">
                        <p class="mt-4 font-black text-sm text-white">{{ a.name }}</p>
                        <p class="text-[9px] text-zinc-400 font-bold uppercase truncate px-2">{{ a.role }}</p>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- Full Gallery (Wallpapers & Posters) -->
            <div class="mt-32">
                <h3 class="text-3xl font-black mb-12 border-l-4 border-rose-600 pl-4 uppercase italic">Media Gallery (Thumbnails)</h3>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {% for img in m.gallery %}
                    <div class="overflow-hidden rounded-3xl border border-zinc-800 shadow-xl"><img src="{{ img }}" class="w-full h-full object-cover hover:scale-110 transition duration-700"></div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </div>

    <!-- Person Detail Modal -->
    <div id="personModal" class="modal" onclick="this.style.display='none'">
        <div class="bg-zinc-900 border border-zinc-800 p-8 rounded-[3.5rem] max-w-3xl w-full max-h-[85vh] overflow-y-auto relative shadow-2xl" onclick="event.stopPropagation()">
            <div id="personContent" class="flex flex-col md:flex-row gap-8"></div>
        </div>
    </div>

    <script>
        async function showPersonDetail(id) {
            const m = document.getElementById('personModal');
            const c = document.getElementById('personContent');
            m.style.display = 'flex';
            c.innerHTML = '<div class="w-full text-center py-20 font-bold text-rose-600">Loading profile data...</div>';
            try {
                const r = await fetch('/api/person/' + id);
                const d = await r.json();
                c.innerHTML = `
                    <img src="${d.photo}" class="w-64 h-80 object-cover rounded-[2.5rem] border border-zinc-700 shadow-2xl mx-auto">
                    <div class="flex-1">
                        <h2 class="text-4xl font-black text-rose-600 mb-2">${d.name}</h2>
                        <p class="text-xs font-black text-zinc-500 uppercase tracking-[0.2em] mb-6">${d.job}</p>
                        <div class="space-y-4 text-sm text-zinc-300">
                            <p><strong>Born:</strong> ${d.birthday || 'Unknown'}</p>
                            <p><strong>From:</strong> ${d.place || 'Unknown'}</p>
                            <p class="leading-relaxed text-zinc-400 mt-6 pt-6 border-t border-zinc-800 italic">${d.bio || 'Biography not available for this person.'}</p>
                        </div>
                    </div>`;
            } catch(e) { c.innerHTML = 'Failed to load details.'; }
        }
    </script>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", m=m)

# --- ৩. এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    
    body = """
    <div class="h-[80vh] flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[4rem] border border-zinc-800 w-full max-w-sm shadow-2xl text-center">
            <h2 class="text-3xl font-black mb-10 text-rose-600 uppercase italic tracking-widest">Admin Hub</h2>
            <input type="password" name="pw" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-5 rounded-3xl mb-6 text-center outline-none focus:border-rose-600 transition text-white">
            <button class="w-full bg-rose-600 py-4 rounded-3xl font-black shadow-xl shadow-rose-900/20 text-white">LOGIN</button>
        </form>
    </div>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>")

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = NAV_HTML + """
    <div class="container mx-auto py-10 px-4 max-w-6xl pb-32">
        <div class="flex justify-between items-center mb-12 border-b border-zinc-800 pb-8">
            <h1 class="text-4xl font-black italic tracking-tighter">CONTROL HUB</h1>
            <a href="/logout" class="text-rose-500 font-bold hover:underline">LOGOUT</a>
        </div>

        <div class="grid md:grid-cols-2 gap-10 mb-16">
            <!-- Unlimited Auto Sync -->
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl text-center">
                <h3 class="text-xl font-bold mb-8 text-blue-500 uppercase tracking-widest italic">Unlimited Auto Sync</h3>
                <div class="flex flex-col gap-4 mb-6">
                    <input type="number" id="yr" placeholder="সাল (যেমন: 2024)" class="bg-black border border-zinc-700 p-4 rounded-3xl flex-1 outline-none text-white text-center">
                    <input type="number" id="pg" placeholder="কয়টি পেজ? (যেমন: 10)" class="bg-black border border-zinc-700 p-4 rounded-3xl w-full outline-none text-white text-center">
                    <select id="type" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center"><option value="movie">Movies</option><option value="tv">TV Shows</option></select>
                </div>
                <button onclick="startSync()" id="btn" class="w-full bg-blue-600 py-5 rounded-[2.5rem] font-black text-white text-xl">START UNLIMITED SYNC</button>
                <div id="stat" class="mt-8 p-6 bg-black/50 rounded-2xl border border-zinc-800 text-[10px] font-mono text-zinc-500 uppercase hidden"></div>
            </div>
            
            <div class="bg-zinc-900 p-10 rounded-[3.5rem] border border-zinc-800 shadow-2xl text-center">
                <h3 class="text-xl font-bold mb-8 text-rose-500 uppercase tracking-widest italic">Manual ID Sync</h3>
                <div class="flex flex-col gap-4 mb-6">
                    <input type="text" id="m_id" placeholder="TMDB Content ID" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center">
                    <select id="m_type" class="bg-black border border-zinc-700 p-4 rounded-3xl outline-none text-white text-center"><option value="movie">Movie</option><option value="tv">TV</option></select>
                </div>
                <button onclick="manualSync()" id="m_btn" class="w-full bg-rose-600 py-5 rounded-[2.5rem] font-black text-white">SYNC ID NOW</button>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-[3.5rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm uppercase font-black tracking-widest"><thead class="bg-zinc-800 text-zinc-500 font-black"><tr><th class="p-8">Content Name</th><th class="p-8 text-center">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800">
                {% for i in items %}
                <tr><td class="p-8 font-black text-lg text-white uppercase">{{ i.title }} <span class="text-zinc-600 ml-2 font-normal">({{ i.year }})</span></td>
                <td class="p-8 text-center flex justify-center gap-6"><a href="/edit/{{ i.tmdb_id }}" class="text-blue-500 text-xl hover:scale-125 transition inline-block"><i class="fa fa-edit"></i></a><a href="/del/{{ i.tmdb_id }}" onclick="return confirm('Delete?')" class="text-rose-500 text-xl hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td></tr>
                {% endfor %}
            </tbody></table>
        </div>
    </div>

    <script>
    async function startSync() {
        const yr = document.getElementById('yr').value;
        const pg = document.getElementById('pg').value || 1;
        const t = document.getElementById('type').value;
        const b = document.getElementById('btn');
        const s = document.getElementById('stat');
        if(!yr) return alert('Enter Year!');
        b.disabled = true; s.classList.remove('hidden');
        for(let p=1; p <= pg; p++) {
            s.innerHTML = 'Fetching IDs Page ' + p + '...';
            const res = await fetch(`/api/get_ids?year=${yr}&page=${p}&type=${t}`);
            const data = await res.json();
            for(let item of data.ids) {
                s.innerHTML = 'Auto Saving: ' + item.title;
                await fetch(`/api/sync_single?id=${item.id}&type=${t}`);
            }
        }
        s.innerHTML = 'ALL SYNCED! RELOADING...'; location.reload();
    }
    async function manualSync() {
        const id = document.getElementById('m_id').value;
        const t = document.getElementById('m_type').value;
        if(!id) return alert('Enter ID!');
        await fetch(`/api/sync_single?id=${id}&type=${t}`);
        location.reload();
    }
    </script>
    """
    return render_template_string(BASE_HEAD + body + "</body></html>", items=items)

# --- ৪. ইন্টারনাল স্ক্র্যাপিং ইঞ্জিন এপিআই ---

@app.route('/api/person/<id>')
def api_person(id):
    url = f"https://api.themoviedb.org/3/person/{id}?api_key={TMDB_API_KEY}"
    d = requests.get(url).json()
    return jsonify({
        "name": d.get('name'), "photo": IMG_BASE + d.get('profile_path') if d.get('profile_path') else "https://via.placeholder.com/200",
        "bio": d.get('biography'), "birthday": d.get('birthday'), "place": d.get('place_of_birth'), "job": d.get('known_for_department')
    })

@app.route('/api/get_ids')
def get_ids():
    y, p, t = request.args.get('year'), request.args.get('page', 1), request.args.get('type', 'movie')
    url = f"https://api.themoviedb.org/3/discover/{t}?api_key={TMDB_API_KEY}&primary_release_year={y}&first_air_date_year={y}&sort_by=popularity.desc&page={p}"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m.get('title') or m.get('name')} for m in res]})

@app.route('/api/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    # Cast & Crew Information
    crew = d.get('credits', {}).get('crew', [])
    director = next(({"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"id": 0, "name": "N/A", "photo": ""})
    producers = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"id": p['id'], "name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character']} for p in d.get('credits', {}).get('cast', [])[:20]]

    # OTT Information
    ott = [{"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']} for prov in d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])]
    
    # Trailer & Gallery
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
def edit(tid):
    if not session.get('logged'): return redirect('/admin')
    m = collection.find_one({"tmdb_id": tid})
    if request.method == 'POST':
        collection.update_one({"tmdb_id": tid}, {"$set": {"title": request.form.get('t'), "story": request.form.get('s')}})
        return redirect('/admin/dashboard')
    body = f"""<div class="h-[80vh] flex items-center justify-center px-4"><form method="POST" class="bg-zinc-900 p-10 rounded-[3rem] w-full max-w-xl shadow-2xl text-white"><h2 class="text-2xl font-black mb-6 italic">Edit: {m['title']}</h2><input name="t" value="{m['title']}" class="w-full bg-black p-4 rounded-2xl mb-4 text-white outline-none"><textarea name="s" class="w-full bg-black p-4 rounded-2xl mb-4 h-40 text-white outline-none">{m['story']}</textarea><button class="w-full bg-blue-600 py-4 rounded-2xl font-black">UPDATE CONTENT</button></form></div>"""
    return render_template_string(BASE_HEAD + body + "</body></html>")

@app.route('/del/<tid>')
def delete(tid):
    if session.get('logged'): collection.delete_one({"tmdb_id": tid})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
