import os
import json
import asyncio
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- ১. কনফিগারেশন ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask অ্যাপ
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB
db = MongoClient(MONGO_URI)['video_database']
videos_col = db['videos']

# Pyrogram Client (Webhook মোডের জন্য)
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f9; margin: 0; text-align: center; }
    header { background: #0088cc; color: white; padding: 20px; font-size: 24px; font-weight: bold; }
    .container { display: flex; flex-wrap: wrap; justify-content: center; padding: 20px; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
    .card img { width: 100%; height: 130px; object-fit: cover; }
    .btn { background: #0088cc; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; margin: 10px; }
    .btn-download { background: #28a745; padding: 15px 35px; font-size: 20px; color: white; border-radius: 10px; text-decoration: none; display: inline-block; }
</style>
"""

# --- ৩. বট লজিক (Start & Channel Forward) ---

async def handle_bot_updates(update):
    if isinstance(update, Message):
        chat_id = update.chat.id
        
        # স্টার্ট কমান্ড
        if update.text and update.text.startswith("/start"):
            args = update.text.split(" ")
            if len(args) > 1:
                # ওয়েবসাইট থেকে ডাউনলোডের জন্য আসলে
                file_id = args[1]
                await bot.send_video(chat_id, video=file_id, caption="🎥 আপনার মুভিটি নিচে দেওয়া হলো। উপভোগ করুন!")
            else:
                # সরাসরি বটে ঢুকলে
                welcome_text = (
                    "👋 **আমাদের মুভি পোর্টালে স্বাগতম!**\n\n"
                    "আপনি এখানে সব ধরনের লেটেস্ট মুভি ও ভিডিও পাবেন। মুভি লিস্ট দেখতে নিচের বাটনে ক্লিক করে আমাদের ওয়েবসাইট ভিজিট করুন।"
                )
                reply_markup = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL)
                ]])
                await bot.send_message(chat_id, welcome_text, reply_markup=reply_markup)

        # চ্যানেল থেকে ভিডিও অটো অ্যাড
        elif chat_id == CHANNEL_ID and update.video:
            file_name = update.video.file_name or "Untitled Movie"
            file_id = update.video.file_id
            file_size = f"{round(update.video.file_size / (1024 * 1024), 2)} MB"
            
            data = {
                "file_name": file_name,
                "file_id": file_id,
                "file_size": file_size,
                "thumb_url": "https://via.placeholder.com/400x250.png?text=New+Movie+Added"
            }
            res = videos_col.insert_one(data)
            
            # অ্যাডমিনকে নোটিফিকেশন
            log_text = f"✅ **নতুন ভিডিও সাইটে অ্যাড হয়েছে!**\n\n📂 নাম: `{file_name}`\n🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
            await bot.send_message(OWNER_ID, log_text)

# --- ৪. ওয়েব হুক ও সেটআপ রুট ---

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.is_json:
        update_data = request.get_json()
        async def run_logic():
            async with bot:
                update = Update.from_dict(update_data, bot)
                if update.message: await handle_bot_updates(update.message)
                elif update.channel_post: await handle_bot_updates(update.channel_post)
        asyncio.run(run_logic())
    return "OK", 200

@app.route('/setup')
def setup():
    async def set_webhook():
        async with bot:
            return await bot.set_webhook(f"{SITE_URL}/webhook")
    result = asyncio.run(set_webhook())
    return "<h1>Webhook Setup Successful!</h1>" if result else "<h1>Setup Failed!</h1>"

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
    if not videos: html += "<h3>No videos found. Forward from channel.</h3>"
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File not found"
    
    # বটের ইউজারনেম ছাড়া সরাসরি লিঙ্কের ট্রিক
    bot_raw_id = BOT_TOKEN.split(':')[0]
    bot_url = f"https://t.me/{(BOT_TOKEN.split(':')[0])}?start={video['file_id']}"
    
    html = f"{CSS}<header>Movie Details</header><div style='padding:30px;'>"
    html += f"""
        <img src='{video.get('thumb_url')}' style='width:100%; max-width:500px; border-radius:15px; box-shadow: 0 5px 15px rgba(0,0,0,0.2);'>
        <h2>{video['file_name']}</h2>
        <p>Size: {video.get('file_size')}</p>
        <br>
        <a href='https://t.me/share/url?url=https://t.me/bot?start={video["file_id"]}' id='download_btn' class='btn-download'>📥 ডাউনলোড করুন (টেলিগ্রাম বটে)</a>
        <br><br><a href='/' style='text-decoration:none;'>← হোম পেজে ফিরে যান</a>
    </div>
    <script>
        // বটের সঠিক লিঙ্ক সেট করার ট্রিক
        var bot_username = "{BOT_TOKEN.split(':')[0]}"; // এটি বটের আইডি, সরাসরি ইউজারনেম দিলে ভালো হয়
        document.getElementById('download_btn').onclick = function() {{
            window.location.href = "https://t.me/" + "YourBotUsername" + "?start=" + "{video['file_id']}";
            return false;
        }};
    </script>
    """
    # নোট: "YourBotUsername" এর জায়গায় আপনার বটের ইউজারনেম (যেমন: MyMovieBot) লিখে দিন।
    return html.replace("YourBotUsername", "Movie_Downloader_Bot") # আপনার বটের আসল ইউজারনেম দিন এখানে

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pass') == ADMIN_PASSWORD:
        session['admin'] = True
    if not session.get('admin'):
        return "<form method='post'>Pass: <input type='password' name='pass'><button>Login</button></form>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = "<h1>Admin Panel</h1>"
    for v in videos:
        html += f"<p>{v['file_name']} <a href='/delete/{v['_id']}'>[Delete]</a></p>"
    return html

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# Vercel entry point (এটি খুবই গুরুত্বপূর্ণ এরর দূর করার জন্য)
app.debug = False

if __name__ == "__main__":
    app.run()
