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

# --- HTML/CSS/JS (Complete Logic) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Real Premium Ludo</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        :root {
            --red: #ff4d4d; --green: #2ecc71; --yellow: #f1c40f; --blue: #3498db;
        }
        body { font-family: sans-serif; background: #2c3e50; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; color: white;}
        
        /* Ludo Board Layout */
        #ludo-container { position: relative; width: 450px; height: 450px; background: white; border: 5px solid #333; display: grid; grid-template-columns: repeat(15, 1fr); grid-template-rows: repeat(15, 1fr); }
        
        .cell { border: 0.5px solid #ccc; box-sizing: border-box; position: relative; }
        
        /* Houses */
        .house { grid-column: span 6; grid-row: span 6; position: relative; border: 2px solid #333; }
        .red-h { background: var(--red); grid-area: 1 / 1 / 7 / 7; }
        .green-h { background: var(--green); grid-area: 1 / 10 / 7 / 16; }
        .blue-h { background: var(--blue); grid-area: 10 / 1 / 16 / 7; }
        .yellow-h { background: var(--yellow); grid-area: 10 / 10 / 16 / 16; }

        .white-inner { position: absolute; top: 15%; left: 15%; width: 70%; height: 70%; background: white; border-radius: 10px; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; }
        
        /* Path coloring */
        .r-path { background: var(--red); } .g-path { background: var(--green); }
        .b-path { background: var(--blue); } .y-path { background: var(--yellow); }
        .safe { background: #bdc3c7 !important; }

        /* Pawns (গুটি) */
        .pawn { width: 22px; height: 22px; border-radius: 50%; border: 2px solid #000; position: absolute; z-index: 100; cursor: pointer; transition: 0.3s; box-shadow: 0 2px 5px rgba(0,0,0,0.5); }
        .p-red { background: var(--red); } .p-green { background: var(--green); }
        .p-blue { background: var(--blue); } .p-yellow { background: var(--yellow); }

        .center { grid-area: 7 / 7 / 10 / 10; background: conic-gradient(var(--red) 0 90deg, var(--green) 0 180deg, var(--yellow) 0 270deg, var(--blue) 0 360deg); }

        /* UI Controls */
        .controls { padding: 20px; text-align: center; }
        #dice { width: 60px; height: 60px; background: white; color: #333; border-radius: 10px; display: inline-flex; align-items: center; justify-content: center; font-size: 30px; font-weight: bold; border: 4px solid #95a5a6; cursor: pointer; }
        .setup-box { background: #34495e; padding: 20px; border-radius: 15px; text-align: center; }
        .btn { background: var(--green); color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
    </style>
</head>
<body>

<div id="setup" class="setup-box">
    <h2>Ludo Premium Multiplayer</h2>
    <input type="text" id="pName" placeholder="আপনার নাম"><br><br>
    <select id="mode">
        <option value="robot">🤖 বনাম রোবট</option>
        <option value="1v1">👥 ১ বনাম ১</option>
        <option value="4way">👨‍👩‍👧‍👦 ৪ জন প্লেয়ার</option>
    </select><br><br>
    <button class="btn" onclick="createGame()">গেম শুরু করুন</button>
</div>

<div id="game-ui" style="display:none">
    <div id="ludo-container">
        <!-- Houses -->
        <div class="house red-h"><div class="white-inner" id="h-red"></div></div>
        <div class="house green-h"><div class="white-inner" id="h-green"></div></div>
        <div class="house blue-h"><div class="white-inner" id="h-blue"></div></div>
        <div class="house yellow-h"><div class="white-inner" id="h-yellow"></div></div>
        <div class="center"></div>
        
        <!-- Cells will be auto-generated -->
    </div>

    <div class="controls">
        <h3 id="status">টার্ন: লালের (Red)</h3>
        <div id="dice" onclick="roll()">🎲</div>
        <p>রুম আইডি: <span id="r-id" style="color:var(--yellow)"></span></p>
    </div>
</div>

<script>
    let roomId, myId, myColor, turn = 'red';
    let boardMap = {}; // ঘরগুলোর লোকেশন

    async function createGame() {
        const name = document.getElementById('pName').value || "Player";
        const mode = document.getElementById('mode').value;
        const res = await fetch('/create', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, mode})
        });
        const data = await res.json();
        roomId = data.room_id; myId = data.player_id; myColor = data.color;
        startUI();
    }

    function startUI() {
        document.getElementById('setup').style.display = 'none';
        document.getElementById('game-ui').style.display = 'block';
        document.getElementById('r-id').innerText = roomId;
        generateBoard();
        setInterval(updateState, 2000);
    }

    function generateBoard() {
        const container = document.getElementById('ludo-container');
        // Path cells generate (This is a simplified grid for demo)
        for(let r=1; r<=15; r++){
            for(let c=1; c<=15; c++){
                if((r>6 && r<10) || (c>6 && c<10)) {
                    if(!((r>6 && r<10) && (c>6 && c<10))) {
                        let cell = document.createElement('div');
                        cell.className = 'cell';
                        cell.id = `cell-${r}-${c}`;
                        // Color start positions
                        if(r==8 && c<=6 && c>1) cell.classList.add('r-path');
                        if(r==8 && c>=10 && c<15) cell.classList.add('y-path');
                        container.appendChild(cell);
                    }
                }
            }
        }
        renderPawns();
    }

    function renderPawns() {
        // Red Pawns
        for(let i=0; i<4; i++) {
            let p = document.createElement('div');
            p.className = 'pawn p-red';
            p.id = `pawn-red-${i}`;
            document.getElementById('h-red').appendChild(p);
        }
        // Blue Pawns
        for(let i=0; i<4; i++) {
            let p = document.createElement('div');
            p.className = 'pawn p-blue';
            p.id = `pawn-blue-${i}`;
            document.getElementById('h-blue').appendChild(p);
        }
    }

    async function roll() {
        if(turn !== myColor) return alert("আপনার চালের জন্য অপেক্ষা করুন!");
        const res = await fetch('/roll', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({room_id: roomId, player_id: myId})
        });
        const data = await res.json();
        document.getElementById('dice').innerText = data.roll;
        updateState();
    }

    async function updateState() {
        if(!roomId) return;
        const res = await fetch(`/state?room_id=${roomId}`);
        const data = await res.json();
        turn = data.turn_color;
        document.getElementById('status').innerText = "টার্ন: " + turn.toUpperCase();
        document.getElementById('status').style.color = "var(--"+turn+")";
        
        // Robot Logic
        if(data.mode === 'robot' && turn === 'blue') {
            await fetch('/roll_robot', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify({room_id:roomId})});
        }
    }
</script>
</body>
</html>
"""

# --- Backend Routes ---

@app.route('/')
def home():
    return render_template_string(HTML_TEMPLATE)

@app.route('/create', methods=['POST'])
def create():
    data = request.json
    r_id = str(uuid.uuid4())[:6].upper()
    players = [{"id": "p1", "name": data['name'], "color": "red"}]
    if data['mode'] == 'robot':
        players.append({"id": "robot", "name": "Robot", "color": "blue"})
    
    room = {
        "room_id": r_id, "mode": data['mode'], "players": players,
        "turn": 0, "turn_color": "red", "last_roll": 1, "status": "active"
    }
    rooms.insert_one(room)
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
    
    # Switch Turn
    next_idx = (room['turn'] + 1) % len(room['players']) if roll_val != 6 else room['turn']
    
    rooms.update_one({"room_id": data['room_id']}, {
        "$set": {"last_roll": roll_val, "turn": next_idx, "turn_color": room['players'][next_idx]['color']}
    })
    return jsonify({"roll": roll_val})

@app.route('/roll_robot', methods=['POST'])
def roll_robot():
    r_id = request.json['room_id']
    roll_val = random.randint(1, 6)
    rooms.update_one({"room_id": r_id}, {"$set": {"last_roll": roll_val, "turn": 0, "turn_color": "red"}})
    return jsonify({"roll": roll_val})

if __name__ == '__main__':
    app.run(debug=True)
