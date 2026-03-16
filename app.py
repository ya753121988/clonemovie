import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_mega_cinema_v26_final"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_v26']
collection = db['media_hub']

# --- কমন নেভিগেশন বার (মোবাইল ও ডেক্সটপ রেসপনসিভ) ---
NAV_HTML = '''
<nav class="bg-zinc-900/90 border-b border-zinc-800 p-4 sticky top-0 z-50 backdrop-blur-md">
    <div class="container mx-auto flex justify-between items-center gap-4">
        <a href="/" class="text-2xl md:text-3xl font-black text-rose-600 italic tracking-tighter">MOVIE-AI</a>
        <form action="/" method="GET" class="flex flex-1 max-w-lg bg-zinc-900 border border-zinc-800 rounded-full px-5 py-2">
            <input type="text" name="q" placeholder="মুভি, টিভি বা এক্টর..." class="bg-transparent outline-none w-full text-xs md:text-sm text-white">
            <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
        </form>
        <a href="/admin" class="bg-zinc-800 hover:bg-rose-600 px-4 py-2 rounded-full font-bold text-[10px] md:text-xs transition text-white">ADMIN</a>
    </div>
</nav>
'''

HEADER_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MOVIE AI - Pro Entertainment Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #050505; color: white; font-family: sans-serif; }
        .m-card:hover { transform: scale(1.05); border-color: #e11d48; transition: 0.4s; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 10px; }
    </style>
</head>
<body>
'''

# --- হোম পেজ রাউট ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1)) if q else list(collection.find().sort('_id', -1))
    
    body = f'''
    {NAV_HTML}
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-6">
            {{% for m in items %}}
            <a href="/details/{{{{ m.tmdb_id }}}}" class="m-card bg-zinc-900 rounded-[2.5rem] overflow-hidden border border-zinc-800 block group relative">
                <div class="relative aspect-[2/3]">
                    <img src="{{{{ m.poster }}}}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa-solid fa-play-circle text-5xl"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-rose-600 text-[10px] font-black px-2 py-1 rounded-full">⭐ {{{{ m.rating }}}}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold text-xs truncate uppercase tracking-tighter">{{{{ m.title }}}}</h3>
                    <p class="text-[9px] text-zinc-500 font-bold mt-1">{{{{ m.year }}}} | {{{{ m.type | upper }}}}</p>
                </div>
            </a>
            {{% endfor %}}
        </div>
    </main>
    '''
    return render_template_string(HEADER_HTML + body + "</body></html>", items=items)

# --- ডিটেইল পেজ রাউট (সব তথ্য এখানে) ---
@app.route('/details/<tid>')
def details(tid):
    m = collection.find_one({"tmdb_id": tid})
    if not m: return redirect('/')
    
    body = f'''
    {NAV_HTML}
    <div class="relative">
        <div class="h-[50vh] md:h-[70vh] relative overflow-hidden">
            <img src="{{{{ m.backdrop }}}}" class="w-full h-full object-cover opacity-20 scale-105 blur-[1px]">
            <div class="absolute inset-0 bg-gradient-to-t from-[#050505] via-transparent"></div>
        </div>

        <div class="container mx-auto px-4 -mt-64 relative z-10 pb-20">
            <div class="flex flex-col lg:flex-row gap-12">
                <div class="w-64 md:w-80 flex-shrink-0 mx-auto lg:mx-0">
                    <img src="{{{{ m.poster }}}}" class="w-full rounded-[3.5rem] border border-zinc-800 shadow-2xl">
                    {{% if m.yt_id != "N/A" %}}
                    <a href="https://www.youtube.com/watch?v={{{{ m.yt_id }}}}" target="_blank" class="mt-8 flex items-center justify-center gap-3 bg-rose-600 py-5 rounded-3xl font-black shadow-xl">
                        <i class="fa fa-play text-xl"></i> WATCH TRAILER
                    </a>
                    {{% endif %}}
                </div>

                <div class="flex-1">
                    <h1 class="text-4xl md:text-7xl font-black mb-6 leading-tight">{{{{ m.title }}}}</h1>
                    <div class="flex flex-wrap gap-2 mb-8">
                        {{% for cat in m.category %}}
                        <span class="bg-zinc-800 border border-zinc-700 px-4 py-1.5 rounded-full text-[10px] font-bold">{{{{ cat }}}}</span>
                        {{% endfor %}}
                        <span class="bg-rose-600 px-4 py-1.5 rounded-full text-[10px] font-bold">{{{{ m.year }}}}</span>
                    </div>
                    
                    <p class="text-xl text-zinc-300 leading-relaxed mb-10">{{{{ m.story }}}}</p>

                    <div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-10 bg-zinc-900/50 p-6 rounded-[2.5rem] border border-zinc-800">
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">TMDB Rating</p><p class="text-xl font-black text-yellow-500">⭐ {{{{ m.rating }}}}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Language</p><p class="text-xl font-black">{{{{ m.language | upper }}}}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Released</p><p class="text-sm font-black">{{{{ m.release_date }}}}</p></div>
                        <div><p class="text-[10px] text-zinc-500 font-bold mb-1 uppercase tracking-widest">Category</p><p class="text-sm font-black">{{{{ m.type | upper }}}}</p></div>
                    </div>

                    {{% if m.ott %}}
                    <div class="mb-10 p-6 bg-zinc-900/30 border border-zinc-800 rounded-[2.5rem]">
                        <p class="text-xs font-black uppercase text-rose-500 mb-5 tracking-widest">Streaming On (OTT Info)</p>
                        <div class="flex flex-wrap gap-6">
                            {{% for ott in m.ott %}}
                            <div class="flex flex-col items-center">
                                <img src="{{{{ ott.logo }}}}" class="w-14 h-14 rounded-2xl shadow-xl">
                                <span class="text-[10px] mt-2 font-bold text-zinc-400">{{{{ ott.name }}}}</span>
                            </div>
                            {{% endfor %}}
                        </div>
                    </div>
                    {{% endif %}}
                </div>
            </div>

            <!-- Cast & Crew -->
            <div class="mt-20">
                <h2 class="text-3xl font-black uppercase tracking-widest italic mb-10 border-l-4 border-rose-600 pl-4">এক্টর, ডিরেক্টর ও প্রডিউসার</h2>
                <div class="flex gap-10 overflow-x-auto pb-10">
                    <div class="min-w-[140px] text-center">
                        <img src="{{{{ m.director.photo }}}}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-rose-600 shadow-2xl">
                        <p class="mt-4 font-black text-sm">{{{{ m.director.name }}}}</p>
                        <p class="text-[10px] text-rose-500 font-black uppercase">Director</p>
                    </div>
                    {{% for p in m.producers %}}
                    <div class="min-w-[140px] text-center">
                        <img src="{{{{ p.photo }}}}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm">{{{{ p.name }}}}</p>
                        <p class="text-[10px] text-zinc-500 font-black uppercase">Producer</p>
                    </div>
                    {{% endfor %}}
                    {{% for a in m.cast %}}
                    <div class="min-w-[140px] text-center">
                        <img src="{{{{ a.photo }}}}" class="w-32 h-32 rounded-full mx-auto object-cover border-4 border-zinc-800">
                        <p class="mt-4 font-black text-sm">{{{{ a.name }}}}</p>
                        <p class="text-[10px] text-zinc-400 font-bold truncate">{{{{ a.role }}}}</p>
                    </div>
                    {{% endfor %}}
                </div>
            </div>

            <!-- Gallery -->
            <div class="mt-20">
                <h2 class="text-3xl font-black uppercase tracking-widest italic mb-10 border-l-4 border-rose-600 pl-4">পোস্টার ও থাম্বনেইল গ্যালারি</h2>
                <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-6">
                    {{% for img in m.gallery %}}
                    <img src="{{{{ img }}}}" class="w-full rounded-3xl border border-zinc-800 shadow-xl hover:scale-110 transition duration-500">
                    {{% endfor %}}
                </div>
            </div>
        </div>
    </div>
    '''
    return render_template_string(HEADER_HTML + body + "</body></html>", m=m)

# --- এডমিন কন্ট্রোল রাউটস ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/dashboard')
    if session.get('logged'): return redirect('/admin/dashboard')
    
    body = f'''
    <div class="h-screen flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-12 rounded-[3.5rem] border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-3xl font-black mb-10 text-center text-rose-600 tracking-tighter uppercase">Admin</h2>
            <input type="password" name="pw" placeholder="Password" class="w-full bg-black border border-zinc-700 p-5 rounded-2xl mb-6 text-center outline-none">
            <button class="w-full bg-rose-600 py-4 rounded-2xl font-black shadow-xl">LOG IN</button>
        </form>
    </div>
    '''
    return render_template_string(HEADER_HTML + body + "</body></html>")

@app.route('/admin/dashboard')
def dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    body = f'''
    {NAV_HTML}
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="grid md:grid-cols-2 gap-10 mb-16">
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-blue-500 uppercase tracking-widest italic">Bulk Year Sync</h3>
                <div class="flex gap-4 mb-4">
                    <input type="number" id="yr" placeholder="2024" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none text-white">
                    <button onclick="startBulk()" id="btn" class="bg-blue-600 px-8 py-4 rounded-2xl font-black">START</button>
                </div>
                <div id="stat" class="mt-4 text-[10px] text-zinc-500 font-mono"></div>
            </div>
            <div class="bg-zinc-900 p-10 rounded-[3rem] border border-zinc-800 shadow-2xl">
                <h3 class="font-bold mb-8 text-rose-600 uppercase tracking-widest italic">Manual ID Sync</h3>
                <form action="/sync_id" method="POST" class="flex flex-col gap-4">
                    <div class="flex gap-3">
                        <input type="text" name="tid" placeholder="TMDB ID" class="bg-black border border-zinc-700 p-4 rounded-2xl flex-1 outline-none text-white">
                        <select name="type" class="bg-black border border-zinc-700 p-4 rounded-2xl text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    </div>
                    <button class="bg-rose-600 py-4 rounded-2xl font-black">SYNC NOW</button>
                </form>
            </div>
        </div>
        <div class="bg-zinc-900 rounded-[3rem] border border-zinc-800 overflow-hidden shadow-2xl">
            <table class="w-full text-left text-sm"><thead class="bg-zinc-800 text-zinc-500 uppercase text-[10px] tracking-widest font-black"><tr><th class="p-8">Content</th><th class="p-8 text-center">Action</th></tr></thead>
            <tbody class="divide-y divide-zinc-800">
                {{% for i in items %}}
                <tr><td class="p-8 font-black text-lg text-white font-bold">{{{{ i.title }}}} ({{{{ i.year }}}})</td>
                <td class="p-8 text-center"><a href="/del/{{{{ i.tmdb_id }}}}" class="text-rose-600 text-xl hover:scale-125 transition inline-block"><i class="fa fa-trash-alt"></i></a></td></tr>
                {{% endfor %}}
            </tbody></table>
        </div>
    </div>
    <script>
    async function startBulk() {{
        const year = document.getElementById('yr').value;
        const btn = document.getElementById('btn');
        const stat = document.getElementById('stat');
        if(!year) return alert('Enter Year');
        btn.disabled = true;
        const r = await fetch(`/get_year_ids?year=${{year}}`);
        const d = await r.json();
        for(let i=0; i<d.ids.length; i++) {{
            stat.innerText = `Syncing (${{i+1}}/${{d.ids.length}}): ${{d.ids[i].title}}`;
            await fetch(`/sync_single?id=${{d.ids[i].id}}&type=movie`);
        }}
        stat.innerText = 'SYNC COMPLETED!'; location.reload();
    }}
    </script>
    '''
    return render_template_string(HEADER_HTML + body + "</body></html>", items=items)

# --- স্ক্র্যাপিং ইঞ্জিন রাউটস ---

@app.route('/get_year_ids')
def get_year_ids():
    yr = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={yr}&sort_by=popularity.desc&page=1"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m['title']} for m in res[:20]]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images,watch/providers"
    d = requests.get(url).json()

    crew = d.get('credits', {}).get('crew', [])
    director = next(({"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] == 'Director'), {"name": "N/A", "photo": ""})
    producers = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150"} for p in crew if p['job'] in ['Producer', 'Executive Producer']][:4]
    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'] if p['profile_path'] else "https://via.placeholder.com/150", "role": p['character'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', [])[:20]]

    ott = []
    providers = d.get('watch/providers', {}).get('results', {}).get('US', {}).get('flatrate', [])
    for prov in providers: ott.append({"name": prov['provider_name'], "logo": IMG_BASE + prov['logo_path']})

    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    gallery = [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:15]]

    data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "story": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "category": [g['name'] for g in d.get('genres', [])], "director": director, "producers": producers, "cast": cast,
        "ott": ott, "yt_id": ytid, "poster": IMG_ORIG + d.get('poster_path'),
        "backdrop": IMG_ORIG + (d.get('backdrop_path') if d.get('backdrop_path') else d.get('poster_path')), "gallery": gallery
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_single?id={request.form.get('tid')}&type={request.form.get('type')}")
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
