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

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = os.urandom(24)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_db']
videos_col = db['videos']

# --- ২. প্রিমিয়াম ডার্ক ডিজাইন (CSS) ---
DESIGN = """
<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;700&display=swap" rel="stylesheet">
<style>
    body { background-color: #0f172a; color: #f8fafc; font-family: 'Inter', sans-serif; }
    .navbar { background: rgba(30, 41, 59, 0.9); backdrop-filter: blur(10px); border-bottom: 1px solid #334155; }
    .movie-card { background: #1e293b; border: 1px solid #334155; border-radius: 15px; overflow: hidden; transition: 0.3s; }
    .movie-card:hover { transform: scale(1.05); border-color: #38bdf8; box-shadow: 0 10px 20px rgba(0,0,0,0.3); }
    .movie-card img { width: 100%; height: 160px; object-fit: cover; }
    .btn-premium { background: #38bdf8; color: #0f172a; font-weight: bold; border-radius: 8px; padding: 10px 20px; text-decoration: none; display: inline-block; transition: 0.3s; }
    .btn-premium:hover { background: #7dd3fc; transform: translateY(-2px); }
    .detail-container { background: #1e293b; border-radius: 20px; padding: 30px; border: 1px solid #334155; margin-top: 50px; }
    .screenshot-img { width: 100%; border-radius: 10px; border: 1px solid #334155; margin-bottom: 10px; }
    .admin-card { background: #1e293b; border-radius: 10px; padding: 15px; margin-bottom: 10px; border-left: 5px solid #38bdf8; }
</style>
"""

# --- ৩. বট হ্যান্ডলার (Start & Auto-Add) ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    args = message.text.split()
    
    if len(args) > 1:
        # ওয়েবসাইট থেকে ডাউনলোডে ক্লিক করলে
        file_id = args[1]
        try:
            bot.send_video(chat_id, file_id, caption="🎬 **আপনার ভিডিওটি প্রস্তুত!** উপভোগ করুন।")
        except:
            bot.send_message(chat_id, "❌ ফাইলটি পাঠাতে সমস্যা হয়েছে।")
    else:
        # সরাসরি স্টার্ট দিলে
        welcome_msg = "👋 **মুভি পোর্টালে স্বাগতম!**\n\nমুভি ডাউনলোড করতে নিচের বাটনে ক্লিক করে আমাদের ওয়েবসাইট ভিজিট করুন।"
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, welcome_msg, reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def handle_channel_post(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "New Movie"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
        
        # ডিফল্ট থাম্বনেইল হিসেবে ভিডিওর অরিজিনাল থাম্বনেইল আইডি নেওয়া
        thumb_url = "https://via.placeholder.com/400x250.png?text=Preview+Available"
        
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb_url": thumb_url
        }
        res = videos_col.insert_one(data)
        
        # অ্যাডমিনকে নোটিফিকেশন
        log = f"✅ **নতুন ভিডিও অ্যাড হয়েছে!**\n📂 নাম: `{file_name}`\n🌐 লিঙ্ক: {SITE_URL}/view/{res.inserted_id}"
        bot.send_message(OWNER_ID, log, parse_mode="Markdown")

# --- ৪. ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    movies_html = ""
    for v in videos:
        movies_html += f'''
        <div class="col-6 col-md-3 mb-4">
            <div class="movie-card h-100">
                <img src="{v.get('thumb_url')}">
                <div class="p-3 text-center">
                    <h6 class="text-truncate">{v['file_name']}</h6>
                    <a href="/view/{v['_id']}" class="btn-premium w-100 mt-2">Details</a>
                </div>
            </div>
        </div>'''
    
    return f"""
    {DESIGN}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-info">MOVIE PORTAL</h3></div></nav>
    <div class="container mt-5"><div class="row">{movies_html if movies_html else "<h4>কোনো মুভি পাওয়া যায়নি।</h4>"}</div></div>
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
            <div class="col-md-8 detail-container">
                <img src="{video.get('thumb_url')}" class="img-fluid rounded mb-4 w-100">
                <h2>{video['file_name']}</h2>
                <p class="text-info">Size: {video.get('file_size')}</p>
                <hr style="border-color:#334155">
                <h4>Screenshots</h4>
                <div class="row g-2 mb-4">
                    <div class="col-6"><img src="{video.get('thumb_url')}" class="screenshot-img"></div>
                    <div class="col-6"><img src="{video.get('thumb_url')}" class="screenshot-img"></div>
                </div>
                <a href="{download_url}" class="btn-premium btn-lg w-100 text-center">📥 Download via Bot</a>
                <div class="mt-4 text-center"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
            </div>
        </div>
    </div>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pass') == ADMIN_PASSWORD:
        session['is_admin'] = True
    if not session.get('is_admin'):
        return f'{DESIGN}<div class="container mt-5 w-50 p-5 detail-container"><form method="post"><h4>Admin Login</h4><input type="password" name="pass" class="form-control mb-3"><button class="btn btn-info w-100">Login</button></form></div>'
    
    videos = list(videos_col.find().sort("_id", -1))
    list_html = ""
    for v in videos:
        list_html += f'<div class="admin-card d-flex justify-content-between"><span>{v["file_name"]}</span><a href="/del/{v["_id"]}" class="text-danger">Delete</a></div>'
    
    return f'{DESIGN}<div class="container mt-5"><h3>Admin Panel</h3><br>{list_html}</div>'

@app.route('/del/<id>')
def delete(id):
    if session.get('is_admin'): videos_col.delete_one({"_id": ObjectId(id)})
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

# Vercel-এর জন্য এক্সপোর্ট
def handler(event, context):
    return app(event, context)

if __name__ == "__main__":
    app.run()
