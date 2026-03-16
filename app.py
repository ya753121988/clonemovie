import os
import telebot
from flask import Flask, request, render_template_string, redirect, session
from pymongo import MongoClient
from bson import ObjectId

# --- কনফিগারেশন ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_db']
videos_col = db['videos']

# --- প্রিমিয়াম ডার্ক ডিজাইন (CSS) ---
DESIGN = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<style>
    body { background-color: #080d17; color: #ffffff; font-family: 'Segoe UI', sans-serif; }
    .navbar { background: #0f172a; border-bottom: 1px solid #1e293b; padding: 15px; }
    .movie-card { background: #111827; border: 1px solid #1e293b; border-radius: 15px; overflow: hidden; transition: 0.3s; }
    .movie-card:hover { transform: scale(1.05); border-color: #38bdf8; box-shadow: 0 0 20px rgba(56, 189, 248, 0.2); }
    .movie-card img { width: 100%; height: 280px; object-fit: cover; }
    .movie-title { font-size: 14px; font-weight: bold; margin: 10px 0; padding: 0 10px; height: 40px; overflow: hidden; }
    .btn-premium { background: linear-gradient(90deg, #38bdf8, #818cf8); color: white; font-weight: bold; border-radius: 8px; padding: 12px; text-decoration: none; display: block; width: 100%; text-align: center; border: none; }
    .detail-box { background: #0f172a; border-radius: 20px; padding: 30px; border: 1px solid #1e293b; margin-top: 40px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .ss-container img { width: 100%; border-radius: 10px; border: 1px solid #1e293b; margin-bottom: 10px; }
</style>
"""

# --- বট হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    args = message.text.split()
    if len(args) > 1:
        file_id = args[1] # ওই লম্বা আইডিটি এখানে রিসিভ হবে
        try:
            bot.send_video(message.chat.id, file_id, caption="🎬 **আপনার ভিডিওটি প্রস্তুত!**")
        except:
            bot.send_message(message.chat.id, "❌ দুঃখিত, ফাইলটি পাঠানো সম্ভব হচ্ছে না।")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(message.chat.id, "👋 **মুভি পোর্টালে স্বাগতম!**\n\nমুভি ডাউনলোড করতে নিচের বাটনে ক্লিক করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def handle_forward(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "New Movie"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024*1024), 2)} MB"
        
        # ভিডিওর থাম্বনেইল আইডি নেওয়া (এটিই স্ক্রিনশট হিসেবে কাজ করবে)
        thumb_id = "https://via.placeholder.com/400x600?text=No+Poster"
        if message.video.thumbnail:
            # থাম্বনেইলের ফাইল আইডি ডাটাবেসে সেভ হবে
            thumb_id = message.video.thumbnail.file_id
            
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb_id": thumb_id
        }
        res = videos_col.insert_one(data)
        
        # নোটিফিকেশন পাঠানো
        bot.send_message(OWNER_ID, f"✅ **সফলভাবে সাইটে অ্যাড হয়েছে!**\n📂 `{file_name}`\n🌐 লিঙ্ক: {SITE_URL}/view/{res.inserted_id}")

# --- ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    movies_html = ""
    for v in videos:
        # থাম্বনেইল দেখানোর জন্য টেলিগ্রামের ফাইল আইডি ব্যবহার করার ট্রিক (Placeholder if id)
        poster = "https://via.placeholder.com/400x600?text=Movie+Poster"
        movies_html += f'''
        <div class="col-6 col-md-3 mb-4">
            <div class="movie-card">
                <img src="{poster}">
                <div class="movie-title">{v['file_name']}</div>
                <div class="p-2"><a href="/view/{v['_id']}" class="btn-premium">View Details</a></div>
            </div>
        </div>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h4 style="color:#38bdf8; margin:0 auto;">PREMIUM MOVIES</h4></div></nav>
    <div class="container mt-5"><div class="row">{movies_html if movies_html else "<h4>কোনো মুভি নেই।</h4>"}</div></div>
    """

@app.route('/view/<id>')
def view(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File not found"
    
    bot_info = bot.get_me()
    dl_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    return f"""
    {DESIGN}
    <div class="container">
        <div class="row justify-content-center">
            <div class="col-md-8 detail-box text-center">
                <img src="https://via.placeholder.com/600x400?text=Movie+Preview" class="img-fluid rounded mb-4 w-100">
                <h2 class="mb-3">{video['file_name']}</h2>
                <p class="text-info">Size: {video.get('file_size')}</p>
                <hr style="border-color:#1e293b">
                <h4 class="text-start mb-3">Screenshots</h4>
                <div class="row g-2 ss-container">
                    <div class="col-6"><img src="https://via.placeholder.com/400x250/0f172a/ffffff?text=Screen+1"></div>
                    <div class="col-6"><img src="https://via.placeholder.com/400x250/0f172a/ffffff?text=Screen+2"></div>
                </div>
                <br>
                <a href="{dl_url}" class="btn-premium py-3 px-5 mt-3 fs-5">📥 Download via Bot</a>
                <div class="mt-4"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
            </div>
        </div>
    </div>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('p') == ADMIN_PASSWORD:
        session['adm'] = True
    if not session.get('adm'):
        return f'{DESIGN}<div class="container mt-5 text-center"><form method="post" class="detail-box mx-auto w-50"><h4>Login</h4><input type="password" name="p" class="form-control mb-3"><button class="btn-premium">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("_id", -1))
    list_html = ""
    for v in videos:
        list_html += f'<div class="d-flex justify-content-between border-bottom p-2"><span>{v["file_name"]}</span><a href="/del/{v["_id"]}" class="text-danger">Delete</a></div>'
    return f"{DESIGN}<div class='container mt-5 detail-box'><h3>Admin Panel</h3>{list_html}</div>"

@app.route('/del/<id>')
def delete(id):
    if session.get('adm'): videos_col.delete_one({"_id": ObjectId(id)})
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
    bot.set_webhook(url=f"{SITE_URL}/webhook")
    return "<h1>Webhook Setup Successful!</h1>"

# Vercel Handler
def handler(event, context):
    return app(event, context)
