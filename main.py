import os
import telebot
from flask import Flask, request, redirect, session, url_for
from pymongo import MongoClient

# --- কনফিগারেশন ---
BOT_TOKEN = "8015568609:AAFEDoWVHzvQGwmNIl540XavKa_OQzXX2sk"
MONGO_URI = "mongodb+srv://Demo270:Demo270@cluster0.ls1igsg.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
ADMIN_PASSWORD = "admin123"
CHANNEL_ID = -1003704764803
OWNER_ID = 7120801813
SITE_URL = "https://clonemovie-six.vercel.app"

# Flask & Bot Setup
app = Flask(__name__)
app.secret_key = "movie_portal_super_secret_key"
bot = telebot.TeleBot(BOT_TOKEN, threaded=False)

# MongoDB Setup
client = MongoClient(MONGO_URI)
db = client['premium_movie_portal']
videos_col = db['movies']

# --- প্রিমিয়াম ডার্ক ডিজাইন (CSS সহ সম্পূর্ণ HTML) ---
DESIGN_HEAD = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Premium Movie Portal</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #080b12; color: #e5e7eb; font-family: 'Inter', sans-serif; margin: 0; padding: 0; }
        .navbar { background: #111827; border-bottom: 2px solid #3b82f6; padding: 15px; sticky: top; }
        .card-container { display: flex; flex-wrap: wrap; justify-content: center; gap: 20px; padding: 30px; }
        .movie-card { background: #1f2937; border-radius: 15px; overflow: hidden; width: 220px; transition: 0.3s; border: 1px solid #374151; text-decoration: none; color: white; display: block; }
        .movie-card:hover { transform: translateY(-10px); border-color: #3b82f6; box-shadow: 0 10px 25px rgba(59, 130, 246, 0.3); }
        .movie-card img { width: 100%; height: 280px; object-fit: cover; }
        .btn-dl { background: linear-gradient(90deg, #2563eb, #7c3aed); color: white; border: none; padding: 12px; border-radius: 10px; font-weight: bold; width: 100%; text-decoration: none; display: block; text-align: center; font-size: 16px; }
        .detail-card { background: #111827; border-radius: 20px; padding: 30px; border: 1px solid #374151; max-width: 500px; margin: 40px auto; }
        .admin-item { background: #1f2937; padding: 15px; border-radius: 10px; margin-bottom: 10px; display: flex; justify-content: space-between; align-items: center; border: 1px solid #374151; }
    </style>
</head>
<body>
"""

# --- টেলিগ্রাম বট হ্যান্ডলার (Message ID Logic) ---

@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    command_args = message.text.split()
    
    # যদি স্টার্ট লিঙ্কে আইডি থাকে (যেমন: /start 10)
    if len(command_args) > 1:
        msg_id = command_args[1]
        try:
            # সরাসরি চ্যানেল থেকে মেসেজটি কপি করে ইউজারের ইনবক্সে পাঠানো
            bot.copy_message(chat_id, CHANNEL_ID, int(msg_id))
        except Exception as e:
            bot.send_message(chat_id, "❌ ফাইলটি পাওয়া যায়নি! সম্ভবত এটি চ্যানেল থেকে ডিলেট করা হয়েছে।")
    else:
        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton("🌐 ওয়েবসাইট ভিজিট করুন", url=SITE_URL))
        bot.send_message(chat_id, "👋 **স্বাগতম!**\n\nমুভি ডাউনলোড করতে আমাদের ওয়েবসাইট থেকে লিঙ্কে ক্লিক করুন।", reply_markup=markup, parse_mode="Markdown")

@bot.channel_post_handler(content_types=['video', 'document'])
def handle_channel_post(message):
    # চ্যানেল পোস্ট থেকে মেসেজ আইডি এবং নাম সেভ করা
    msg_id = message.message_id
    file_name = "New Movie File"
    if message.video:
        file_name = message.video.file_name or message.caption or "Video_File"
    elif message.document:
        file_name = message.document.file_name or message.caption or "Document_File"

    data = {
        "file_name": file_name,
        "msg_id": msg_id,
        "thumb": "https://via.placeholder.com/400x600/080b12/ffffff?text=Premium+Movie"
    }
    # ডাটাবেসে সেভ (যদি আইডি এক হয় তবে আপডেট হবে)
    videos_col.update_one({"msg_id": msg_id}, {"$set": data}, upsert=True)
    
    # বটের মালিককে অ্যালার্ট পাঠানো
    bot.send_message(OWNER_ID, f"✅ **নতুন মুভি অ্যাড হয়েছে!**\n📂 নাম: {file_name}\n🆔 আইডি: {msg_id}\n🌐 লিঙ্ক: {SITE_URL}/view/{msg_id}")

# --- ফ্লাস্ক ওয়েবসাইট রুটস ---

@app.route('/')
def home():
    videos = list(videos_col.find().sort("msg_id", -1))
    movies_html = ""
    for v in videos:
        movies_html += f'''
        <a href="/view/{v['msg_id']}" class="movie-card">
            <img src="{v.get('thumb')}">
            <div class="p-3 text-center">
                <h6 class="text-truncate">{v['file_name']}</h6>
                <small class="text-secondary">ID: {v['msg_id']}</small>
            </div>
        </a>'''
    
    return f"""
    {DESIGN_HEAD}
    <nav class="navbar"><div class="container"><h3 class="mx-auto text-primary">MOVIE PORTAL</h3></div></nav>
    <div class="card-container">
        {movies_html if movies_html else '<h4 class="text-center">No movies found. Please forward a video to your channel.</h4>'}
    </div>
    </body></html>
    """

@app.route('/view/<msg_id>')
def view(msg_id):
    try:
        video = videos_col.find_one({"msg_id": int(msg_id)})
    except:
        return "Invalid ID Format"
        
    if not video: return "Movie Not Found in Database"
    
    bot_info = bot.get_me()
    # এখানে আমরা ডাটাবেস থেকে পাওয়া মেসেজ আইডি ব্যবহার করছি
    download_url = f"https://t.me/{bot_info.username}?start={msg_id}"
    
    return f"""
    {DESIGN_HEAD}
    <div class="container">
        <div class="detail-card text-center">
            <img src="{video.get('thumb')}" class="img-fluid rounded mb-4 shadow-lg">
            <h2 class="mb-3">{video['file_name']}</h2>
            <p class="text-secondary">Message ID: {msg_id}</p>
            <hr style="border-color: #374151;">
            <a href="{download_url}" class="btn-dl py-3 fs-5">📥 Get File via Telegram Bot</a>
            <div class="mt-4"><a href="/" class="text-secondary text-decoration-none">← Back to Home</a></div>
        </div>
    </div>
    </body></html>
    """

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST' and request.form.get('password') == ADMIN_PASSWORD:
        session['is_admin'] = True
    
    if not session.get('is_admin'):
        return f"""
        {DESIGN_HEAD}
        <div class="container mt-5 w-50">
            <div class="detail-card">
                <h4 class="mb-3 text-center">Admin Login</h4>
                <form method="post">
                    <input type="password" name="password" class="form-control mb-3 bg-dark text-white border-secondary" placeholder="Enter Password">
                    <button type="submit" class="btn-dl">Login</button>
                </form>
            </div>
        </div>
        </body>
        OWNERDOMAIN=vercel.app
MANAGERDOMAIN=themoneytizer.com
themoneytizer.com,130188,DIRECT
smartadserver.com,1097,DIRECT,060d053dcf45cbf3
pubmatic.com,156439,RESELLER,5d62403b186f2ace
pubmatic.com,154037,RESELLER,5d62403b186f2ace
rubiconproject.com,16114,RESELLER,0bfd66d529a55807
openx.com,537149888,RESELLER,6a698e2ec38604c6
appnexus.com,3703,RESELLER,f5ab79cb980f11d1
loopme.com,5679,RESELLER,6c8d5f95897a5a3b
video.unrulymedia.com,2564526802,RESELLER,6f752381ad5ec0e5
smaato.com,1100044045,RESELLER,07bcf65f187117b4
pubnative.net,1006576,RESELLER,d641df8625486a7b
adyoulike.com,b4bf4fdd9b0b915f746f6747ff432bde,RESELLER,4ad745ead2958bf7
axonix.com,57264,RESELLER,bc385f2b4a87b721
admanmedia.com,43,RESELLER
sharethrough.com,OAW69Fon,RESELLER,d53b998a7bd4ecd2
contextweb.com,560288,RESELLER,89ff185a4c4e857c
contextweb.com,563115,RESELLER,89ff185a4c4e857c
adcolony.com,496220845654deec,RESELLER,1ad675c9de6b5176
appads.in,107606,RESELLER
rubiconproject.com,24600,RESELLER,0bfd66d529a55807
pubmatic.com,156177,RESELLER,5d62403b186f2ace
rubiconproject.com,17328,RESELLER,0bfd66d529a55807
rubiconproject.com,11740,RESELLER,0bfd66d529a55807
rubiconproject.com,22014,RESELLER,0bfd66d529a55807
flashb.id,7ea636d8-701f-5b93-9d03-0e5cd43bc8fa,DIRECT
152media.info,152M33,RESELLER
adform.com,3125,RESELLER
adyoulike.com,bcf6c423bc90ec180005086dd9935a1b,RESELLER
improvedigital.com,1723,RESELLER
smartadserver.com,3389,RESELLER,060d053dcf45cbf3
rubiconproject.com,20922,RESELLER,0bfd66d529a55807
themediagrid.com,QUZDR9,RESELLER,35d5010d7789b49d
onetag.com,5cca11704094eb8,RESELLER
openx.com,559913615,RESELLER,6a698e2ec38604c6
pubmatic.com,160107,RESELLER,5d62403b186f2ace
risecodes.com,65b9125633dab2000102902c,RESELLER
pubmatic.com,160295,RESELLER,5d62403b186f2ace
triplelift.com,12738,RESELLER,6c33edb13117fd86
video.unrulymedia.com,273421059,RESELLER
appnexus.com,11701,RESELLER
appnexus.com,3153,RESELLER,f5ab79cb980f11d1
appnexus.com,11924,RESELLER,f5ab79cb980f11d1
smartadserver.com,4144,RESELLER
rubiconproject.com,20736,RESELLER,0bfd66d529a55807
spotim.market,sp_AYL2022,RESELLER,077e5f709d15bdbb
appnexus.com,7664,RESELLER
pubmatic.com,160925,RESELLER,5d62403b186f2ace
onetag.com,7a07370227fc000,RESELLER
nativo.com,5848,RESELLER,59521ca7cc5e9fee
33across.com,0015a00003HljHyAAJ,RESELLER
risecodes.com,64c7a4acd6298f0001a7d867,RESELLER
xapads.com,196344,RESELLER
richaudience.com,JAHJ4YZq4O,RESELLER
appnexus.com,15941,RESELLER
openx.com,559680764,RESELLER,6a698e2ec38604c6
rubiconproject.com,12186,RESELLER,0bfd66d529a55807
pubmatic.com,156631,RESELLER,5d62403b186f2ace
sharethrough.com,23830661,RESELLER,d53b998a7bd4ecd2
contextweb.com,562965,RESELLER,89ff185a4c4e857c
zetaglobal.net,891,RESELLER
mgid.com,833178,RESELLER,d4c29acad76ce94f
amxrtb.com,105199704,RESELLER
onetag.com,5927d926323dc2c,RESELLER
rubiconproject.com,11006,RESELLER,0bfd66d529a55807
appnexus.com,13099,RESELLER
smartadserver.com,4111,RESELLER
xandr.com,14082,RESELLER
rubiconproject.com,23876,RESELLER,0bfd66d529a55807
openx.com,537140488,RESELLER,6a698e2ec38604c6
sharethrough.com,5926d422,RESELLER,d53b998a7bd4ecd2
media.net,8CUQ6928Q,RESELLER
sonobi.com,4a289cdd79,RESELLER,d1a215d9eb5aee9e
video.unrulymedia.com,335119963,RESELLER
onetag.com,69f48c2160c8113,RESELLER
themediagrid.com,4DQHAP,RESELLER,35d5010d7789b49d
loopme.com,11362,RESELLER,6c8d5f95897a5a3b
smartadserver.com,4284,RESELLER
adform.com,3119,RESELLER,9f5210a2f0999e32
freewheel.tv,1590601,RESELLER
freewheel.tv,1590606,RESELLER
sharethrough.com,332baa08,RESELLER,d53b998a7bd4ecd2
33across.com,0013300001kQj2HAAS,RESELLER,bbea06d9c4d2853c
openx.com,540274407,RESELLER,6a698e2ec38604c6
pubmatic.com,156557,RESELLER
rubiconproject.com,18694,RESELLER,0bfd66d529a55807
smaato.com,1100047713,RESELLER,07bcf65f187117b4
video.unrulymedia.com,266978658,RESELLER
aniview.com,603f65a2e291680ef30af9c7,RESELLER,78b21b97965ec3f8
appnexus.com,12637,RESELLER,f5ab79cb980f11d1
appnexus.com,9382,RESELLER,f5ab79cb980f11d1
appnexus.com,6849,RESELLER
google.com,pub-6346866704322274,RESELLER,f08c47fec0942fa0
google.com,pub-3565385483761681,RESELLER,f08c47fec0942fa0
google.com,pub-5717092533913515,RESELLER,f08c47fec0942fa0
pubmatic.com,159277,RESELLER
pubmatic.com,161335,RESELLER,5d62403b186f2ace
pubmatic.com,160993,RESELLER,5d62403b186f2ace
rubiconproject.com,13918,RESELLER,0bfd66d529a55807
rubiconproject.com,15268,RESELLER
improvedigital.com,1033,RESELLER
appnexus.com,2579,RESELLER
improvedigital.com,1220,RESELLER
quantum-advertising.com,4758,RESELLER
improvedigital.com,1602,RESELLER
adagio.io,1015,RESELLER
rubiconproject.com,19116,RESELLER,0bfd66d529a55807
pubmatic.com,159110,RESELLER,5d62403b186f2ace
improvedigital.com,1790,RESELLER
onetag.com,6b859b96c564fbe,RESELLER
pubmatic.com,161593,RESELLER,5d62403b186f2ace
33across.com,0015a00002oUk4aAAC,RESELLER,bbea06d9c4d2853c
appnexus.com,10239,RESELLER,f5ab79cb980f11d1
rubiconproject.com,16414,RESELLER,0bfd66d529a55807
pubmatic.com,156423,RESELLER,5d62403b186f2ace
rubiconproject.com,21642,RESELLER,0bfd66d529a55807
conversantmedia.com,100141,RESELLER
triplelift.com,12503,RESELLER,6c33edb13117fd86
smartadserver.com,3554,RESELLER
video.unrulymedia.com,2564526802,RESELLER
lijit.com,367236,RESELLER,fafdf38b16bf6b2b
openx.com,538959099,RESELLER,6a698e2ec38604c6
pubmatic.com,137711,RESELLER,5d62403b186f2ace
pubmatic.com,156212,RESELLER,5d62403b186f2ace
rubiconproject.com,17960,RESELLER,0bfd66d529a55807
e-planning.net,83c06e81531537f4,RESELLER,c1ba615865ed87b2
admanmedia.com,2216,RESELLER
connectad.io,456,RESELLER,85ac85a30c93b3e5
rubiconproject.com,26800,RESELLER,0bfd66d529a55807
insticator.com,4ec3ed85-2830-4174-9f7f-f545620598b9,RESELLER,b3511ffcafb23a32
sharethrough.com,Q9IzHdvp,RESELLER,d53b998a7bd4ecd2
pubmatic.com,161784,RESELLER,5d62403b186f2ace
smilewanted.com,1362,RESELLER
pubmatic.com,158810,RESELLER,5d62403b186f2ace
appnexus.com,10040,RESELLER
smartadserver.com,2491,RESELLER
rubiconproject.com,19814,RESELLER,0bfd66d529a55807
openx.com,557083110,RESELLER,6a698e2ec38604c6
lijit.com,346012,DIRECT,fafdf38b16bf6b2b
improvedigital.com,1010,RESELLER
indexexchange.com,193216,RESELLER
adform.com,3027,RESELLER
sharethrough.com,TZ1ahFV8,RESELLER,d53b998a7bd4ecd2
smaato.com,1100055901,RESELLER,07bcf65f187117b4
smaato.com,1100004890,RESELLER,07bcf65f187117b4
33across.com,001Pg000009Gtq2IAC,DIRECT,bbea06d9c4d2853c
loopme.com,11468,RESELLER,6c8d5f95897a5a3b
video.unrulymedia.com,1767448067723954599,RESELLER
vidoomy.com,7763608,RESELLER
adform.com,2742,RESELLER
onetag.com,7f5d22b0006ab5a,RESELLER
152media.info,152M728,RESELLER
videoheroes.tv,212648,RESELLER,064bc410192443d8
amxrtb.com,105199841,RESELLER
adwmg.com,100746,RESELLER
adform.com,2623,DIRECT,9f5210a2f0999e32
kueez.com,1f90819a4cb4c67be57ecf39973f1b97,DIRECT
themediagrid.com,UOT45Z,RESELLER,35d5010d7789b49d
rubiconproject.com,16920,RESELLER,0bfd66d529a55807
openx.com,557564833,RESELLER,6a698e2ec38604c6
pubmatic.com,162110,RESELLER,5d62403b186f2ace
lijit.com,407406,RESELLER,fafdf38b16bf6b2b
sharethrough.com,n98xDzeL,RESELLER,d53b998a7bd4ecd2
sonobi.com,4c4fba1717,RESELLER,d1a215d9eb5aee9e
appnexus.com,8826,RESELLER,f5ab79cb980f11d1
33across.com,0010b00002ODU4HAAX,RESELLER,bbea06d9c4d2853c
video.unrulymedia.com,3486482593,RESELLER
media.net,8CU4JTRF9,RESELLER
disqus.com,108,RESELLER
onetag.com,6e053d779444c00,RESELLER
adform.com,2926,RESELLER
improvedigital.com,2106,RESELLER
smartadserver.com,4288,RESELLER
loopme.com,11576,RESELLER
zetaglobal.com,108,RESELLER
yieldmo.com,3133660606033240149,RESELLER
video.unrulymedia.com,572325444,DIRECT
trustedstack.com,TS7LELSN3,DIRECT
rubiconproject.com,26144,RESELLER,0bfd66d529a55807
pubmatic.com,164187,RESELLER,5d62403b186f2ace
amxrtb.com,105199734,RESELLER
appnexus.com,12290,RESELLER
media.net,8CU67TH23,RESELLER
openx.com,559911747,RESELLER,6a698e2ec38604c6
yieldmo.com,3377199372461613093,RESELLER
onetag.com,87f58fe90234d0e,RESELLER
video.unrulymedia.com,799061815,RESELLER
smartadserver.com,5302,RESELLER,060d053dcf45cbf3
iqzone.com,IQ326,RESELLER
amxrtb.com,105199542,DIRECT
rubiconproject.com,23844,RESELLER
adform.com,2865,RESELLER
openx.com,559680764,RESELLER
lijit.com,260380,RESELLER
pubmatic.com,161527,RESELLER
sharethrough.com,a6a34444,RESELLER,d53b998a7bd4ecd2
smartadserver.com,3056,RESELLER
gumgum.com,13857,RESELLER,ffdef49475d318a9
rubiconproject.com,23434,RESELLER,0bfd66d529a55807
pubmatic.com,157897,RESELLER,5d62403b186f2ace
appnexus.com,2758,RESELLER,f5ab79cb980f11d1
contextweb.com,558355,RESELLER,89ff185a4c4e857c
openx.com,537149485,RESELLER,6a698e2ec38604c6
improvedigital.com,1884,RESELLER
smartadserver.com,4005,RESELLER,060d053dcf45cbf3
admedia.com,1606,RESELLER
iqzone.com,IQ204,RESELLER
admanmedia.com,799,RESELLER
betweendigital.com,41430,DIRECT
videoheroes.tv,212692,RESELLER,064bc410192443d8
rubiconproject.com,25060,RESELLER,0bfd66d529a55807
appnexus.com,12976,RESELLER,f5ab79cb980f11d1
thebrave.io,1234750,DIRECT,c25b2154543746ac
onlinemediasolutions.com,21097,DIRECT,b3868b187e4b6402
rubiconproject.com,20416,RESELLER,0bfd66d529a55807
onomagic.com,210971,DIRECT
rubiconproject.com,24364,RESELLER,0bfd66d529a55807
getmediamx.com,1221097,DIRECT
pubstack.io,dd8810a6-2df6-48d7-a782-399ee88c1ff1,DIRECT
appnexus.com,15871,RESELLER
adform.com,3272,RESELLER
gumgum.com,16010,RESELLER,ffdef49475d318a9
rubiconproject.com,23434,RESELLER,0bfd66d529a55807
pubmatic.com,157897,RESELLER,5d62403b186f2ace
appnexus.com,2758,RESELLER,f5ab79cb980f11d1
contextweb.com,558355,RESELLER,89ff185a4c4e857c
openx.com,537149485,RESELLER,6a698e2ec38604c6
improvedigital.com,1884,RESELLER
smartadserver.com,4005,RESELLER,060d053dcf45cbf3
admanmedia.com,799,RESELLER
conversantmedia.com,100978,RESELLER,03113cd04947736d
improvedigital.com,2559,RESELLER
rubiconproject.com,26972,RESELLER,0bfd66d529a55807
ogury.com,8a18c5b6-cc22-4670-90cc-4f4d7c8f5d15,DIRECT
appnexus.com,11470,RESELLER
pubmatic.com,163238,RESELLER,5d62403b186f2ace
smartadserver.com,4537,RESELLER,060d053dcf45cbf3
rubiconproject.com,25198,RESELLER,0bfd66d529a55807
video.unrulymedia.com,533898005,RESELLER
onetag.com,87d1f0db05b6e24,DIRECT
pubmatic.com,166516,RESELLER,5d62403b186f2ac
richaudience.com,B45mvBz0n6,RESELLER
appnexus.com,8233,RESELLER
pubmatic.com,81564,RESELLER,5d62403b186f2ace
pubmatic.com,156538,RESELLER,5d62403b186f2ace
rubiconproject.com,13510,RESELLER
adform.com,1942,RESELLER
lijit.com,249425,RESELLER
google.com,pub-4673227357197067,RESELLER,f08c47fec0942fa0
smartadserver.com,1999,RESELLER,060d053dcf45cbf3
rtbhouse.com,axQYcWclgd0Dgci5usl9,DIRECT
seedtag.com,65a6761b39be3f0007c13e98,DIRECT
loopme.com,11712,RESELLER,6c8d5f95897a5a3b
adform.com,3083,RESELLER
lijit.com,400766,RESELLER,fafdf38b16bf6b2b
freewheel.tv,1137745,RESELLER
sonobi.com,b43e9530e7,RESELLER,d1a215d9eb5aee9e
smartadserver.com,4937,RESELLER,060d053dcf45cbf3
axonix.com,57264,RESELLER
triplelift.com,14588,RESELLER,6c33edb13117fd86
admixer.net,b0411519-d717-49e1-9051-eaf1cb5280b0,DIRECT
inmobi.com,61d733c3779d43e590c51c8bc078e10c,RESELLER,83e75a7ae333ca9d
pubmatic.com,160846,RESELLER,5d62403b186f2ace
loopme.com,11488,RESELLER,6c8d5f95897a5a3b
        </html>
        """
    
    videos = list(videos_col.find().sort("msg_id", -1))
    rows = ""
    for v in videos:
        rows += f'''
        <div class="admin-item">
            <span>{v["file_name"]} (ID: {v["msg_id"]})</span>
            <a href="/del/{v["msg_id"]}" class="btn btn-danger btn-sm">Delete</a>
        </div>'''
        
    return f"""
    {DESIGN_HEAD}
    <div class="container mt-5">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h3>Admin Panel</h3>
            <a href="/" class="btn btn-secondary btn-sm">View Site</a>
        </div>
        <hr style="border-color: #374151;">
        {rows if rows else '<p>No data available.</p>'}
    </div>
    </body></html>
    """

@app.route('/del/<msg_id>')
def delete(msg_id):
    if session.get('is_admin'):
        videos_col.delete_one({"msg_id": int(msg_id)})
    return redirect(url_for('admin'))

@app.route('/webhook', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "OK", 200
    return "Forbidden", 403

@app.route('/setup')
def setup():
    bot.remove_webhook()
    success = bot.set_webhook(url=f"{SITE_URL}/webhook")
    return f"<h1>{'✅ Webhook Success!' if success else '❌ Webhook Failed!'}</h1>"

@app.route('/favicon.ico')
def favicon():
    return '', 200

# Vercel-এর জন্য app অবজেক্ট প্রয়োজন
if __name__ == "__main__":
    app.run(debug=True)
