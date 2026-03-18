import os
from flask import Flask, render_template_string, request, redirect, session, flash
from pymongo import MongoClient
import requests
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "smm_bd_secret_key_pro"

# --- আপনার তথ্যসমূহ ---
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_EMAIL = "admin@gmail.com" # এই ইমেইল দিয়ে রেজিস্টার করলে এডমিন প্যানেল পাবেন
DOLLAR_TO_BDT = 120 # ১ ডলার = ১২০ টাকা (লাভসহ)

# ডাটাবেস কানেকশন
try:
    client = MongoClient(MONGO_URI)
    db = client['smm_database']
    users_col = db['users']
    orders_col = db['orders']
except Exception as e:
    print(f"Database Connection Error: {e}")

# --- HTML ডিজাইন (Tailwind CSS ব্যবহার করা হয়েছে) ---
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM BD - Professional Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-50 font-sans">
    <nav class="bg-indigo-700 p-4 text-white shadow-lg">
        <div class="container mx-auto flex justify-between items-center">
            <a href="/" class="text-2xl font-bold tracking-tight">SMM BD</a>
            <div class="space-x-4 font-medium">
                {% if session.get('user') %}
                    <a href="/dashboard" class="hover:text-indigo-200">Dashboard</a>
                    <a href="/services" class="hover:text-indigo-200">Services</a>
                    {% if session['user'] == admin_mail %}
                        <a href="/admin" class="bg-red-500 px-3 py-1 rounded hover:bg-red-600">Admin</a>
                    {% endif %}
                    <a href="/logout" class="text-indigo-200">Logout</a>
                {% else %}
                    <a href="/login" class="hover:text-indigo-200">Login</a>
                    <a href="/register" class="bg-white text-indigo-700 px-4 py-2 rounded">Sign Up</a>
                {% endif %}
            </div>
        </div>
    </nav>
    <div class="container mx-auto mt-8 px-4">
        {% with messages = get_flashed_messages() %}
            {% if messages %}{% for message in messages %}
                <div class="bg-blue-100 border-l-4 border-blue-500 text-blue-700 p-4 mb-6 shadow-sm" role="alert">{{ message }}</div>
            {% endfor %}{% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="text-center py-20">
        <h1 class="text-5xl font-extrabold text-gray-900 mb-4">স্বল্প মূল্যে মেম্বার ও ভিউ কিনুন</h1>
        <p class="text-xl text-gray-600 mb-8">টেলিগ্রামের সকল সার্ভিস এখন এক ক্লিকেই। অটোমেটিক ডেলিভারি।</p>
        <a href="/register" class="bg-indigo-600 text-white px-8 py-4 rounded-full text-lg font-bold shadow-xl hover:bg-indigo-700">এখনই শুরু করুন</a>
    </div>
    {% endblock %}
    """, admin_mail=ADMIN_EMAIL)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        if users_col.find_one({"email": email}): flash("ইমেইলটি আগে থেকেই আছে!")
        else:
            users_col.insert_one({"email": email, "password": password, "balance": 0.0})
            flash("রেজিস্ট্রেশন সফল! লগইন করুন।")
            return redirect('/login')
    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
        <h2 class="text-3xl font-bold mb-6 text-center">Registration</h2>
        <form method="POST">
            <label class="block mb-2 text-sm font-bold text-gray-700">Email Address</label>
            <input type="email" name="email" class="w-full p-3 border rounded-lg mb-4 focus:ring-2 focus:ring-indigo-500 outline-none" required>
            <label class="block mb-2 text-sm font-bold text-gray-700">Password</label>
            <input type="password" name="password" class="w-full p-3 border rounded-lg mb-6 focus:ring-2 focus:ring-indigo-500 outline-none" required>
            <button class="w-full bg-indigo-600 text-white p-3 rounded-lg font-bold hover:bg-indigo-700 transition">Create Account</button>
        </form>
    </div>
    {% endblock %}
    """, admin_mail=ADMIN_EMAIL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = users_col.find_one({"email": email, "password": password})
        if user:
            session['user'] = email
            return redirect('/dashboard')
        flash("ভুল ইমেইল বা পাসওয়ার্ড!")
    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-xl border border-gray-100">
        <h2 class="text-3xl font-bold mb-6 text-center">User Login</h2>
        <form method="POST">
            <input type="email" name="email" placeholder="Email" class="w-full p-3 border rounded-lg mb-4" required>
            <input type="password" name="password" placeholder="Password" class="w-full p-3 border rounded-lg mb-6" required>
            <button class="w-full bg-indigo-600 text-white p-3 rounded-lg font-bold">Login</button>
        </form>
    </div>
    {% endblock %}
    """, admin_mail=ADMIN_EMAIL)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user = users_col.find_one({"email": session['user']})
    orders = list(orders_col.find({"email": session['user']}).sort("_id", -1))
    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="grid grid-cols-1 md:grid-cols-2 gap-8 mb-10">
        <div class="bg-white p-8 rounded-2xl shadow-md border-t-4 border-indigo-600">
            <h3 class="text-gray-500 font-bold uppercase text-xs">আপনার ব্যালেন্স</h3>
            <p class="text-4xl font-black text-indigo-700 mt-2">{{ u.balance }} TK</p>
        </div>
        <div class="bg-white p-8 rounded-2xl shadow-md border-t-4 border-green-500">
            <h3 class="text-gray-500 font-bold uppercase text-xs">রিচার্জ পদ্ধতি</h3>
            <p class="mt-2 text-gray-700 font-medium">বিকাশ/নগদ (পার্সোনাল): 017XXXXXXXX</p>
            <p class="text-sm text-gray-500 mt-1">টাকা পাঠিয়ে ট্রানজেকশন আইডি এডমিনকে দিন।</p>
        </div>
    </div>
    <div class="bg-white rounded-2xl shadow-md overflow-hidden">
        <div class="p-6 border-b"><h3 class="font-bold text-xl">আপনার অর্ডারসমূহ</h3></div>
        <table class="w-full text-left">
            <thead class="bg-gray-50 text-gray-600 uppercase text-xs font-bold">
                <tr><th class="p-4">Order ID</th><th class="p-4">Cost</th><th class="p-4">Status</th></tr>
            </thead>
            <tbody class="divide-y">
                {% for o in ord %}
                <tr><td class="p-4 font-mono">{{ o.order_id }}</td><td class="p-4 font-bold">{{ o.cost }} TK</td>
                <td class="p-4"><span class="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-xs font-bold">{{ o.status }}</span></td></tr>
                {% endfor %}
            </tbody>
        </table>
    </div>
    {% endblock %}
    """, u=user, ord=orders, admin_mail=ADMIN_EMAIL)

@app.route('/services')
def services():
    if 'user' not in session: return redirect('/login')
    try:
        res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
    except: res = []
    return render_template_string(BASE_HTML + """
    {% block content %}
    <h2 class="text-3xl font-black mb-8 text-gray-800">সার্ভিস লিস্ট</h2>
    <div class="bg-white rounded-2xl shadow-lg overflow-x-auto">
        <table class="w-full text-left">
            <tr class="bg-indigo-700 text-white uppercase text-sm font-bold">
                <th class="p-4">ID</th><th class="p-4">Service Name</th><th class="p-4">Price (1k)</th><th class="p-4">Action</th>
            </tr>
            {% for s in serv %}
            <tr class="border-b hover:bg-gray-50 transition">
                <td class="p-4 font-bold text-gray-500">{{ s.service }}</td>
                <td class="p-4 text-gray-700">{{ s.name }}</td>
                <td class="p-4 font-black text-indigo-600">{{ (s.rate|float * rate)|round(2) }} TK</td>
                <td class="p-4"><a href="/order/{{ s.service }}" class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-bold shadow-md">Order</a></td>
            </tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, serv=res, rate=DOLLAR_TO_BDT, admin_mail=ADMIN_EMAIL)

@app.route('/order/<int:sid>', methods=['GET', 'POST'])
def order(sid):
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        link, qty = request.form['link'], int(request.form['qty'])
        user = users_col.find_one({"email": session['user']})
        
        # সার্ভিস রেট চেক
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = next((float(s['rate']) for s in services if int(s['service']) == sid), None)
        
        if rate is None: flash("Invalid Service ID")
        else:
            cost = (qty / 1000) * (rate * DOLLAR_TO_BDT)
            if user['balance'] < cost: flash("Insufficient Balance!")
            else:
                payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': sid, 'link': link, 'quantity': qty}
                res = requests.post(PEAKERR_API_URL, data=payload).json()
                if 'order' in res:
                    users_col.update_one({"email": session['user']}, {"$inc": {"balance": -cost}})
                    orders_col.insert_one({"email": session['user'], "order_id": res['order'], "cost": round(cost,2), "status": "Pending"})
                    flash(f"Order Successful! Order ID: {res['order']}")
                    return redirect('/dashboard')
                else: flash(f"API Error: {res.get('error')}")

    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="max-w-lg mx-auto bg-white p-10 rounded-3xl shadow-2xl border border-gray-100">
        <h2 class="text-3xl font-black mb-6 text-indigo-700">Place Order</h2>
        <p class="text-sm text-gray-500 mb-6 font-bold uppercase">Service ID: {{ sid }}</p>
        <form method="POST" class="space-y-6">
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Target Link</label>
                <input type="text" name="link" placeholder="https://t.me/yourchannel" class="w-full p-4 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" required>
            </div>
            <div>
                <label class="block text-sm font-bold text-gray-700 mb-1">Quantity</label>
                <input type="number" name="qty" placeholder="1000" class="w-full p-4 border rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none" required>
            </div>
            <button class="w-full bg-indigo-600 text-white p-4 rounded-xl font-black text-lg shadow-xl hover:bg-indigo-700 transition">Confirm Order</button>
        </form>
    </div>
    {% endblock %}
    """, sid=sid, admin_mail=ADMIN_EMAIL)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != ADMIN_EMAIL: return "Access Denied"
    if request.method == 'POST':
        target_email, amount = request.form['email'], float(request.form['amount'])
        users_col.update_one({"email": target_email}, {"$inc": {"balance": amount}})
        flash(f"Success! Added {amount} TK to {target_email}")
    
    users_list = list(users_col.find())
    return render_template_string(BASE_HTML + """
    {% block content %}
    <div class="bg-white p-8 rounded-3xl shadow-lg mb-10 border-l-8 border-red-500">
        <h2 class="text-2xl font-black mb-6">User Balance Manager</h2>
        <form method="POST" class="flex flex-col md:flex-row gap-4">
            <input type="email" name="email" placeholder="User Email" class="flex-grow p-3 border rounded-xl shadow-inner" required>
            <input type="number" name="amount" placeholder="Amount (TK)" class="flex-grow p-3 border rounded-xl shadow-inner" required>
            <button class="bg-red-600 text-white px-8 py-3 rounded-xl font-bold hover:bg-red-700">Add Balance</button>
        </form>
    </div>
    <div class="bg-white rounded-3xl shadow-lg overflow-hidden">
        <h3 class="p-6 bg-gray-50 font-bold border-b">Registered Users</h3>
        <table class="w-full text-left divide-y">
            <tr class="bg-gray-100 text-gray-600 text-xs font-bold uppercase">
                <th class="p-4">User Email</th><th class="p-4">Balance</th>
            </tr>
            {% for u in users %}
            <tr><td class="p-4 font-medium">{{ u.email }}</td><td class="p-4 font-black text-green-600">{{ u.balance }} TK</td></tr>
            {% endfor %}
        </table>
    </div>
    {% endblock %}
    """, users=users_list, admin_mail=ADMIN_EMAIL)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True)
