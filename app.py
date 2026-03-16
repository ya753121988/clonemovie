import os
import telebot
from flask import Flask, request, render_template_string, redirect, session, url_for
from pymongo import MongoClient
from bson import ObjectId

# --- ১. কনফিগারেশন (আপনার দেওয়া তথ্য অনুযায়ী) ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803 # আপনার প্রাইভেট চ্যানেল আইডি
OWNER_ID = 7120801813        # আপনার টেলিগ্রাম আইডি
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask ও Bot সেটআপ (threaded=False ভার্সেলের জন্য জরুরি)
app = Flask(__name__)
app.secret_key = os.urandom(24)
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB সেটআপ
client = MongoClient(MONGO_URI)
db = client['video_database']
videos_col = db['videos']

# --- ২. ডিজাইন (CSS) ---
CSS = """
<style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: #f0f2f5; margin: 0; padding: 0; color: #333; }
    header { background: #0088cc; color: white; padding: 20px; text-align: center; font-size: 26px; font-weight: bold; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
    .container { max-width: 1200px; margin: 20px auto; padding: 10px; display: flex; flex-wrap: wrap; justify-content: center; }
    .card { background: white; width: 230px; margin: 15px; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.1); transition: 0.3s; text-align: center; }
    .card:hover { transform: translateY(-5px); }
    .card img { width: 100%; height: 140px; object-fit: cover; background: #222; }
    .card-body { padding: 15px; }
    .card-title { font-size: 15px; font-weight: bold; margin-bottom: 10px; height: 35px; overflow: hidden; }
    .btn { background: #0088cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 6px; display: inline-block; font-weight: bold; border: none; cursor: pointer; }
    .btn-download { background: #28a745; font-size: 20px; padding: 15px 35px; color: white; border-radius: 10px; text-decoration: none; display: inline-block; box-shadow: 0 4px 12px rgba(40,167,69,0.3); font-weight: bold; }
    .admin-list { max-width: 800px; margin: 20px auto; background: white; padding: 20px; border-radius: 10px; text-align: left; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }
    .admin-item { border-bottom: 1px solid #eee; padding: 10px; display: flex; justify-content: space-between; align-items: center; }
</style>
"""

# --- ৩. টেলিগ্রাম বট লজিক (Start & Auto-Add) ---

@bot.message_handler(commands=['start'])
def start_handler(message):
    chat_id = message.chat.id
    command_parts = message.text.split()
    
    # ওয়েবসাইট থেকে ডাউনলোড রিকোয়েস্ট আসলে
    if len(command_parts) > 1:
        file_id = command_parts[1]
        bot.send_video(chat_id, file_id, caption="🎬 **আপনার ভিডিওটি প্রস্তুত!** আমাদের সাথে থাকার জন্য ধন্যবাদ।")
    else:
        # সাধারণ স্টার্ট মেসেজ বাটনসহ
        welcome_text = (
            "👋 **মুভি পোর্টালে স্বাগতম!**\n\n"
            "মুভি ও ভিডিও ডাউনলোড করতে নিচের বাটনে ক্লিক করে আমাদের ওয়েবসাইট ভিজিট করুন।"
        )
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video'])
def channel_video_handler(message):
    if message.chat.id == CHANNEL_ID:
        file_name = message.video.file_name or "Untitled_Movie"
        file_id = message.video.file_id
        file_size = f"{round(message.video.file_size / (1024 * 1024), 2)} MB"
        
        # ভিডিওতে থাম্বনেইল থাকলে সেটি নেওয়া, না থাকলে ডিফল্ট
        thumb_url = "https://via.placeholder.com/400x250.png?text=New+Movie+Added"
        
        # ডাটাবেসে সেভ করা
        data = {
            "file_name": file_name,
            "file_id": file_id,
            "file_size": file_size,
            "thumb_url": thumb_url
        }
        res = videos_col.insert_one(data)
        
        # আপনাকে (মালিককে) নোটিফিকেশন পাঠানো
        log_text = (
            "✅ **নতুন ভিডিও সাইটে অ্যাড হয়েছে!**\n\n"
            f"📂 নাম: `{file_name}`\n"
            f"⚖️ সাইজ: {file_size}\n"
            f"🌐 লিঙ্ক: {SITE_URL}/details/{res.inserted_id}"
        )
        bot.send_message(OWNER_ID, log_text, parse_mode="Markdown")

# --- ৪. ফ্ল্যাক্স ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Movie Portal</header><div class='container'>"
    for v in videos:
        html += f"""
        <div class='card'>
            <img src='{v.get('thumb_url')}'>
            <div class='card-body'>
                <div class='card-title'>{v['file_name'][:40]}</div>
                <a href='/details/{v["_id"]}' class='btn'>বিস্তারিত দেখুন</a>
            </div>
        </div>
        """
    if not videos: html += "<h3>কোনো মুভি পাওয়া যায়নি। চ্যানেলে ভিডিও ফরওয়ার্ড করুন।</h3>"
    return html + "</div>"

@app.route('/details/<id>')
def details(id):
    video = videos_col.find_one({"_id": ObjectId(id)})
    if not video: return "ফাইলটি খুঁজে পাওয়া যায়নি!"
    
    # বটের ইউজারনেম বের করা
    bot_info = bot.get_me()
    download_url = f"https://t.me/{bot_info.username}?start={video['file_id']}"
    
    html = f"{CSS}<header>Movie Details</header><div style='padding:40px; text-align:center;'>"
    html += f"""
        <img src='{video.get('thumb_url')}' style='width:100%; max-width:600px; border-radius:15px; box-shadow: 0 5px 20px rgba(0,0,0,0.2);'>
        <h2 style='margin-top:25px;'>{video['file_name']}</h2>
        <p style='font-size:18px;'><b>ফাইল সাইজ:</b> {video.get('file_size')}</p>
        <hr style='width:50%; margin:20px auto;'>
        <p>সরাসরি টেলিগ্রাম বটে ফাইলটি পেতে নিচের বাটনে ক্লিক করুন।</p>
        <br>
        <a href='{download_url}' class='btn-download'>📥 ডাউনলোড করুন (Bot)</a>
        <br><br><a href='/' style='text-decoration:none; color:#0088cc;'>← হোম পেজে ফিরে যান</a>
    </div>
    """
    return html

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['admin_logged_in'] = True
    if not session.get('admin_logged_in'):
        return f"{CSS}<div style='margin-top:100px; text-align:center;'><form method='post'>পাসওয়ার্ড: <input type='password' name='password'><button type='submit' class='btn'>Login</button></form></div>"
    
    videos = list(videos_col.find().sort("_id", -1))
    html = f"{CSS}<header>Admin Panel</header><div class='admin-list'><h3>ফাইল ম্যানেজমেন্ট</h3>"
    for v in videos:
        html += f"<div class='admin-item'><span>{v['file_name']}</span><a href='/delete/{v['_id']}' style='color:red; text-decoration:none;'>ডিলিট</a></div>"
    return html + "</div>"

@app.route('/delete/<id>')
def delete(id):
    if session.get('admin_logged_in'): videos_col.delete_one({"_id": ObjectId(id)})
    return redirect(url_for('admin'))

# --- ৫. Webhook ও Setup রুট (ভার্সেলের জন্য জরুরি) ---

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

# Vercel-এর জন্য মেইন হ্যান্ডলার
def handler(event, context):
    return app(event, context)

if __name__ == "__main__":
    app.run()
