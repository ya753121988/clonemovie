import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session, jsonify
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "full_movie_system_key"

# --- কনফিগারেশন (আপনার দেওয়া তথ্য) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"
ADMIN_PASSWORD = "admin123"

# মঙ্গোডিবি কানেকশন
client = MongoClient(MONGO_URI)
db = client['mega_movie_db_v2']
collection = db['all_media']

# --- এইচটিএমএল টেমপ্লেট (একশ ভাগ কমপ্লিট) ---
HTML_LAYOUT = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ultimate Movie & TV DB</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #080808; color: white; scroll-behavior: smooth; }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-thumb { background: #e11d48; border-radius: 10px; }
        .modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; }
    </style>
</head>
<body class="font-sans">

    <!-- Navbar -->
    <nav class="bg-black/90 border-b border-zinc-800 p-4 sticky top-0 z-50 backdrop-blur-md">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-3xl font-black text-rose-600 tracking-tighter">AI-CINEMA</a>
            
            <form action="/" method="GET" class="hidden md:flex bg-zinc-900 border border-zinc-700 rounded-full px-5 py-1.5 w-1/3">
                <input type="text" name="search" placeholder="Search movies, tv shows..." class="bg-transparent outline-none w-full text-sm">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>

            <div class="flex gap-4">
                <a href="/admin" class="bg-rose-600 px-5 py-2 rounded-full font-bold text-sm hover:bg-rose-700 transition">Admin Panel</a>
            </div>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <!-- Global Trailer Player -->
    <div id="trailerModal" class="modal" onclick="this.style.display='none'; document.getElementById('player').src=''">
        <div class="w-full max-w-5xl p-4">
            <div class="aspect-video bg-black rounded-2xl overflow-hidden shadow-2xl border border-zinc-800">
                <iframe id="player" class="w-full h-full" src="" frameborder="0" allow="autoplay; fullscreen" allowfullscreen></iframe>
            </div>
        </div>
    </div>

    <script>
        function openTrailer(ytId) {
            if(!ytId || ytId === 'N/A') return alert('Trailer not found!');
            document.getElementById('player').src = `https://www.youtube.com/embed/${ytId}?autoplay=1`;
            document.getElementById('trailerModal').style.display = 'flex';
        }
    </script>
</body>
</html>
'''

# --- হোম পেজ ডিটেইলস ---
HOME_PAGE = '''
{% extends "layout" %}
{% block content %}
<main class="container mx-auto py-12 px-4">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-10">
        {% for m in items %}
        <div class="bg-zinc-900 rounded-3xl overflow-hidden border border-zinc-800 shadow-xl group">
            <div class="relative h-96 overflow-hidden">
                <img src="{{ m.main_poster }}" class="w-full h-full object-cover group-hover:scale-110 transition duration-700">
                <div class="absolute inset-0 bg-gradient-to-t from-black via-transparent opacity-90"></div>
                
                <div class="absolute top-4 right-4 bg-yellow-500 text-black font-bold px-3 py-1 rounded-full text-xs shadow-lg">⭐ {{ m.rating }}</div>
                
                <div class="absolute bottom-4 left-4 right-4">
                    <span class="text-rose-500 font-bold uppercase text-[10px] tracking-widest">{{ m.type }} | {{ m.year }}</span>
                    <h3 class="text-xl font-black mt-1 line-clamp-1">{{ m.title }}</h3>
                </div>

                <div class="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition duration-300">
                    <button onclick="openTrailer('{{ m.yt_id }}')" class="bg-rose-600 h-16 w-16 rounded-full flex items-center justify-center text-2xl shadow-2xl">
                        <i class="fa fa-play ml-1"></i>
                    </button>
                </div>
            </div>

            <div class="p-5 space-y-4">
                <p class="text-zinc-500 text-xs line-clamp-2 italic">"{{ m.summary }}"</p>
                
                <div class="text-[11px] space-y-1">
                    <p><span class="text-rose-500 font-bold">Hero:</span> {{ m.hero }}</p>
                    <p><span class="text-rose-500 font-bold">Heroine:</span> {{ m.heroine }}</p>
                    <p><span class="text-rose-500 font-bold">Director:</span> {{ m.director }}</p>
                </div>

                <!-- Cast List -->
                <div>
                    <p class="text-[10px] font-bold text-zinc-600 uppercase mb-2">Top Cast</p>
                    <div class="flex -space-x-3">
                        {% for actor in m.cast[:6] %}
                        <img src="{{ actor.photo }}" title="{{ actor.name }}" class="h-10 w-10 rounded-full object-cover ring-2 ring-zinc-900">
                        {% endfor %}
                    </div>
                </div>

                <!-- Gallery Preview -->
                <div class="flex gap-2 overflow-hidden">
                    {% for img in m.backdrops[:3] %}
                    <img src="{{ img }}" class="h-12 w-20 object-cover rounded-lg border border-zinc-800">
                    {% endfor %}
                </div>
            </div>
        </div>
        {% endfor %}
    </div>
</main>
{% endblock %}
'''

# --- এডমিন ড্যাশবোর্ড ---
ADMIN_DASHBOARD = '''
{% extends "layout" %}
{% block content %}
<div class="container mx-auto py-10 px-4 max-w-6xl">
    <div class="flex justify-between items-center mb-10 border-b border-zinc-800 pb-5">
        <h1 class="text-3xl font-black">Admin Dashboard</h1>
        <a href="/logout" class="text-rose-500 font-bold">Logout</a>
    </div>

    <div class="grid md:grid-cols-2 gap-10 mb-16">
        <!-- Single Sync -->
        <div class="bg-zinc-900 p-8 rounded-3xl border border-zinc-800">
            <h3 class="text-xl font-bold mb-5 flex items-center gap-2"><i class="fa fa-plus-circle text-rose-500"></i> Add Content</h3>
            <form action="/sync" method="POST" class="space-y-4">
                <input type="text" name="tmdb_id" placeholder="TMDB ID" required class="w-full bg-black border border-zinc-700 p-3 rounded-xl outline-none focus:border-rose-500">
                <select name="type" class="w-full bg-black border border-zinc-700 p-3 rounded-xl outline-none">
                    <option value="movie">Movie</option>
                    <option value="tv">TV Show</option>
                </select>
                <button class="w-full bg-rose-600 py-3 rounded-xl font-bold shadow-lg shadow-rose-900/20">Sync Now</button>
            </form>
        </div>

        <!-- Bulk Sync Year -->
        <div class="bg-zinc-900 p-8 rounded-3xl border border-zinc-800">
            <h3 class="text-xl font-bold mb-5 flex items-center gap-2"><i class="fa fa-calendar-alt text-blue-500"></i> Yearly Bulk Upload</h3>
            <form action="/sync_year" method="POST" class="space-y-4">
                <input type="number" name="year" placeholder="Enter Year (e.g. 2024)" required class="w-full bg-black border border-zinc-700 p-3 rounded-xl outline-none focus:border-blue-500">
                <button class="w-full bg-blue-600 py-3 rounded-xl font-bold shadow-lg shadow-blue-900/20">Sync Everything for Year</button>
            </form>
            <p class="text-[10px] text-zinc-500 mt-3 text-center uppercase tracking-widest">It will sync top 40 movies & shows</p>
        </div>
    </div>

    <!-- Manage Table -->
    <div class="bg-zinc-900 rounded-3xl border border-zinc-800 overflow-hidden">
        <table class="w-full text-left">
            <thead class="bg-zinc-800 text-zinc-400 text-xs uppercase tracking-widest">
                <tr>
                    <th class="p-5">Content</th>
                    <th class="p-5 text-center">Type</th>
                    <th class="p-5 text-center">Action</th>
                </tr>
            </thead>
            <tbody class="divide-y divide-zinc-800">
                {% for item in items %}
                <tr>
                    <td class="p-5 flex items-center gap-4">
                        <img src="{{ item.main_poster }}" class="w-12 h-16 object-cover rounded shadow-lg">
                        <div>
                            <p class="font-bold">{{ item.title }}</p>
                            <p class="text-xs text-zinc-500">{{ item.year }}</p>
                        </div>
                    </td>
                    <td class="p-5 text-center"><span class="bg-zinc-800 px-3 py-1 rounded-full text-[10px] font-bold">{{ item.type | upper }}</span></td>
                    <td class="p-5 text-center">
                        <a href="/delete/{{ item.tmdb_id }}" onclick="return confirm('Delete this?')" class="text-rose-500 hover:underline"><i class="fa fa-trash"></i></a>
                    </td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
</div>
{% endblock %}
'''

# --- সাহায্যকারী ফাংশন (পুরো সিস্টেমের ইঞ্জিন) ---

def fetch_details(tmdb_id, m_type):
    try:
        url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
        data = requests.get(url).json()
        if 'id' not in data: return False

        # ১. কাস্ট এবং হিরো/হিরোইন আলাদা করা
        cast_list = []
        for p in data.get('credits', {}).get('cast', []):
            if p.get('profile_path'):
                cast_list.append({
                    "name": p.get('name'),
                    "photo": IMG_BASE + p['profile_path'],
                    "gender": p.get('gender')
                })
        
        hero = next((a['name'] for a in cast_list if a['gender'] == 2), "N/A")
        heroine = next((a['name'] for a in cast_list if a['gender'] == 1), "N/A")
        director = next((p['name'] for p in data.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")

        # ২. সব পোস্টার এবং ব্যাকড্রপ গ্যালারি
        posters = [IMG_ORIGINAL + i['file_path'] for i in data.get('images', {}).get('posters', [])[:15]]
        backdrops = [IMG_ORIGINAL + i['file_path'] for i in data.get('images', {}).get('backdrops', [])[:15]]

        # ৩. ট্রেলার (ইউটিউব আইডি)
        yt_id = "N/A"
        for v in data.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                yt_id = v['key']
                break

        # ৪. ইপিসোড ডিটেইলস (যদি টিভি শো হয়)
        episodes = []
        if m_type == 'tv':
            for s in data.get('seasons', []):
                s_num = s['season_number']
                s_url = f"https://api.themoviedb.org/3/tv/{tmdb_id}/season/{s_num}?api_key={TMDB_API_KEY}"
                s_data = requests.get(s_url).json()
                for ep in s_data.get('episodes', []):
                    episodes.append({
                        "name": ep.get('name'), "num": ep.get('episode_number'), "season": s_num,
                        "img": IMG_BASE + ep['still_path'] if ep.get('still_path') else None
                    })

        final_post = {
            "tmdb_id": str(tmdb_id),
            "type": m_type,
            "title": data.get('title') or data.get('name'),
            "year": (data.get('release_date') or data.get('first_air_date', "0000"))[:4],
            "rating": round(data.get('vote_average', 0), 1),
            "summary": data.get('overview'),
            "director": director, "hero": hero, "heroine": heroine,
            "main_poster": IMG_ORIGINAL + data.get('poster_path') if data.get('poster_path') else None,
            "all_posters": posters, "backdrops": backdrops,
            "cast": cast_list, "yt_id": yt_id, "episodes": episodes
        }
        collection.update_one({"tmdb_id": str(tmdb_id)}, {"$set": final_post}, upsert=True)
        return True
    except: return False

# --- রাউটস (লজিক) ---

@app.route('/')
def index():
    query = request.args.get('search')
    if query:
        items = list(collection.find({"title": {"$regex": query, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', HOME_PAGE), items=items)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged'] = True
            return redirect('/admin/dashboard')
    if session.get('admin_logged'): return redirect('/admin/dashboard')
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', '''
    <div class="h-screen flex items-center justify-center px-4">
        <form method="POST" class="bg-zinc-900 p-10 rounded-3xl border border-zinc-800 w-full max-w-sm shadow-2xl">
            <h2 class="text-2xl font-black mb-6 text-center text-rose-600">Admin Auth</h2>
            <input type="password" name="password" placeholder="Admin Password" class="w-full bg-black border border-zinc-700 p-4 rounded-xl mb-4 outline-none focus:border-rose-600">
            <button class="w-full bg-rose-600 py-4 rounded-xl font-black hover:bg-rose-700 transition">Login</button>
        </form>
    </div>
    '''))

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('admin_logged'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    return render_template_string(HTML_LAYOUT.replace('{% block content %}{% endblock %}', ADMIN_DASHBOARD), items=items)

@app.route('/sync', methods=['POST'])
def sync():
    if not session.get('admin_logged'): return redirect('/admin')
    fetch_details(request.form.get('tmdb_id'), request.form.get('type'))
    return redirect('/admin/dashboard')

@app.route('/sync_year', methods=['POST'])
def sync_year():
    if not session.get('admin_logged'): return redirect('/admin')
    year = request.form.get('year')
    for page in range(1, 3):
        m_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page={page}&sort_by=popularity.desc"
        t_url = f"https://api.themoviedb.org/3/discover/tv?api_key={TMDB_API_KEY}&first_air_date_year={year}&page={page}&sort_by=popularity.desc"
        for m in requests.get(m_url).json().get('results', []): fetch_details(m['id'], 'movie')
        for t in requests.get(t_url).json().get('results', []): fetch_details(t['id'], 'tv')
    return redirect('/admin/dashboard')

@app.route('/delete/<tmdb_id>')
def delete(tmdb_id):
    if not session.get('admin_logged'): return redirect('/admin')
    collection.delete_one({"tmdb_id": tmdb_id})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('admin_logged', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
