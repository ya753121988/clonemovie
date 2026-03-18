import os
from flask import Flask, render_template_string, request, redirect, session, flash
from pymongo import MongoClient
import requests

app = Flask(__name__)
app.secret_key = "smm_bd_pro_secure"

# --- আপনার তথ্য ---
PEAKERR_API_KEY = "2de9db5d595a2e304699565d9745d492"
PEAKERR_API_URL = "https://peakerr.com/api/v2"
MONGO_URI = "mongodb+srv://roxiw19528:roxiw19528@cluster0.vl508y4.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_EMAIL = "admin@gmail.com"
DOLLAR_TO_BDT = 120

# ডাটাবেস কানেকশন (Try-Except সহ যাতে ক্রাশ না করে)
try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    db = client['smm_database']
    users_col = db['users']
    orders_col = db['orders']
except Exception as e:
    print(f"DB Connection Error: {e}")

# HTML ডিজাইন
LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SMM Panel BD</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <nav class="bg-indigo-700 p-4 text-white flex justify-between items-center shadow-lg">
        <a href="/" class="font-bold text-xl">SMM BD</a>
        <div class="space-x-4">
            {% if user_session %}
                <a href="/dashboard">Dashboard</a>
                <a href="/services">Services</a>
                {% if user_session == admin_mail %}
                    <a href="/admin" class="bg-red-500 px-2 py-1 rounded">Admin</a>
                {% endif %}
                <a href="/logout" class="text-gray-300">Logout</a>
            {% else %}
                <a href="/login">Login</a>
                <a href="/register" class="bg-white text-indigo-700 px-3 py-1 rounded">Sign Up</a>
            {% endif %}
        </div>
    </nav>
    <div class="container mx-auto p-4">
        {% with messages = get_flashed_messages() %}
            {% if messages %}{% for message in messages %}
                <div class="bg-blue-100 p-3 mb-4 text-center rounded border border-blue-300">{{ message }}</div>
            {% endfor %}{% endif %}
        {% endwith %}
        {% block content %}{% endblock %}
    </div>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(LAYOUT + "{% block content %}<div class='text-center py-20'><h1 class='text-4xl font-bold'>The Best SMM Panel</h1><p class='mt-4 text-gray-600'>Get Members, Views, and Likes instantly.</p><div class='mt-6'><a href='/register' class='bg-indigo-600 text-white px-6 py-2 rounded'>Start Now</a></div></div>{% endblock %}", user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email, pwd = request.form['email'], request.form['password']
        if users_col.find_one({"email": email}): flash("Email already registered!")
        else:
            users_col.insert_one({"email": email, "password": pwd, "balance": 0.0})
            flash("Registration Successful! Please Login.")
            return redirect('/login')
    return render_template_string(LAYOUT + "{% block content %}<div class='max-w-md mx-auto bg-white p-8 rounded shadow'><h2 class='text-2xl font-bold mb-4'>Register</h2><form method='POST'><input type='email' name='email' placeholder='Email' class='w-full border p-2 mb-4' required><input type='password' name='password' placeholder='Password' class='w-full border p-2 mb-4' required><button class='w-full bg-indigo-600 text-white p-2 rounded'>Create Account</button></form></div>{% endblock %}", user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email, pwd = request.form['email'], request.form['password']
        user = users_col.find_one({"email": email, "password": pwd})
        if user:
            session['user'] = email
            return redirect('/dashboard')
        flash("Invalid Credentials!")
    return render_template_string(LAYOUT + "{% block content %}<div class='max-w-md mx-auto bg-white p-8 rounded shadow'><h2 class='text-2xl font-bold mb-4'>Login</h2><form method='POST'><input type='email' name='email' placeholder='Email' class='w-full border p-2 mb-4' required><input type='password' name='password' placeholder='Password' class='w-full border p-2 mb-4' required><button class='w-full bg-green-600 text-white p-2 rounded'>Login</button></form></div>{% endblock %}", user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session: return redirect('/login')
    user = users_col.find_one({"email": session['user']})
    orders = list(orders_col.find({"email": session['user']}).sort("_id", -1))
    return render_template_string(LAYOUT + "{% block content %}<div class='grid grid-cols-1 md:grid-cols-2 gap-4'><div class='bg-white p-6 rounded shadow border-t-4 border-indigo-600'><h3>Balance</h3><p class='text-3xl font-bold'>{{ u.balance }} TK</p></div><div class='bg-white p-6 rounded shadow border-t-4 border-green-500'><h3>Payment</h3><p>Send money to 017XXXXXXXX</p></div></div><div class='bg-white mt-6 rounded shadow'><table class='w-full text-left'><tr class='bg-gray-100'><th class='p-2'>Order ID</th><th class='p-2'>Cost</th><th class='p-2'>Status</th></tr>{% for o in ord %}<tr><td class='p-2'>{{ o.order_id }}</td><td class='p-2'>{{ o.cost }} TK</td><td class='p-2'>{{ o.status }}</td></tr>{% endfor %}</table></div>{% endblock %}", user_session=session.get('user'), admin_mail=ADMIN_EMAIL, u=user, ord=orders)

@app.route('/services')
def services():
    if 'user' not in session: return redirect('/login')
    res = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
    return render_template_string(LAYOUT + """
    {% block content %}
    <h2 class='text-2xl font-bold mb-4'>Services</h2>
    <div class='bg-white rounded shadow overflow-x-auto'><table class='w-full text-left'>
    <tr class='bg-indigo-600 text-white'>
        <th class='p-2 text-sm'>ID</th><th class='p-2 text-sm'>Name</th><th class='p-2 text-sm'>Price (1k)</th><th class='p-2 text-sm'>Action</th>
    </tr>
    {% for s in serv[:50] %}
    <tr class='border-b'><td class='p-2'>{{ s.service }}</td><td class='p-2'>{{ s.name }}</td><td class='p-2'>{{ (s.rate|float * rate)|round(2) }} TK</td><td class='p-2'><a href='/order/{{ s.service }}' class='text-indigo-600 font-bold'>Order</a></td></tr>
    {% endfor %}
    </table></div>{% endblock %}""", user_session=session.get('user'), admin_mail=ADMIN_EMAIL, serv=res, rate=DOLLAR_TO_BDT)

@app.route('/order/<int:sid>', methods=['GET', 'POST'])
def order(sid):
    if 'user' not in session: return redirect('/login')
    if request.method == 'POST':
        link, qty = request.form['link'], int(request.form['qty'])
        user = users_col.find_one({"email": session['user']})
        services = requests.post(PEAKERR_API_URL, data={'key': PEAKERR_API_KEY, 'action': 'services'}).json()
        rate = next(float(s['rate']) for s in services if int(s['service']) == sid)
        cost = (qty / 1000) * (rate * DOLLAR_TO_BDT)
        if user['balance'] < cost: flash("Insufficient balance!")
        else:
            payload = {'key': PEAKERR_API_KEY, 'action': 'add', 'service': sid, 'link': link, 'quantity': qty}
            res = requests.post(PEAKERR_API_URL, data=payload).json()
            if 'order' in res:
                users_col.update_one({"email": session['user']}, {"$inc": {"balance": -cost}})
                orders_col.insert_one({"email": session['user'], "order_id": res['order'], "cost": round(cost,2), "status": "Pending"})
                flash("Order Placed Successfully!")
                return redirect('/dashboard')
            else: flash("API Error")
    return render_template_string(LAYOUT + """{% block content %}<div class='max-w-md mx-auto bg-white p-6 rounded shadow'><h2 class='font-bold mb-4'>Order Service</h2><form method='POST'><input type='text' name='link' placeholder='Link' class='w-full border p-2 mb-4' required><input type='number' name='qty' placeholder='Quantity' class='w-full border p-2 mb-4' required><button class='w-full bg-indigo-600 text-white p-2 rounded'>Confirm Order</button></form></div>{% endblock %}""", user_session=session.get('user'), admin_mail=ADMIN_EMAIL)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if session.get('user') != ADMIN_EMAIL: return "Access Denied"
    if request.method == 'POST':
        target, amount = request.form['email'], float(request.form['amount'])
        users_col.update_one({"email": target}, {"$inc": {"balance": amount}})
        flash("Balance Added!")
    all_users = list(users_col.find())
    return render_template_string(LAYOUT + """{% block content %}<div class='bg-white p-6 rounded shadow mb-4'><h2 class='font-bold mb-4'>Add Money</h2><form method='POST'><input type='email' name='email' placeholder='User Email' class='border p-2 mr-2'><input type='number' name='amount' placeholder='Amount' class='border p-2 mr-2'><button class='bg-red-500 text-white px-4 py-2 rounded'>Add</button></form></div><div class='bg-white p-6 rounded shadow'><table class='w-full text-left'>{% for u in u_list %}<tr><td class='p-2'>{{ u.email }}</td><td class='p-2 font-bold'>{{ u.balance }} TK</td></tr>{% endfor %}</table></div>{% endblock %}""", user_session=session.get('user'), admin_mail=ADMIN_EMAIL, u_list=all_users)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/')

# Flask App for Vercel
if __name__ == "__main__":
    app.run()
