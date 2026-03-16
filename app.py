import os
import json
import asyncio
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- ১. কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask অ্যাপ সেটআপ
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB সেটআপ
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# Pyrogram বট সেটআপ (Webhook মোডে ব্যবহারের জন্য)
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; margin: 0; padding: 0; color: #333; }
    header { background: #0088cc; color: white; padding: 20px; text-align: center; font-size: 26px; font-weight: bold; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .container { max-width: 1200px; margin: 20px auto; padding: 10px; display: flex; flex-wrap: wrap; justify-content: center; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: 0.3s; }
    .card:hover { transform: translateY(-5px); }
    .card img { width: 100%; height: 140px; object-fit: cover; background: #222; }
    .card-body { padding: 15px; text-align: center; }
    .card-title { font-size: 15px; font-weight: bold; margin-bottom: 10px; height: 35px; overflow: hidden; }
    .btn { background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; border: none; }
    .btn-download { background: #28a745; font-size: 20px; padding: 15px 35px; color: white; border-radius: 10px; text-decoration: none; display: inline-block; box-shadow: 0 4px 12px rgba(40,167,69,0.3); }
    .admin-list { max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 10px; text-align: left; }
    .admin-item { border-bottom: 1px solid #eee; padding: 10px; display: flex; justify-content: space-between; align-items: center; }
</style>
"""

# --- ৩. টেলিগ্রাম বট লজিক (Start & Notification) ---

async def handle_bot_logic(update):
    if isinstance(update, Message):
        chat_id = update.chat.id

        # স্টার্ট কমান্ড
        if update.text and update.text.startswith("/start"):
            args = update.text.split(" ")
            
            # সাইট থেকে ডাউনলোডের জন্য আসলে
            if len(args) > 1:
                file_id = args[1]
                await bot.send_video(chat_id, video=file_id, caption="🎬 আপনার ভিডিওটি প্রস্তুত! উপভোগ করুন।")
            
            # সরাসরি স্টার্ট দিলে
            else:
                welcome_text = (
                    "👋 **আমাদের মুভি বক্সে স্বাগতম!**\n\n"
                    "আপনি কি লেটেস্ট মুভি বা ভিডিও খুঁজছেন? আমাদের ওয়েবসাইটে রয়েছে বিশাল কালেকশন। "
                    "নিচের বাটনে ক্লিক করে সরাসরি আমাদের ওয়েবসাইট ভিজিট করুন।"
                )
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL)
                ]])
                await bot.send_message(chat_id, welcome_text, reply_markup=keyboard)

        # চ্যানেল থেকে ভিডিও আসলে (অটো অ্যাড)
        elif chat_id == CHANNEL_ID and update.video:
            file_name = update.video.file_name or "Untitled_Video"
            file_id = update.video.file_id
            file_size = f"{round(update.video.file_size / (1024 * 1024), 2)} MB"
            
            # ডাটাবেসে সেভ
            video_data = {
                "file_name": file_name,
                "file_id": file_id,
                "file_size": file_size,
                "thumb_url": "https://via.placeholder.com/400x250.png?text=Video+Thumbnail"
            }
            res = videos_col.insert_one(video_data)
            
            # অ্যাডমিনকে নোটিফিকেশন পাঠানো
            log_text = f"✅ **নতুন ভিডিও অ্যাড হয়েছে!**\n\n📂 নাম: `{file_name}`\n🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
            await bot.send_message(OWNER_ID, log_text)

# --- ৪. ফ্ল্যাক্স ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Movie Portal</header><div class='container'>"
    for v in videos:
        thumb = v.get('thumb_url', 'https://via.placeholder.com/300x150?text=Movie')
        html += f"""
        <div class='card'>
            <img src='{thumb}'>
            <div class='card-body'>
                <div class='card-title'>{v['file_name'][:40]}</div>
                <a href='/details/{v["_id"]}' class='btn'>View Details</a>
            </div>
        </div>
        """
    if not videos: html += "<h3>কোনো ভিডিও পাওয়া যায়নি। চ্যানেলে ভিডিও দিন।</h3>"
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইলটি পাওয়া যায়নি!"
    
    # বটের ইউজারনেম বের করার ট্রিক
    bot_id = BOT_TOKEN.split(':')[0]
    download_url = f"https://t.me/{(BOT_TOKEN.split(':')[0])}?start={video['file_id']}"
    
    html = f"{CSS}<header>Video Details</header><div style='padding:40px;'>"
    html += f"""
        <img src='{video.get('thumb_url')}' style='width:100%; max-width:600px; border-radius:15px; box-shadow: 0 5px 20px rgba(0,0,0,0.1);'>
        <h2>{video['file_name']}</h2>
        <p style='font-size:18px;'>ফাইল সাইজ: {video.get('file_size')}</p>
        <hr style='width:50%; margin:20px auto;'>
        <h3>Screenshots (Preview)</h3>
        <p>ভিডিওটি সরাসরি টেলিগ্রাম বটে পেতে নিচের ডাউনলোড বাটনে ক্লিক করুন।</p>
        <br>
        <a href='https://t.me/bot?start={video["file_id"]}' id='tg_link' class='btn-download'>📥 ডাউনলোড করুন</a>
        <br><br><a href='/' style='text-decoration:none; color:#0088cc;'>← হোম পেজে ফিরে যান</a>
    </div>
    <script>
        // বটের ইউজারনেম অটো সেট করা (ইউজার ক্লিক করলে বটের আইডিতে যাবে)
        document.getElementById('tg_link').href = "https://t.me/share/url?url=t.me/" + "{bot_id}" + "?start=" + "{video['file_id']}";
        // সহজ করার জন্য সরাসরি বটের লিঙ্কে পাঠিয়ে দিন
        document.getElementById('tg_link').href = "https://t.me/" + "{(BOT_TOKEN.split(':')[0])}" + "?start=" + "{video['file_id']}";
    </script>
    """
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['admin'] = True
    if not session.get('admin'):
        return f"{CSS}<div style='margin-top:100px;'><form method='post'>পাসওয়ার্ড: <input type='password' name='password'><button type='submit' class='btn'>Login</button></form></div>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Admin Panel</header><div class='admin-list'><h3>ফাইল ম্যানেজমেন্ট</h3>"
    for v in videos:
        html += f"<div class='admin-item'><span>{v['file_name']}</span><a href='/delete/{v['_id']}' style='color:red;'>ডিলিট</a></div>"
    return html + "</div>"

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# --- ৫. Webhook & Setup ---

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.is_json:
        data = request.get_json()
        async def run_update():
            async with bot:
                update = Update.from_dict(data, bot)
                if update.message: await handle_bot_logic(update.message)
                elif update.channel_post: await handle_bot_logic(update.channel_post)
        asyncio.run(run_update())
    return "OK", 200

@app.route('/setup')
def setup():
    async def set_webhook():
        async with bot:
            return await bot.set_webhook(f"{SITE_URL}/webhook")
    result = asyncio.run(set_webhook())
    return "✅ Webhook Setup Successful!" if result else "❌ Setup Failed!"

# Vercel Handler
def handler(event, context):
    return app(event, context)

if __name__ == "__main__":
    app.run(debug=True)
