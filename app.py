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

# Flask ও Bot সেটআপ
app = Flask(__name__)
app.secret_key = "movie_portal_secret"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB সেটআপ
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# --- CSS ডিজাইন ---
CSS = """
<style>
    body { font-family: sans-serif; background: #f0f2f5; margin: 0; text-align: center; }
    header { background: #0088cc; color: white; padding: 20px; font-size: 22px; font-weight: bold; }
    .container { display: flex; flex-wrap: wrap; justify-content: center; padding: 20px; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); overflow: hidden; }
    .card img { width: 100%; height: 130px; object-fit: cover; }
    .btn { background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }
</style>
"""

# --- বট হ্যান্ডলার ---

@bot.message_handler(commands=['start'])
def start_msg(message):
    text_parts = message.text.split()
    if len(text_parts) > 1:
        file_id = text_parts[1]
        bot.send_video(message.chat.id, file_id, caption="🎬 আপনার ভিডিওটি এখানে!")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(message.chat.id, "👋 স্বাগতম! মুভি ডাউনলোড করতে ওয়েবসাইট দেখুন।", reply_markup=markup)

@bot.channel_post_handler(content_types=['video'])
def handle_channel(message):
    if message.chat.id == CHANNEL_ID:
        data = {
            "file_name": message.video.file_name or "New Movie",
            "file_id": message.video.file_id,
            "file_size": f"{round(message.video.file_size / (1024*1024), 2)} MB",
            "thumb_url": "https://via.placeholder.com/400x250.png?text=New+Movie"
        }
        res = videos_col.insert_one(data)
        log = f"✅ নতুন মুভি অ্যাড হয়েছে!\n📂 {data['file_name']}\n🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
        bot.send_message(OWNER_ID, log)

# --- ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Movie Portal</header><div class='container'>"
    for v in videos:
        html += f"<div class='card'><img src='{v.get('thumb_url')}'><div style='padding:10px;'><p>{v['file_name'][:30]}</p><a href='/details/{v['_id']}' class='btn'>Details</a></div></div>"
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইল পাওয়া যায়নি"
    bot_info = bot.get_me()
    dl_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    html = f"{CSS}<header>Details</header><div style='padding:30px;'><img src='{video.get('thumb_url')}' style='width:300px; border-radius:10px;'><h2>{video['file_name']}</h2><p>Size: {video.get('file_size')}</p><a href='{dl_url}' class='btn' style='background:green;'>📥 ডাউনলোড করুন</a><br><br><a href='/'>হোমে ফিরুন</a></div>"
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('p') == ADMIN_PASSWORD:
        session['a'] = True
    if not session.get('a'):
        return "<form method='post'>Pass: <input type='password' name='p'><button>Login</button></form>"
    videos = list(videos_col.find().sort("_id", -1))
    h = "<h1>Admin</h1>"
    for v in videos:
        h += f"<p>{v['file_name']} <a href='/delete/{v['_id']}'>[Delete]</a></p>"
    return h

@app.route('/delete/<id>')
def delete(id):
    if session.get('a'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# --- Webhook & Setup ---

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

# Vercel-এর জন্য শুধু app ব্যবহার করলেই হয়
# এখানে কোনো handler ফাংশন দরকার নেই
