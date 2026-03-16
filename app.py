import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient
from urllib.parse import quote_plus

app = Flask(__name__)
app.secret_key = "super_secret_movie_key_99"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"
ADMIN_PASSWORD = "admin123"

# ডাটাবেস কানেকশন (dnspython সহ)
try:
    client = MongoClient(MONGO_URI)
    db = client['movie_portal_db']
    collection = db['media_items']
except Exception as e:
    print(f"Database Connection Error: {e}")

# --- ফ্রন্টেন্ড ডিজাইন (CSS & HTML) ---
UI_LAYOUT = '''
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Movie Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #0a0a0a; color: #fff; font-family: 'Inter', sans-serif; }
        .movie-card:hover { transform: translateY(-10px); transition: 0.4s; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <nav class="bg-zinc-900/80 backdrop-blur-md sticky top-0 z-50 p-4 border-b border-zinc-800">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-black text-rose-600 tracking-tighter italic">MOVIE AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-zinc-800 rounded-full px-4 py-1 w-1/3 border border-zinc-700">
                <input type="text" name="q" placeholder="মুভি বা টিভি শো খুঁজুন..." class="bg-transparent outline-none w-full text-sm py-1">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="text-sm font-bold border border-rose-600 px-4 py-1.5 rounded-full hover:bg-rose-600 transition">এডমিন</a>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <div id="videoModal" class="modal" onclick="closePlayer()">
        <div class="w-full max-w-4xl p-4">
            <div class="aspect-video bg-black rounded-xl overflow-hidden shadow-2xl">
                <iframe id="ytPlayer" class="w-full h-full" src="" frameborder="0" allowfullscreen></iframe>
            </div>
        </div>
    </div>

    <script>
        function playTrailer(id) {
            if(!id || id === 'N/A') return alert('ট্রেলার পাওয়া যায়নি!');
            document.getElementById('ytPlayer').src = `https://www.youtube.com/embed/${id}?autoplay=1`;
            document.getElementById('videoModal').style.display = 'flex';
        }
        function closePlayer() {
            document.getElementById('videoModal').style.display = 'none';
            document.getElementById('ytPlayer').src = '';
        }
    </script>
</body>
</html>
'''

# --- সাহায্যকারী ফাংশন (মুভি ডাটা সিঙ্ক) ---
def sync_tmdb_data(tmdb_id, m_type):
    try:
        url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
        resp = requests.get(url, timeout=10)
        d = resp.json()
        
        if 'id' not in d: return False

        # কাস্ট সংগ্রহ
        cast = []
        for p in d.get('credits', {}).get('cast', [])[:15]:
            if p.get('profile_path'):
                cast.append({"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']})
        
        # ট্রেলার
        yt_id = "N/A"
        for v in d.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                yt_id = v['key']; break

        # ডিরেক্টর, নায়ক, নায়িকা
        director = next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "অজানা")
        hero = next((a['name'] for a in cast if a['gender'] == 2), "N/A")
        heroine = next((a['name'] for a in cast if a['gender'] == 1), "N/A")

        # ডাটা অবজেক্ট
        movie_data = {
            "tmdb_id": str(tmdb_id),
            "type": m_type,
            "title": d.get('title') or d.get('name'),
            "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
            "rating": round(d.get('vote_average', 0), 1),
            "summary": d.get('overview'),
            "director": director, "hero": hero, "heroine": heroine,
            "poster": IMG_ORIGINAL + d.get('poster_path') if d.get('poster_path') else None,
            "backdrops": [IMG_ORIGINAL + i['file_path'] for i in d.get('images', {}).get('backdrops', [])[:5]],
            "yt_id": yt_id, "cast": cast
        }
        collection.update_one({"tmdb_id": str(tmdb_id)}, {"$set": movie_data}, upsert=True)
        return True
    except Exception as e:
        print(f"Sync Error: {e}")
        return False

# --- রাউটস ---
@app.route('/')
def home():
    q = request.args.get('q')
    if q:
        items = list(collection.find({"title": {"$regex": q, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    return render_template_string(UI_LAYOUT + '''
    {% block content %}
    <div class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-6">
            {% for m in items %}
            <div class="movie-card bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800 shadow-xl group cursor-pointer" onclick="playTrailer('{{ m.yt_id }}')">
                <div class="relative aspect-[2/3]">
                    <img src="{{ m.poster }}" class="w-full h-full object-cover">
                    <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 flex items-center justify-center transition">
                        <i class="fa fa-play-circle text-5xl text-rose-600"></i>
                    </div>
                    <div class="absolute top-2 right-2 bg-yellow-500 text-black text-[10px] font-black px-2 py-1 rounded">⭐ {{ m.rating }}</div>
                </div>
                <div class="p-3">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500">{{ m.year }} | {{ m.type | upper }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endblock %}
    ''', items=items)

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('pw') == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect('/admin/panel')
    if session.get('admin'): return redirect('/admin/panel')
    return render_template_string(UI_LAYOUT + '<div class="h-[80vh] flex items-center justify-center"><form method="POST" class="bg-zinc-900 p-8 rounded-2xl border border-zinc-800 w-full max-w-xs text-center"><h2 class="text-xl font-bold mb-4">এডমিন লগইন</h2><input type="password" name="pw" class="w-full bg-black border border-zinc-700 p-3 rounded-xl mb-4 text-center outline-none focus:border-rose-600"><button class="w-full bg-rose-600 py-3 rounded-xl font-bold">Login</button></form></div>')

@app.route('/admin/panel')
def admin_panel():
    if not session.get('admin'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    return render_template_string(UI_LAYOUT + '''
    {% block content %}
    <div class="container mx-auto py-10 px-4 max-w-4xl">
        <div class="flex justify-between items-center mb-8">
            <h1 class="text-2xl font-bold">Admin Panel</h1>
            <a href="/logout" class="text-rose-600">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-6 mb-10">
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
                <h3 class="font-bold mb-3">ID দিয়ে সিঙ্ক করুন</h3>
                <form action="/sync_id" method="POST" class="flex gap-2">
                    <input type="text" name="tmdb_id" placeholder="ID" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-2 rounded text-xs"><option value="movie">Movie</option><option value="tv">TV</option></select>
                    <button class="bg-rose-600 px-4 py-2 rounded text-sm font-bold">Sync</button>
                </form>
            </div>
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
                <h3 class="font-bold mb-3">সাল দিয়ে বাল্ক সিঙ্ক (Yearly)</h3>
                <form action="/sync_year" method="POST" class="flex gap-2">
                    <input type="number" name="year" placeholder="2024" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <button class="bg-blue-600 px-4 py-2 rounded text-sm font-bold">Bulk Sync</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800"><tr><th class="p-4">মুভির নাম</th><th class="p-4">একশন</th></tr></thead>
                <tbody>
                    {% for i in items %}
                    <tr class="border-b border-zinc-800"><td class="p-4">{{ i.title }} ({{ i.year }})</td><td class="p-4"><a href="/del/{{ i.tmdb_id }}" class="text-rose-500">মুছে ফেলুন</a></td></tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endblock %}
    ''', items=items)

@app.route('/sync_id', methods=['POST'])
def sync_id():
    if session.get('admin'):
        sync_tmdb_data(request.form.get('tmdb_id'), request.form.get('type'))
    return redirect('/admin/panel')

@app.route('/sync_year', methods=['POST'])
def sync_year():
    if session.get('admin'):
        year = request.form.get('year')
        # টাইমআউট এড়াতে এক ক্লিকে মাত্র ২০টি মুভি সিঙ্ক করবে (Page 1)
        m_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page=1&sort_by=popularity.desc"
        for m in requests.get(m_url).json().get('results', []):
            sync_tmdb_data(m['id'], 'movie')
    return redirect('/admin/panel')

@app.route('/del/<id>')
def delete_item(id):
    if session.get('admin'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin/panel')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
