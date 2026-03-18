import os
import telebot
import requests
from pymongo import MongoClient
from flask import Flask
from threading import Thread

# --- আপনার দেওয়া তথ্যসমূহ ---
BOT_TOKEN = "8773638161:AAFCdZeOCp6mzGbNcV2QeRpp0j09Gtu-I5o"
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_ID = 7120801813

# প্রফিট সেটআপ (১০০০ মেম্বারের জন্য আপনি কত টাকা চার্জ করবেন)
# পিক্যারের রেট অনুযায়ী এখানে আপনার লাভ যোগ করে একটি গড় রেট বসান
RATE_PER_1000 = 25  # উদাহরণ: ১০০০ মেম্বার ২৫ টাকা (এটি আপনার ইচ্ছেমতো পরিবর্তন করুন)

# বট এবং ডাটাবেস কানেকশন
bot = telebot.TeleBot(BOT_TOKEN)
client = MongoClient(MONGO_URI)
db = client['smm_database']
users_col = db['users']

# ফ্লাস্ক অ্যাপ (বটকে সচল রাখতে)
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

def run_flask():
    app.run(host='0.0.0.0', port=8080)

# --- ডাটাবেস ফাংশন ---
def get_user_data(user_id):
    user = users_col.find_one({"user_id": user_id})
    if not user:
        user = {"user_id": user_id, "balance": 0.0}
        users_col.insert_one(user)
    return user

def update_user_balance(user_id, amount):
    users_col.update_one({"user_id": user_id}, {"$inc": {"balance": amount}}, upsert=True)

# --- বট হ্যান্ডলারস ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    get_user_data(message.from_user.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 প্রোফাইল", "🛒 অর্ডার করুন")
    markup.add("💰 ব্যালেন্স রিচার্জ", "📊 সার্ভিস লিস্ট")
    
    bot.send_message(
        message.chat.id, 
        "👋 স্বাগতম! আমাদের অটোমেটিক SMM প্যানেল বটে।\nএখান থেকে আপনি সস্তায় টেলিগ্রাম সার্ভিস নিতে পারবেন।", 
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "👤 প্রোফাইল")
def show_profile(message):
    user = get_user_data(message.from_user.id)
    text = (f"👤 **আপনার প্রোফাইল**\n\n"
            f"🆔 আইডি: `{message.from_user.id}`\n"
            f"💰 ব্যালেন্স: {round(user['balance'], 2)} TK")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💰 ব্যালেন্স রিচার্জ")
def recharge_info(message):
    text = (f"💳 **ব্যালেন্স রিচার্জ করার নিয়ম**\n\n"
            f"আপনার ইউজার আইডি: `{message.from_user.id}`\n\n"
            f"বিকাশ/নগদ (Personal): `01XXXXXXXXX`\n"
            f"টাকা পাঠিয়ে আপনার ট্রানজেকশন আইডি (TrxID) এবং ইউজার আইডি এডমিনকে পাঠান।\n\n"
            f"এডমিন: @YourUsername") # এখানে আপনার টেলিগ্রাম ইউজারনেম দিন
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 সার্ভিস লিস্ট")
def service_list(message):
    bot.send_message(message.chat.id, "সার্ভিস লিস্ট দেখতে [Peakerr.com](https://peakerr.com/services) ভিজিট করুন এবং সার্ভিস আইডিটি নোট করুন।", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🛒 অর্ডার করুন")
def order_instruction(message):
    text = ("🛒 **অর্ডার করার নিয়ম**\n\n"
            "নিচের ফরম্যাটে মেসেজ দিন:\n"
            "`ServiceID_Link_Quantity`\n\n"
            "উদাহরণ: আপনি যদি ১০৫ নম্বর সার্ভিসের ১০০০ মেম্বার নিতে চান তবে লিখুন:\n"
            "`105_https://t.me/yourchannel_1000`")
    bot.send_message(message.chat.id, text, parse_mode="Markdown")

# অর্ডার প্রসেস (ID_Link_Quantity)
@bot.message_handler(func=lambda message: "_" in message.text)
def handle_order(message):
    try:
        data = message.text.split('_')
        if len(data) != 3: return
        
        s_id = data[0].strip()
        link = data[1].strip()
        qty = int(data[2].strip())
        
        user = get_user_data(message.from_user.id)
        cost = (qty / 1000) * RATE_PER_1000 # আপনার লাভসহ খরচ
        
        if user['balance'] < cost:
            bot.reply_to(message, f"❌ আপনার ব্যালেন্স পর্যাপ্ত নয়! প্রয়োজন {cost} TK।")
            return

        # Peakerr API Call
        payload = {
            'key': PEAKERR_API_KEY,
            'action': 'add',
            'service': s_id,
            'link': link,
            'quantity': qty
        }
        response = requests.post(PEAKERR_API_URL, data=payload).json()

        if 'order' in response:
            update_user_balance(message.from_user.id, -cost)
            bot.reply_to(message, f"✅ অর্ডার সফল হয়েছে!\n\n🆔 অর্ডার আইডি: {response['order']}\n💰 খরচ: {cost} TK\n📉 অবশিষ্ট ব্যালেন্স: {round(get_user_data(message.from_user.id)['balance'], 2)} TK")
            # এডমিনকে জানানো
            bot.send_message(ADMIN_ID, f"🔔 নতুন অর্ডার!\nইউজার: {message.from_user.id}\nসার্ভিস: {s_id}\nপরিমাণ: {qty}")
        else:
            bot.reply_to(message, f"❌ API ত্রুটি: {response.get('error', 'অর্ডার করা যায়নি')}")

    except Exception as e:
        bot.reply_to(message, "⚠️ ভুল ফরম্যাট! দয়া করে `ID_Link_Quantity` এভাবে লিখুন।")

# --- এডমিন কমান্ডস ---

@bot.message_handler(commands=['add'])
def add_balance_admin(message):
    if message.from_user.id == ADMIN_ID:
        try:
            # /add 1234567 500
            args = message.text.split()
            target_id = int(args[1])
            amount = float(args[2])
            
            update_user_balance(target_id, amount)
            bot.send_message(message.chat.id, f"✅ ইউজার `{target_id}` এর অ্যাকাউন্টে {amount} TK যোগ করা হয়েছে।", parse_mode="Markdown")
            bot.send_message(target_id, f"💰 এডমিন আপনার অ্যাকাউন্টে {amount} TK যোগ করেছেন।")
        except:
            bot.reply_to(message, "ব্যবহার: `/add [User_ID] [Amount]`")
    else:
        bot.reply_to(message, "🚫 আপনি এডমিন নন।")

# রান বোট
if __name__ == "__main__":
    print("Bot is starting...")
    Thread(target=run_flask).start()
    bot.infinity_polling()
