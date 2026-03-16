import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient

# --- কনফিগারেশন (বিন্দু পরিমান পরিবর্তন ছাড়াই আপনার তথ্য দেওয়া আছে) ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = "premium_movie_portal_secret_key"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_portal']
videos_col = db['movies']

# --- প্রিমিয়াম ডিজাইন (একদম সম্পূর্ণ CSS সহ) ---
DESIGN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080b12; color: #e5e7eb; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .navbar { background: #111827; border-bottom: 2px solid #3b82f6; padding: 15px; position: sticky; top: 0; z-index: 1000; }
        .card-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 30px; }
        .movie-card { background: #1f2937; border-radius: 15px; overflow: hidden; width: 220px; transition: 0.3s; border: 1px solid #374151; text-decoration: none; color: white; display: block; }
        .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3); }
        .movie-card img { width: 100%; height: 280px; object-fit: cover; }
        .btn-dl { background: linear-gradient(90deg, #2563eb, #7c3aed); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: bold; width: 100%; text-decoration: none; display: block; text-align: center; font-size: 16px; }
        .btn-dl:hover { color: white; opacity: 0.9; }
        .detail-card { background: #111827; border-radius: 20px; padding: 30px; border: 1px solid #374151; max-width: 500px; margin: 40px auto; box-shadow: 0 0 20px rgba(0,0,0,0.5); }
        .admin-item { background: #1f2937; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #374151; }
        .text-truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    </style>
</head>
<body>
"""

# --- টেলিগ্রাম বট লজিক (Message ID ভিত্তিক) ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    command_parts = message.text.split()
    
    # যদি লিঙ্কে মেসেজ আইডি থাকে (যেমন: /start 10)
    if len(command_parts) > 1:
        msg_id = command_parts[1]
        try:
            # সরাসরি চ্যানেল থেকে মেসেজ আইডি অনুযায়ী কপি করে পাঠানো
            bot.copy_message(chat_id, CHANNEL_ID, int(msg_id))
        except Exception as e:
            bot.send_message(chat_id, "❌ দুঃখিত! এই ফাইলটি পাওয়া যায়নি বা চ্যানেল থেকে ডিলেট করা হয়েছে।")
    else:
        # সাধারণ স্টার্ট মেসেজ
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, "👋 **মুভি পোর্টালে স্বাগতম!**\n\nমুভি ডাউনলোড করতে নিচের বাটনে ক্লিক করে আমাদের ওয়েবসাইট ভিজিট করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video', 'document'])
def handle_channel_post(message):
    # চ্যানেল থেকে মেসেজ আইডি এবং নাম সেভ করা
    msg_id = message.message_id
    file_name = "New Movie"
    
    if message.video:
        file_name = message.video.file_name or message.caption or "Movie_File"
    elif message.document:
        file_name = message.document.file_name or message.caption or "Document_File"
        
    data = {
        "file_name": file_name,
        "msg_id": msg_id,
        "thumb": "https://via.placeholder.com/400x600/080b12/ffffff?text=Premium+Movie"
    }
    # ডাটাবেসে সেভ (যদি আগে না থাকে)
    videos_col.update_one({"msg_id": msg_id}, {"$set": data}, upsert=True)
    
    # ওনারকে অ্যালার্ট দেওয়া
    bot.send_message(OWNER_ID, f"✅ **মুভি অ্যাড হয়েছে!**\n📂 নাম: {file_name}\n🆔 আইডি: {msg_id}\n🌐 লিঙ্ক: {SITE_URL}/view/{msg_id}")

# --- ওয়েবসাইট রুটস ---

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
                <small class="text-secondary">Message ID: {v['msg_id']}</small>
            </div>
        </a>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-primary">MOVIE PORTAL</h3></div></nav>
    <div class="card-container">{movies_html if movies_html else '<h4 class="text-center">No movies found. Post to your channel first.</h4>'}</div>
    </body></html>
    """

@app.route('/view/<msg_id>')
def view(msg_id):
    video = videos_col.find_one({"msg_id": int(msg_id)})
    if not video: return "Movie Not Found"
    
    bot_info = bot.get_me()
    # লিঙ্কে মেসেজ আইডি ব্যবহার করা হয়েছে
    download_url = f"https://t.me/{bot_info.username}?start={msg_id}"
    
    return f"""
    {DESIGN}
    <div class="container">
        <div class="detail-card text-center">
            <img src="{video.get('thumb')}" class="img-fluid rounded mb-4" style="max-height:350px;">
            <h2 class="mb-3">{video['file_name']}</h2>
            <p class="text-secondary">চ্যানেল মেসেজ আইডি: {msg_id}</p>
            <hr style="border-color: #374151;">
            <a href="{download_url}" class="btn-dl py-3 fs-5">📥 Get File via Telegram Bot</a>
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
        return f'{DESIGN}<div class="container mt-5 w-50 detail-card"><form method="post"><h4>Admin Login</h4><input type="password" name="p" class="form-control mb-3 bg-dark text-white" placeholder="Password"><button class="btn-dl">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("msg_id", -1))
    rows = ""
    for v in videos:
        rows += f'<div class="admin-item"><span>{v["file_name"]} (ID: {v["msg_id"]})</span><a href="/del/{v["msg_id"]}" class="btn btn-danger btn-sm text-white">Delete</a></div>'
    return f'{DESIGN}<div class="container mt-5"><h3>Admin Panel</h3><hr style="border-color: #374151;">{rows}</div></body></html>'

@app.route('/del/<msg_id>')
def delete(msg_id):
    if session.get('adm'):
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
    return "<h1>✅ Webhook Setup Successful!</h1>" if success else "<h1>❌ Setup Failed!</h1>"

@app.route('/favicon.ico')
def favicon():
    return '', 200

# Vercel Entry Point
if __name__ == "__main__":
    app.run(debug=True)
