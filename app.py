import os
import requests
from flask import Flask, render_template_string, request, redirect, url_for, session
from pymongo import MongoClient

app = Flask(__name__)
app.secret_key = "secret_key_for_session" # সেশন সিকিউরিটির জন্য

# --- কনফিগারেশন ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
TMDB_API_KEY = "275aff9f1c570308fa10d14c6f49f998"
IMG_BASE = "https://image.tmdb.org/t/p/w500"
IMG_ORIGINAL = "https://image.tmdb.org/t/p/original"
ADMIN_PASSWORD = "admin123" # আপনার এডমিন পাসওয়ার্ড

client = MongoClient(MONGO_URI)
db = client['ultimate_media_db']
collection = db['content']

# --- UI ডিজাইন (টেইলউইন্ড সিএসএস) ---
BASE_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mega MovieDB - Admin Control</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
    <style>
        body { background-color: #050505; color: white; }
        .trailer-modal { display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.95); z-index: 1000; align-items: center; justify-content: center; }
    </style>
</head>
<body>
    <nav class="bg-zinc-900 border-b border-zinc-800 p-4 sticky top-0 z-50">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-black text-red-600">MOVIE AI</a>
            
            <!-- Search Box -->
            <form action="/" method="GET" class="hidden md:flex bg-black border border-zinc-700 rounded-full px-4 py-1">
                <input type="text" name="search" placeholder="Search movies..." class="bg-transparent outline-none p-1 text-sm w-64">
                <button type="submit"><i class="fa fa-search text-zinc-500"></i></button>
            </form>

            <div class="flex gap-4 items-center">
                <a href="/admin" class="text-sm font-bold bg-zinc-800 px-4 py-2 rounded-lg hover:bg-red-600 transition">Admin Panel</a>
            </div>
        </div>
    </nav>

    {% block content %}{% endblock %}

    <!-- Trailer Modal -->
    <div id="trailerModal" class="trailer-modal" onclick="closeTrailer()">
        <div class="relative w-full max-w-4xl p-4">
            <button class="absolute -top-10 right-0 text-white text-2xl">&times; Close</button>
            <div class="aspect-video">
                <iframe id="trailerFrame" class="w-full h-full rounded-xl" src="" frameborder="0" allowfullscreen></iframe>
            </div>
        </div>
    </div>

    <script>
        function playTrailer(url) {
            if(url === 'N/A') return alert('Trailer not available');
            const videoId = url.split('v=')[1];
            document.getElementById('trailerFrame').src = `https://www.youtube.com/embed/${videoId}?autoplay=1`;
            document.getElementById('trailerModal').style.display = 'flex';
        }
        function closeTrailer() {
            document.getElementById('trailerModal').style.display = 'none';
            document.getElementById('trailerFrame').src = '';
        }
    </script>
</body>
</html>
'''

# --- হোম পেজ রাউট ---
@app.route('/')
def index():
    search_query = request.args.get('search')
    if search_query:
        # সার্চ লজিক
        items = list(collection.find({"title": {"$regex": search_query, "$options": "i"}}).sort('_id', -1))
    else:
        items = list(collection.find().sort('_id', -1))
    
    return render_template_string(BASE_HTML + '''
    {% block content %}
    <main class="container mx-auto py-10 px-4">
        <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
            {% for item in items %}
            <div class="bg-zinc-900 rounded-xl overflow-hidden border border-zinc-800 group hover:border-red-600 transition">
                <div class="relative aspect-[2/3] overflow-hidden">
                    <img src="{{ item.main_poster }}" class="w-full h-full object-cover group-hover:scale-110 transition duration-500">
                    <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                        <button onclick="playTrailer('{{ item.trailer }}')" class="bg-red-600 h-12 w-12 rounded-full flex items-center justify-center text-xl">
                            <i class="fa fa-play"></i>
                        </button>
                    </div>
                    <div class="absolute top-2 right-2 bg-yellow-500 text-black font-bold text-xs px-2 py-1 rounded">⭐ {{ item.rating }}</div>
                </div>
                <div class="p-4">
                    <h3 class="font-bold truncate text-sm">{{ item.title }}</h3>
                    <p class="text-zinc-500 text-[10px] mt-1">{{ item.year }} | {{ item.language | upper }}</p>
                </div>
            </div>
            {% endfor %}
        </div>
    </main>
    {% endblock %}
    ''', items=items)

# --- এডমিন প্যানেল রাউট ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['logged_in'] = True
            return redirect('/admin/dashboard')
    
    if session.get('logged_in'):
        return redirect('/admin/dashboard')

    return render_template_string(BASE_HTML + '''
    {% block content %}
    <div class="flex items-center justify-center h-[70vh]">
        <form method="POST" class="bg-zinc-900 p-8 rounded-xl border border-zinc-800 w-full max-w-sm">
            <h2 class="text-xl font-bold mb-4 text-center">Admin Login</h2>
            <input type="password" name="password" placeholder="Password" class="w-full bg-black border border-zinc-700 p-3 rounded mb-4 outline-none">
            <button class="w-full bg-red-600 py-3 rounded font-bold">Login</button>
        </form>
    </div>
    {% endblock %}
    ''')

@app.route('/admin/dashboard')
def admin_dashboard():
    if not session.get('logged_in'): return redirect('/admin')
    items = list(collection.find().sort('_id', -1))
    return render_template_string(BASE_HTML + '''
    {% block content %}
    <div class="container mx-auto py-10 px-4">
        <div class="flex justify-between items-center mb-10">
            <h1 class="text-2xl font-bold">Admin Dashboard</h1>
            <a href="/logout" class="text-red-500">Logout</a>
        </div>

        <!-- Sync Control -->
        <div class="grid md:grid-cols-2 gap-6 mb-12">
            <div class="bg-zinc-900 p-6 rounded-xl border border-zinc-800">
                <h3 class="font-bold mb-4">Sync by Year</h3>
                <form action="/sync_year" method="POST" class="flex gap-2">
                    <input type="number" name="year" placeholder="2024" class="bg-black border border-zinc-700 p-2 rounded flex-1">
                    <button class="bg-blue-600 px-6 py-2 rounded font-bold">Bulk Sync</button>
                </form>
            </div>
            <div class="bg-zinc-900 p-6 rounded-xl border border-zinc-800">
                <h3 class="font-bold mb-4">Sync by ID</h3>
                <form action="/sync" method="POST" class="flex gap-2">
                    <input type="text" name="tmdb_id" placeholder="ID" class="bg-black border border-zinc-700 p-2 rounded flex-1">
                    <select name="type" class="bg-black border border-zinc-700 p-2 rounded">
                        <option value="movie">Movie</option>
                        <option value="tv">TV</option>
                    </select>
                    <button class="bg-red-600 px-6 py-2 rounded font-bold">Sync</button>
                </form>
            </div>
        </div>

        <!-- Content List with Delete -->
        <div class="overflow-x-auto">
            <table class="w-full text-left bg-zinc-900 rounded-xl overflow-hidden">
                <thead class="bg-zinc-800">
                    <tr>
                        <th class="p-4">Title</th>
                        <th class="p-4">Type</th>
                        <th class="p-4">Year</th>
                        <th class="p-4">Action</th>
                    </tr>
                </thead>
                <tbody>
                    {% for item in items %}
                    <tr class="border-b border-zinc-800">
                        <td class="p-4 font-bold">{{ item.title }}</td>
                        <td class="p-4 uppercase text-xs">{{ item.type }}</td>
                        <td class="p-4 text-zinc-500">{{ item.year }}</td>
                        <td class="p-4">
                            <a href="/delete/{{ item.tmdb_id }}" class="text-red-500 hover:underline" onclick="return confirm('Delete this?')">Delete</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>
    {% endblock %}
    ''', items=items)

# --- সাহায্যকারী ফাংশন (সেম থাকবে) ---
def fetch_and_save(tmdb_id, m_type):
    try:
        url = f"https://api.themoviedb.org/3/{m_type}/{tmdb_id}?api_key={TMDB_API_KEY}&append_to_response=credits,videos"
        data = requests.get(url).json()
        if 'id' not in data: return False
        
        cast = []
        for p in data.get('credits', {}).get('cast', []):
            if p.get('profile_path'):
                cast.append({"name": p.get('name'), "photo": IMG_BASE + p['profile_path'], "gender": "Female" if p.get('gender') == 1 else "Male"})
        
        trailer = "N/A"
        for v in data.get('videos', {}).get('results', []):
            if v['type'] == 'Trailer' and v['site'] == 'YouTube':
                trailer = f"https://www.youtube.com/watch?v={v['key']}"
                break

        final_data = {
            "tmdb_id": str(tmdb_id),
            "type": m_type,
            "title": data.get('title') or data.get('name'),
            "year": (data.get('release_date') or data.get('first_air_date', "0000"))[:4],
            "language": data.get('original_language'),
            "rating": round(data.get('vote_average', 0), 1),
            "summary": data.get('overview'),
            "main_poster": IMG_ORIGINAL + data.get('poster_path') if data.get('poster_path') else None,
            "cast_details": cast,
            "trailer": trailer
        }
        collection.update_one({"tmdb_id": str(tmdb_id)}, {"$set": final_data}, upsert=True)
        return True
    except: return False

@app.route('/sync', methods=['POST'])
def sync():
    if not session.get('logged_in'): return redirect('/admin')
    fetch_and_save(request.form.get('tmdb_id'), request.form.get('type'))
    return redirect('/admin/dashboard')

@app.route('/sync_year', methods=['POST'])
def sync_year():
    if not session.get('logged_in'): return redirect('/admin')
    year = request.form.get('year')
    for p in range(1, 3):
        m_url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&primary_release_year={year}&page={p}"
        for m in requests.get(m_url).json().get('results', []): fetch_and_save(m['id'], 'movie')
    return redirect('/admin/dashboard')

@app.route('/delete/<tmdb_id>')
def delete(tmdb_id):
    if not session.get('logged_in'): return redirect('/admin')
    collection.delete_one({"tmdb_id": tmdb_id})
    return redirect('/admin/dashboard')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
