import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "ultimate_cinema_secret"

# --- আপনার তথ্য ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"
ADMIN_PASSWORD = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_final']
collection = db['all_content']

# --- লেআউট এবং ডিজাইন ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Cinema - Home</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #050505; color: white; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.9); z-index: 1000; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <nav class="bg-zinc-900/90 border-b border-zinc-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-rose-600">AI-CINEMA</a>
            <form action="/" method="GET" class="hidden md:flex bg-black border border-zinc-800 rounded-full px-4 py-1 w-1/3">
                <input type="text" name="search" placeholder="Search..." class="bg-transparent outline-none w-full text-sm py-1">
                <button type="submit"><i class="fa fa-search text-zinc-600"></i></button>
            </form>
            <a href="/admin" class="bg-rose-600 px-4 py-1.5 rounded-full font-bold text-sm">Admin Panel</a>
        </div>
    </nav>
    {% block content %}{% endblock %}

    <div id="vModal" class="modal" onclick="this.style.display='none'; document.getElementById('yt-player').src=''">
        <div class="w-full max-w-4xl p-4 aspect-video">
            <iframe id="yt-player" class="w-full h-full rounded-2xl shadow-2xl" src="" frameborder="0" allowfullscreen></iframe>
        </div>
    </div>

    <script>
        function playVid(id) {
            if(!id || id === 'N/A') return alert('No Trailer Found');
            document.getElementById('yt-player').src = `https://www.youtube.com/embed/${id}?autoplay=1`;
            document.getElementById('vModal').style.display = 'flex';
        }
    </script>
</body>
</html>
'''

# --- হোম পেজ ---
@app.route('/')
def index():
    q = request.args.get('search')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}) if q else collection.find().sort('_id', -1))
    
    return render_template_string(LAYOUT + '''
    {% block content %}
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {% for m in items %}
            <div class="bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800 group relative">
                <img src="{{ m.main_poster }}" class="w-full aspect-[2/3] object-cover group-hover:scale-105 transition duration-500">
                <div class="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition flex flex-col justify-center items-center p-4 text-center">
                    <button onclick="playVid('{{ m.yt_id }}')" class="bg-rose-600 h-12 w-12 rounded-full mb-3 shadow-xl"><i class="fa fa-play"></i></button>
                    <h3 class="font-bold text-sm">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-400 mt-2">{{ m.summary[:80] }}...</p>
                </div>
                <div class="absolute top-2 right-2 bg-yellow-500 text-black font-black text-[10px] px-2 py-1 rounded">⭐ {{ m.rating }}</div>
            </div>
            {% endfor %}
        </div>
    </main>
    {% endblock %}
    ''', items=items)

# --- এডমিন ড্যাশবোর্ড (Bulk Sync Year এখানে আছে) ---
@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    
    return render_template_string(LAYOUT + '''
    {% block content %}
    <div class="container mx-auto py-10 px-4 max-w-5xl">
        <div class="flex justify-between items-center mb-10">
            <h2 class="text-2xl font-bold">Admin Dashboard (Total: {{ items|length }})</h2>
            <a href="/logout" class="text-rose-500">Logout</a>
        </div>

        <div class="grid md:grid-cols-2 gap-8 mb-12">
            <!-- নির্দিষ্ট ID সিঙ্ক -->
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
                <h3 class="font-bold mb-4"><i class="fa fa-plus mr-2"></i>Sync by TMDB ID</h3>
                <form action="/sync" method="POST" class="flex gap-2">
                    <input type="text" name="tmdb_id" placeholder="ID" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <select name="type" class="bg-black border border-zinc-700 p-2 rounded text-sm">
                        <option value="movie">Movie</option>
                        <option value="tv">TV</option>
                    </select>
                    <button class="bg-rose-600 px-4 py-2 rounded font-bold">Sync</button>
                </form>
            </div>

            <!-- বাল্ক সিঙ্ক সাল অনুযায়ী (ইয়ার সিঙ্ক) -->
            <div class="bg-zinc-900 p-6 rounded-2xl border border-zinc-800">
                <h3 class="font-bold mb-4 text-blue-500"><i class="fa fa-calendar-alt mr-2"></i>Bulk Sync by Year</h3>
                <form action="/sync_year" method="POST" class="flex gap-2">
                    <input type="number" name="year" placeholder="2024" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                    <button class="bg-blue-600 px-4 py-2 rounded font-bold">Bulk Upload</button>
                </form>
            </div>
        </div>

        <div class="bg-zinc-900 rounded-2xl overflow-hidden border border-zinc-800">
            <table class="w-full text-left text-sm">
                <thead class="bg-zinc-800">
                    <tr><th class="p-4">Content</th><th class="p-4">Action</th></tr>
                </thead>
                <tbody>
                    {% for i in items %}
                    <tr class="border-b border-zinc-800">
                        <td class="p-4 font-bold">{{ i.title }} ({{ i.year }})</td>
                        <td class="p-4"><a href="/delete/{{ i.tmdb_id }}" class="text-rose-500">Delete</a></td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endblock %}
    ''', items=items)

# --- সিঙ্ক লজিক (সব তথ্য আনার জন্য) ---
def fetch_and_save(tmdb_id, m_type):
    try:
        url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
        d = requests.get(url).json()
        if 'id' not in d: return False

        # কাস্ট এবং ডিটেইলস
        cast = [{"name": p['name'], "photo": IMG_BASE + p['profile_path'], "gender": p['gender']} for p in d.get('credits', {}).get('cast', []) if p.get('profile_path')]
        
        # ট্রেলার আইডি
        yt_id = "N/A"
        for v in d.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                yt_id = v['key']; break

        data = {
            "tmdb_id": str(tmdb_id), "type": m_type, "title": d.get('title') or d.get('name'),
            "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
            "rating": round(d.get('vote_average', 0), 1), "summary": d.get('overview'),
            "main_poster": IMG_ORIGINAL + d.get('poster_path'),
            "yt_id": yt_id, "cast": cast[:10],
            "director": next((p['name'] for p in d.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A"),
            "hero": next((a['name'] for a in cast if a['gender'] == 2), "N/A"),
            "heroine": next((a['name'] for a in cast if a['gender'] == 1), "N/A")
        }
        collection.update_one({"tmdb_id": str(tmdb_id)}, {"$set": data}, upsert=True)
        return True
    except: return False

# --- বাল্ক সিঙ্ক রাউট (Yearly Upload) ---
@app.route('/sync_year', methods=['POST'])
def sync_year():
    if not session.get('logged'): return redirect('/admin')
    year = request.form.get('year')
    # প্রথম ২ পেজ (প্রায় ৪০টি মুভি ও টিভি শো) অটো অ্যাড হবে
    for p in range(1, 3):
        m_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page={p}&sort_by=popularity.desc"
        t_url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&first_air_date_year={year}&page={p}&sort_by=popularity.desc"
        for m in requests.get(m_url).json().get('results', []): fetch_and_save(m['id'], 'movie')
        for t in requests.get(t_url).json().get('results', []): fetch_and_save(t['id'], 'tv')
    return redirect('/admin/dashboard')

@app.route('/sync', methods=['POST'])
def sync():
    if not session.get('logged'): return redirect('/admin')
    fetch_and_save(request.form.get('tmdb_id'), request.form.get('type'))
    return redirect('/admin/dashboard')

# --- অন্যান্য রাউট ---
@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        if request.form.get('pass') == ADMIN_PASSWORD:
            session['logged'] = True
            return redirect('/admin/dashboard')
    return render_template_string(LAYOUT + '<div class="h-screen flex items-center justify-center"><form method="POST" class="bg-zinc-900 p-8 rounded-2xl border border-zinc-800 w-full max-w-sm"><h2 class="text-xl font-bold mb-4 text-center">Admin Login</h2><input type="password" name="pass" class="w-full bg-black border border-zinc-700 p-3 rounded mb-4 outline-none focus:border-rose-600"><button class="w-full bg-rose-600 py-3 rounded font-bold">Login</button></form></div>')

@app.route('/delete/<tmdb_id>')
def delete(tmdb_id):
    if session.get('logged'): collection.delete_one({"tmdb_id": tmdb_id})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
