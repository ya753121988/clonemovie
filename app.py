import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId

# --- CONFIGURATION ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask App
app = Flask(__name__)
app.secret_key = "premium_portal_key"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB
client = MongoClient(MONGO_URI)
db = client['movie_portal_db']
videos_col = db['videos']

# --- UI DESIGN (Premium Dark) ---
DESIGN = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
    body { background-color: #0b0f19; color: #e5e7eb; font-family: 'Segoe UI', sans-serif; }
    .navbar { background: #111827; border-bottom: 1px solid #1f2937; padding: 15px; }
    .movie-card { background: #1f2937; border-radius: 12px; border: 1px solid #374151; overflow: hidden; transition: 0.3s; height: 100%; }
    .movie-card:hover { transform: translateY(-5px); border-color: #3b82f6; box-shadow: 0 10px 20px rgba(0,0,0,0.4); }
    .movie-card img { width: 100%; height: 180px; object-fit: cover; }
    .btn-blue { background: #2563eb; color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: bold; text-decoration: none; display: inline-block; }
    .btn-blue:hover { background: #1d4ed8; color: white; }
    .detail-box { background: #111827; border-radius: 20px; border: 1px solid #374151; padding: 30px; margin-top: 40px; }
    .ss-img { width: 100%; border-radius: 10px; border: 1px solid #374151; }
    .admin-card { background: #1f2937; padding: 15px; border-radius: 10px; border-left: 4px solid #ef4444; margin-bottom: 10px; }
</style>
"""

# --- BOT HANDLERS ---
@bot.message_handler(commands=['start'])
def start(message):
    args = message.text.split()
    if len(args) > 1:
        # User came from website to download
        file_id = args[1]
        bot.send_video(message.chat.id, file_id, caption="🎬 **Your Movie is Ready!**\\nEnjoy your watching.")
    else:
        # Simple start message
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 Visit Website", url=SITE_URL))
        bot.send_message(message.chat.id, "👋 **Welcome to Movie Portal!**\\nDownload latest movies from our site.", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def handle_channel_video(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "New Upload"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024*1024), 2)} MB"
        
        # Save to DB
        data = {"file_name": file_name, "file_id": file_id, "file_size": file_size}
        res = videos_col.insert_one(data)
        
        # Notify Owner
        bot.send_message(OWNER_ID, f"✅ **New Movie Added!**\\n📂 {file_name}\\n🌐 Link: {SITE_URL}/view/{res.inserted_id}", parse_mode="Markdown")

# --- WEBSITE ROUTES ---
@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    movies_html = ""
    for v in videos:
        movies_html += f'''
        <div class="col-6 col-md-3 mb-4">
            <div class="movie-card">
                <img src="https://via.placeholder.com/400x220/1f2937/ffffff?text={v['file_name'][:10]}">
                <div class="p-3">
                    <h6 class="text-truncate">{v['file_name']}</h6>
                    <a href="/view/{v['_id']}" class="btn-blue btn-sm w-100 text-center mt-2">Details</a>
                </div>
            </div>
        </div>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h4 class="text-primary m-0">PREMIUM MOVIES</h4></div></nav>
    <div class="container mt-5"><div class="row">{movies_html if movies_html else '<p>No movies yet.</p>'}</div></div>
    """

@app.route('/view/<id>')
def view(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File not found"
    
    bot_info = bot.get_me()
    dl_link = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    return f"""
    {DESIGN}
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8 detail-box">
                <h2 class="text-white mb-3">{video['file_name']}</h2>
                <p class="text-secondary">File Size: {video.get('file_size')}</p>
                <hr class="border-secondary">
                <h5 class="mb-3">Screenshots Preview</h5>
                <div class="row g-2 mb-4">
                    <div class="col-4"><img src="https://via.placeholder.com/400x250/374151/ffffff?text=SS+1" class="ss-img"></div>
                    <div class="col-4"><img src="https://via.placeholder.com/400x250/374151/ffffff?text=SS+2" class="ss-img"></div>
                    <div class="col-4"><img src="https://via.placeholder.com/400x250/374151/ffffff?text=SS+3" class="ss-img"></div>
                </div>
                <a href="{dl_link}" class="btn-blue btn-lg w-100 text-center">📥 DOWNLOAD NOW (VIA BOT)</a>
                <div class="text-center mt-4"><a href="/" class="text-secondary text-decoration-none">← Back Home</a></div>
            </div>
        </div>
    </div>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pass') == ADMIN_PASSWORD:
        session['is_admin'] = True
    if not session.get('is_admin'):
        return f'{DESIGN}<div class="container mt-5 w-50 detail-box"><form method="post"><h4>Admin Login</h4><input type="password" name="pass" class="form-control mb-3 bg-dark text-white"><button class="btn btn-primary w-100">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("_id", -1))
    list_html = ""
    for v in videos:
        list_html += f'<div class="admin-card d-flex justify-content-between"><span>{v["file_name"]}</span><a href="/del/{v["_id"]}" class="text-danger">Delete</a></div>'
    
    return f'{DESIGN}<div class="container mt-5"><h3>Admin Panel</h3><hr>{list_html}</div>'

@app.route('/del/<id>')
def delete(id):
    if session.get('is_admin'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# --- WEBHOOK LOGIC ---
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/setup')
def setup():
    bot.remove_webhook()
    bot.set_webhook(url=f"{SITE_URL}/webhook")
    return "<h1>Webhook Setup Successful!</h1>"
