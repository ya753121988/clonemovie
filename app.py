from flask import Flask, render_template_string

app = Flask(__name__)

# আগের সেই নিয়ন গেমের কোডটি এখানে
HTML_CODE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Neon Space Adventure</title>
    <style>
        body { margin: 0; background: #0a0a0a; display: flex; align-items: center; justify-content: center; height: 100vh; overflow: hidden; font-family: sans-serif; }
        #gameCanvas { border: 4px solid #00d2ff; background: #000; border-radius: 10px; }
        .score { position: absolute; top: 20px; color: white; font-size: 30px; font-weight: bold; text-shadow: 0 0 10px #00d2ff; pointer-events: none; }
    </style>
</head>
<body>
    <div class="score" id="sb">Score: 0</div>
    <canvas id="gameCanvas"></canvas>
    <script>
        const canvas = document.getElementById("gameCanvas");
        const ctx = canvas.getContext("2d");
        canvas.width = 400; canvas.height = 600;

        let bird = { x: 50, y: 300, w: 30, h: 30, velocity: 0, gravity: 0.5 };
        let pipes = []; let score = 0; let frame = 0;

        function draw() {
            ctx.clearRect(0,0,400,600);
            bird.velocity += bird.gravity; bird.y += bird.velocity;
            
            ctx.fillStyle = "#00d2ff";
            ctx.shadowBlur = 15; ctx.shadowColor = "#00d2ff";
            ctx.fillRect(bird.x, bird.y, bird.w, bird.h);

            if(frame % 100 === 0) {
                let h = Math.random() * 300 + 50;
                pipes.push({x: 400, y: 0, w: 50, h: h, type:'t'}, {x: 400, y: h+150, w: 50, h: 600, type:'b'});
            }
            
            pipes.forEach((p, i) => {
                p.x -= 3;
                ctx.fillStyle = "#f72585"; ctx.shadowColor = "#f72585";
                ctx.fillRect(p.x, p.y, p.w, p.h);
                if(p.x < -50) pipes.splice(i, 1);
                if(bird.x < p.x + p.w && bird.x + 30 > p.x && bird.y < p.y + p.h && bird.y + 30 > p.y) location.reload();
                if(p.x === 52 && p.type === 't') { score++; document.getElementById('sb').innerText = "Score: " + score; }
            });
            if(bird.y > 600 || bird.y < 0) location.reload();
            frame++; requestAnimationFrame(draw);
        }
        window.addEventListener("mousedown", () => bird.velocity = -8);
        draw();
    </script>
</body>
</html>
"""

@app.route('/')
def home():
    return render_template_string(HTML_CODE)

if __name__ == '__main__':
    app.run(debug=True)
