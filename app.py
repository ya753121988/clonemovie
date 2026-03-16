import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "cinema_v3_secure"

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"
ADMIN_PASSWORD = "admin123"

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['cinema_db_v3']
collection = db['media']

# --- UI ডিজাইন ---
LAYOUT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Movie Portal</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background: #050505; color: white; font-family: sans-serif; }
        .m-card:hover { transform: scale(1.03); transition: 0.3s; }
    </style>
</head>
<body>
    <nav class="bg-zinc-900 p-4 border-b border-zinc-800 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-black text-red-600 tracking-tighter">MOVIE-AI</a>
            <form action="/" method="GET" class="hidden md:flex bg-black border border-zinc-700 rounded-full px-4 py-1">
                <input type="text" name="q" placeholder="Search..." class="bg-transparent outline-none p-1 text-sm w-64">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>
            <a href="/admin" class="bg-zinc-800 px-4 py-2 rounded-lg text-sm font-bold">Admin</a>
        </div>
    </nav>
    {% block content %}{% endblock %}
</body>
</html>
'''

# --- হোম পেজ ---
@app.route('/')
def home():
    q = request.args.get('q')
    items = list(collection.find({"title": {"$regex": q, "$options": "i"}}) if q else collection.find().sort('_id', -1))
    return render_template_string(LAYOUT + '''
    {% block content %}
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
            {% for m in items %}
            <div class="m-card bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 shadow-xl">
                <img src="{{ m.poster }}" class="w-full aspect-[2/3] object-cover">
                <div class="p-3">
                    <h3 class="font-bold text-sm truncate">{{ m.title }}</h3>
                    <p class="text-[10px] text-zinc-500">{{ m.year }} | ⭐ {{ m.rating }}</p>
                    <a href="{{ m.trailer }}" target="_blank" class="mt-2 block text-center bg-red-600 py-1 rounded text-[10px] font-bold">Watch Trailer</a>
                </div>
            </div>
            {% endfor %}
        </div>
    </main>
    {% endblock %}
    ''', items=items)

# --- এডমিন প্যানেল ---
@app.route('/admin')
def admin():
    if not session.get('logged'):
        return render_template_string(LAYOUT + '<div class="h-screen flex items-center justify-center"><form action="/login" method="POST" class="bg-zinc-900 p-8 rounded-xl border border-zinc-800 w-80 shadow-2xl"><h2 class="text-xl font-bold mb-4 text-center">Login</h2><input type="password" name="pw" class="w-full bg-black border border-zinc-700 p-2 rounded mb-4 text-center"><button class="w-full bg-red-600 py-2 rounded font-bold">Login</button></form></div>')
    
    items = list(collection.find().sort('_id', -1))
    return render_template_string(LAYOUT + '''
    {% block content %}
    <div class="container mx-auto py-10 px-4 max-w-4xl">
        <div class="flex justify-between mb-8">
            <h1 class="text-2xl font-bold">Admin Dashboard</h1>
            <a href="/logout" class="text-red-500">Logout</a>
        </div>

        <div class="bg-zinc-900 p-6 rounded-xl border border-zinc-800 mb-10">
            <h3 class="font-bold mb-4">Bulk Sync by Year</h3>
            <div class="flex gap-2">
                <input type="number" id="yearInput" placeholder="2024" class="bg-black border border-zinc-700 p-2 rounded flex-1 outline-none">
                <button onclick="startBulkSync()" id="syncBtn" class="bg-blue-600 px-6 py-2 rounded font-bold">Start Bulk Sync</button>
            </div>
            <div id="status" class="mt-4 text-sm text-zinc-400"></div>
        </div>

        <table class="w-full bg-zinc-900 rounded-xl overflow-hidden">
            <thead class="bg-zinc-800 text-left text-xs uppercase font-bold">
                <tr><th class="p-4">Title</th><th class="p-4">Action</th></tr>
            </thead>
            <tbody>
                {% for i in items %}
                <tr class="border-b border-zinc-800">
                    <td class="p-4">{{ i.title }} ({{ i.year }})</td>
                    <td class="p-4"><a href="/delete/{{ i.tmdb_id }}" class="text-red-500">Delete</a></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>

    <script>
    async function startBulkSync() {
        const year = document.getElementById('yearInput').value;
        const btn = document.getElementById('syncBtn');
        const status = document.getElementById('status');
        if(!year) return alert('Enter Year');

        btn.disabled = true;
        btn.innerText = 'Fetching IDs...';
        status.innerText = 'Fetching movie list from TMDB...';

        try {
            const resp = await fetch(`/get_year_ids?year=${year}`);
            const data = await resp.json();
            const ids = data.ids;

            for(let i=0; i<ids.length; i++) {
                status.innerText = `Syncing (${i+1}/${ids.length}): ${ids[i].title}`;
                await fetch(`/sync_single?id=${ids[i].id}&type=${ids[i].type}`);
            }
            status.innerText = 'Successfully Synced All Movies!';
            location.reload();
        } catch(e) {
            status.innerText = 'Error happened during sync.';
            btn.disabled = false;
        }
    }
    </script>
    {% endblock %}
    ''', items=items)

# --- লজিক রাউটস (Internal APIs) ---

@app.route('/login', methods=['POST'])
def login():
    if request.form.get('pw') == ADMIN_PASSWORD:
        session['logged'] = True
    return redirect('/admin')

@app.route('/get_year_ids')
def get_year_ids():
    year = request.args.get('year')
    url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&sort_by=popularity.desc"
    results = requests.get(url).json().get('results', [])
    ids = [{"id": m['id'], "type": "movie", "title": m['title']} for m in results[:20]]
    return jsonify({"ids": ids})

@app.route('/sync_single')
def sync_single():
    tmdb_id = request.args.get('id')
    m_type = request.args.get('type')
    
    url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
    d = requests.get(url).json()
    
    yt_id = "N/A"
    for v in d.get('videos', {}).get('results', []):
        if v['type'] == 'Trailer' and v['site'] == 'YouTube':
            yt_id = v['key']; break

    data = {
        "tmdb_id": str(tmdb_id),
        "title": d.get('title') or d.get('name'),
        "year": (d.get('release_date') or d.get('first_air_date', "0000"))[:4],
        "rating": round(d.get('vote_average', 0), 1),
        "poster": IMG_ORIGINAL + d.get('poster_path') if d.get('poster_path') else None,
        "trailer": f"https://www.youtube.com/watch?v={yt_id}" if yt_id != "N/A" else "N/A"
    }
    collection.update_one({"tmdb_id": str(tmdb_id)}, {"$set": data}, upsert=True)
    return jsonify({"status": "ok"})

@app.route('/delete/<id>')
def delete(id):
    if session.get('logged'): collection.delete_one({"tmdb_id": id})
    return redirect('/admin')

@app.route('/logout')
def logout():
    session.pop('logged', None); return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
