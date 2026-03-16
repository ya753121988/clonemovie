import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId

# --- কনফিগারেশন ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask Setup
app = Flask(__name__)
app.secret_key = "super_secret_key_123" # সরাসরি একটি স্ট্রিং দেওয়া ভালো Vercel এর জন্য
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_portal']
videos_col = db['movies']

# --- ডিজাইন (Netflix Theme) ---
DESIGN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080b12; color: #e5e7eb; font-family: 'Inter', sans-serif; }
        .navbar { background: #111827; border-bottom: 2px solid #3b82f6; padding: 15px; }
        .card-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 30px; }
        .movie-card { background: #1f2937; border-radius: 15px; overflow: hidden; width: 220px; transition: 0.3s; border: 1px solid #374151; }
        .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3); }
        .movie-card img { width: 100%; height: 280px; object-fit: cover; }
        .btn-dl { background: linear-gradient(90deg, #2563eb, #7c3aed); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: bold; width: 100%; text-decoration: none; display: block; text-align: center; }
        .detail-card { background: #111827; border-radius: 20px; padding: 30px; border: 1px solid #374151; max-width: 800px; margin: 40px auto; }
        .ss-img { width: 100%; border-radius: 10px; border: 1px solid #374151; margin-bottom: 10px; }
        .admin-item { background: #1f2937; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; }
    </style>
</head>
<body>
"""

# --- বট লজিক ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    command_text = message.text.split()
    
    if len(command_text) > 1:
        file_id = command_text[1]
        try:
            bot.send_chat_action(chat_id, 'upload_video')
            bot.send_video(chat_id, file_id, caption="🎬 **আপনার ফাইলটি প্রস্তুত!**", parse_mode="Markdown")
        except:
            try:
                bot.send_document(chat_id, file_id, caption="🎬 **আপনার ফাইলটি প্রস্তুত!**")
            except:
                bot.send_message(chat_id, "❌ দুঃখিত! ফাইলটি পাঠাতে সমস্যা হচ্ছে।")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, "👋 **মুভি পোর্টালে স্বাগতম!**", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video', 'document'])
def handle_channel_post(message):
    if message.chat.id == CHANNEL_ID:
        file_name = "New Movie"
        file_id = ""
        file_size = "Unknown"
        
        if message.video:
            file_name = message.video.file_name or "Movie_File"
            file_id = message.video.file_id
            file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
        elif message.document:
            file_name = message.document.file_name or "Document_File"
            file_id = message.document.file_id
            file_size = f"{round(message.document.file_size / (1024 * 1024), 2)} MB"
            
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb": "https://via.placeholder.com/400x600/080b12/ffffff?text=Premium+Content"
        }
        res = videos_col.insert_one(data)
        log = f"✅ **নতুন ফাইল অ্যাড হয়েছে!**\n📂 `{file_name}`\n🌐 লিঙ্ক: {SITE_URL}/view/{res.inserted_id}"
        bot.send_message(OWNER_ID, log, parse_mode="Markdown")

# --- ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    movies_html = ""
    for v in videos:
        movies_html += f'''
        <div class="movie-card">
            <img src="{v.get('thumb')}">
            <div class="p-3 text-center">
                <h6 class="text-truncate">{v['file_name']}</h6>
                <a href="/view/{v['_id']}" class="btn-dl btn-sm mt-2">Details</a>
            </div>
        </div>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-primary">MOVIE PORTAL</h3></div></nav>
    <div class="card-container">{movies_html if movies_html else '<h4 class="text-center">No movies found.</h4>'}</div>
    </body></html>
    """

@app.route('/view/<id>')
def view(id):
    try:
        video = videos_col.find_one({"_id": ObjectId(id)})
    except:
        return "Invalid ID"
    
    if not video: return "File not found"
    
    bot_info = bot.get_me()
    download_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    return f"""
    {DESIGN}
    <div class="container">
        <div class="detail-card text-center">
            <img src="{video.get('thumb')}" class="img-fluid rounded mb-4" style="max-height:400px;">
            <h2 class="mb-2">{video['file_name']}</h2>
            <p class="text-secondary">File Size: {video.get('file_size')}</p>
            <hr style="border-color: #374151;">
            <div class="row g-2">
                <div class="col-6"><img src="{video.get('thumb')}" class="ss-img"></div>
                <div class="col-6"><img src="{video.get('thumb')}" class="ss-img"></div>
            </div>
            <br>
            <a href="{download_url}" class="btn-dl py-3 fs-5">📥 Download via Telegram Bot</a>
            <div class="mt-4"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
        </div>
    </div>
    </body></html>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('p') == ADMIN_PASSWORD:
        session['adm'] = True
    if not session.get('adm'):
        return f'{DESIGN}<div class="container mt-5 w-50 detail-card"><form method="post"><h4>Admin Login</h4><input type="password" name="p" class="form-control mb-3 bg-dark text-white"><button class="btn-dl">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("_id", -1))
    rows = ""
    for v in videos:
        rows += f'<div class="admin-item"><span>{v["file_name"]}</span><a href="/del/{v["_id"]}" class="text-danger">Delete</a></div>'
    return f'{DESIGN}<div class="container mt-5"><h3>Admin Panel</h3>{rows}</div></body></html>'

@app.route('/del/<id>')
def delete(id):
    if session.get('adm'): 
        videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

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

# Vercel এর জন্য সরাসরি app ব্যবহার করতে হয়
if __name__ == "__main__":
    app.run(debug=True)
