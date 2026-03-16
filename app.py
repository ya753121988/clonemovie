import os
import asyncio
import threading
from flask import Flask, render_template_string, request, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId
from pyrogram import Client, filters, idle

# --- কনফিগারেশন ---
API_ID = int(os.getenv("API_ID", "29904834"))
API_HASH = os.getenv("API_HASH", "8b4fd9ef578af114502feeafa2d31938")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk")
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
CHANNEL_ID = int(os.getenv("CHANNEL_ID", "-1003704764803"))

# Flask setup
app = Flask(__name__)
app.secret_key = os.urandom(24)

# MongoDB setup
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# Pyrogram Bot setup
bot = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# --- CSS Design ---
CSS = """
<style>
    body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; margin: 0; text-align: center; }
    header { background: #0088cc; color: white; padding: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
    .container { max-width: 1000px; margin: 20px auto; display: flex; flex-wrap: wrap; justify-content: center; }
    .card { background: white; width: 220px; margin: 15px; border-radius: 10px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); overflow: hidden; }
    .card img { width: 100%; height: 130px; object-fit: cover; }
    .card-body { padding: 10px; }
    .btn { background: #0088cc; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px; }
    .btn-del { background: #dc3545; color: white; border: none; padding: 5px 10px; cursor: pointer; border-radius: 3px; }
    table { width: 90%; margin: 20px auto; border-collapse: collapse; background: white; }
    th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
</style>
"""

# --- Routes ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Movie Portal</h1></header><div class='container'>"
    for v in videos:
        thumb = v.get('thumb_url', 'https://via.placeholder.com/300x150?text=No+Thumbnail')
        html += f"""
        <div class='card'>
            <img src='{thumb}'>
            <div class='card-body'>
                <small>{v['file_name'][:30]}...</small><br>
                <a href='/details/{v["_id"]}' class='btn'>Details</a>
            </div>
        </div>
        """
    html += "</div>"
    return html

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "File Not Found!"
    
    # বটের ইউজারনেম গেট করা (বট অনলাইন থাকা অবস্থায়)
    bot_username = "your_bot_username" 
    try:
        bot_username = bot.me.username
    except: pass

    html = f"{CSS}<header><h1>Video Details</h1></header>"
    html += f"""
    <div style='max-width: 600px; margin: 20px auto; background: white; padding: 20px; border-radius: 10px;'>
        <img src='{video.get("thumb_url")}' style='width:100%;'>
        <h2>{video['file_name']}</h2>
        <p>Size: {video.get('file_size')}</p>
        <a href='https://t.me/{bot_username}?start={video["file_id"]}' class='btn' style='background:green; padding: 15px 30px;'>Download via Bot</a>
        <br><br><a href='/'>Back to Home</a>
    </div>
    """
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin'] = True
    if not session.get('admin'):
        return f"{CSS}<form method='POST' style='margin-top:100px;'><input type='password' name='password'><button type='submit'>Login</button></form>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header><h1>Admin Panel</h1><a href='/'>Home</a></header><table>"
    for v in videos:
        html += f"<tr><td>{v['file_name']}</td><td><a href='/delete/{v['_id']}' class='btn-del'>Delete</a></td></tr>"
    html += "</table>"
    return html

@app.route('/delete/<id>')
def delete_file(id):
    if session.get('admin'):
        videos_col.delete_one({"_id": ObjectId(id)})
    return redirect('/admin')

# --- Bot Logic ---

@bot.on_message(filters.chat(CHANNEL_ID) & filters.video)
async def handle_video(client, message):
    data = {
        "file_name": message.video.file_name or "New Video",
        "file_id": message.video.file_id,
        "file_size": f"{round(message.video.file_size / (1024*1024), 2)} MB",
        "thumb_url": "https://via.placeholder.com/400x200.png?text=Video+Thumbnail"
    }
    videos_col.insert_one(data)
    print(f"Saved: {data['file_name']}")

@bot.on_message(filters.command("start") & filters.private)
async def start(client, message):
    if len(message.command) > 1:
        await message.reply_video(message.command[1], caption="আপনার ফাইলটি নিচে দেওয়া হলো।")
    else:
        await message.reply("স্বাগতম! ওয়েবসাইট ভিজিট করে মুভি ডাউনলোড করুন।")

# --- Runner Logic (Fixing Event Loop) ---

def run_flask():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

async def main():
    await bot.start()
    print("Bot Started!")
    # Flask-কে আলাদা থ্রেডে চালানো
    threading.Thread(target=run_flask, daemon=True).start()
    await idle()
    await bot.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        pass
