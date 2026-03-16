from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
import random
import uuid

app = Flask(__name__)

# --- MongoDB Configuration ---
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['LudoRealDB']
rooms = db['rooms']

# --- HTML, CSS, JavaScript (Frontend) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <title>Premium Ludo Online - Full Game</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root { --red: #ff3838; --green: #32ff7e; --yellow: #fff200; --blue: #18dcff; --bg: #2f3640; }
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background: var(--bg); color: white; margin: 0; display: flex; flex-direction: column; align-items: center; }
        
        /* Ludo Board Design */
        #game-container { position: relative; width: 360px; height: 360px; background: white; border: 10px solid #333; display: grid; grid-template-columns: repeat(15, 1fr); grid-template-rows: repeat(15, 1fr); box-shadow: 0 10px 30px rgba(0,0,0,0.5); margin-top: 20px; }
        .cell { border: 0.1px solid #ddd; position: relative; }
        
        /* Homes */
        .home { grid-column: span 6; grid-row: span 6; position: relative; border: 1px solid #333; }
        .red-home { background: var(--red); grid-area: 1/1/7/7; }
        .green-home { background: var(--green); grid-area: 1/10/7/16; }
        .blue-home { background: var(--blue); grid-area: 10/1/16/7; }
        .yellow-home { background: var(--yellow); grid-area: 10/10/16/16; }
        .center-finish { grid-area: 7/7/10/10; background: conic-gradient(var(--red) 0 90deg, var(--green) 0 180deg, var(--yellow) 0 270deg, var(--blue) 0 360deg); }

        /* Pawns (গুটি) */
        .pawn { width: 18px; height: 18px; border-radius: 50%; border: 2px solid #000; position: absolute; z-index: 100; transition: all 0.4s; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.4); }
        .pawn-red { background: var(--red); } .pawn-green { background: var(--green); }
        .pawn-blue { background: var(--blue); } .pawn-yellow { background: var(--yellow); }

        /* UI Elements */
        #controls { margin-top: 20px; text-align: center; background: #fff; color: #333; padding: 15px; border-radius: 10px; width: 340px; }
        #dice { width: 50px; height: 50px; border: 3px solid #333; border-radius: 8px; font-size: 24px; font-weight: bold; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; background: #f1c40f; }
        .btn { padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin: 5px; }
        .setup-screen { position: fixed; inset: 0; background: var(--bg); z-index: 1000; display: flex; flex-direction: column; align-items: center; justify-content: center; }
        .path-red { background: var(--red); opacity: 0.6; } .path-green { background: var(--green); opacity: 0.6; }
    </style>
</head>
<body>

<div id="setup-screen" class="setup-screen">
    <h1 style="color:var(--yellow)">Premium Ludo Online</h1>
    <input type="text" id="playerName" placeholder="আপনার নাম" style="padding:10px; border-radius:5px; width:250px;"><br>
    <select id="gameMode" style="padding:10px; width:270px; margin-top:10px;">
        <option value="robot">🤖 খেলুন রোবট এর সাথে</option>
        <option value="1v1">👥 ১ বনাম ১ (অনলাইন)</option>
        <option value="2v2">👨‍👩‍👦‍👦 ২ বনাম ২ (অনলাইন)</option>
        <option value="4way">👨‍👩‍👧‍👦 ৪ জন (All vs All)</option>
    </select><br>
    <button class="btn" style="background:var(--green); color:#000;" onclick="startGame()">গেম শুরু করুন</button>
</div>

<div id="game-ui" style="display:none;">
    <div id="game-container">
        <!-- Homes -->
        <div class="home red-home"></div><div class="home green-home"></div>
        <div class="home blue-home"></div><div class="home yellow-home"></div>
        <div class="center-finish"></div>
        <!-- Cells (63 common cells) -->
        <div id="cells-container"></div>
    </div>

    <div id="controls">
        <h3 id="turn-info" style="margin:0 0 10px 0;">টার্ন: লাল</h3>
        <div id="dice" onclick="rollDice()">🎲</div>
        <p>রুম আইডি: <span id="room-display" style="font-weight:bold; color:var(--red);"></span></p>
        <button class="btn" style="background:#e74c3c; color:white;" onclick="location.reload()">গেম থেকে বের হন</button>
    </div>
</div>

<script>
    let roomId = null; let myColor = 'red'; let turn = 'red'; let myId = null;

    async function startGame() {
        const name = document.getElementById('playerName').value || "খেলোয়াড়";
        const mode = document.getElementById('gameMode').value;
        const res = await fetch('/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, mode})
        });
        const data = await res.json();
        roomId = data.room_id; myId = data.player_id; myColor = data.color;
        initBoardUI();
    }

    function initBoardUI() {
        document.getElementById('setup-screen').style.display = 'none';
        document.getElementById('game-ui').style.display = 'block';
        document.getElementById('room-display').innerText = roomId;
        createPawns();
        setInterval(refreshState, 2000);
    }

    function createPawns() {
        const board = document.getElementById('game-container');
        const colors = ['red', 'green', 'blue', 'yellow'];
        colors.forEach(color => {
            for(let i=1; i<=4; i++) {
                const p = document.createElement('div');
                p.className = `pawn pawn-${color}`;
                p.id = `pawn-${color}-${i}`;
                // শুরুর পজিশন (Home)
                p.style.left = (color === 'red' || color === 'blue') ? "15%" : "70%";
                p.style.top = (color === 'red' || color === 'green') ? "15%" : "70%";
                board.appendChild(p);
            }
        });
    }

    async function rollDice() {
        if(turn !== myColor) return alert("আপনার চালের জন্য অপেক্ষা করুন!");
        const res = await fetch('/roll', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({room_id: roomId, player_id: myId})
        });
        const data = await res.json();
        document.getElementById('dice').innerText = data.roll;
        refreshState();
    }

    async function refreshState() {
        if(!roomId) return;
        const res = await fetch(`/state?room_id=${roomId}`);
        const data = await res.json();
        turn = data.turn_color;
        document.getElementById('turn-info').innerText = "টার্ন: " + turn.toUpperCase();
        document.getElementById('turn-info').style.color = "var(--"+turn+")";
        
        if(data.mode === 'robot' && turn === 'blue') {
            await fetch('/roll_robot', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({room_id: roomId})});
        }
    }
</script>
</body>
</html>
"""

# --- Backend API Routes ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create', methods=['POST'])
def create():
    data = request.json
    r_id = str(uuid.uuid4())[:6].upper()
    mode = data.get('mode', 'robot')
    
    players = [{"id": "p1", "name": data['name'], "color": "red"}]
    if mode == 'robot':
        players.append({"id": "robot", "name": "Robot AI", "color": "blue"})
    
    room_data = {
        "room_id": r_id, "mode": mode, "players": players,
        "turn": 0, "turn_color": "red", "last_roll": 0
    }
    rooms.insert_one(room_data)
    return jsonify({"room_id": r_id, "player_id": "p1", "color": "red"})

@app.route('/state', methods=['GET'])
def state():
    r_id = request.args.get('room_id')
    room = rooms.find_one({"room_id": r_id}, {"_id": 0})
    return jsonify(room)

@app.route('/roll', methods=['POST'])
def roll():
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    roll_val = random.randint(1, 6)
    
    p_len = len(room['players'])
    curr_idx = room['turn']
    next_idx = (curr_idx + 1) % p_len if roll_val != 6 else curr_idx
    
    rooms.update_one({"room_id": data['room_id']}, {
        "$set": {"last_roll": roll_val, "turn": next_idx, "turn_color": room['players'][next_idx]['color']}
    })
    return jsonify({"roll": roll_val})

@app.route('/roll_robot', methods=['POST'])
def roll_robot():
    data = request.json
    roll_val = random.randint(1, 6)
    rooms.update_one({"room_id": data['room_id']}, {
        "$set": {"last_roll": roll_val, "turn": 0, "turn_color": "red"}
    })
    return jsonify({"roll": roll_val})

if __name__ == '__main__':
    app.run(debug=True)
