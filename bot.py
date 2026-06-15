import telebot
from telebot import types
import sqlite3
import time
import threading
import re
import hashlib
import os
from flask import Flask, redirect

# --- কনফিগারেশন ---
TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DB_FILE = "user_database.db"  
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

# আপনার রেন্ডার অ্যাপের লাইভ ইউআরএল (যেমন: https://rupa-coin.onrender.com)
RENDER_APP_URL = "https://your-app-name.onrender.com" 

bot = telebot.TeleBot(TOKEN, num_threads=100) # মাল্টি-থ্রেডিং ক্ষমতা ১০০ এ উন্নীত করা হয়েছে
app = Flask(__name__)
db_lock = threading.Lock()

# ইন-মেমোরি রিয়েল-টাইম সিকিউরিটি ট্র্যাকার
user_click_timers = {} 
user_pro_clicks = {}
active_withdrawals = set()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE, timeout=60.0, isolation_level=None) 
    conn.execute('PRAGMA journal_mode=WAL;')       
    conn.execute('PRAGMA synchronous=NORMAL;')    
    conn.execute('PRAGMA cache_size=-128000;') # কোটি ইউজারের হাই ট্রাফিকের জন্য ক্যাশ মেমোরি দ্বিগুণ করা হয়েছে
    return conn

def init_db():
    with db_lock:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                # ডাটাবেজ ফাইলের সাইজ অটো অপ্টিমাইজ রাখার জন্য ভ্যাকুয়াম অন
                cursor.execute('PRAGMA auto_vacuum = FULL;')
                
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS users (
                        u_id TEXT PRIMARY KEY,
                        name TEXT,
                        balance REAL DEFAULT 0.0,
                        bkash TEXT DEFAULT 'Not Set',
                        nagad TEXT DEFAULT 'Not Set',
                        completed_pro_links TEXT DEFAULT ''
                    )
                ''')
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS tasks (
                        id INTEGER PRIMARY KEY,
                        ads_link TEXT,
                        ads_reward REAL,
                        ads_time INTEGER,
                        pro_link TEXT,
                        pro_reward REAL
                    )
                ''')
                
                # হাই-স্পিড সার্চিং নিশ্চিত করতে ডাটাবেজ ইনডেক্সিং (কোটি ইউজারের জন্য অতি জরুরি)
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_uid ON users(u_id);')
                
                cursor.execute("SELECT COUNT(*) FROM tasks")
                if cursor.fetchone()[0] == 0:
                    cursor.execute('''
                        INSERT INTO tasks (id, ads_link, ads_reward, ads_time, pro_link, pro_reward)
                        VALUES (1, 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 0.2, 15, 'https://t.me/rupacoin27bd', 1.0)
                    ''')
        except Exception as e:
            print(f"Database Init Error: {e}")

init_db()

def get_tasks_config():
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT ads_link, ads_reward, ads_time, pro_link, pro_reward FROM tasks WHERE id=1")
                row = cursor.fetchone()
                if row:
                    return {'ads_link': row[0], 'ads_reward': row[1], 'ads_time': row[2], 'pro_link': row[3], 'pro_reward': row[4]}
    except Exception: pass
    return {'ads_link': 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 'ads_reward': 0.2, 'ads_time': 15, 'pro_link': 'https://t.me/rupacoin27bd', 'pro_reward': 1.0}

def get_user(u_id):
    try:
        with db_lock:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name, balance, bkash, nagad, completed_pro_links FROM users WHERE u_id=?", (str(u_id),))
                row = cursor.fetchone()
                if row:
                    return {'name': row[0], 'balance': row[1], 'bkash': row[2], 'nagad': row[3], 'completed_pro_links': [x for x in row[4].split(',') if x] if row[4] else []}
    except Exception: pass
    return None

def add_user(u_id, name):
    if not name: name = "User"
    name = re.sub(r'[<>&\'"\*\_]', '', name)
    with db_lock:
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT OR IGNORE INTO users (u_id, name) VALUES (?, ?)", (str(u_id), name))
        except Exception: pass

# --- ফ্ল্যাঙ্ক গেটওয়ে রিডাইরেকশন এবং ক্লিক ট্র্যাকিং ইঞ্জিন ---
@app.route('/')
def home(): 
    return "Rupa Coin Server: 100% Active & Pro Scaled"

@app.route('/click/ad/<u_id>')
def track_ad_click(u_id):
    config = get_tasks_config()
    add_user(str(u_id), "User") 
    user_click_timers[str(u_id)] = {"start_time": time.time(), "status": "counting"}
    return redirect(config['ads_link'])

@app.route('/click/pro/<u_id>')
def track_pro_click(u_id):
    config = get_tasks_config()
    add_user(str(u_id), "User") 
    link_hash = hashlib.md5(config['pro_link'].encode()).hexdigest()
    user_pro_clicks[str(u_id)] = {"clicked": True, "link_hash": link_hash}
    return redirect(config['pro_link'])


# --- টেলিগ্রাম বট কোর হ্যান্ডলার ---
@bot.message_handler(commands=['start'])
def start(msg):
    try:
        u_id = str(msg.from_user.id)
        add_user(u_id, msg.from_user.first_name)
        m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        m.add('👤 প্রোফাইল', '📋 সাধারণ টাস্ক', '⚡ প্রো টাস্ক', '💰 ওয়ালেট', '👥 রেফারেল', '👥 কমিউনিটি')
        bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)
    except Exception: pass

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    try:
        u_id = str(msg.from_user.id)
        user = get_user(u_id)
        config = get_tasks_config()
        txt = msg.text

        # --- অ্যাডমিন প্যানেল কমান্ডস ---
        if u_id == str(ADMIN_ID):
            if txt.startswith('/setlink'):
                parts = txt.split()
                if len(parts) == 4:
                    with db_lock:
                        try:
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE tasks SET ads_link=?, ads_time=?, ads_reward=? WHERE id=1", (parts[1], int(parts[2]), float(parts[3])))
                        except Exception: pass
                    bot.reply_to(msg, f"✅ সাধারণ টাস্ক আপডেট সফল!")
                return
            elif txt.startswith('/setpro'):
                parts = txt.split()
                if len(parts) == 3:
                    with db_lock:
                        try:
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE tasks SET pro_link=?, pro_reward=? WHERE id=1", (parts[1], float(parts[2])))
                        except Exception: pass
                    bot.reply_to(msg, f"🚀 নতুন প্রো টাস্ক লিংক সেট হয়েছে!")
                return
            elif txt == '/backup':
                # ডাটাবেজ সিকিউরিটি ব্যাকআপ মেকানিজম
                if os.path.exists(DB_FILE):
                    with open(DB_FILE, 'rb') as doc:
                        bot.send_document(ADMIN_ID, doc, caption="📦 Rupa Coin ওয়ান-ক্লিক ডাটাবেজ ব্যাকআপ সফল!")
                else:
                    bot.reply_to(msg, "❌ ডাটাবেজ ফাইল পাওয়া যায়নি।")
                return

        if not user: 
            add_user(u_id, msg.from_user.first_name)
            return

        if txt == '👤 প্রোফাইল':
            bot.send_message(msg.chat.id, f"👤 প্রোফাইল:\n\n🆔 আইডি: {u_id}\n👤 নাম: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}")
        
        elif txt == '💰 ওয়ালেট':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📱 বিকাশ সেট", callback_data="set_bkash"), types.InlineKeyboardButton("📱 নগদ সেট", callback_data="set_nagad"))
            markup.add(types.InlineKeyboardButton("💸 উইথড্র করুন", callback_data="do_withdraw"))
            bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {user['balance']} Rupa Coin", reply_markup=markup)
        
        elif txt == '📋 সাধারণ টাস্ক':
            if u_id not in user_click_timers or user_click_timers[u_id]["status"] != "counting":
                user_click_timers[u_id] = {"start_time": 0, "status": "pending"}
                
            tracking_url = f"{RENDER_APP_URL}/click/ad/{u_id}"
            markup = types.InlineKeyboardMarkup(row_width=1)
            button_url = types.InlineKeyboardButton(text="🔗 ১. এখানে ক্লিক করে বিজ্ঞাপনটি দেখুন", url=tracking_url)
            button_claim = types.InlineKeyboardButton(text="🎁 ২. Claim Reward", callback_data="final_claim_task")
            markup.add(button_url, button_claim)
            
            bot.send_message(
                msg.chat.id, 
                f"📋 **Rupa Coin সাধারণ টাস্ক**\n\n"
                f"১️⃣ প্রথমে নিচের ১ নম্বর লিংকে ক্লিক করে বিজ্ঞাপনে প্রবেশ করুন। (টিপ দিলেই আপনার ১৫ সেকেন্ড কাউন্ট শুরু হবে)।\n"
                f"২️⃣ ঠিক **{config['ads_time']} সেকেন্ড** বিজ্ঞাপন দেখে এসে ২ নম্বর **'Claim Reward'** বাটনে চাপ দিন।", 
                reply_markup=markup
            )

        elif txt == '⚡ প্রো টাস্ক':
            pro_url = config['pro_link']
            current_link_hash = hashlib.md5(pro_url.encode()).hexdigest()
            
            if current_link_hash in user['completed_pro_links']:
                bot.send_message(msg.chat.id, "❌ **আপনার জন্য এখনো নতুন কোন Task আসে نی!**")
                return
                
            pro_tracking_url = f"{RENDER_APP_URL}/click/pro/{u_id}"
            
            if u_id not in user_pro_clicks or user_pro_clicks[u_id]["link_hash"] != current_link_hash:
                user_pro_clicks[u_id] = {"clicked": False, "link_hash": current_link_hash}
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn_url = types.InlineKeyboardButton(text="🔗 ১. এখানে ক্লিক করে প্রো টাস্ক ভিজিট করুন", url=pro_tracking_url)
            btn_claim = types.InlineKeyboardButton(text="🎁 ২. Claim Pro Reward", callback_data="claim_pro_task")
            markup.add(btn_url, btn_claim)
            
            bot.send_message(msg.chat.id, f"⚡ **Premium Pro Task** ⚡\n\n💰 রিওয়ার্ড: **{config['pro_reward']} Rupa Coin**\n\n⚠️ ১ নম্বর লিংকে চাপ দিয়ে টাস্ক ভিজিট করার পর ২ নম্বর বাটনে ক্লিক করুন।", reply_markup=markup)

        elif txt == '👥 রেফারেল':
            bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")
        elif txt == '👥 কমিউনিটি':
            bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")
    except Exception: pass

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        u_id = str(call.from_user.id)
        user = get_user(u_id)
        config = get_tasks_config()
        if not user: return

        # ================= সাধারণ টাস্ক ভেরিফিকেশন =================
        if call.data == "final_claim_task":
            current_time = time.time()
            ad_time = config['ads_time']
            reward = config['ads_reward']
            
            if u_id in user_click_timers and user_click_timers[u_id]["status"] == "counting":
                start_time = user_click_timers[u_id]["start_time"]
                elapsed_time = current_time - start_time
                
                if elapsed_time < ad_time:
                    user_click_timers.pop(u_id, None)
                    bot.answer_callback_query(call.id, text=f"🚨 ধোঁকাবাজি সনাক্ত হয়েছে! আপনি সম্পূর্ণ ১৫ সেকেন্ড অপেক্ষা করেননি। টাস্ক বাতিল, আবার শুরু করুন!", show_alert=True)
                else:
                    user_click_timers.pop(u_id, None)
                    new_balance = user['balance'] + reward
                    with db_lock:
                        try:
                            with get_db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute("UPDATE users SET balance=? WHERE u_id=?", (new_balance, u_id))
                        except Exception: pass
                    bot.answer_callback_query(call.id, text=f"🎉 সফল হয়েছে! {reward} Coin যোগ করা হয়েছে।", show_alert=True)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ **টাস্ক সফলভাবে সম্পন্ন!**")
            else:
                bot.answer_callback_query(call.id, text="❌ জاليةতি! আপনি ১ নম্বর বাটনে ক্লিক করে বিজ্ঞাপনে প্রবেশ করেননি।", show_alert=True)

        # ================= প্রো টাস্ক ভেরিফিকেশন =================
        elif call.data == "claim_pro_task":
            pro_url = config['pro_link']
            pro_reward = config['pro_reward']
            current_link_hash = hashlib.md5(pro_url.encode()).hexdigest()
            
            if current_link_hash in user['completed_pro_links']:
                bot.answer_callback_query(call.id, text="❌ আপনার জন্য এখনো নতুন কোন Task আসে নি!", show_alert=True)
                return

            if u_id in user_pro_clicks and user_pro_clicks[u_id]["clicked"] is True and user_pro_clicks[u_id]["link_hash"] == current_link_hash:
                user_pro_clicks.pop(u_id, None)
                new_balance = user['balance'] + pro_reward
                user['completed_pro_links'].append(current_link_hash)
                new_pro_links_str = ",".join([x for x in user['completed_pro_links'] if x])
                
                with db_lock:
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET balance=?, completed_pro_links=? WHERE u_id=?", (new_balance, new_pro_links_str, u_id))
                    except Exception: pass
                
                bot.answer_callback_query(call.id, text=f"🎉 অভিনন্দন! {pro_reward} Rupa Coin যোগ হয়েছে।", show_alert=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ **PRO টাস্ক সফলভাবে সম্পন্ন!**")
            else:
                bot.answer_callback_query(call.id, text="❌ জاليةতি! আপনি ১ নম্বর প্রো টাস্ক লিংকে ক্লিক করেননি।", show_alert=True)

        # ================= উইথড্র ও অ্যাকাউন্ট সিস্টেম =================
        elif call.data == "set_bkash":
            msg = bot.send_message(call.message.chat.id, "আপনার বিকাশ নম্বরটি লিখুন:")
            bot.register_next_step_handler(msg, lambda m: save_num(m, 'bkash'))
        elif call.data == "set_nagad":
            msg = bot.send_message(call.message.chat.id, "আপনার নগদ নম্বরটি লিখুন:")
            bot.register_next_step_handler(msg, lambda m: save_num(m, 'nagad'))
        
        elif call.data == "do_withdraw":
            if u_id in active_withdrawals: return
            if user['balance'] >= 300:
                active_withdrawals.add(u_id)
                clean_name = re.sub(r'[\_*\[\]\(\)~`>#\+\-=|{}.!]', '', user['name'])
                withdraw_msg = f"🚨 *নতুন উইথড্র রিকোয়েস্ট!*\n\n👤 ইউজার: {clean_name}\n🆔 আইডি: {u_id}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 পরিমাণ: {user['balance']} Rupa Coin"
                
                with db_lock:
                    try:
                        with get_db_connection() as conn:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE users SET balance=0.0 WHERE u_id=?", (u_id,))
                    except Exception: pass

                try: bot.send_message(ADMIN_ID, withdraw_msg, parse_mode="Markdown")
                except Exception: bot.send_message(ADMIN_ID, withdraw_msg.replace('*', ''))
                
                active_withdrawals.discard(u_id)
                bot.answer_callback_query(call.id, "✅ উইথড্র রিকোয়েস্ট সফল!", show_alert=True)
                bot.edit_message_text("✅ আপনার রিকোয়েস্টটি অ্যাডমিনের কাছে পাঠানো হয়েছে।", call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, f"⚠️ সর্বনিম্ন ৩০০ কয়েন প্রয়োজন!", show_alert=True)
    except Exception: pass

def save_num(msg, key):
    try:
        u_id = str(msg.from_user.id)
        if not msg.text: return
        clean_text = re.sub(r'[<>\'&"\'\*\_]', '', msg.text)
        with db_lock:
            try:
                with get_db_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute(f"UPDATE users SET {key}=? WHERE u_id=?", (clean_text, u_id))
            except Exception: pass
        bot.reply_to(msg, f"✅ আপনার {key} নম্বর সফলভাবে সেভ হয়েছে!")
    except Exception: pass

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False, threaded=True)).start()
    while True:
        try: 
            bot.infinity_polling(timeout=120, long_polling_timeout=120, restart_on_status_update=True, skip_pending=True)
        except Exception: 
            time.sleep(5)
