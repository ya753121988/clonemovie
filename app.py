import os
from flask import Flask, render_template_string, request, redirect, session, url_for, flash
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.secret_key = "smm_secret_key_99"

# --- আপনার তথ্য ---
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_EMAIL = "admin@gmail.com" # আপনার ইমেইল এখানে দিন
DOLLAR_RATE = 125 

# ডাটাবেস কানেকশন
client = MongoClient(MONGO_URI)
db = client['smm_panel_db']
users_col = db['users']
orders_col = db['orders']

# ডিজাইন (HTML Layout)
LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM Panel</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-blue-600 p-4 text-white flex justify-between items-center">
        <a href="/" class="font-bold text-xl">SMM BD</a>
        <div class="space-x-4">
            {% if session.get('user') %}
                <a href="/dashboard">Dashboard</a>
                <a href="/services">Services</a>
                {% if session['user'] == admin_mail %}
                    <a href="/admin" class="bg-red-500 px-2 py-1 rounded">Admin</a>
                {% endif %}
                <a href="/logout">Logout</a>
            {% else %}
                <a href="/login">Login</a>
                <a href="/register">Register</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mx-auto p-4">
        {% with messages = get_flashed_messages() %}{% if messages %}
            {% for message in messages %}<div class="bg-yellow-200 p-2 mb-4 text-center rounded">{{ message }}</div>{% endfor %}
        {% endif %}{% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(LAYOUT + "{% block content %}<div class='text-center py-20'><h1 class='text-4xl font-bold'>Welcome to SMM Panel</h1><p class='mt-4'>Get Telegram Members and Views Instantly.</p></div>{% endblock %}", admin_mail=ADMIN_EMAIL)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        if users_col.find_one({"email": email}): flash("Email already exists!")
        else:
            users_col.insert_one({"email": email, "password": password, "balance": 0.0})
            flash("Success! Please Login.")
            return redirect('/login')
    return render_template_string(LAYOUT + "{% block content %}<div class='max-w-md mx-auto bg-white p-6 rounded shadow'><h2 class='text-xl font-bold mb-4'>Register</h2><form method='POST'><input type='email' name='email' placeholder='Email' class='w-full border p-2 mb-2' required><input type='password' name='password' placeholder='Password' class='w-full border p-2 mb-2' required><button class='w-full bg-blue-600 text-white p-2 rounded'>Register</button></form></div>{% endblock %}", admin_mail=ADMIN_EMAIL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, password = request.form['email'], request.form['password']
        user = users_col.find_one({"email": email, "password": password})
        if user:
            session['user'] = email
            return redirect('/dashboard')
        flash("Invalid login!")
    return render_template_string(LAYOUT + "{% block content %}<div class='max-w-md mx-auto bg-white p-6 rounded shadow'><h2 class='text-xl font-bold mb-4'>Login</h2><form method='POST'><input type='email' name='email' placeholder='Email' class='w-full border p-2 mb-2' required><input type='password' name='password' placeholder='Password' class='w-full border p-2 mb-2' required><button class='w-full bg-green-600 text-white p-2 rounded'>Login</button></form></div>{% endblock %}", admin_mail=ADMIN_EMAIL)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user = users_col.find_one({"email": session['user']})
    orders = list(orders_col.find({"email": session['user']}).sort("_id", -1))
    return render_template_string(LAYOUT + "{% block content %}<div class='grid grid-cols-1 md:grid-cols-2 gap-4'><div class='bg-blue-500 p-6 text-white rounded'><h3>Balance</h3><p class='text-2xl'>{{ u.balance }} TK</p></div><div class='bg-white p-6 rounded shadow'><h3>Order History</h3><table class='w-full text-sm mt-2'>{% for o in ord %}<tr><td class='border-b p-1'>ID: {{ o.order_id }}</td><td class='border-b p-1'>{{ o.cost }} TK</td><td class='border-b p-1 text-blue-500'>{{ o.status }}</td></tr>{% endfor %}</table></div></div>{% endblock %}", u=user, ord=orders, admin_mail=ADMIN_EMAIL)

@app.route('/services')
def services():
    if 'user' not in session: return redirect('/login')
    res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class='text-xl font-bold mb-4'>Services</h2>
    <div class='bg-white rounded shadow overflow-x-auto'>
    <table class='w-full text-left'>
    <tr class='bg-gray-200 font-bold'><td class='p-2'>ID</td><td class='p-2'>Name</td><td class='p-2'>Price (1k)</td><td class='p-2'>Action</td></tr>
    {% for s in serv[:30] %}
    <tr><td class='p-2'>{{ s.service }}</td><td class='p-2'>{{ s.name }}</td><td class='p-2'>{{ (s.rate|float * rate)|round(2) }} TK</td><td class='p-2'><a href='/order/{{ s.service }}' class='text-blue-600'>Order</a></td></tr>
    {% endfor %}
    </table></div>{% endblock %}""", serv=res, rate=DOLLAR_RATE, admin_mail=ADMIN_EMAIL)

@app.route('/order/<int:sid>', methods=['GET', 'POST'])
def order(sid):
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        link, qty = request.form['link'], int(request.form['qty'])
        user = users_col.find_one({"email": session['user']})
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = next(float(s['rate']) for s in services if int(s['service']) == sid)
        cost = (qty / 1000) * (rate * DOLLAR_RATE)
        
        if user['balance'] < cost: flash("Low balance!")
        else:
            payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': sid, 'link': link, 'quantity': qty}
            res = requests.post(PEAKERR_API_URL, data=payload).json()
            if 'order' in res:
                users_col.update_one({"email": session['user']}, {"$inc": {"balance": -cost}})
                orders_col.insert_one({"email": session['user'], "order_id": res['order'], "cost": round(cost,2), "status": "Pending"})
                flash("Order Placed!")
                return redirect('/dashboard')
            else: flash("Error: " + str(res.get('error')))
    return render_template_string(LAYOUT + f"{{% block content %}}<div class='max-w-md mx-auto bg-white p-6 shadow'><h2 class='font-bold mb-4'>Place Order (ID: {sid})</h2><form method='POST'><input type='text' name='link' placeholder='Channel Link' class='w-full border p-2 mb-2'><input type='number' name='qty' placeholder='Quantity' class='w-full border p-2 mb-2'><button class='w-full bg-blue-600 text-white p-2 rounded'>Order Now</button></form></div>{{% endblock %}}", admin_mail=ADMIN_EMAIL)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != ADMIN_EMAIL: return "Access Denied"
    if request.method == 'POST':
        target, amount = request.form['email'], float(request.form['amount'])
        users_col.update_one({"email": target}, {"$inc": {"balance": amount}})
        flash("Balance Added!")
    all_users = list(users_col.find())
    return render_template_string(LAYOUT + """
    {% block content %}
    <div class='bg-white p-6 rounded shadow mb-4'><h2 class='font-bold mb-2'>Add Balance</h2><form method='POST'><input type='email' name='email' placeholder='User Email' class='border p-2 mr-2'><input type='number' name='amount' placeholder='Amount' class='border p-2 mr-2'><button class='bg-red-500 text-white p-2 px-4 rounded'>Add</button></form></div>
    <div class='bg-white p-6 rounded shadow'><h2 class='font-bold mb-2'>Users</h2><table class='w-full'>{% for u in u_list %}<tr><td>{{ u.email }}</td><td>{{ u.balance }} TK</td></tr>{% endfor %}</table></div>
    {% endblock %}""", u_list=all_users, admin_mail=ADMIN_EMAIL)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Vercel needs this
if __name__ == '__main__':
    app.run()
