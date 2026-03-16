import os
import asyncio
import threading
from flask import Flask, render_template_string, request, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters, idle
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- ১. কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
API_ID = 29904834
API_HASH = "8b4fd9ef578af114502feeafa2d31938"
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app" # আপনার সাইটের আসল লিঙ্ক

# Flask অ্যাপ সেটআপ
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB সেটআপ
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# Pyrogram বট সেটআপ
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
    header { background: #0088cc; color: white; padding: 20px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .container { max-width: 1200px; margin: 20px auto; padding: 10px; display: flex; flex-wrap: wrap; justify-content: center; }
    .card { background: white; width: 230px; margin: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: 0.3s; }
    .card:hover { transform: translateY(-5px); }
    .card img { width: 100%; height: 140px; object-fit: cover; background: #333; }
    .card-body { padding: 15px; text-align: center; }
    .card-title { font-size: 15px; font-weight: bold; margin-bottom: 10px; color: #333; height: 35px; overflow: hidden; }
    .btn { background: #0088cc; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; display: inline-block; border: none; cursor: pointer; }
    .btn-download { background: #28a745; font-size: 18px; padding: 15px 30px; color: white; border-radius: 10px; text-decoration: none; font-weight: bold; }
    .admin-table { width: 95%; margin: 20px auto; border-collapse: collapse; background: white; border-radius: 10px; overflow: hidden; }
    .admin-table th, .admin-table td { padding: 15px; border: 1px solid #ddd; text-align: left; }
    .btn-delete { background: #dc3545; color: white; border: none; padding: 8px 12px; cursor: pointer; border-radius: 4px; text-decoration: none; }
</style>
"""

# --- ৩. ওয়েবসাইট রুটস (Flask Routes) ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Movie Portal</h1></header><div class='container'>"
    for v in videos:
        thumb = v.get('thumb_url', 'https://via.placeholder.com/300x150?text=Movie+Thumbnail')
        html += f"""
        <div class='card'>
            <img src='{thumb}'>
            <div class='card-body'>
                <div class='card-title'>{v['file_name'][:40]}</div>
                <a href='/details/{v["_id"]}' class='btn'>View Details</a>
            </div>
        </div>
        """
    if not videos:
        html += "<h3>কোনো ফাইল পাওয়া যায়নি। চ্যানেলে ভিডিও ফরওয়ার্ড করুন।</h3>"
    html += "</div>"
    return html

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইলটি ডাটাবেসে পাওয়া যায়নি!"
    
    bot_info = bot.get_me() if bot.is_connected else None
    bot_username = bot_info.username if bot_info else "bot"
    
    html = f"""
    {CSS}
    <header><h1>Video Details</h1></header>
    <div style='max-width: 800px; margin: 30px auto; background: white; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 5px 20px rgba(0,0,0,0.1);'>
        <img src='{video.get("thumb_url", "https://via.placeholder.com/600x300")}' style='width: 100%; border-radius: 10px; border: 2px solid #0088cc;'>
        <h2 style='color: #333; margin-top: 20px;'>{video['file_name']}</h2>
        <p style='font-size: 18px;'><b>সাইজ:</b> {video.get('file_size', 'N/A')}</p>
        <hr>
        <p>নিচের বাটনে ক্লিক করলে টেলিগ্রাম বটে আপনাকে ফাইলটি পাঠিয়ে দেওয়া হবে।</p>
        <br>
        <a href='https://t.me/{bot_username}?start={video["file_id"]}' class='btn-download'>Download via Bot</a>
        <br><br>
        <a href='/' style='text-decoration:none; color:#0088cc;'>← হোম পেজে ফিরে যান</a>
    </div>
    """
    return html

# --- ৪. এডমিন প্যানেল ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
    
    if not session.get('admin_logged_in'):
        return f"""
        {CSS}<div style='text-align:center; margin-top: 100px;'>
        <form method='POST'><h2>Admin Login</h2><input type='password' name='password' placeholder='Password'><br><br><button type='submit' class='btn'>Login</button></form></div>
        """
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Admin Panel</h1><a href='/' style='color:white;'>Go Home</a></header>"
    html += "<table class='admin-table'><tr><th>ফাইল নাম</th><th>অ্যাকশন</th></tr>"
    for v in videos:
        html += f"<tr><td>{v['file_name']}</td><td><a href='/delete/{v['_id']}' class='btn-delete' onclick='return confirm(\"নিশ্চিত ডিলিট করবেন?\")'>Delete</a></td></tr>"
    html += "</table>"
    return html

@app.route('/delete/<id>')
def delete_file(id):
    if session.get('admin_logged_in'):
        videos_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

# --- ৫. টেলিগ্রাম বট হ্যান্ডলার ---

@bot.on_message(filters.chat(CHANNEL_ID) & filters.video)
async def handle_new_video(client, message):
    file_name = message.video.file_name or "Untitled_Video"
    file_id = message.video.file_id
    file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
    
    # ডাটাবেসে সেভ
    video_data = {
        "file_name": file_name,
        "file_id": file_id,
        "file_size": file_size,
        "thumb_url": "https://via.placeholder.com/400x250.png?text=New+Movie+Added"
    }
    result = videos_col.insert_one(video_data)
    
    # অ্যাডমিনকে (আপনাকে) মেসেজ পাঠানো
    try:
        log_msg = (
            "✅ **নতুন ফাইল সাইটে অ্যাড হয়েছে!**\n\n"
            f"📂 **নাম:** `{file_name}`\n"
            f"⚖️ **সাইজ:** {file_size}\n"
            f"🌐 **সাইট লিঙ্ক:** {SITE_URL}/details/{result.inserted_id}"
        )
        await client.send_message(OWNER_ID, log_msg)
    except Exception as e:
        print(f"Error notifying owner: {e}")

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if len(message.command) > 1:
        file_id = message.command[1]
        await message.reply_video(file_id, caption="আপনার অনুরোধ করা ভিডিওটি নিচে দেওয়া হলো।")
    else:
        await message.reply(f"স্বাগতম! মুভি ডাউনলোড করতে আমাদের ওয়েবসাইট ভিজিট করুন:\n{SITE_URL}")

# --- ৬. রানার লজিক (Event Loop & Threading) ---

def run_flask():
    # Render বা Koyeb এর জন্য পোর্ট সেটআপ
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

async def main():
    print("Starting Bot...")
    await bot.start()
    print("Bot is Online!")
    
    # Flask-কে আলাদা থ্রেডে চালানো যাতে বট এবং সাইট একসাথে চলে
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()
    
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
