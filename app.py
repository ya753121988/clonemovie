import os
import telebot
import requests
from pymongo import MongoClient
from flask import Flask
from threading import Thread
import time
from datetime import datetime

# --- কনফিগারেশন (আপনার দেওয়া তথ্য) ---
BOT_TOKEN = "8773638161:AAFCdZeOCp6mzGbNcV2QeRpp0j09Gtu-I5o"
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_ID = 7120801813

# ডলার টু টাকা কনভার্টার (আপনার লাভসহ)
# Peakerr এর রেট যদি $1 হয়, আপনি কাস্টমারের থেকে ১২০ টাকা নিবেন।
DOLLAR_TO_BDT = 120 

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")
app = Flask('')

# --- ডাটাবেস কানেকশন ---
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['smm_panel_db']
    users_col = db['users']
    orders_col = db['orders']
    print("✅ MongoDB কানেক্টেড!")
except Exception as e:
    print(f"❌ MongoDB এরর: {e}")

# --- ইউজার ম্যানেজমেন্ট ফাংশন ---
def get_user(user_id, username="Unknown"):
    user = users_col.find_one({"user_id": user_id})
    if not user:
        user = {
            "user_id": user_id,
            "username": username,
            "balance": 0.0,
            "total_spent": 0.0,
            "join_date": datetime.now().strftime("%Y-%m-%d")
        }
        users_col.insert_one(user)
    return user

def update_balance(user_id, amount):
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)

# --- কিবোর্ড মেনু ---
def main_menu():
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("🛒 অর্ডার করুন", "📊 সার্ভিস লিস্ট")
    markup.row("👤 প্রোফাইল", "💰 রিচার্জ")
    markup.row("📜 অর্ডার হিস্ট্রি", "📞 সাপোর্ট")
    return markup

# --- ফ্লাস্ক রুট (Koyeb এর জন্য) ---
@app.route('/')
def home():
    return "SMM Bot is Active!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- কমান্ড হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def start(message):
    get_user(message.from_user.id, message.from_user.username)
    welcome_text = (
        f"👋 <b>স্বাগতম, {message.from_user.first_name}!</b>\n\n"
        "এটি একটি অটোমেটিক SMM প্যানেল বট। এখান থেকে আপনি টেলিগ্রাম মেম্বার, "
        "ভিউ, রিয়েকশন ইত্যাদি সস্তায় কিনতে পারবেন।\n\n"
        "নিচের মেনু থেকে আপনার পছন্দমতো অপশন বেছে নিন।"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda m: m.text == "👤 প্রোফাইল")
def profile(message):
    user = get_user(message.from_user.id)
    text = (
        "<b>👤 আপনার প্রোফাইল তথ্য</b>\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🆔 ইউজার আইডি: <code>{user['user_id']}</code>\n"
        f"💰 বর্তমান ব্যালেন্স: <b>{round(user['balance'], 2)} TK</b>\n"
        f"💸 মোট খরচ: {round(user['total_spent'], 2)} TK\n"
        f"📅 জয়েনিং ডেট: {user['join_date']}\n"
        "━━━━━━━━━━━━━━━━━━"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "📊 সার্ভিস লিস্ট")
def service_list(message):
    # সরাসরি Peakerr থেকে সার্ভিস লিস্ট আনা (প্রথম ১০টি উদাহরণ হিসেবে)
    bot.send_message(message.chat.id, "🔄 সার্ভিস লিস্ট লোড হচ্ছে...")
    try:
        res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        text = "<b>📊 জনপ্রিয় সার্ভিসসমূহ (প্রতি ১০০০ এর দাম):</b>\n\n"
        for s in res[:15]: # প্রথম ১৫টি সার্ভিস দেখাচ্ছি
            price_bdt = float(s['rate']) * DOLLAR_TO_BDT
            text += f"🆔 <code>{s['service']}</code> - {s['name']}\n💰 মূল্য: <b>{round(price_bdt, 2)} TK</b>\n\n"
        bot.send_message(message.chat.id, text)
    except:
        bot.send_message(message.chat.id, "❌ সার্ভিস লিস্ট পেতে সমস্যা হচ্ছে।")

@bot.message_handler(func=lambda m: m.text == "💰 রিচার্জ")
def recharge(message):
    text = (
        "<b>💰 ব্যালেন্স রিচার্জ করার নিয়ম:</b>\n\n"
        "১. বিকাশ/নগদ (Personal): <code>017XXXXXXXX</code>\n"
        "২. টাকা পাঠিয়ে ট্রানজেকশন আইডি (TrxID) কপি করুন।\n"
        "৩. এডমিনকে আপনার ইউজার আইডি এবং TrxID পাঠান।\n\n"
        f"আপনার আইডি: <code>{message.from_user.id}</code>\n"
        "এডমিন আইডি: @AdminUsername"
    )
    bot.send_message(message.chat.id, text)

@bot.message_handler(func=lambda m: m.text == "🛒 অর্ডার করুন")
def order_now(message):
    msg = (
        "<b>🛒 নতুন অর্ডার করতে নিচের ফরম্যাটে মেসেজ দিন:</b>\n\n"
        "<code>ID_Link_Quantity</code>\n\n"
        "উদাহরণ: আপনি 105 নাম্বার সার্ভিসের 500 মেম্বার নিতে চাইলে লিখবেন:\n"
        "<code>105_https://t.me/channel_500</code>"
    )
    bot.send_message(message.chat.id, msg)

@bot.message_handler(func=lambda m: m.text == "📜 অর্ডার হিস্ট্রি")
def history(message):
    orders = orders_col.find({"user_id": message.from_user.id}).sort("_id", -1).limit(5)
    text = "<b>📜 আপনার শেষ ৫টি অর্ডার:</b>\n\n"
    count = 0
    for o in orders:
        count += 1
        text += f"🔹 অর্ডার আইডি: {o['order_id']}\n🔸 স্ট্যাটাস: {o['status']}\n💰 খরচ: {o['cost']} TK\n\n"
    if count == 0: text = "আপনার কোনো অর্ডার হিস্ট্রি নেই।"
    bot.send_message(message.chat.id, text)

# --- অর্ডার প্রসেসিং ---
@bot.message_handler(func=lambda m: "_" in m.text)
def handle_order_logic(message):
    try:
        parts = message.text.split('_')
        if len(parts) != 3: return
        
        s_id, link, qty = parts[0], parts[1], int(parts[2])
        user = get_user(message.from_user.id)
        
        # সার্ভিস রেট চেক (API থেকে)
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = 0
        for s in services:
            if str(s['service']) == str(s_id):
                rate = float(s['rate'])
                break
        
        if rate == 0:
            bot.reply_to(message, "❌ ভুল সার্ভিস আইডি!")
            return

        cost = (qty / 1000) * (rate * DOLLAR_TO_BDT)
        
        if user['balance'] < cost:
            bot.reply_to(message, f"❌ পর্যাপ্ত ব্যালেন্স নেই। আপনার প্রয়োজন {round(cost, 2)} TK।")
            return

        # Peakerr এ অর্ডার সাবমিট
        payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': s_id, 'link': link, 'quantity': qty}
        res = requests.post(PEAKERR_API_URL, data=payload).json()

        if 'order' in res:
            update_balance(message.from_user.id, -cost)
            users_col.update_one({"user_id": message.from_user.id}, {"$inc": {"total_spent": cost}})
            
            # ডাটাবেসে অর্ডার সেভ
            orders_col.insert_one({
                "user_id": message.from_user.id,
                "order_id": res['order'],
                "cost": round(cost, 2),
                "status": "Pending",
                "date": datetime.now()
            })
            
            bot.send_message(message.chat.id, f"✅ <b>অর্ডার সফল!</b>\n\n🆔 অর্ডার আইডি: <code>{res['order']}</code>\n💰 খরচ: {round(cost, 2)} TK")
            bot.send_message(ADMIN_ID, f"🔔 <b>নতুন অর্ডার!</b>\nইউজার: {message.from_user.id}\nখরচ: {round(cost, 2)} TK")
        else:
            bot.reply_to(message, f"❌ ত্রুটি: {res.get('error')}")

    except Exception as e:
        bot.reply_to(message, "⚠️ সঠিক ফরম্যাটে দিন: ServiceID_Link_Quantity")

# --- অ্যাডমিন কমান্ডস ---

@bot.message_handler(commands=['add'])
def admin_add_bal(message):
    if message.from_user.id == ADMIN_ID:
        try:
            _, t_id, amt = message.text.split()
            update_balance(int(t_id), float(amt))
            bot.send_message(message.chat.id, f"✅ ইউজার {t_id} এ {amt} TK যোগ করা হয়েছে।")
            bot.send_message(int(t_id), f"💰 অভিনন্দন! এডমিন আপনার অ্যাকাউন্টে {amt} TK যোগ করেছেন।")
        except:
            bot.reply_to(message, "ফরম্যাট: /add [UserID] [Amount]")

@bot.message_handler(commands=['broadcast'])
def broadcast(message):
    if message.from_user.id == ADMIN_ID:
        msg_text = message.text.replace("/broadcast ", "")
        all_users = users_col.find()
        count = 0
        for u in all_users:
            try:
                bot.send_message(u['user_id'], f"📢 <b>ঘোষণা:</b>\n\n{msg_text}")
                count += 1
            except: pass
        bot.send_message(ADMIN_ID, f"✅ {count} জন ইউজারের কাছে মেসেজ পাঠানো হয়েছে।")

@bot.message_handler(func=lambda m: m.text == "📞 সাপোর্ট")
def support(message):
    bot.send_message(message.chat.id, "যেকোনো সমস্যায় যোগাযোগ করুন: @YourUsername")

# --- রান বোট ---
if __name__ == "__main__":
    Thread(target=run_flask).start()
    print("🚀 SMM Bot is Polling...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            time.sleep(5)
