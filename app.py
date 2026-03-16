import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "absolute_final_fix_v6"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIG = "https://image.tmdb.org/t/p/original"
ADMIN_PW = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_fixed']
collection = db['media_content']

# --- CSS & JS Assets ---
NAVBAR = '''
<nav class="bg-zinc-900/90 border-b border-zinc-800 p-4 sticky top-0 z-50 backdrop-blur-md">
    <div class="container mx-auto flex justify-between items-center">
        <a href="/" class="text-3xl font-black text-red-600 italic tracking-tighter">MOVIE AI</a>
        <form action="/" method="GET" class="hidden md:flex bg-black border border-zinc-700 rounded-full px-5 py-1.5 w-1/3">
            <input type="text" name="q" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
            <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
        </form>
        <a href="/admin" class="bg-red-600 px-5 py-2 rounded-full font-bold text-xs hover:bg-red-700 transition">ADMIN</a>
    </div>
</nav>
'''

# --- ১. হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Movie AI - Explore</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>body {{ background:#050505; color:white; font-family:sans-serif; }} .m-card:hover {{ border-color:#ef4444; transform:scale(1.03); transition:0.3s; }}</style>
    </head>
    <body>
        {NAVBAR}
        <main class="container mx-auto py-12 px-4">
            <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8">
                {{% for m in items %}}
                <a href="/details/{{{{ m.tmdb_id }}}}" class="m-card bg-zinc-900 rounded-[2rem] overflow-hidden border border-zinc-800 block shadow-2xl">
                    <img src="{{{{ m.poster }}}}" class="w-full aspect-[2/3] object-cover">
                    <div class="p-4">
                        <h3 class="font-bold text-sm truncate">{{{{ m.title }}}}</h3>
                        <p class="text-[10px] text-zinc-500 mt-1 uppercase tracking-widest font-bold">{{{{ m.year }}}} | {{{{ m.type }}}}</p>
                    </div>
                </a>
                {{% endfor %}}
            </div>
        </main>
    </body>
    </html>
    '''
    return render_template_string(html, items=items)

# --- ২. ডিটেইল পেজ ---
@app.route('/details/<tmdb_id>')
def details(tmdb_id):
    m = collection.find_one({"tmdb_id": tmdb_id})
    if not m: return redirect('/')
    
    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>{{{{ m.title }}}}</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
        <style>body {{ background:#050505; color:white; font-family:sans-serif; }}</style>
    </head>
    <body>
        {NAVBAR}
        <div class="relative min-h-screen">
            <div class="h-[60vh] relative"><img src="{{{{ m.all_thumbnails[0] if m.all_thumbnails else m.poster }}}}" class="w-full h-full object-cover opacity-20"><div class="absolute inset-0 bg-gradient-to-t from-[#050505]"></div></div>
            <div class="container mx-auto px-4 -mt-64 relative z-10">
                <div class="flex flex-col lg:flex-row gap-10">
                    <div class="w-72 flex-shrink-0 mx-auto lg:mx-0">
                        <img src="{{{{ m.poster }}}}" class="w-full rounded-[2.5rem] shadow-2xl border border-zinc-800">
                        {{% if m.yt_id != "N/A" %}}<a href="https://www.youtube.com/watch?v={{{{ m.yt_id }}}}" target="_blank" class="mt-6 flex items-center justify-center bg-red-600 py-3 rounded-xl font-bold">Watch Trailer</a>{{% endif %}}
                    </div>
                    <div class="flex-1">
                        <h1 class="text-5xl font-black mb-4">{{{{ m.title }}}} ({{{{ m.year }}}})</h1>
                        <div class="flex gap-4 mb-6 text-sm text-zinc-400"><span>⭐ {{{{ m.rating }}}}</span><span>{{{{ m.language | upper }}}}</span><span>{{{{ m.release_date }}}}</span></div>
                        <p class="text-lg text-zinc-300 mb-8 leading-relaxed">{{{{ m.summary }}}}</p>
                        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 bg-zinc-900 p-6 rounded-3xl border border-zinc-800">
                            <div><p class="text-xs text-zinc-500 uppercase font-bold mb-1">Director</p><p class="text-red-500 font-bold">{{{{ m.director }}}}</p></div>
                            <div><p class="text-xs text-zinc-500 uppercase font-bold mb-1">Lead Hero</p><p class="font-bold">{{{{ m.hero }}}}</p></div>
                            <div><p class="text-xs text-zinc-500 uppercase font-bold mb-1">Lead Heroine</p><p class="font-bold">{{{{ m.heroine }}}}</p></div>
                        </div>
                    </div>
                </div>
                <!-- Cast -->
                <div class="mt-20"><h3 class="text-2xl font-bold mb-8">Cast Details</h3><div class="flex gap-6 overflow-x-auto pb-4">
                    {{% for actor in m.cast_details %}}<div class="min-w-[100px] text-center"><img src="{{{{ actor.photo }}}}" class="w-20 h-20 rounded-full mx-auto object-cover border-2 border-zinc-800 mb-2"><p class="text-[10px] font-bold truncate">{{{{ actor.name }}}}</p></div>{{% endfor %}}
                </div></div>
                <!-- Episodes (if TV) -->
                {{% if m.episodes %}}<div class="mt-20"><h3 class="text-2xl font-bold mb-8">Episodes List</h3><div class="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {{% for ep in m.episodes %}}<div class="bg-zinc-900 p-4 rounded-2xl border border-zinc-800 flex items-center gap-4"><img src="{{{{ ep.img }}}}" class="w-20 h-14 object-cover rounded-lg"><div><p class="text-xs font-bold">{{{{ ep.name }}}}</p></div></div>{{% endfor %}}
                </div></div>{{% endif %}}
                <!-- Gallery -->
                <div class="mt-20 pb-20"><h3 class="text-2xl font-bold mb-8">Image Gallery</h3><div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {{% for img in m.all_posters[:12] %}}<img src="{{{{ img }}}}" class="rounded-xl border border-zinc-800">{{% endfor %}}
                </div></div>
            </div>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html, m=m)

# --- ৩. এডমিন কন্ট্রোল ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST' and request.form.get('pw') == ADMIN_PW:
        session['logged'] = True
        return redirect('/admin/panel')
    if session.get('logged'): return redirect('/admin/panel')
    return render_template_string(f'''
    <html><head><script src="https://cdn.tailwindcss.com"></script></head><body class="bg-black text-white h-screen flex items-center justify-center">
        <form method="POST" class="bg-zinc-900 p-10 rounded-3xl border border-zinc-800 w-full max-w-sm"><h2 class="text-2xl font-bold mb-6 text-center">Admin Login</h2><input type="password" name="pw" class="w-full bg-black border border-zinc-700 p-3 rounded-xl mb-4 text-center outline-none"><button class="w-full bg-red-600 py-3 rounded-xl font-bold">LOGIN</button></form>
    </body></html>
    ''')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    return render_template_string(f'''
    <html><head><script src="https://cdn.tailwindcss.com"></script><link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css"></head><body class="bg-black text-white">
        {NAVBAR}
        <div class="container mx-auto py-10 px-4 max-w-5xl">
            <div class="grid md:grid-cols-2 gap-8 mb-12">
                <div class="bg-zinc-900 p-8 rounded-3xl border border-zinc-800">
                    <h3 class="font-bold mb-4 text-blue-500 uppercase tracking-widest">Bulk Sync (Year & Pages)</h3>
                    <input type="number" id="yr" placeholder="Year" class="w-full bg-black border border-zinc-700 p-3 rounded-xl mb-4 outline-none">
                    <input type="number" id="pgs" placeholder="Total Pages (1-10)" class="w-full bg-black border border-zinc-700 p-3 rounded-xl mb-4 outline-none">
                    <button onclick="startBulk()" id="btn" class="w-full bg-blue-600 py-3 rounded-xl font-bold">START BULK SYNC</button>
                    <div id="stat" class="mt-4 text-xs text-zinc-500"></div>
                </div>
                <div class="bg-zinc-900 p-8 rounded-3xl border border-zinc-800">
                    <h3 class="font-bold mb-4 text-red-500 uppercase tracking-widest">Single Sync (ID)</h3>
                    <form action="/sync_id" method="POST" class="space-y-4">
                        <input type="text" name="tid" placeholder="TMDB ID" class="w-full bg-black border border-zinc-700 p-3 rounded-xl outline-none">
                        <select name="type" class="w-full bg-black border border-zinc-700 p-3 rounded-xl"><option value="movie">Movie</option><option value="tv">TV</option></select>
                        <button class="w-full bg-red-600 py-3 rounded-xl font-bold">SYNC ID</button>
                    </form>
                </div>
            </div>
            <table class="w-full bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800"><thead class="bg-zinc-800"><tr><th class="p-6 text-left">Title</th><th class="p-6">Action</th></tr></thead><tbody>
                {{% for i in items %}}<tr class="border-b border-zinc-800"><td class="p-6 font-bold">{{{{ i.title }}}} ({{{{ i.year }}}})</td><td class="p-6 text-center text-red-500"><a href="/del/{{{{ i.tmdb_id }}}}"><i class="fa fa-trash"></i></a></td></tr>{{% endfor %}}
            </tbody></table>
        </div>
        <script>
        async function startBulk() {{
            const yr = document.getElementById('yr').value;
            const pgs = document.getElementById('pgs').value || 1;
            const btn = document.getElementById('btn');
            const stat = document.getElementById('stat');
            if(!yr) return alert('Enter Year');
            btn.disabled = true; stat.innerText = 'Initializing...';
            for(let p=1; p<=pgs; p++) {{
                stat.innerText = `Fetching Page ${{p}} of ${{pgs}}...`;
                const r = await fetch(`/get_ids?year=${{yr}}&page=${{p}}`);
                const d = await r.json();
                for(let item of d.ids) {{
                    stat.innerText = `Syncing Page ${{p}}: ${{item.title}}`;
                    await fetch(`/sync_single?id=${{item.id}}&type=movie`);
                }}
            }}
            stat.innerText = 'Sync Done!'; location.reload();
        }}
        </script>
    </body></html>
    ''', items=items)

# --- ৪. ইন্টারনাল লজিক (API Engines) ---

@app.route('/get_ids')
def get_ids():
    yr, pg = request.args.get('year'), request.args.get('page', 1)
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={yr}&page={pg}&sort_by=popularity.desc"
    res = requests.get(url).json().get('results', [])
    return jsonify({"ids": [{"id": m['id'], "title": m['title']} for m in res]})

@app.route('/sync_single')
def sync_single():
    tid, mtype = request.args.get('id'), request.args.get('type')
    url = f"https://api.themoviedb.org/3/{mtype}/{tid}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    d = requests.get(url).json()

    cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', []) if p.get('profile_path')][:20]
    director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")
    hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
    heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")
    ytid = next((v['key'] for v in d.get('videos', {}).get('results', []) if v['type'] == 'Trailer'), "N/A")
    
    eps = []
    if mtype == 'tv':
        try:
            s_data = requests.get(f"https://api.themoviedb.org/3/tv/{tid}/season/1?api_key={TMDB_API_KEY}").json()
            for ep in s_data.get('episodes', []):
                eps.append({"name": ep.get('name'), "num": ep.get('episode_number'), "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None})
        except: pass

    data = {
        "tmdb_id": str(tid), "type": mtype, "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
        "language": d.get('original_language'), "release_date": d.get('release_date') or d.get('first_air_date'),
        "director": director, "hero": hero, "heroine": heroine, "yt_id": ytid,
        "poster": IMG_ORIG + d.get('poster_path'), "all_posters": [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('posters', [])[:15]],
        "all_thumbnails": [IMG_ORIG + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:10]],
        "cast_details": cast, "episodes": eps
    }
    collection.update_one({"tmdb_id": str(tid)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('logged'):
        requests.get(f"{request.url_root}sync_single?id={request.form.get('tid')}&type={request.form.get('type')}")
    return redirect('/admin/panel')

@app.route('/del/<id>')
def delete(id):
    if session.get('logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/panel')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
