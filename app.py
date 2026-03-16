import os
import json
import asyncio
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import Update, Message, InlineKeyboardMarkup, InlineKeyboardButton

# --- ১. কনফিগারেশন (আপনার দেওয়া তথ্য) ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"
BOT_USERNAME = "clonemovie_bot" # আপনার বটের আসল ইউজারনেম এখানে দিন (@ ছাড়া)

# Flask অ্যাপ
app = Flask(__name__)
app.secret_key = "vercel_fix_v4"

# MongoDB
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# Pyrogram Client (Webhook মোডের জন্য No-Session লজিক)
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f4f7f9; margin: 0; text-align: center; }
    header { background: #0088cc; color: white; padding: 20px; font-size: 24px; font-weight: bold; }
    .container { display: flex; flex-wrap: wrap; justify-content: center; padding: 20px; max-width: 1200px; margin: auto; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
    .card img { width: 100%; height: 130px; object-fit: cover; background: #333; }
    .btn { background: #0088cc; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; margin-top: 10px; }
    .btn-download { background: #28a745; padding: 15px 35px; font-size: 20px; color: white; border-radius: 10px; text-decoration: none; display: inline-block; }
</style>
"""

# --- ৩. বট লজিক (Start & Notification) ---

async def handle_bot_logic(update):
    if isinstance(update, Message):
        chat_id = update.chat.id
        # ১. স্টার্ট কমান্ড
        if update.text and update.text.startswith("/start"):
            args = update.text.split(" ")
            if len(args) > 1:
                await bot.send_video(chat_id, video=args[1], caption="✨ ভিডিওটি প্রস্তুত! উপভোগ করুন।")
            else:
                welcome_text = "👋 **মুভি পোর্টালে স্বাগতম!**\n\nমুভি ডাউনলোড করতে নিচের বাটনে ক্লিক করে সাইট ভিজিট করুন।"
                await bot.send_message(chat_id, welcome_text, reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL)
                ]]))
        # ২. চ্যানেল পোস্ট
        elif chat_id == CHANNEL_ID and update.video:
            data = {
                "file_name": update.video.file_name or "New Movie",
                "file_id": update.video.file_id,
                "file_size": f"{round(update.video.file_size / (1024 * 1024), 2)} MB",
                "thumb_url": "https://via.placeholder.com/400x250.png?text=New+Movie+Added"
            }
            res = videos_col.insert_one(data)
            log_text = f"✅ নতুন ভিডিও সাইটে অ্যাড হয়েছে!\n\n📂 {data['file_name']}\n🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
            await bot.send_message(OWNER_ID, log_text)

# --- ৪. Webhook & Setup (Fixing 500 Error) ---

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.is_json:
        data = request.get_json()
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        async def run():
            async with bot:
                update = Update.from_dict(data, bot)
                if update.message: await handle_bot_logic(update.message)
                elif update.channel_post: await handle_bot_logic(update.channel_post)
        loop.run_until_complete(run())
        return "OK", 200
    return "Forbidden", 403

@app.route('/setup')
def setup():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    async def set_hook():
        async with bot:
            return await bot.set_webhook(f"{SITE_URL}/webhook")
    try:
        success = loop.run_until_complete(set_hook())
        return "<h1>✅ Webhook Setup Successful!</h1>" if success else "<h1>❌ Setup Failed!</h1>"
    except Exception as e:
        return f"<h1>Error: {str(e)}</h1>"

# --- ৫. ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Movie Portal</header><div class='container'>"
    for v in videos:
        html += f"""
        <div class='card'>
            <img src='{v.get('thumb_url')}'>
            <div style='padding:15px;'>
                <p><b>{v['file_name'][:35]}</b></p>
                <a href='/details/{v["_id"]}' class='btn'>বিস্তারিত দেখুন</a>
            </div>
        </div>
        """
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইলটি পাওয়া যায়নি!"
    
    # বটের লিঙ্ক জেনারেট
    dl_url = f"https://t.me/{BOT_USERNAME}?start={video['file_id']}"
    
    html = f"{CSS}<header>মুভি ডিটেইলস</header><div style='padding:40px;'>"
    html += f"""
        <img src='{video.get('thumb_url')}' style='width:100%; max-width:500px; border-radius:15px; box-shadow: 0 5px 20px rgba(0,0,0,0.2);'>
        <h2>{video['file_name']}</h2>
        <p style='font-size:18px;'>সাইজ: {video.get('file_size')}</p>
        <br>
        <a href='{dl_url}' class='btn-download'>📥 ডাউনলোড করুন (টেলিগ্রাম বটের মাধ্যমে)</a>
        <br><br><a href='/' style='color:#0088cc; text-decoration:none;'>← হোম পেজে ফিরে যান</a>
    </div>
    """
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('pass') == ADMIN_PASSWORD:
        session['admin'] = True
    if not session.get('admin'):
        return f"{CSS}<div style='padding:50px;'><form method='post'>পাসওয়ার্ড দিন: <input type='password' name='pass'><br><br><button type='submit' class='btn'>লগইন</button></form></div>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>অ্যাডমিন প্যানেল</header><div style='padding:20px; max-width:600px; margin:auto;'>"
    for v in videos:
        html += f"<div style='border-bottom:1px solid #ddd; padding:10px; text-align:left;'>{v['file_name']} <a href='/delete/{v['_id']}' style='color:red; float:right;'>[Delete]</a></div>"
    return html + "</div>"

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# Vercel-এর জন্য 'app' অবজেক্টটি এক্সপোর্ট করা হলো
if __name__ == "__main__":
    app.run()
