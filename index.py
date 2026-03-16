import os
import telebot
from flask import Flask, request, redirect, session, url_for
from pymongo import MongoClient

# --- কনফিগারেশন (আপনার দেওয়া ডাটা) ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask অ্যাপ তৈরি
app = Flask(__name__)
app.secret_key = "any_random_secret_key"

# টেলিগ্রাম বট সেটআপ
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# ডাটাবেস সেটআপ
try:
    client = MongoClient(MONGO_URI, connectTimeoutMS=5000, serverSelectionTimeoutMS=5000)
    db = client['premium_movie_portal']
    videos_col = db['movies']
except Exception as e:
    print(f"Database Connection Error: {e}")

# --- ডিজাইন ---
DESIGN = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080b12; color: #e5e7eb; font-family: sans-serif; }
        .navbar { background: #111827; border-bottom: 2px solid #3b82f6; padding: 15px; }
        .card-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 20px; }
        .movie-card { background: #1f2937; border-radius: 12px; overflow: hidden; width: 200px; border: 1px solid #374151; text-decoration: none; color: white; transition: 0.3s; }
        .movie-card:hover { transform: scale(1.05); border-color: #3b82f6; }
        .movie-card img { width: 100%; height: 260px; object-fit: cover; }
        .btn-dl { background: #3b82f6; color: white; border: none; padding: 12px; border-radius: 8px; width: 100%; display: block; text-align: center; font-weight: bold; text-decoration: none; }
        .detail-card { background: #111827; border-radius: 15px; padding: 25px; border: 1px solid #374151; max-width: 450px; margin: 40px auto; }
    </style>
</head>
<body>
"""

# --- বট হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def start_cmd(message):
    chat_id = message.chat.id
    text = message.text.split()
    
    if len(text) > 1:
        msg_id = text[1] # যেমন: ১০
        try:
            bot.copy_message(chat_id, CHANNEL_ID, int(msg_id))
        except:
            bot.send_message(chat_id, "❌ ফাইলটি পাওয়া যায়নি।")
    else:
        btn = telebot.types.InlineKeyboardMarkup()
        btn.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট", url=SITE_URL))
        bot.send_message(chat_id, "👋 মুভি ডাউনলোড করতে ওয়েবসাইট ভিজিট করুন।", reply_markup=btn)

@bot.channel_post_handler(content_types=['video', 'document'])
def channel_msg(message):
    msg_id = message.message_id
    file_name = "New Movie"
    if message.video: file_name = message.video.file_name or "Video File"
    elif message.document: file_name = message.document.file_name or "Document File"
    
    videos_col.update_one({"msg_id": msg_id}, {"$set": {"msg_id": msg_id, "file_name": file_name, "thumb": "https://via.placeholder.com/400x600/080b12/ffffff?text=Movie"}}, upsert=True)
    bot.send_message(OWNER_ID, f"✅ মুভি অ্যাড হয়েছে!\n📂 {file_name}\n🌐 {SITE_URL}/view/{msg_id}")

# --- ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("msg_id", -1))
    html = f"{DESIGN}<nav class='navbar'><h3 class='text-center w-100 text-primary'>MOVIE PORTAL</h3></nav><div class='card-container'>"
    for v in videos:
        html += f'<a href="/view/{v["msg_id"]}" class="movie-card"><img src="{v["thumb"]}"><div class="p-2 text-center text-truncate">{v["file_name"]}</div></a>'
    return html + "</div></body></html>"

@app.route('/view/<int:msg_id>')
def view(msg_id):
    video = videos_col.find_one({"msg_id": msg_id})
    if not video: return "Not Found"
    bot_user = bot.get_me().username
    return f"""{DESIGN}<div class="container"><div class="detail-card text-center">
    <img src="{video['thumb']}" class="img-fluid rounded mb-3">
    <h3>{video['file_name']}</h3>
    <a href="https://t.me/{bot_user}?start={msg_id}" class="btn-dl">📥 Get File in Telegram</a>
    <a href="/" class="d-block mt-3 text-secondary text-decoration-none">← Back</a>
    </div></div></body></html>"""

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('p') == ADMIN_PASSWORD:
        session['logged_in'] = True
    if not session.get('logged_in'):
        return f"{DESIGN}<div class='detail-card'><form method='post'><h4>Admin Login</h4><input type='password' name='p' class='form-control mb-2'><button class='btn-dl'>Login</button></form></div>"
    
    videos = list(videos_col.find().sort("msg_id", -1))
    rows = "".join([f"<div class='p-2 border-bottom d-flex justify-content-between'><span>{v['file_name']}</span><a href='/del/{v['msg_id']}' class='text-danger'>Delete</a></div>" for v in videos])
    return f"{DESIGN}<div class='container mt-4'><h3>Admin Panel</h3>{rows}</div></body></html>"

@app.route('/del/<int:msg_id>')
def delete(msg_id):
    if session.get('logged_in'): videos_col.delete_one({"msg_id": msg_id})
    return redirect('/admin')

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_str = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/setup')
def setup():
    bot.remove_webhook()
    s = bot.set_webhook(url=f"{SITE_URL}/webhook")
    return "✅ Webhook Connected!" if s else "❌ Failed!"

@app.route('/favicon.ico')
def favicon(): return '', 200

# Vercel-এর জন্য app সরাসরি থাকতে হবে
