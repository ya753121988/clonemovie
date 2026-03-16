import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId

# --- ১. কনফিগারেশন (আপনার দেওয়া তথ্য) ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup (threaded=False is must for Vercel)
app = Flask(__name__)
app.secret_key = "premium_secret_v10"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB
client = MongoClient(MONGO_URI)
db = client['premium_movie_db']
videos_col = db['videos']

# --- ২. প্রিমিয়াম ডার্ক ডিজাইন (Netflix Style) ---
DESIGN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background-color: #06090f; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
        .navbar { background: #0b0f19; border-bottom: 2px solid #1f2937; padding: 15px; }
        .movie-card { background: #111827; border: 1px solid #1f2937; border-radius: 15px; overflow: hidden; transition: 0.3s; position: relative; }
        .movie-card:hover { transform: translateY(-8px); border-color: #3b82f6; box-shadow: 0 10px 30px rgba(59, 130, 246, 0.2); }
        .movie-card img { width: 100%; height: 260px; object-fit: cover; }
        .movie-info { padding: 15px; text-align: center; }
        .btn-premium { background: linear-gradient(45deg, #2563eb, #7c3aed); color: white; border: none; padding: 12px 20px; border-radius: 10px; font-weight: bold; width: 100%; transition: 0.3s; text-decoration: none; display: inline-block; }
        .btn-premium:hover { opacity: 0.9; box-shadow: 0 0 15px rgba(124, 58, 237, 0.5); color: white; }
        .glass-detail { background: rgba(31, 41, 55, 0.5); backdrop-filter: blur(10px); border-radius: 20px; border: 1px solid #374151; padding: 30px; margin-top: 50px; }
        .ss-grid img { width: 100%; border-radius: 12px; border: 1px solid #1f2937; margin-bottom: 10px; }
        .admin-item { background: #1f2937; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
"""

# --- ৩. বট লজিক (Start & Channel Post) ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    text_parts = message.text.split()
    if len(text_parts) > 1:
        file_id = text_parts[1]
        try:
            bot.send_video(message.chat.id, file_id, caption="✅ **আপনার ভিডিওটি প্রস্তুত!**\\n\\nউপভোগ করতে প্লে বাটনে ক্লিক করুন।", parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "❌ দুঃখিত, ভিডিওটি পাঠাতে সমস্যা হয়েছে।")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(message.chat.id, "👋 **মুভি পোর্টালে স্বাগতম!**\\n\\nলেটেস্ট সব মুভি ও ভিডিও ডাউনলোড করতে নিচের বাটনে ক্লিক করে ওয়েবসাইট ভিজিট করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def handle_channel_video(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "New Movie"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
        
        # ডাটাবেসে সেভ
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb_url": "https://via.placeholder.com/400x600/0b0f19/ffffff?text=Premium+Movie"
        }
        res = videos_col.insert_one(data)
        
        # আপনাকে নোটিফিকেশন পাঠানো
        log = f"✅ **নতুন মুভি সাইটে অ্যাড হয়েছে!**\\n📂 `{file_name}`\\n🌐 লিঙ্ক: {SITE_URL}/view/{res.inserted_id}"
        bot.send_message(OWNER_ID, log, parse_mode="Markdown")

# --- ৪. ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    movies_list = ""
    for v in videos:
        movies_list += f'''
        <div class="col-6 col-md-3 mb-4">
            <div class="movie-card">
                <img src="{v.get('thumb_url')}">
                <div class="movie-info">
                    <h6 class="text-truncate">{v['file_name']}</h6>
                    <a href="/view/{v['_id']}" class="btn-premium btn-sm mt-2">Details</a>
                </div>
            </div>
        </div>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-primary">MOVIE PORTAL</h3></div></nav>
    <div class="container mt-5"><div class="row">{movies_list if movies_list else '<h4 class="text-center">No movies found.</h4>'}</div></div>
    </body></html>
    """

@app.route('/view/<id>')
def view(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File not found"
    
    bot_info = bot.get_me()
    download_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    return f"""
    {DESIGN}
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8 glass-detail">
                <img src="{video.get('thumb_url')}" class="img-fluid rounded mb-4 w-100" style="max-height:400px; object-fit:contain;">
                <h2 class="mb-2">{video['file_name']}</h2>
                <p class="text-secondary">Size: {video.get('file_size')}</p>
                <hr style="border-color: #374151;">
                <h5 class="mb-3">Screenshots</h5>
                <div class="row g-2 ss-grid">
                    <div class="col-6"><img src="{video.get('thumb_url')}"></div>
                    <div class="col-6"><img src="{video.get('thumb_url')}"></div>
                </div>
                <br>
                <a href="{download_url}" class="btn-premium py-3 fs-5">📥 Download via Telegram Bot</a>
                <div class="text-center mt-4"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
            </div>
        </div>
    </div>
    </body></html>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('p') == ADMIN_PASSWORD:
        session['adm'] = True
    if not session.get('adm'):
        return f'{DESIGN}<div class="container mt-5 w-50 glass-detail"><form method="post"><h4>Admin Login</h4><input type="password" name="p" class="form-control mb-3 bg-dark text-white border-secondary"><button class="btn-premium">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("_id", -1))
    list_html = ""
    for v in videos:
        list_html += f'<div class="admin-item"><span>{v["file_name"]}</span><a href="/del/{v["_id"]}" class="text-danger">Delete</a></div>'
    return f'{DESIGN}<div class="container mt-5"><h3>Admin Panel</h3><br>{list_html}</div></body></html>'

@app.route('/del/<id>')
def delete(id):
    if session.get('adm'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# --- ৫. Webhook & Setup ---

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
    success = bot.set_webhook(url=f"{SITE_URL}/webhook")
    return "<h1>✅ Webhook Setup Successful!</h1>" if success else "<h1>❌ Setup Failed!</h1>"

# Vercel-এর জন্য 'app' অবজেক্ট
