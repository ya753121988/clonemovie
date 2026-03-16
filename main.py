from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
import os
import random
import uuid

app = Flask(__name__)

# --- MongoDB Configuration ---
# Vercel Environment Variable থেকে MONGO_URI নিবে
MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client['ludo_database']
rooms = db['rooms']

# --- HTML/CSS/JS (Frontend) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Online Multiplayer Ludo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; text-align: center; background: #2c3e50; color: white; }
        .container { max-width: 600px; margin: auto; padding: 20px; }
        #board { 
            width: 320px; height: 320px; margin: 20px auto; 
            display: grid; grid-template-columns: repeat(15, 1fr); 
            grid-template-rows: repeat(15, 1fr); background: #ecf0f1; border: 5px solid #34495e;
        }
        .cell { border: 1px solid #bdc3c7; width: 20px; height: 20px; }
        .red { background: #e74c3c; } .blue { background: #3498db; }
        .green { background: #2ecc71; } .yellow { background: #f1c40f; }
        .dice-box { background: #fff; color: #333; padding: 15px; border-radius: 10px; display: inline-block; margin: 10px; }
        button { padding: 10px 20px; font-size: 16px; cursor: pointer; border-radius: 5px; border: none; background: #e67e22; color: white; }
        .status-bar { margin: 15px; font-weight: bold; font-size: 1.2em; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Ludo Online 🎲</h1>
        <div id="setup">
            <input type="text" id="playerName" placeholder="আপনার নাম লিখুন">
            <select id="gameMode">
                <option value="1v1">1 vs 1</option>
                <option value="2v2">2 vs 2 (Team)</option>
                <option value="4way">1 vs 1 vs 1 vs 1</option>
            </select>
            <button onclick="createRoom()">নতুন গেম শুরু করুন</button>
            <br><br>
            <input type="text" id="roomInput" placeholder="রুম আইডি লিখুন">
            <button onclick="joinRoom()">রুমে জয়েন করুন</button>
        </div>

        <div id="gameArea" style="display:none;">
            <div class="status-bar" id="status">প্লেয়ারের জন্য অপেক্ষা করা হচ্ছে...</div>
            <p>রুম আইডি: <span id="displayRoomId" style="color:#f1c40f"></span></p>
            
            <div id="board">
                <!-- বোর্ডে গ্রিড লজিক জাভাস্ক্রিপ্ট দিয়ে জেনারেট হবে -->
            </div>

            <div class="dice-box">
                <div id="diceResult" style="font-size: 30px; margin-bottom: 10px;">🎲</div>
                <button id="rollBtn" onclick="rollDice()">চাল দিন (Roll)</button>
            </div>
        </div>
    </div>

    <script>
        let roomId = null;
        let myId = null;
        let myColor = null;
        let isMyTurn = false;

        async function createRoom() {
            const name = document.getElementById('playerName').value;
            const mode = document.getElementById('gameMode').value;
            const res = await fetch('/create_room', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, mode})
            });
            const data = await res.json();
            roomId = data.room_id;
            myId = data.player_id;
            myColor = data.color;
            startGameUI();
        }

        async function joinRoom() {
            const name = document.getElementById('playerName').value;
            const rId = document.getElementById('roomInput').value;
            const res = await fetch('/join_room', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({name, room_id: rId})
            });
            const data = await res.json();
            if(data.error) return alert(data.error);
            roomId = rId;
            myId = data.player_id;
            myColor = data.color;
            startGameUI();
        }

        function startGameUI() {
            document.getElementById('setup').style.display = 'none';
            document.getElementById('gameArea').style.display = 'block';
            document.getElementById('displayRoomId').innerText = roomId;
            initBoard();
            setInterval(fetchGameState, 2000); // Polling every 2 seconds
        }

        function initBoard() {
            const board = document.getElementById('board');
            board.innerHTML = '';
            for (let i = 0; i < 225; i++) {
                const div = document.createElement('div');
                div.className = 'cell';
                board.appendChild(div);
            }
        }

        async function fetchGameState() {
            if(!roomId) return;
            const res = await fetch(`/get_state?room_id=${roomId}`);
            const data = await res.json();
            
            const status = document.getElementById('status');
            if(data.status === 'waiting') {
                status.innerText = "প্লেয়ারের জন্য অপেক্ষা করুন...";
            } else {
                status.innerText = `এখন চাল: ${data.turn_color.toUpperCase()}`;
                isMyTurn = (data.turn_color === myColor);
                document.getElementById('rollBtn').disabled = !isMyTurn;
                document.getElementById('diceResult').innerText = data.last_roll || '🎲';
            }
        }

        async function rollDice() {
            if(!isMyTurn) return;
            const res = await fetch('/roll', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({room_id: roomId, player_id: myId})
            });
            const data = await res.json();
            document.getElementById('diceResult').innerText = data.roll;
            fetchGameState();
        }
    </script>
</body>
</html>
"""

# --- API Routes ---

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create_room', methods=['POST'])
def create_room():
    data = request.json
    room_id = str(uuid.uuid4())[:6].upper()
    mode = data.get('mode', '1v1')
    
    room_data = {
        "room_id": room_id,
        "mode": mode,
        "status": "waiting",
        "players": [{"id": "p1", "name": data['name'], "color": "red"}],
        "turn": 0,
        "turn_color": "red",
        "last_roll": 0,
        "positions": {"red": [0,0,0,0], "blue": [0,0,0,0], "green": [0,0,0,0], "yellow": [0,0,0,0]}
    }
    rooms.insert_one(room_data)
    return jsonify({"room_id": room_id, "player_id": "p1", "color": "red"})

@app.route('/join_room', methods=['POST'])
def join_room():
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    if not room: return jsonify({"error": "রুম পাওয়া যায়নি!"})
    
    colors = ["red", "blue", "green", "yellow"]
    p_count = len(room['players'])
    
    # Mode check
    limit = 2 if room['mode'] == '1v1' else 4
    if p_count >= limit: return jsonify({"error": "রুম ফুল!"})
    
    new_player = {
        "id": f"p{p_count+1}",
        "name": data['name'],
        "color": colors[p_count]
    }
    
    new_status = "active" if p_count + 1 == limit else "waiting"
    
    rooms.update_one(
        {"room_id": data['room_id']},
        {"$push": {"players": new_player}, "$set": {"status": new_status}}
    )
    return jsonify({"player_id": new_player['id'], "color": new_player['color']})

@app.route('/get_state', methods=['GET'])
def get_state():
    room_id = request.args.get('room_id')
    room = rooms.find_one({"room_id": room_id}, {"_id": 0})
    return jsonify(room)

@app.route('/roll', methods=['POST'])
def roll():
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    
    # সঠিক প্লেয়ার চাল দিচ্ছে কি না চেক
    current_player_idx = room['turn']
    if room['players'][current_player_idx]['id'] != data['player_id']:
        return jsonify({"error": "Not your turn"})

    dice_roll = random.randint(1, 6)
    
    # পরবর্তী টার্ন সেট করা (যদি ৬ না পড়ে)
    next_turn = current_player_idx
    if dice_roll != 6:
        next_turn = (current_player_idx + 1) % len(room['players'])
    
    # ২ বনাম ২ টিমের চাল স্কিপ করার লজিক (ঐচ্ছিক)
    # (Team 1 = 0 & 2 index, Team 2 = 1 & 3 index)

    rooms.update_one(
        {"room_id": data['room_id']},
        {
            "$set": {
                "last_roll": dice_roll,
                "turn": next_turn,
                "turn_color": room['players'][next_turn]['color']
            }
        }
    )
    
    return jsonify({"roll": dice_roll})

if __name__ == '__main__':
    app.run(debug=True)
