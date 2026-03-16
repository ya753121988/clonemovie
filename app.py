import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId

# --- ১. কনফিগারেশন ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = "movie_portal_key_v5"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f9; margin: 0; text-align: center; }
    header { background: #0088cc; color: white; padding: 20px; font-size: 24px; font-weight: bold; }
    .container { display: flex; flex-wrap: wrap; justify-content: center; padding: 20px; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; transition: 0.3s; }
    .card:hover { transform: translateY(-5px); }
    .card img { width: 100%; height: 130px; object-fit: cover; background: #333; }
    .btn { background: #0088cc; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; margin: 10px; }
    .btn-download { background: #28a745; padding: 15px 35px; font-size: 20px; color: white; border-radius: 10px; text-decoration: none; display: inline-block; }
</style>
"""

# --- ৩. বট হ্যান্ডলার (Start & Auto-Add) ---

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    text = message.text.split()
    
    # যদি ওয়েবসাইট থেকে ডাউনলোড রিকোয়েস্ট আসে
    if len(text) > 1:
        file_id = text[1]
        bot.send_video(chat_id, file_id, caption="✨ আপনার ভিডিওটি নিচে দেওয়া হলো। উপভোগ করুন!")
    else:
        # সাধারণ স্টার্ট মেসেজ বাটনসহ
        welcome_text = "👋 **মুভি পোর্টালে স্বাগতম!**\n\nমুভি ডাউনলোড করতে নিচের বাটনে ক্লিক করে সাইট ভিজিট করুন।"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def handle_channel_video(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "New Movie"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
        
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb_url": "https://via.placeholder.com/400x250.png?text=New+Movie+Added"
        }
        res = videos_col.insert_one(data)
        
        # আপনাকে নোটিফিকেশন পাঠানো
        log_text = f"✅ নতুন ভিডিও সাইটে অ্যাড হয়েছে!\n\n📂 {file_name}\n🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
        bot.send_message(OWNER_ID, log_text, parse_mode="Markdown")

# --- ৪. ওয়েব হুক ও সেটআপ ---

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
    if success:
        return "<h1>✅ Webhook Setup Successful!</h1>"
    else:
        return "<h1>❌ Webhook Setup Failed!</h1>"

# --- ৫. ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Movie Portal</header><div class='container'>"
    for v in videos:
        html += f"""
        <div class='card'>
            <img src='{v.get('thumb_url')}'>
            <div style='padding:10px;'>
                <p><b>{v['file_name'][:30]}...</b></p>
                <a href='/details/{v["_id"]}' class='btn'>Details</a>
            </div>
        </div>
        """
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File not found"
    
    # বটের ইউজারনেম বের করা
    bot_info = bot.get_me()
    dl_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    html = f"{CSS}<header>Movie Details</header><div style='padding:40px;'>"
    html += f"""
        <img src='{video.get('thumb_url')}' style='width:100%; max-width:500px; border-radius:15px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
        <h2>{video['file_name']}</h2>
        <p>Size: {video.get('file_size')}</p>
        <br>
        <a href='{dl_url}' class='btn-download'>📥 ডাউনলোড করুন (টেলিগ্রাম বটের মাধ্যমে)</a>
        <br><br><a href='/' style='text-decoration:none;'>← হোম পেজে ফিরে যান</a>
    </div>
    """
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pass') == ADMIN_PASSWORD:
        session['admin'] = True
    if not session.get('admin'):
        return "<form method='post'>Password: <input type='password' name='pass'><button>Login</button></form>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = "<h1>Admin Panel</h1>"
    for v in videos:
        html += f"<p>{v['file_name']} <a href='/delete/{v['_id']}'>[Delete]</a></p>"
    return html

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# Vercel Handler
def handler(event, context):
    return app(event, context)

if __name__ == "__main__":
    app.run()
