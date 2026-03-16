import os
import asyncio
from flask import Flask, render_template_string, request, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- কনফিগারেশন (Environment Variables থেকে নিবে) ---
API_ID = os.getenv("API_ID", "YOUR_API_ID")
API_HASH = os.getenv("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN")
MONGO_URI = os.getenv("MONGO_URI", "YOUR_MONGODB_URI")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-100xxxxxx")) # আপনার প্রাইভেট চ্যানেল আইডি

# Flask অ্যাপ সেটআপ
app = Flask(__name__)
app.secret_key = "super_secret_key"

# MongoDB সেটআপ
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# Pyrogram বট সেটআপ
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 0; }
    header { background: #0088cc; color: white; padding: 20px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .container { max-width: 1000px; margin: 20px auto; padding: 10px; display: flex; flex-wrap: wrap; justify-content: center; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: 0.3s; }
    .card:hover { transform: translateY(-5px); }
    .card img { width: 100%; height: 150px; object-fit: cover; background: #ddd; }
    .card-body { padding: 15px; text-align: center; }
    .card-title { font-size: 16px; font-weight: bold; margin-bottom: 10px; color: #333; height: 40px; overflow: hidden; }
    .btn { background: #0088cc; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; display: inline-block; }
    .btn-download { background: #28a745; font-size: 18px; padding: 12px 25px; }
    .admin-table { width: 90%; margin: 20px auto; border-collapse: collapse; background: white; }
    .admin-table th, .admin-table td { padding: 12px; border: 1px solid #ddd; text-align: left; }
    .btn-delete { background: #dc3545; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px; }
</style>
"""

# --- ওয়েবসাইট রুটস (Flask Routes) ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Video Portal</h1></header><div class='container'>"
    for v in videos:
        # থাম্বনেইল না থাকলে ডিফল্ট ইমেজ
        thumb = v.get('thumb_url', 'https://via.placeholder.com/300x150?text=No+Thumbnail')
        html += f"""
        <div class='card'>
            <img src='{thumb}'>
            <div class='card-body'>
                <div class='card-title'>{v['file_name'][:40]}</div>
                <a href='/details/{v["_id"]}' class='btn'>View Details</a>
            </div>
        </div>
        """
    html += "</div>"
    return html

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইলটি খুঁজে পাওয়া যায়নি!"
    
    bot_info = bot.get_me() if not bot.is_connected else bot.me # বটের ইউজারনেম পেতে
    
    html = f"""
    {CSS}
    <header><h1>Video Details</h1></header>
    <div style='max-width: 700px; margin: 30px auto; background: white; padding: 30px; border-radius: 15px; text-align: center; box-shadow: 0 5px 20px rgba(0,0,0,0.1);'>
        <img src='{video.get("thumb_url", "https://via.placeholder.com/600x300")}' style='width: 100%; border-radius: 10px;'>
        <h2 style='color: #333; margin-top: 20px;'>{video['file_name']}</h2>
        <p><b>ফাইল সাইজ:</b> {video.get('file_size', 'N/A')}</p>
        <hr>
        <h3>Screenshots (From Video Preview)</h3>
        <p>টেলিগ্রাম বটের মাধ্যমে সরাসরি ভিডিওটি ডাউনলোড করতে নিচের বাটনে ক্লিক করুন।</p>
        <br>
        <a href='https://t.me/{bot.me.username}?start={video["file_id"]}' class='btn btn-download'>Download via Bot</a>
        <br><br>
        <a href='/'>হোম পেজে ফিরে যান</a>
    </div>
    """
    return html

# --- এডমিন প্যানেল (Admin Panel) ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
    
    if not session.get('admin_logged_in'):
        return f"""
        {CSS}<div style='text-align:center; margin-top: 100px;'>
        <form method='POST'>
            <h2>Admin Login</h2>
            <input type='password' name='password' placeholder='Password' style='padding:10px;'><br><br>
            <button type='submit' class='btn'>Login</button>
        </form></div>
        """
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Admin Panel</h1><a href='/logout' style='color:white;'>Logout</a></header>"
    html += "<table class='admin-table'><tr><th>File Name</th><th>Action</th></tr>"
    for v in videos:
        html += f"""
        <tr>
            <td>{v['file_name']}</td>
            <td><a href='/delete/{v["_id"]}' class='btn-delete' onclick="return confirm('নিশ্চিত ডিলিট করবেন?')">Delete</a></td>
        </tr>
        """
    html += "</table>"
    return html

@app.route('/delete/<id>')
def delete_file(id):
    if session.get('admin_logged_in'):
        videos_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('home'))

# --- টেলিগ্রাম বট হ্যান্ডলার (Bot Logic) ---

@bot.on_message(filters.chat(CHANNEL_ID) & filters.video)
async def handle_new_video(client, message):
    file_name = message.video.file_name or "Untitled_Video"
    file_id = message.video.file_id
    file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
    
    # বড় ভিডিওর ক্ষেত্রে ক্রাশ এড়াতে আমরা ডাউনলোড ছাড়াই থাম্বনেইল হ্যান্ডেল করবো।
    # যদি ভিডিওতে থাম্ব থাকে, সেটা ইউজ হবে। (এখানে placeholder দেওয়া হয়েছে, 
    # প্রফেশনাল ক্ষেত্রে থাম্ব ডাউলোড করে ImgBB তে আপলোড করা যায়)
    
    video_data = {
        "file_name": file_name,
        "file_id": file_id,
        "file_size": file_size,
        "thumb_url": "https://via.placeholder.com/400x250.png?text=Video+Thumbnail"
    }
    videos_col.insert_one(video_data)
    print(f"Added to Site: {file_name}")

@bot.on_message(filters.command("start") & filters.private)
async def start_command(client, message):
    if len(message.command) > 1:
        file_id = message.command[1]
        await message.reply_video(file_id, caption="আপনার অনুরোধ করা ভিডিওটি নিচে দেওয়া হলো।")
    else:
        await message.reply("স্বাগতম! ভিডিও ডাউনলোড করতে ওয়েবসাইট ভিজিট করুন।")

# --- রানার (Vercel & Local Support) ---

if __name__ == "__main__":
    # বট স্টার্ট করার থ্রেড
    from threading import Thread
    def start_bot():
        bot.run()

    Thread(target=start_bot).start()
    app.run(host='0.0.0.0', port=5000)

# Vercel-এর জন্য হ্যান্ডলার
def handler(event, context):
    return app(event, context)
