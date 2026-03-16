import os
import telebot
from flask import Flask, request, redirect, session, url_for
from pymongo import MongoClient

# --- কনফিগারেশন ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = "movie_portal_super_secret_key"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_portal']
videos_col = db['movies']

# --- প্রিমিয়াম ডার্ক ডিজাইন (CSS সহ সম্পূর্ণ HTML) ---
DESIGN_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Movie Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080b12; color: #e5e7eb; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .navbar { background: #111827; border-bottom: 2px solid #3b82f6; padding: 15px; sticky: top; }
        .card-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 30px; }
        .movie-card { background: #1f2937; border-radius: 15px; overflow: hidden; width: 220px; transition: 0.3s; border: 1px solid #374151; text-decoration: none; color: white; display: block; }
        .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3); }
        .movie-card img { width: 100%; height: 280px; object-fit: cover; }
        .btn-dl { background: linear-gradient(90deg, #2563eb, #7c3aed); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: bold; width: 100%; text-decoration: none; display: block; text-align: center; font-size: 16px; }
        .detail-card { background: #111827; border-radius: 20px; padding: 30px; border: 1px solid #374151; max-width: 500px; margin: 40px auto; }
        .admin-item { background: #1f2937; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #374151; }
    </style>
</head>
<body>
"""

# --- টেলিগ্রাম বট হ্যান্ডলার (Message ID Logic) ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    command_args = message.text.split()
    
    # যদি স্টার্ট লিঙ্কে আইডি থাকে (যেমন: /start 10)
    if len(command_args) > 1:
        msg_id = command_args[1]
        try:
            # সরাসরি চ্যানেল থেকে মেসেজটি কপি করে ইউজারের ইনবক্সে পাঠানো
            bot.copy_message(chat_id, CHANNEL_ID, int(msg_id))
        except Exception as e:
            bot.send_message(chat_id, "❌ ফাইলটি পাওয়া যায়নি! সম্ভবত এটি চ্যানেল থেকে ডিলেট করা হয়েছে।")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, "👋 **স্বাগতম!**\n\nমুভি ডাউনলোড করতে আমাদের ওয়েবসাইট থেকে লিঙ্কে ক্লিক করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video', 'document'])
def handle_channel_post(message):
    # চ্যানেল পোস্ট থেকে মেসেজ আইডি এবং নাম সেভ করা
    msg_id = message.message_id
    file_name = "New Movie File"
    if message.video:
        file_name = message.video.file_name or message.caption or "Video_File"
    elif message.document:
        file_name = message.document.file_name or message.caption or "Document_File"

    data = {
        "file_name": file_name,
        "msg_id": msg_id,
        "thumb": "https://via.placeholder.com/400x600/080b12/ffffff?text=Premium+Movie"
    }
    # ডাটাবেসে সেভ (যদি আইডি এক হয় তবে আপডেট হবে)
    videos_col.update_one({"msg_id": msg_id}, {"$set": data}, upsert=True)
    
    # বটের মালিককে অ্যালার্ট পাঠানো
    bot.send_message(OWNER_ID, f"✅ **নতুন মুভি অ্যাড হয়েছে!**\n📂 নাম: {file_name}\n🆔 আইডি: {msg_id}\n🌐 লিঙ্ক: {SITE_URL}/view/{msg_id}")

# --- ফ্লাস্ক ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("msg_id", -1))
    movies_html = ""
    for v in videos:
        movies_html += f'''
        <a href="/view/{v['msg_id']}" class="movie-card">
            <img src="{v.get('thumb')}">
            <div class="p-3 text-center">
                <h6 class="text-truncate">{v['file_name']}</h6>
                <small class="text-secondary">ID: {v['msg_id']}</small>
            </div>
        </a>'''
    
    return f"""
    {DESIGN_HEAD}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-primary">MOVIE PORTAL</h3></div></nav>
    <div class="card-container">
        {movies_html if movies_html else '<h4 class="text-center">No movies found. Please forward a video to your channel.</h4>'}
    </div>
    </body></html>
    """

@app.route('/view/<msg_id>')
def view(msg_id):
    try:
        video = videos_col.find_one({"msg_id": int(msg_id)})
    except:
        return "Invalid ID Format"
        
    if not video: return "Movie Not Found in Database"
    
    bot_info = bot.get_me()
    # এখানে আমরা ডাটাবেস থেকে পাওয়া মেসেজ আইডি ব্যবহার করছি
    download_url = f"https://t.me/{bot_info.username}?start={msg_id}"
    
    return f"""
    {DESIGN_HEAD}
    <div class="container">
        <div class="detail-card text-center">
            <img src="{video.get('thumb')}" class="img-fluid rounded mb-4 shadow-lg">
            <h2 class="mb-3">{video['file_name']}</h2>
            <p class="text-secondary">Message ID: {msg_id}</p>
            <hr style="border-color: #374151;">
            <a href="{download_url}" class="btn-dl py-3 fs-5">📥 Get File via Telegram Bot</a>
            <div class="mt-4"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
        </div>
    </div>
    </body></html>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
    
    if not session.get('is_admin'):
        return f"""
        {DESIGN_HEAD}
        <div class="container mt-5 w-50">
            <div class="detail-card">
                <h4 class="mb-3 text-center">Admin Login</h4>
                <form method="post">
                    <input type="password" name="password" class="form-control mb-3 bg-dark text-white border-secondary" placeholder="Enter Password">
                    <button type="submit" class="btn-dl">Login</button>
                </form>
            </div>
        </div>
        </body></html>
        """
    
    videos = list(videos_col.find().sort("msg_id", -1))
    rows = ""
    for v in videos:
        rows += f'''
        <div class="admin-item">
            <span>{v["file_name"]} (ID: {v["msg_id"]})</span>
            <a href="/del/{v["msg_id"]}" class="btn btn-danger btn-sm">Delete</a>
        </div>'''
        
    return f"""
    {DESIGN_HEAD}
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h3>Admin Panel</h3>
            <a href="/" class="btn btn-secondary btn-sm">View Site</a>
        </div>
        <hr style="border-color: #374151;">
        {rows if rows else '<p>No data available.</p>'}
    </div>
    </body></html>
    """

@app.route('/del/<msg_id>')
def delete(msg_id):
    if session.get('is_admin'):
        videos_col.delete_one({"msg_id": int(msg_id)})
    return redirect(url_for('admin'))

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
    return f"<h1>{'✅ Webhook Success!' if success else '❌ Webhook Failed!'}</h1>"

@app.route('/favicon.ico')
def favicon():
    return '', 200

# Vercel-এর জন্য app অবজেক্ট প্রয়োজন
if __name__ == "__main__":
    app.run(debug=True)
