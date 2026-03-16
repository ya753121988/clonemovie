import os
import requests
from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient

app = Flask(__name__)

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"  # <-- আপনার TMDB API Key এখানে বসান
IMG_URL = "https://image.tmdb.org/t/p/original"

# মঙ্গোডিবি কানেকশন
client = MongoClient(MONGO_URI)
db = client['media_database']
collection = db['all_content']

# --- এইচটিএমএল ডিজাইন (ইউজার ইন্টারফেস) ---
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TMDB Ultimate Auto Poster</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white font-sans min-h-screen">
    <div class="container mx-auto py-10 px-4">
        <header class="text-center mb-12">
            <h1 class="text-4xl font-bold text-red-500 mb-2">TMDB MEGA SYNCER</h1>
            <p class="text-slate-400">মুভি, টিভি শো এবং ইপিসোডের সব তথ্য এক ক্লিকে সেভ করুন</p>
        </header>

        <div class="max-w-2xl mx-auto bg-slate-800 p-8 rounded-xl shadow-2xl border border-slate-700">
            <form action="/sync" method="POST" class="space-y-6">
                <div>
                    <label class="block text-sm font-medium mb-2">TMDB ID দিন</label>
                    <input type="text" name="tmdb_id" placeholder="যেমন: 550 (Fight Club)" required 
                           class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 focus:ring-2 focus:ring-red-500 outline-none">
                </div>
                
                <div>
                    <label class="block text-sm font-medium mb-2">টাইপ সিলেক্ট করুন</label>
                    <select name="type" class="w-full bg-slate-700 border border-slate-600 rounded-lg px-4 py-2 outline-none">
                        <option value="movie">Movie</option>
                        <option value="tv">TV Show (সব সিজন ও ইপিসোড সহ)</option>
                    </select>
                </div>

                <button type="submit" class="w-full bg-red-600 hover:bg-red-700 text-white font-bold py-3 rounded-lg transition duration-300">
                    তথ্য সংগ্রহ এবং সেভ করুন
                </button>
            </form>
            
            {% if message %}
            <div class="mt-6 p-4 bg-green-900/50 border border-green-500 text-green-200 rounded-lg text-center">
                {{ message }}
            </div>
            {% endif %}
        </div>

        <div class="mt-12 text-center text-slate-500 text-sm">
            ডেটাবেস: <span class="text-green-500">Connected</span> | 
            সোর্স: <span class="text-blue-400">TMDB API</span>
        </div>
    </div>
</body>
</html>
'''

def get_images(tmdb_id, media_type):
    """মুভি বা টিভি শোর সব পোস্টার এবং থাম্বনেইল আনে"""
    url = f"https://api.themoviedb.org/3/{media_type}/{tmdb_id}/images?api_key={TMDB_API_KEY}"
    res = requests.get(url).json()
    posters = [IMG_URL + i['file_path'] for i in res.get('posters', [])]
    backdrops = [IMG_URL + i['file_path'] for i in res.get('backdrops', [])]
    return posters, backdrops

def get_cast_details(credits):
    """সব অভিনেতার ছবি, নাম এবং রোল সংগ্রহ করে"""
    cast_list = []
    for person in credits.get('cast', []):
        cast_list.append({
            "name": person.get('name'),
            "character": person.get('character'),
            "photo": (IMG_URL + person['profile_path']) if person.get('profile_path') else None,
            "gender": "Female" if person.get('gender') == 1 else "Male"
        })
    return cast_list

def get_episodes(tv_id, seasons):
    """টিভি শোর প্রতিটা সিজনের প্রতিটা ইপিসোড ডিটেইলস আনে"""
    full_seasons = []
    for s in seasons:
        s_num = s['season_number']
        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{s_num}?api_key={TMDB_API_KEY}"
        s_data = requests.get(url).json()
        episodes = []
        for ep in s_data.get('episodes', []):
            ep_data = {
                "episode_number": ep.get('episode_number'),
                "name": ep.get('name'),
                "summary": ep.get('overview'),
                "air_date": ep.get('air_date'),
                "rating": ep.get('vote_average'),
                "still_path": (IMG_URL + ep['still_path']) if ep.get('still_path') else None
            }
            episodes.append(ep_data)
        full_seasons.append({
            "season_name": s.get('name'),
            "season_number": s_num,
            "episodes": episodes
        })
    return full_seasons

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/sync', methods=['POST'])
def sync():
    tmdb_id = request.form.get('tmdb_id')
    m_type = request.form.get('type')

    # ১. মেইন ডিটেইলস এবং ক্রেডিট আনা
    base_url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
    data = requests.get(base_url).json()

    if 'id' not in data:
        return render_template_string(HTML_TEMPLATE, message="ভুল TMDB ID দেওয়া হয়েছে!")

    # ২. সব ইমেজ সংগ্রহ
    all_posters, all_backdrops = get_images(tmdb_id, m_type)

    # ৩. অ্যাক্টর এবং ডিরেক্টর তথ্য
    actors = get_cast_details(data.get('credits', {}))
    director = next((p['name'] for p in data.get('credits', {}).get('crew', []) if p['job'] == 'Director'), "N/A")
    
    # নায়ক/নায়িকা আলাদা করা (অ্যাক্টর লিস্টের প্রথম দুই জন যারা জেন্ডার অনুযায়ী)
    hero = next((a['name'] for a in actors if a['gender'] == "Male"), "N/A")
    heroine = next((a['name'] for a in actors if a['gender'] == "Female"), "N/A")

    # ৪. ট্রেলার
    trailer = "N/A"
    for v in data.get('videos', {}).get('results', []):
        if v['type'] == 'Trailer' and v['site'] == 'YouTube':
            trailer = f"https://www.youtube.com/watch?v={v['key']}"
            break

    # ৫. টিভি শোর ক্ষেত্রে ইপিসোড ডাটা
    seasons_data = []
    if m_type == 'tv':
        seasons_data = get_episodes(tmdb_id, data.get('seasons', []))

    # চূড়ান্ত ডাটা অবজেক্ট
    final_post = {
        "tmdb_id": tmdb_id,
        "type": m_type,
        "title": data.get('title') or data.get('name'),
        "year": (data.get('release_date') or data.get('first_air_date', "0000"))[:4],
        "language": data.get('original_language'),
        "rating": data.get('vote_average'),
        "release_date": data.get('release_date') or data.get('first_air_date'),
        "summary": data.get('overview'),
        "director": director,
        "hero": hero,
        "heroine": heroine,
        "trailer": trailer,
        "main_poster": IMG_URL + data.get('poster_path') if data.get('poster_path') else None,
        "all_posters": all_posters,
        "all_thumbnails": all_backdrops,
        "cast_details": actors,
        "seasons_episodes": seasons_data # মুভি হলে এটি খালি থাকবে
    }

    # ডাটাবেসে সেভ (থাকলে আপডেট, না থাকলে নতুন সেভ)
    collection.update_one({"tmdb_id": tmdb_id}, {"$set": final_post}, upsert=True)

    return render_template_string(HTML_TEMPLATE, message=f"সফলভাবে '{final_post['title']}' এর সব তথ্য সেভ করা হয়েছে!")

if __name__ == '__main__':
    app.run(debug=True)
