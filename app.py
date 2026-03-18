import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
import requests
from datetime import datetime

app = Flask(__name__)
app.secret_key = "secret_key_123" # নিরাপত্তার জন্য এটি পরিবর্তন করতে পারেন

# --- আপনার দেওয়া তথ্যসমূহ ---
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_EMAIL = "admin@gmail.com" # আপনার এডমিন ইমেইল
DOLLAR_RATE = 125 # ১ ডলার = ১২৫ টাকা (আপনার লাভসহ)

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['smm_website_db']
users_col = db['users']
orders_col = db['orders']

# --- HTML টেমপ্লেট (ডিজাইন) ---
# সুবিধার্থে আমি সব ডিজাইন এক ফাইলেই স্ট্রিং আকারে রাখছি
LAYOUT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM Panel - Professional</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 p-4 text-white flex justify-between">
        <a href="/" class="font-bold text-xl">SMM PANEL BD</a>
        <div>
            {% if session.get('user') %}
                <a href="/dashboard" class="mx-2">Dashboard</a>
                <a href="/services" class="mx-2">Services</a>
                {% if session['user'] == 'admin@gmail.com' %}
                    <a href="/admin" class="bg-red-500 px-3 py-1 rounded">Admin Panel</a>
                {% endif %}
                <a href="/logout" class="mx-2 text-gray-200">Logout</a>
            {% else %}
                <a href="/login" class="mx-2">Login</a>
                <a href="/register" class="mx-2">Register</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mx-auto p-6">
        {% with messages = get_flashed_messages() %}
          {% if messages %}
            {% for message in messages %}
              <div class="bg-yellow-200 p-3 mb-4 rounded text-center">{{ message }}</div>
            {% endfor %}
          {% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

# --- রুটস (Routes) ---

@app.route('/')
def index():
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="text-center mt-20">
        <h1 class="text-5xl font-bold text-blue-700">বাংলাদেশের সেরা SMM প্যানেল</h1>
        <p class="mt-4 text-gray-600">টেলিগ্রাম মেম্বার, ভিউ এবং রিয়েকশন পান সবচেয়ে কম দামে।</p>
        <div class="mt-6">
            <a href="/register" class="bg-blue-600 text-white px-6 py-3 rounded-lg shadow-lg">শুরু করুন</a>
        </div>
    </div>
    {% endblock %}
    """)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        if users_col.find_one({"email": email}):
            flash("ইমেইলটি আগে থেকেই আছে!")
        else:
            users_col.insert_one({"email": email, "password": password, "balance": 0.0})
            flash("রেজিস্ট্রেশন সফল! লগইন করুন।")
            return redirect('/login')
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">অ্যাকাউন্ট তৈরি করুন</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" class="w-full p-2 mb-4 border rounded" required>
            <input type="password" name="password" placeholder="Password" class="w-full p-2 mb-4 border rounded" required>
            <button class="w-full bg-blue-600 text-white p-2 rounded">Register</button>
        </form>
    </div>
    {% endblock %}
    """)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = users_col.find_one({"email": email, "password": password})
        if user:
            session['user'] = email
            return redirect('/dashboard')
        flash("ভুল ইমেইল বা পাসওয়ার্ড!")
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">লগইন করুন</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" class="w-full p-2 mb-4 border rounded" required>
            <input type="password" name="password" placeholder="Password" class="w-full p-2 mb-4 border rounded" required>
            <button class="w-full bg-green-600 text-white p-2 rounded">Login</button>
        </form>
    </div>
    {% endblock %}
    """)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user = users_col.find_one({"email": session['user']})
    orders = list(orders_col.find({"email": session['user']}).sort("_id", -1))
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div class="bg-blue-500 p-6 text-white rounded shadow">
            <h3 class="text-lg">বর্তমান ব্যালেন্স</h3>
            <p class="text-3xl font-bold">{{ user.balance }} TK</p>
        </div>
        <div class="bg-green-500 p-6 text-white rounded shadow col-span-2">
            <h3 class="text-lg">বিকাশ/নগদ রিচার্জ</h3>
            <p>টাকা পাঠিয়ে ট্রানজেকশন আইডি এডমিনকে দিন: 017XXXXXXXX</p>
        </div>
    </div>
    <div class="mt-10 bg-white p-6 rounded shadow">
        <h3 class="text-xl font-bold mb-4">অর্ডার হিস্ট্রি</h3>
        <table class="w-full text-left">
            <thead>
                <tr><th class="border-b p-2">Order ID</th><th class="border-b p-2">Cost</th><th class="border-b p-2">Status</th></tr>
            </thead>
            <tbody>
                {% for o in orders %}
                <tr><td class="p-2">{{ o.order_id }}</td><td class="p-2">{{ o.cost }} TK</td><td class="p-2 text-blue-600">{{ o.status }}</td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endblock %}
    """, user=user, orders=orders)

@app.route('/services')
def services():
    if 'user' not in session: return redirect('/login')
    # Peakerr থেকে সার্ভিস আনা
    res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class="text-2xl font-bold mb-6">আমাদের সার্ভিসসমূহ</h2>
    <div class="bg-white rounded shadow overflow-hidden">
        <table class="w-full text-left">
            <tr class="bg-gray-200">
                <th class="p-3">ID</th><th class="p-3">Service Name</th><th class="p-3">Rate (1000)</th><th class="p-3">Action</th>
            </tr>
            {% for s in services[:50] %}
            <tr class="border-b">
                <td class="p-3">{{ s.service }}</td>
                <td class="p-3">{{ s.name }}</td>
                <td class="p-3">{{ (s.rate|float * rate)|round(2) }} TK</td>
                <td class="p-3"><a href="/order/{{ s.service }}" class="bg-blue-600 text-white px-3 py-1 rounded">Order</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, services=res, rate=DOLLAR_RATE)

@app.route('/order/<int:sid>', methods=['GET', 'POST'])
def order(sid):
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        link = request.form['link']
        qty = int(request.form['qty'])
        user = users_col.find_one({"email": session['user']})
        
        # সার্ভিস রেট বের করা (নিরাপত্তার জন্য আবার চেক করা)
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = next(float(s['rate']) for s in services if int(s['service']) == sid)
        cost = (qty / 1000) * (rate * DOLLAR_RATE)
        
        if user['balance'] < cost:
            flash("পর্যাপ্ত ব্যালেন্স নেই!")
        else:
            # Peakerr API Call
            payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': sid, 'link': link, 'quantity': qty}
            res = requests.post(PEAKERR_API_URL, data=payload).json()
            if 'order' in res:
                users_col.update_one({"email": session['user']}, {"$inc": {"balance": -cost}})
                orders_col.insert_one({"email": session['user'], "order_id": res['order'], "cost": cost, "status": "Pending"})
                flash("অর্ডার সফল হয়েছে!")
                return redirect('/dashboard')
            else:
                flash("API Error: " + res.get('error'))
                
    return render_template_string(LAYOUT + f"""
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded shadow">
        <h2 class="text-2xl font-bold mb-4">অর্ডার কনফার্ম করুন (Service ID: {sid})</h2>
        <form method="POST">
            <input type="text" name="link" placeholder="Link (Example: https://t.me/channel)" class="w-full p-2 mb-4 border rounded" required>
            <input type="number" name="qty" placeholder="Quantity (Example: 1000)" class="w-full p-2 mb-4 border rounded" required>
            <button class="w-full bg-blue-700 text-white p-2 rounded">অর্ডার দিন</button>
        </form>
    </div>
    {% endblock %}
    """)

# --- ADMIN PANEL ---

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != ADMIN_EMAIL: return "Access Denied"
    
    if request.method == 'POST':
        target_email = request.form['email']
        amount = float(request.form['amount'])
        users_col.update_one({"email": target_email}, {"$inc": {"balance": amount}})
        flash(f"সফলভাবে {amount} TK এড করা হয়েছে!")

    all_users = list(users_col.find())
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class="text-3xl font-bold mb-6 text-red-600">Admin Panel</h2>
    <div class="bg-white p-6 rounded shadow mb-10">
        <h3 class="text-xl mb-4">ইউজার ব্যালেন্স এড করুন</h3>
        <form method="POST" class="flex gap-4">
            <input type="email" name="email" placeholder="User Email" class="border p-2 rounded w-full" required>
            <input type="number" name="amount" placeholder="Amount (TK)" class="border p-2 rounded w-full" required>
            <button class="bg-red-500 text-white px-6 py-2 rounded">Add Money</button>
        </form>
    </div>
    <div class="bg-white p-6 rounded shadow">
        <h3 class="text-xl mb-4">ইউজার লিস্ট</h3>
        <table class="w-full text-left border">
            <tr class="bg-gray-100">
                <th class="p-2">Email</th><th class="p-2">Balance</th>
            </tr>
            {% for u in users %}
            <tr><td class="p-2">{{ u.email }}</td><td class="p-2">{{ u.balance }} TK</td></tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, users=all_users)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
