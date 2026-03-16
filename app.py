import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"  # <-- আপনার TMDB API Key এখানে দিন
IMG_URL = "https://image.tmdb.org/t/p/w500"
ORIGINAL_IMG = "https://image.tmdb.org/t/p/original"

client = MongoClient(MONGO_URI)
db = client['media_database']
collection = db['all_content']

# --- এইচটিএমএল ডিজাইন (হোম পেজ + কার্ড ডিজাইন) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Movie & TV Database</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .movie-card:hover .overlay { opacity: 1; }
        ::-webkit-scrollbar { width: 8px; }
        ::-webkit-scrollbar-thumb { background: #ef4444; border-radius: 10px; }
    </style>
</head>
<body class="bg-black text-white font-sans min-h-screen">
    
    <!-- নেভিগেশন বার -->
    <nav class="bg-zinc-900 p-4 border-b border-zinc-800 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <h1 class="text-2xl font-extrabold text-red-600 tracking-tighter">MOVIE-DB</h1>
            <div class="flex gap-4">
                <a href="/" class="hover:text-red-500 font-medium">Home</a>
                <button onclick="document.getElementById('sync-modal').style.display='flex'" class="bg-red-600 px-4 py-1 rounded text-sm font-bold">Add New</button>
            </div>
        </div>
    </nav>

    <!-- ডাটা সেভ করার পপ-আপ ফর্ম -->
    <div id="sync-modal" class="fixed inset-0 bg-black/80 hidden items-center justify-center z-[100] px-4">
        <div class="bg-zinc-900 p-6 rounded-xl border border-zinc-700 w-full max-w-md">
            <h2 class="text-xl font-bold mb-4">Sync from TMDB</h2>
            <form action="/sync" method="POST" class="space-y-4">
                <input type="text" name="tmdb_id" placeholder="Enter TMDB ID" required class="w-full bg-zinc-800 p-3 rounded border border-zinc-600">
                <select name="type" class="w-full bg-zinc-800 p-3 rounded border border-zinc-600">
                    <option value="movie">Movie</option>
                    <option value="tv">TV Show</option>
                </select>
                <div class="flex gap-2">
                    <button type="submit" class="flex-1 bg-red-600 py-2 rounded font-bold">Sync Now</button>
                    <button type="button" onclick="document.getElementById('sync-modal').style.display='none'" class="flex-1 bg-zinc-700 py-2 rounded">Close</button>
                </div>
            </form>
        </div>
    </div>

    <div class="container mx-auto py-10 px-4">
        <h2 class="text-3xl font-bold mb-8 border-l-4 border-red-600 pl-4">Recently Synced</h2>
        
        <!-- মুভি গ্রিড -->
        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-8">
            {% for item in items %}
            <div class="bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 shadow-2xl">
                <!-- মেইন পোস্টার -->
                <div class="relative group">
                    <img src="{{ item.main_poster }}" class="w-full h-[450px] object-cover" alt="Poster">
                    <div class="absolute top-2 right-2 bg-black/70 px-2 py-1 rounded text-yellow-500 font-bold">⭐ {{ item.rating }}</div>
                </div>

                <div class="p-5">
                    <h3 class="text-xl font-bold text-red-500 mb-1">{{ item.title }} ({{ item.year }})</h3>
                    <p class="text-zinc-400 text-sm line-clamp-2 mb-4">{{ item.summary }}</p>
                    
                    <div class="space-y-2 text-sm text-zinc-300">
                        <p><strong>Director:</strong> {{ item.director }}</p>
                        <p><strong>Hero:</strong> {{ item.hero }} | <strong>Heroine:</strong> {{ item.heroine }}</p>
                        <p><strong>Language:</strong> {{ item.language | upper }}</p>
                    </div>

                    <!-- সব ছবির স্লাইডার (ছোট করে) -->
                    <div class="mt-4">
                        <p class="text-xs font-bold mb-2 uppercase text-zinc-500">More Images</p>
                        <div class="flex gap-2 overflow-x-auto pb-2">
                            {% for p in item.all_posters[:5] %}
                                <img src="{{ p }}" class="w-16 h-24 object-cover rounded border border-zinc-700">
                            {% endfor %}
                        </div>
                    </div>

                    <!-- সব অ্যাক্টরের ছবি -->
                    <div class="mt-4">
                        <p class="text-xs font-bold mb-2 uppercase text-zinc-500">Cast</p>
                        <div class="flex gap-2 overflow-x-auto pb-2">
                            {% for actor in item.cast_details[:6] %}
                                <div class="text-center min-w-[60px]">
                                    <img src="{{ actor.photo }}" class="w-12 h-12 rounded-full mx-auto object-cover border border-red-600">
                                    <p class="text-[10px] mt-1 truncate w-14">{{ actor.name }}</p>
                                </div>
                            {% endfor %}
                        </div>
                    </div>

                    {% if item.trailer != "N/A" %}
                    <a href="{{ item.trailer }}" target="_blank" class="block mt-6 text-center bg-zinc-800 hover:bg-zinc-700 py-2 rounded-lg font-bold text-sm transition">Watch Trailer</a>
                    {% endif %}
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

# --- আগের সব ফাংশন (সেম থাকবে) ---
def get_images(tmdb_id, media_type):
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/images?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    posters = [ORIGINAL_IMG + i['file_path'] for i in res.get('posters', [])]
    backdrops = [ORIGINAL_IMG + i['file_path'] for i in res.get('backdrops', [])]
    return posters, backdrops

def get_cast_details(credits):
    cast_list = []
    for person in credits.get('cast', []):
        if person.get('profile_path'): # শুধু ছবি আছে এমন অ্যাক্টরদের নিবে
            cast_list.append({
                "name": person.get('name'),
                "photo": IMG_URL + person['profile_path'],
                "gender": "Female" if person.get('gender') == 1 else "Male"
            })
    return cast_list

@app.route('/')
def index():
    # ডাটাবেস থেকে সব ডাটা নিয়ে এসে হোম পেজে পাঠানো
    items = list(collection.find().sort('_id', -1))
    return render_template_string(HTML_TEMPLATE, items=items)

@app.route('/sync', methods=['POST'])
def sync():
    tmdb_id = request.form.get('tmdb_id')
    m_type = request.form.get('type')
    
    base_url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
    data = requests.get(base_url).json()

    if 'id' in data:
        all_posters, all_backdrops = get_images(tmdb_id, m_type)
        actors = get_cast_details(data.get('credits', {}))
        director = next((p['name'] for p in data.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")
        hero = next((a['name'] for a in actors if a['gender'] == "Male"), "N/A")
        heroine = next((a['name'] for a in actors if a['gender'] == "Female"), "N/A")
        
        trailer = "N/A"
        for v in data.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break

        final_post = {
            "tmdb_id": tmdb_id,
            "title": data.get('title') or data.get('name'),
            "year": (data.get('release_date') or data.get('first_air_date', "0000"))[:4],
            "rating": data.get('vote_average'),
            "summary": data.get('overview'),
            "director": director,
            "hero": hero,
            "heroine": heroine,
            "language": data.get('original_language'),
            "trailer": trailer,
            "main_poster": ORIGINAL_IMG + data.get('poster_path'),
            "all_posters": all_posters,
            "cast_details": actors
        }
        collection.update_one({"tmdb_id": tmdb_id}, {"$set": final_post}, upsert=True)

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
