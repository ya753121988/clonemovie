import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# --- কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"

# মঙ্গোডিবি কানেকশন
client = MongoClient(MONGO_URI)
db = client['ultimate_media_db']
collection = db['content']

# --- UI ডিজাইন (HTML & Tailwind CSS) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mega Movie Database</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        ::-webkit-scrollbar { width: 5px; height: 5px; }
        ::-webkit-scrollbar-thumb { background: #E50914; border-radius: 10px; }
        body { background-color: #0f172a; }
        .movie-card:hover { transform: scale(1.02); transition: 0.3s; }
    </style>
</head>
<body class="text-gray-100">

    <!-- Navbar -->
    <nav class="bg-slate-900/90 backdrop-blur-md sticky top-0 z-50 border-b border-slate-800 p-4">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-3xl font-black text-red-600 tracking-tighter">AI-POSTER</h1>
            <button onclick="document.getElementById('sync-modal').style.display='flex'" 
                    class="bg-red-600 hover:bg-red-700 px-6 py-2 rounded-full font-bold shadow-lg transition">
                <i class="fa-solid fa-plus mr-2"></i> Sync New
            </button>
        </div>
    </nav>

    <!-- Sync Modal -->
    <div id="sync-modal" class="fixed inset-0 bg-black/90 hidden items-center justify-center z-[100] px-4">
        <div class="bg-slate-900 border border-slate-700 p-8 rounded-2xl w-full max-w-lg shadow-2xl">
            <h2 class="text-2xl font-bold mb-6 text-red-500">Sync Data from TMDB</h2>
            <form action="/sync" method="POST" class="space-y-5">
                <div>
                    <label class="block text-sm text-slate-400 mb-2">TMDB Content ID</label>
                    <input type="text" name="tmdb_id" placeholder="e.g. 1399 (Game of Thrones)" required 
                           class="w-full bg-slate-800 border border-slate-700 p-3 rounded-lg focus:ring-2 focus:ring-red-500 outline-none">
                </div>
                <div>
                    <label class="block text-sm text-slate-400 mb-2">Category</label>
                    <select name="type" class="w-full bg-slate-800 border border-slate-700 p-3 rounded-lg">
                        <option value="movie">Movie</option>
                        <option value="tv">TV Show (with Episodes)</option>
                    </select>
                </div>
                <div class="flex gap-3 pt-4">
                    <button type="submit" class="flex-1 bg-red-600 py-3 rounded-lg font-bold">Start Syncing</button>
                    <button type="button" onclick="document.getElementById('sync-modal').style.display='none'" 
                            class="flex-1 bg-slate-700 py-3 rounded-lg font-bold">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Main Content -->
    <main class="container mx-auto py-12 px-4">
        <h2 class="text-2xl font-bold mb-10 flex items-center gap-3">
            <span class="w-2 h-8 bg-red-600 rounded-full"></span>
            Database Library
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
            {% for item in items %}
            <div class="bg-slate-900 border border-slate-800 rounded-3xl overflow-hidden shadow-xl movie-card">
                <!-- Poster -->
                <div class="relative h-96">
                    <img src="{{ item.main_poster }}" class="w-full h-full object-cover" alt="Poster">
                    <div class="absolute inset-0 bg-gradient-to-t from-slate-900 via-transparent"></div>
                    <div class="absolute bottom-4 left-4">
                        <span class="bg-red-600 px-3 py-1 rounded-md text-xs font-bold uppercase">{{ item.type }}</span>
                        <h3 class="text-2xl font-black mt-2 leading-tight">{{ item.title }}</h3>
                    </div>
                    <div class="absolute top-4 right-4 bg-yellow-500 text-black px-3 py-1 rounded-full font-bold text-sm">
                        ⭐ {{ item.rating }}
                    </div>
                </div>

                <div class="p-6 space-y-4">
                    <p class="text-slate-400 text-sm line-clamp-3 italic">"{{ item.summary }}"</p>
                    
                    <div class="grid grid-cols-2 gap-4 text-xs">
                        <div class="bg-slate-800 p-3 rounded-xl border border-slate-700">
                            <p class="text-red-500 font-bold mb-1">Director</p>
                            <p class="truncate">{{ item.director }}</p>
                        </div>
                        <div class="bg-slate-800 p-3 rounded-xl border border-slate-700">
                            <p class="text-red-500 font-bold mb-1">Release Year</p>
                            <p>{{ item.year }}</p>
                        </div>
                    </div>

                    <!-- Lead Cast -->
                    <div>
                        <p class="text-xs font-bold text-slate-500 uppercase mb-3 tracking-widest">Main Cast</p>
                        <div class="flex -space-x-3 overflow-hidden">
                            {% for actor in item.cast_details[:5] %}
                            <img title="{{ actor.name }}" class="inline-block h-12 w-12 rounded-full ring-2 ring-slate-900 object-cover" src="{{ actor.photo }}" alt="">
                            {% endfor %}
                        </div>
                        <p class="text-xs mt-2 text-slate-400">Hero: <span class="text-white">{{ item.hero }}</span> | Heroine: <span class="text-white">{{ item.heroine }}</span></p>
                    </div>

                    <!-- Gallery Section -->
                    <div>
                        <p class="text-xs font-bold text-slate-500 uppercase mb-3 tracking-widest">Wallpapers ({{ item.all_thumbnails|length }})</p>
                        <div class="flex gap-2 overflow-x-auto pb-2">
                            {% for thumb in item.all_thumbnails[:4] %}
                            <img src="{{ thumb }}" class="h-16 w-28 object-cover rounded-lg border border-slate-700 flex-shrink-0">
                            {% endfor %}
                        </div>
                    </div>

                    {% if item.type == 'tv' %}
                    <div class="bg-blue-900/20 p-3 rounded-lg border border-blue-500/30 text-xs text-blue-300">
                        <i class="fa-solid fa-layer-group mr-2"></i> Seasons & Episodes Synced
                    </div>
                    {% endif %}

                    {% if item.trailer != "N/A" %}
                    <a href="{{ item.trailer }}" target="_blank" class="block w-full text-center bg-white text-black py-3 rounded-xl font-bold hover:bg-red-600 hover:text-white transition">
                        <i class="fa-brands fa-youtube mr-2"></i> Play Trailer
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </main>

</body>
</html>
'''

# --- Helper Functions ---

def get_full_cast(credits):
    cast_data = []
    for p in credits.get('cast', []):
        if p.get('profile_path'):
            cast_data.append({
                "name": p.get('name'),
                "photo": IMG_BASE + p['profile_path'],
                "gender": "Female" if p.get('gender') == 1 else "Male"
            })
    return cast_data

def get_tv_episodes(tv_id, seasons):
    seasons_list = []
    for s in seasons:
        s_num = s['season_number']
        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{s_num}?api_key={TMDB_API_KEY}"
        data = requests.get(url).json()
        eps = []
        for ep in data.get('episodes', []):
            eps.append({
                "ep_no": ep.get('episode_number'),
                "name": ep.get('name'),
                "img": (IMG_BASE + ep['still_path']) if ep.get('still_path') else None,
                "summary": ep.get('overview')
            })
        seasons_list.append({"season": s_num, "episodes": eps})
    return seasons_list

# --- Routes ---

@app.route('/')
def index():
    # ডাটাবেস থেকে সব ডাটা রিড করা
    items = list(collection.find().sort('_id', -1))
    return render_template_string(HTML_TEMPLATE, items=items)

@app.route('/sync', methods=['POST'])
def sync():
    tmdb_id = request.form.get('tmdb_id')
    m_type = request.form.get('type')

    # ১. ডাটা ফেচ করা
    url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos,images"
    res = requests.get(url)
    data = res.json()

    if 'id' in data:
        # ২. কাস্ট ও ডিরেক্টর
        cast = get_full_cast(data.get('credits', {}))
        director = next((p['name'] for p in data.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "Unknown")
        hero = next((a['name'] for a in cast if a['gender'] == "Male"), "N/A")
        heroine = next((a['name'] for a in cast if a['gender'] == "Female"), "N/A")

        # ৩. ইমেজ গ্যালারি (পোস্টার ও থাম্বনেইল)
        posters = [IMG_ORIGINAL + i['file_path'] for i in data.get('images', {}).get('posters', [])]
        backdrops = [IMG_ORIGINAL + i['file_path'] for i in data.get('images', {}).get('backdrops', [])]

        # ৪. ট্রেলার
        trailer = "N/A"
        for v in data.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break

        # ৫. টিভি শো ইপিসোড লজিক
        episodes_data = []
        if m_type == 'tv':
            episodes_data = get_tv_episodes(tmdb_id, data.get('seasons', []))

        # ৬. অবজেক্ট তৈরি
        final_data = {
            "tmdb_id": tmdb_id,
            "type": m_type,
            "title": data.get('title') or data.get('name'),
            "year": (data.get('release_date') or data.get('first_air_date', "0000"))[:4],
            "language": data.get('original_language'),
            "rating": round(data.get('vote_average', 0), 1),
            "summary": data.get('overview'),
            "director": director,
            "hero": hero,
            "heroine": heroine,
            "main_poster": IMG_ORIGINAL + data.get('poster_path'),
            "all_posters": posters,
            "all_thumbnails": backdrops,
            "cast_details": cast,
            "trailer": trailer,
            "seasons": episodes_data
        }

        # ৭. মঙ্গোডিবি-তে সেভ (Upsert)
        collection.update_one({"tmdb_id": tmdb_id}, {"$set": final_data}, upsert=True)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
