from flask import Flask, request, jsonify, render_template_string
from pymongo import MongoClient
import os

app = Flask(__name__)

# আপনার দেওয়া MongoDB Connection String
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['test_db']
collection = db['users']

# ফ্রন্টেন্ড HTML (এক ফাইলেই রাখা হয়েছে)
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MongoDB + Vercel (Python)</title>
    <style>
        body { font-family: Arial; text-align: center; margin-top: 50px; background: #f4f4f4; }
        input { padding: 10px; width: 200px; }
        button { padding: 10px; cursor: pointer; background: blue; color: white; border: none; }
        ul { list-style: none; padding: 0; }
        li { background: white; margin: 5px auto; width: 300px; padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <h1>Python MongoDB App</h1>
    <form action="/add" method="POST">
        <input type="text" name="username" placeholder="Enter Name" required>
        <button type="submit">Add User</button>
    </form>
    <h2>User List:</h2>
    <ul>
        {% for user in users %}
            <li>{{ user.username }}</li>
        {% endfor %}
    </ul>
</body>
</html>
'''

@app.route('/')
def index():
    users = list(collection.find({}, {'_id': 0}))
    return render_template_string(HTML_TEMPLATE, users=users)

@app.route('/add', methods=['POST'])
def add_user():
    username = request.form.get('username')
    if username:
        collection.insert_one({'username': username})
    return '''<script>window.location.href="/";</script>'''

if __name__ == '__main__':
    app.run(debug=True)
