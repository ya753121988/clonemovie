import os
import requests
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
from datetime import datetime

app = Flask(__name__)
app.secret_key = "smm_bd_pro_secure_key_99"

# --- আপনার কনফিগারেশন ---
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_EMAIL = "admin@gmail.com" # এই ইমেইল দিয়ে রেজিস্টার করলে এডমিন প্যানেল খুলবে
DOLLAR_RATE = 125 # ১ ডলার = ১২৫ টাকা (আপনার লাভসহ)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['smm_database']
users_col = db['users']
orders_col = db['orders']

# --- প্রফেশনাল ডিজাইন (Tailwind CSS) ---
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM PANEL BD - Best SMM Service</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body class="bg-gray-50 flex flex-col min-h-screen">
    <!-- Navbar -->
    <nav class="bg-indigo-600 text-white shadow-lg">
        <div class="container mx-auto px-4 py-3 flex justify-between items-center">
            <a href="/" class="text-2xl font-bold flex items-center"><i class="fas fa-rocket mr-2"></i> SMM BD</a>
            <div class="hidden md:flex space-x-6 items-center">
                {% if user_session %}
                    <a href="/dashboard" class="hover:text-indigo-200">Dashboard</a>
                    <a href="/services" class="hover:text-indigo-200">Services</a>
                    {% if user_session == admin_mail %}
                        <a href="/admin" class="bg-red-500 px-3 py-1 rounded text-sm font-bold shadow hover:bg-red-600">ADMIN PANEL</a>
                    {% endif %}
                    <a href="/logout" class="bg-indigo-700 px-4 py-2 rounded-lg text-sm">Logout</a>
                {% else %}
                    <a href="/login" class="hover:text-indigo-200">Login</a>
                    <a href="/register" class="bg-white text-indigo-700 px-4 py-2 rounded-lg font-bold shadow">Sign Up</a>
                {% endif %}
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="flex-grow container mx-auto px-4 py-8">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6 rounded shadow-sm">
                        {{ message }}
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        {% block content %}{% endblock %}
    </div>

    <!-- Footer -->
    <footer class="bg-gray-800 text-gray-400 py-6 mt-10">
        <div class="container mx-auto px-4 text-center">
            <p>&copy; 2024 SMM PANEL BD. All Rights Reserved.</p>
        </div>
    </footer>
</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def index():
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="text-center py-16">
        <h1 class="text-5xl font-extrabold text-gray-900 mb-6">বাংলাদেশের সবচেয়ে বিশ্বস্ত <span class="text-indigo-600">SMM প্যানেল</span></h1>
        <p class="text-xl text-gray-600 mb-10 max-w-2xl mx-auto">টেলিগ্রাম মেম্বার, ভিউ এবং রিয়েকশন পান মাত্র কয়েক সেকেন্ডে। সবচেয়ে কম দামে এবং সেরা কোয়ালিটি।</p>
        <div class="flex justify-center space-x-4">
            <a href="/register" class="bg-indigo-600 text-white px-8 py-3 rounded-full text-lg font-bold shadow-xl hover:bg-indigo-700 transition">অ্যাকাউন্ট খুলুন</a>
            <a href="/services" class="bg-white border-2 border-indigo-600 text-indigo-600 px-8 py-3 rounded-full text-lg font-bold hover:bg-indigo-50 transition">সার্ভিস দেখুন</a>
        </div>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if users_col.find_one({"email": email}):
            flash("এই ইমেইল দিয়ে আগেই অ্যাকাউন্ট খোলা হয়েছে!")
        else:
            users_col.insert_one({"email": email, "password": password, "balance": 0.0, "total_spent": 0.0})
            flash("রেজিস্ট্রেশন সফল! এখন লগইন করুন।")
            return redirect('/login')
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
        <h2 class="text-3xl font-bold mb-6 text-center text-gray-800">অ্যাকাউন্ট তৈরি করুন</h2>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-gray-700 font-bold mb-2">ইমেইল এড্রেস</label>
                <input type="email" name="email" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="example@gmail.com" required>
            </div>
            <div class="mb-6">
                <label class="block text-gray-700 font-bold mb-2">পাসওয়ার্ড</label>
                <input type="password" name="password" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="******" required>
            </div>
            <button class="w-full bg-indigo-600 text-white p-3 rounded-xl font-bold hover:bg-indigo-700 transition shadow-lg">Register Now</button>
        </form>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = users_col.find_one({"email": email, "password": password})
        if user:
            session['user'] = email
            return redirect('/dashboard')
        flash("ভুল ইমেইল অথবা পাসওয়ার্ড!")
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
        <h2 class="text-3xl font-bold mb-6 text-center text-gray-800">লগইন</h2>
        <form method="POST">
            <div class="mb-4">
                <input type="email" name="email" placeholder="Email" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" required>
            </div>
            <div class="mb-6">
                <input type="password" name="password" placeholder="Password" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" required>
            </div>
            <button class="w-full bg-green-600 text-white p-3 rounded-xl font-bold hover:bg-green-700 shadow-lg">Login</button>
        </form>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user = users_col.find_one({"email": session['user']})
    orders = list(orders_col.find({"email": session['user']}).sort("_id", -1))
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        <div class="bg-indigo-600 p-6 rounded-2xl text-white shadow-lg">
            <h3 class="text-sm uppercase font-bold opacity-80">বর্তমান ব্যালেন্স</h3>
            <p class="text-3xl font-black mt-2">{{ u.balance }} TK</p>
        </div>
        <div class="bg-white p-6 rounded-2xl border border-gray-100 shadow-md">
            <h3 class="text-sm uppercase font-bold text-gray-500">মোট খরচ</h3>
            <p class="text-3xl font-black text-gray-800 mt-2">{{ u.total_spent }} TK</p>
        </div>
        <div class="bg-green-500 p-6 rounded-2xl text-white shadow-lg">
            <h3 class="text-sm uppercase font-bold opacity-80">টাকা অ্যাড করুন</h3>
            <p class="text-lg mt-2 font-bold">বিকাশ/নগদ: 017XXXXXXXX</p>
        </div>
    </div>
    <div class="bg-white rounded-2xl shadow-md overflow-hidden">
        <div class="bg-gray-50 p-4 border-b"><h3 class="font-bold">অর্ডার হিস্ট্রি</h3></div>
        <table class="w-full text-left">
            <thead class="bg-gray-100 text-gray-600 uppercase text-xs">
                <tr><th class="p-4">Order ID</th><th class="p-4">Cost</th><th class="p-4">Status</th></tr>
            </thead>
            <tbody class="divide-y">
                {% for o in ord %}
                <tr class="hover:bg-gray-50">
                    <td class="p-4 font-mono text-sm">{{ o.order_id }}</td>
                    <td class="p-4 font-bold">{{ o.cost }} TK</td>
                    <td class="p-4"><span class="bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-xs font-bold">{{ o.status }}</span></td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL, u=user, ord=orders)

@app.route('/services')
def services():
    if 'user' not in session: return redirect('/login')
    try:
        res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
    except: res = []
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class="text-3xl font-black mb-8 text-gray-800">সার্ভিস লিস্ট</h2>
    <div class="bg-white rounded-2xl shadow-lg overflow-x-auto">
        <table class="w-full text-left">
            <tr class="bg-indigo-600 text-white">
                <th class="p-4 text-sm font-bold uppercase">ID</th>
                <th class="p-4 text-sm font-bold uppercase">Service Name</th>
                <th class="p-4 text-sm font-bold uppercase">Rate (1k)</th>
                <th class="p-4 text-sm font-bold uppercase">Action</th>
            </tr>
            {% for s in serv %}
            <tr class="border-b hover:bg-indigo-50">
                <td class="p-4 font-bold text-gray-500">{{ s.service }}</td>
                <td class="p-4 text-gray-700 text-sm font-medium">{{ s.name }}</td>
                <td class="p-4 font-black text-indigo-600">{{ (s.rate|float * rate_val)|round(2) }} TK</td>
                <td class="p-4"><a href="/order/{{ s.service }}" class="bg-indigo-600 text-white px-4 py-1 rounded-lg text-sm font-bold shadow hover:bg-indigo-700">Order</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL, serv=res, rate_val=DOLLAR_RATE)

@app.route('/order/<int:sid>', methods=['GET', 'POST'])
def order(sid):
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        link = request.form.get('link')
        qty = int(request.form.get('qty', 0))
        user = users_col.find_one({"email": session['user']})
        
        # API থেকে সার্ভিসের রেট আনা
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = next((float(s['rate']) for s in services if int(s['service']) == sid), None)
        
        if rate is not None:
            cost = (qty / 1000) * (rate * DOLLAR_RATE)
            if user['balance'] < cost:
                flash("আপনার ব্যালেন্স পর্যাপ্ত নয়!")
            else:
                payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': sid, 'link': link, 'quantity': qty}
                res = requests.post(PEAKERR_API_URL, data=payload).json()
                if 'order' in res:
                    users_col.update_one({"email": session['user']}, {"$inc": {"balance": -cost, "total_spent": cost}})
                    orders_col.insert_one({"email": session['user'], "order_id": res['order'], "cost": round(cost, 2), "status": "Pending", "date": datetime.now()})
                    flash("অর্ডার সফল হয়েছে!")
                    return redirect('/dashboard')
                else:
                    flash(f"ভুল হয়েছে: {res.get('error')}")
                    
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="max-w-lg mx-auto bg-white p-8 rounded-3xl shadow-xl border border-gray-100">
        <h2 class="text-2xl font-black mb-6 text-indigo-700">অর্ডার কনফার্ম করুন</h2>
        <div class="mb-6 p-4 bg-gray-50 rounded-xl">
            <p class="text-sm text-gray-500 font-bold">Service ID: {{ service_id }}</p>
        </div>
        <form method="POST">
            <div class="mb-4">
                <label class="block text-gray-700 font-bold mb-2">লিঙ্ক (Link)</label>
                <input type="text" name="link" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="https://t.me/yourchannel" required>
            </div>
            <div class="mb-6">
                <label class="block text-gray-700 font-bold mb-2">পরিমাণ (Quantity)</label>
                <input type="number" name="qty" class="w-full p-3 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" placeholder="1000" required>
            </div>
            <button class="w-full bg-indigo-600 text-white p-3 rounded-xl font-bold hover:bg-indigo-700 shadow-lg">Confirm Order</button>
        </form>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL, service_id=sid)

# --- এডমিন প্যানেল ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != ADMIN_EMAIL: return "অনুমতি নেই!", 403
    if request.method == 'POST':
        target_email = request.form.get('email')
        amount = float(request.form.get('amount', 0))
        users_col.update_one({"email": target_email}, {"$inc": {"balance": amount}})
        flash(f"সফলভাবে {amount} TK এড করা হয়েছে!")
    
    users = list(users_col.find())
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class="text-3xl font-black mb-10 text-red-600">এডমিন ড্যাশবোর্ড</h2>
    <div class="bg-white p-8 rounded-3xl shadow-lg border border-red-100 mb-10">
        <h3 class="text-xl font-bold mb-6">ইউজার ব্যালেন্স রিচার্জ করুন</h3>
        <form method="POST" class="flex flex-col md:flex-row gap-4">
            <input type="email" name="email" placeholder="User Email" class="flex-grow p-3 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none" required>
            <input type="number" name="amount" placeholder="Amount (TK)" class="flex-grow p-3 border rounded-xl focus:ring-2 focus:ring-red-500 outline-none" required>
            <button class="bg-red-600 text-white px-8 py-3 rounded-xl font-bold shadow-lg hover:bg-red-700">Add Money</button>
        </form>
    </div>
    <div class="bg-white rounded-3xl shadow-lg overflow-hidden border border-gray-100">
        <table class="w-full text-left">
            <tr class="bg-gray-100 text-gray-600 uppercase text-xs font-bold">
                <th class="p-4">Email</th><th class="p-4">Current Balance</th>
            </tr>
            {% for u in all_users %}
            <tr class="border-b">
                <td class="p-4">{{ u.email }}</td>
                <td class="p-4 font-black text-green-600">{{ u.balance }} TK</td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, user_session=session.get('user'), admin_mail=ADMIN_EMAIL, all_users=users)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Vercel এ রান করার জন্য
if __name__ == '__main__':
    app.run(debug=True)
