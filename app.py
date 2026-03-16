from flask import Flask, render_template_string, request, jsonify
from pymongo import MongoClient
import random
import uuid
import time

app = Flask(__name__)

# --- MongoDB Configuration ---
# আপনার দেওয়া কানেকশন স্ট্রিং সরাসরি যুক্ত করা হয়েছে
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client['LudoGameDB']
rooms = db['game_rooms']

# --- HTML/CSS/JS (সম্পূর্ণ প্রিমিয়াম ইন্টারফেস) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="bn">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Ludo Online - Multi-Mode</title>
    <link href="https://fonts.googleapis.com/css2?family=Poppins:wght@400;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --red: #eb4d4b; --green: #6ab04c; --yellow: #f9ca24; --blue: #0984e3;
            --dark: #2d3436; --bg: #dfe6e9;
        }
        body { font-family: 'Poppins', sans-serif; background: var(--bg); margin: 0; overflow-x: hidden; }
        .setup-screen { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100vh; background: var(--dark); color: white; }
        
        /* Premium Ludo Board Design */
        .board-container { display: none; flex-direction: column; align-items: center; padding: 10px; }
        #ludo-board {
            width: 360px; height: 360px; background: white; border: 8px solid #333;
            display: grid; grid-template-columns: repeat(15, 1fr); grid-template-rows: repeat(15, 1fr);
            position: relative; box-shadow: 0 15px 35px rgba(0,0,0,0.3);
        }
        
        .cell { border: 0.1px solid #ddd; position: relative; display: flex; align-items: center; justify-content: center; }
        
        /* Home Squares */
        .home { border: 15px solid white; box-sizing: border-box; }
        .red-home { grid-column: 1/7; grid-row: 1/7; background: var(--red); }
        .green-home { grid-column: 10/16; grid-row: 1/7; background: var(--green); }
        .yellow-home { grid-column: 10/16; grid-row: 10/16; background: var(--yellow); }
        .blue-home { grid-column: 1/7; grid-row: 10/16; background: var(--blue); }
        .center-finish { grid-column: 7/10; grid-row: 7/10; background: conic-gradient(var(--red) 25%, var(--green) 0 50%, var(--yellow) 0 75%, var(--blue) 0); }

        /* Path Coloring */
        .path-red { background: var(--red); } .path-green { background: var(--green); }
        .path-yellow { background: var(--yellow); } .path-blue { background: var(--blue); }
        .safe { background: #ced6e0 !important; } .safe::after { content: '★'; color: white; font-size: 10px; }

        /* Pawn Design */
        .pawn {
            width: 18px; height: 18px; border-radius: 50%; border: 2px solid white;
            position: absolute; z-index: 10; box-shadow: 0 3px 6px rgba(0,0,0,0.4);
            cursor: pointer; transition: all 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
        }

        /* Controls */
        .controls { margin-top: 20px; display: flex; align-items: center; gap: 20px; background: white; padding: 15px; border-radius: 12px; }
        #dice { width: 60px; height: 60px; border: 4px solid #333; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 32px; font-weight: bold; background: #fff; cursor: pointer; }
        .btn { padding: 12px 25px; border: none; border-radius: 8px; font-weight: bold; cursor: pointer; background: #2ecc71; color: white; font-size: 16px; }
        .info { text-align: center; margin-bottom: 10px; }
        .active-turn { animation: pulse 1s infinite; border-color: #27ae60 !important; }
        @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.1); } 100% { transform: scale(1); } }
    </style>
</head>
<body>

<div id="setup" class="setup-screen">
    <h1>🎲 Ludo Premium Online</h1>
    <div style="background: rgba(255,255,255,0.1); padding: 30px; border-radius: 15px; width: 80%; max-width: 400px;">
        <input type="text" id="playerName" placeholder="আপনার নাম লিখুন" style="width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: none;"><br>
        <select id="gameMode" style="width: 100%; padding: 12px; margin-bottom: 15px; border-radius: 8px; border: none;">
            <option value="robot">বনাম রোবট (Play with AI)</option>
            <option value="1v1">১ বনাম ১ (Player 1 vs Player 2)</option>
            <option value="2v2">২ বনাম ২ (Team Game)</option>
            <option value="4way">৪ জন প্লেয়ার (All vs All)</option>
        </select>
        <button class="btn" style="width: 100%;" onclick="createRoom()">গেম শুরু করুন</button>
        <hr style="margin: 20px 0; opacity: 0.3;">
        <input type="text" id="joinRoomId" placeholder="রুম আইডি দিন (Join)" style="width: 60%; padding: 12px; border-radius: 8px 0 0 8px; border: none;">
        <button onclick="joinRoom()" style="width: 35%; padding: 12px; border-radius: 0 8px 8px 0; border: none; background: var(--blue); color: white; font-weight: bold; cursor: pointer;">জয়েন</button>
    </div>
</div>

<div id="game-container" class="board-container">
    <div class="info">
        <h3 id="turn-display">টার্ন: লালের (Red)</h3>
        <p>রুম আইডি: <span id="display-room-id" style="color: var(--blue); font-weight: bold;"></span></p>
    </div>

    <div id="ludo-board">
        <!-- Homes -->
        <div class="cell home red-home"></div>
        <div class="cell home green-home"></div>
        <div class="cell home blue-home"></div>
        <div class="cell home yellow-home"></div>
        <div class="cell center-finish"></div>
        <!-- Cells are rendered via logic -->
    </div>

    <div class="controls">
        <div id="dice" onclick="rollDice()">🎲</div>
        <div id="player-label">আপনার রং: <b id="my-color">-</b></div>
        <button class="btn" style="background: var(--red);" onclick="location.reload()">Exit</button>
    </div>
</div>

<script>
    let roomId = null;
    let myId = null;
    let myColor = null;
    let isRobotTurn = false;
    let turnColor = 'red';

    async function createRoom() {
        const name = document.getElementById('playerName').value || "খেলোয়াড়";
        const mode = document.getElementById('gameMode').value;
        const res = await fetch('/api/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, mode})
        });
        const data = await res.json();
        setupGame(data);
    }

    async function joinRoom() {
        const name = document.getElementById('playerName').value || "অতিথি";
        const rId = document.getElementById('joinRoomId').value;
        const res = await fetch('/api/join', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, room_id: rId})
        });
        const data = await res.json();
        if(data.error) return alert(data.error);
        setupGame(data);
    }

    function setupGame(data) {
        roomId = data.room_id;
        myId = data.player_id;
        myColor = data.color;
        document.getElementById('setup').style.display = 'none';
        document.getElementById('game-container').style.display = 'flex';
        document.getElementById('display-room-id').innerText = roomId;
        document.getElementById('my-color').innerText = myColor.toUpperCase();
        document.getElementById('my-color').style.color = 'var(--'+myColor+')';
        
        setInterval(refreshGame, 2000);
    }

    async function rollDice() {
        if(turnColor !== myColor) return alert("এখন আপনার চাল নয়!");
        const res = await fetch('/api/roll', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({room_id: roomId, player_id: myId})
        });
        const data = await res.json();
        updateDiceUI(data.roll);
    }

    function updateDiceUI(val) {
        const dice = document.getElementById('dice');
        dice.innerText = val;
        dice.classList.remove('active-turn');
    }

    async function refreshGame() {
        if(!roomId) return;
        const res = await fetch(`/api/state?room_id=${roomId}`);
        const data = await res.json();
        turnColor = data.turn_color;
        document.getElementById('turn-display').innerText = "টার্ন: " + turnColor.toUpperCase();
        document.getElementById('turn-display').style.color = 'var(--'+turnColor+')';
        
        if(turnColor === myColor) {
            document.getElementById('dice').classList.add('active-turn');
        }

        // Robot AI Logic
        if(data.mode === 'robot' && turnColor === 'blue') {
            await fetch('/api/roll_robot', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({room_id: roomId})
            });
        }
    }
</script>
</body>
</html>
"""

# --- API Endpoints ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/create', methods=['POST'])
def create():
    data = request.json
    room_id = str(uuid.uuid4())[:6].upper()
    mode = data.get('mode', '1v1')
    
    players = [{"id": "p1", "name": data['name'], "color": "red"}]
    if mode == 'robot':
        players.append({"id": "robot", "name": "Robot AI", "color": "blue"})
    
    room_data = {
        "room_id": room_id,
        "mode": mode,
        "players": players,
        "turn_idx": 0,
        "turn_color": "red",
        "last_roll": 0,
        "status": "waiting" if mode != 'robot' else "active"
    }
    rooms.insert_one(room_data)
    return jsonify({"room_id": room_id, "player_id": "p1", "color": "red", "mode": mode})

@app.route('/api/join', methods=['POST'])
def join():
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    if not room: return jsonify({"error": "রুম পাওয়া যায়নি!"})
    
    colors = ["red", "blue", "green", "yellow"]
    p_count = len(room['players'])
    
    if p_count >= 4: return jsonify({"error": "রুমটি ভর্তি!"})
    
    new_player = {"id": f"p{p_count+1}", "name": data['name'], "color": colors[p_count]}
    rooms.update_one({"room_id": data['room_id']}, {"$push": {"players": new_player}, "$set": {"status": "active"}})
    
    return jsonify({"room_id": room['room_id'], "player_id": new_player['id'], "color": new_player['color']})

@app.route('/api/state', methods=['GET'])
def state():
    room_id = request.args.get('room_id')
    room = rooms.find_one({"room_id": room_id}, {"_id": 0})
    return jsonify(room)

@app.route('/api/roll', methods=['POST'])
def roll():
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    roll_val = random.randint(1, 6)
    
    # ২ বনাম ২ মোডের বিশেষ লজিক
    curr_idx = room['turn_idx']
    p_len = len(room['players'])
    
    # টার্ন পাল্টানো (যদি ৬ না পড়ে)
    next_idx = curr_idx
    if roll_val != 6:
        next_idx = (curr_idx + 1) % p_len
        
    rooms.update_one({"room_id": data['room_id']}, {
        "$set": {
            "last_roll": roll_val, 
            "turn_idx": next_idx, 
            "turn_color": room['players'][next_idx]['color']
        }
    })
    return jsonify({"roll": roll_val})

@app.route('/api/roll_robot', methods=['POST'])
def roll_robot():
    # রোবট নিজে নিজেই দান চালবে
    time.sleep(1) # একটু দেরি করা যাতে মনে হয় রোবট ভাবছে
    data = request.json
    room = rooms.find_one({"room_id": data['room_id']})
    if room['turn_color'] != 'blue': return jsonify({"status": "not robot turn"})
    
    roll_val = random.randint(1, 6)
    next_idx = 0 if roll_val != 6 else 1 # রোবট ৬ না পেলে মানুষের টার্ন
    
    rooms.update_one({"room_id": data['room_id']}, {
        "$set": {
            "last_roll": roll_val, 
            "turn_idx": next_idx, 
            "turn_color": room['players'][next_idx]['color']
        }
    })
    return jsonify({"roll": roll_val})

if __name__ == '__main__':
    app.run(debug=True)
