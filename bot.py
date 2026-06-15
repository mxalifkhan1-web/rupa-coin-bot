import telebot
from telebot import types
import sqlite3
import time
import threading
import re
from flask import Flask

# --- কনফিগারেশন ---
TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DB_FILE = "user_database.db"  
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

# হাই-কনকারেন্সি থ্রেড পুল (একসাথে ৬০টি রিকোয়েস্ট প্যারালালি প্রসেস করবে)
bot = telebot.TeleBot(TOKEN, num_threads=60)
app = Flask(__name__)

# ডাটাবেজ এবং ট্রানজেকশনের ডেডলক প্রতিরোধের জন্য গ্লোবাল লক
db_lock = threading.Lock()

# ইন-মেমোরি আল্ট্রা-ফাস্ট ট্র্যাকিং ও স্প্যাম প্রটেকশন সেশন
user_click_timers = {} 
user_pro_clicks = {}
active_withdrawals = set()  # উইথড্র স্প্যামিং লক করার জন্য বিশেষ সেট

# --- অত্যন্ত সুরক্ষিত ডাটাবেজ কানেকশন স্কিম (হাই-ট্রাফিক অপ্টিমাইজড) ---
def get_db_connection():
    """রেন্ডার সার্ভারের জন্য আল্ট্রা-ফাস্ট এবং লক-ফ্রি WAL মোড কানেকশন তৈরি করে"""
    conn = sqlite3.connect(DB_FILE, timeout=60.0, isolation_level=None) 
    conn.execute('PRAGMA journal_mode=WAL;')       
    conn.execute('PRAGMA synchronous=NORMAL;')    
    conn.execute('PRAGMA cache_size=-64000;')  # ৬৪ মেগাবাইট ক্যাশ মেমোরি বুস্টার
    return conn

# --- ডাটাবেজ ইনিশিয়ালাইজেশন ---
def init_db():
    with db_lock:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
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
            
            cursor.execute("SELECT COUNT(*) FROM tasks")
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO tasks (id, ads_link, ads_reward, ads_time, pro_link, pro_reward)
                    VALUES (1, 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 0.2, 15, 'https://t.me/rupacoin27bd', 1.0)
                ''')
            conn.close()
        except Exception as e:
            print(f"Database Init Error: {e}")

init_db()

def get_tasks_config():
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ads_link, ads_reward, ads_time, pro_link, pro_reward FROM tasks WHERE id=1")
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'ads_link': row[0], 'ads_reward': row[1], 'ads_time': row[2],
                    'pro_link': row[3], 'pro_reward': row[4]
                }
    except Exception as e:
        print(f"Error fetching tasks config: {e}")
    return {
        'ads_link': 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 'ads_reward': 0.2, 'ads_time': 15,
        'pro_link': 'https://t.me/rupacoin27bd', 'pro_reward': 1.0
    }

def get_user(u_id):
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT name, balance, bkash, nagad, completed_pro_links FROM users WHERE u_id=?", (str(u_id),))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'name': row[0], 'balance': row[1], 'bkash': row[2], 'nagad': row[3],
                    'completed_pro_links': [x for x in row[4].split(',') if x] if row[4] else []
                }
    except Exception as e:
        print(f"Error fetching user {u_id}: {e}")
    return None

def add_user(u_id, name):
    if not name:
        name = "User"
    # XSS, HTML ও ডাটাবেজ ইনজেকশন সম্পূর্ণ ক্লিন করার ফিল্টার
    name = re.sub(r'[<>&\'"\*\_]', '', name)
    with db_lock:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("INSERT OR IGNORE INTO users (u_id, name) VALUES (?, ?)", (str(u_id), name))
            conn.close()
        except Exception as e:
            print(f"Error adding user {u_id}: {e}")

# --- স্মার্ট মেমোরি গার্বেজ কালেক্টর (র‍্যাম প্রটেকশন লেয়ার) ---
def cache_cleaner():
    while True:
        try:
            time.sleep(180) # প্রতি ৩ মিনিট পর পর অটো-ক্লিন রান হবে ও র‍্যাম ফ্রি করবে
            now = time.time()
            for uid, data in list(user_click_timers.items()):
                if data["start_time"] > 0 and now - data["start_time"] > 600: 
                    user_click_timers.pop(uid, None)
            for uid, url in list(user_pro_clicks.items()):
                if uid not in user_click_timers and now % 3600 == 0:
                    user_pro_clicks.pop(uid, None)
        except Exception as e:
            print(f"Error in cache cleaner: {e}")

threading.Thread(target=cache_cleaner, daemon=True).start()

# --- লাইভ আপটাইম মনিটরিং ফ্লাস্ক গেটওয়ে ---
@app.route('/')
def home(): 
    return "Bot Core Architecture Status: 100% Operational & Safe!"

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=120, long_polling_timeout=120)
        except Exception as e:
            print(f"Bot Polling Exception: {e}. Reconnecting Core in 5 seconds...")
            time.sleep(5)

# --- কোর মেসেজিং রাউটার ---
@bot.message_handler(commands=['start'])
def start(msg):
    try:
        u_id = str(msg.from_user.id)
        add_user(u_id, msg.from_user.first_name)
        
        m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        m.add('👤 প্রোফাইল', '📋 সাধারণ টাস্ক', '⚡ প্রো টাস্ক', '💰 ওয়ালেট', '👥 রেফারেল', '👥 কমিউনিটি')
        bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)
    except Exception as e:
        print(f"Start command exception: {e}")

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    try:
        u_id = str(msg.from_user.id)
        user = get_user(u_id)
        config = get_tasks_config()
        txt = msg.text

        # --- প্রিমিয়াম অ্যাডমিন প্যানেল কমান্ডস ---
        if u_id == str(ADMIN_ID):
            if txt.startswith('/setlink'):
                parts = txt.split()
                if len(parts) == 4:
                    with db_lock:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tasks SET ads_link=?, ads_time=?, ads_reward=? WHERE id=1", (parts[1], int(parts[2]), float(parts[3])))
                        conn.close()
                    bot.reply_to(msg, f"✅ সাধারণ টাস্ক আপডেট হয়েছে!\nলিংক: {parts[1]}\nসময়: {parts[2]} সেকেন্ড\nপয়েন্ট: {parts[3]}")
                return
                
            elif txt.startswith('/setpro'):
                parts = txt.split()
                if len(parts) == 3:
                    with db_lock:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE tasks SET pro_link=?, pro_reward=? WHERE id=1", (parts[1], float(parts[2])))
                        conn.close()
                    bot.reply_to(msg, f"🚀 **প্রো টাস্ক আপডেট হয়েছে!**\n\n🔗 নতুন লিংক: {parts[1]}\n💰 রিওয়ার্ড কয়েন: {parts[2]}")
                return

        if not user: 
            add_user(u_id, msg.from_user.first_name)
            user = get_user(u_id)
            if not user: return

        if txt == '👤 প্রোফাইল':
            bot.send_message(msg.chat.id, f"👤 প্রোফাইল:\n\n🆔 আইডি: {u_id}\n👤 নাম: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}")
        
        elif txt == '💰 ওয়ালেট':
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("📱 বিকাশ সেট", callback_data="set_bkash"),
                       types.InlineKeyboardButton("📱 নগদ সেট", callback_data="set_nagad"))
            markup.add(types.InlineKeyboardButton("💸 উইথড্র করুন", callback_data="do_withdraw"))
            bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {user['balance']} Rupa Coin\n\nপেমেন্ট মেথড সেট করুন বা উইথড্র করুন:", reply_markup=markup)
        
        elif txt == '📋 সাধারণ টাস্ক':
            ad_time = config['ads_time']
            user_click_timers[u_id] = {"start_time": 0, "status": "pending"}
            
            markup = types.InlineKeyboardMarkup(row_width=1)
            button_url = types.InlineKeyboardButton(text="🔗 ১. এখানে ক্লিক করে বিজ্ঞাপনটি দেখুন", url=config['ads_link'])
            button_start = types.InlineKeyboardButton(text="⏱️ ২. বিজ্ঞাপনে ঢুকে এখানে চাপ দিন (টাইমার চালু)", callback_data="start_timer_clock")
            button_claim = types.InlineKeyboardButton(text="🎁 ৩. Claim Reward / ভেরিফাই", callback_data="final_claim_task")
            markup.add(button_url, button_start, button_claim)
            
            bot.send_message(
                msg.chat.id, 
                f"📋 **Rupa Coin টাস্ক গেটওয়ে**\n\n"
                f"১️⃣ প্রথমে **'🔗 ১. এখানে ক্লিক করে বিজ্ঞাপনটি দেখুন'** বাটনে চাপ দিয়ে বিজ্ঞাপনে যান।\n"
                f"২️⃣ বিজ্ঞাপনে প্রবেশ করার সাথে সাথে দ্রুত বটের এই মেসেজে ব্যাক এসে **'⏱️ ২. বিজ্ঞাপনে ঢুকে এখানে চাপ দিন'** বাটনে চাপুন। এতে বটের আসল টাইমার সচল হবে।\n"
                f"৩️⃣ ঠিক **{ad_time} সেকেন্ড** পর **'🎁 ৩. Claim Reward'** বাটনে চাপ দিয়ে পয়েন্ট ridicu করুন।\n\n"
                f"⚠️ **সতর্কতা:** সময় শেষ হওয়ার আগে ক্লেইম করার চেষ্টা করলে পুরো টাস্ক বাতিল হবে এবং পুনরায় প্রথম থেকে শুরু করতে হবে!", 
                reply_markup=markup
            )

        elif txt == '⚡ প্রো টাস্ক':
            pro_url = config['pro_link']
            pro_reward = config['pro_reward']
            
            if pro_url in user['completed_pro_links']:
                bot.send_message(msg.chat.id, "❌ **আপনার জন্য এই মুহূর্তে কোনো টাস্ক নেই!**")
                return
                
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn_get_pro = types.InlineKeyboardButton(text="🚀 ১. প্রো টাস্ক লিংকটি আনুন", callback_data="get_pro_link")
            btn_claim_pro = types.InlineKeyboardButton(text="🎁 ২. Claim Pro Reward", callback_data="claim_pro_task")
            markup.add(btn_get_pro, btn_claim_pro)
            
            bot.send_message(
                msg.chat.id, 
                f"⚡ **Premium Pro Task** ⚡\n\n💰 রিওয়ার্ড: **{pro_reward} Rupa Coin**",
                reply_markup=markup
            )

        elif txt == '👥 রেফারেল':
            bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")

        elif txt == '👥 কমিউনিটি':
            bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")
    except Exception as e:
        print(f"Message reply handler exception: {e}")


# --- সিকিউরড কলব্যাক কুয়েরি ইন্টেলিজেন্স (উইথড্র ও অ্যান্টি-ফ্রড বুস্টেড) ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    try:
        u_id = str(call.from_user.id)
        user = get_user(u_id)
        config = get_tasks_config()
        if not user: 
            bot.answer_callback_query(call.id, text="❌ সেশন আউট! অনুগ্রহ করে বটটি রিস্টার্ট করুন (/start)", show_alert=True)
            return

        # ================= সাধারণ বিজ্ঞাপন টাস্ক প্রটেকশন ব্লক =================
        if call.data == "start_timer_clock":
            if u_id in user_click_timers and user_click_timers[u_id]["status"] == "pending":
                user_click_timers[u_id] = {"start_time": time.time(), "status": "counting"}
                bot.answer_callback_query(call.id, text=f"🚀 টাইমার সচল হয়েছে! ঠিক {config['ads_time']} সেকেন্ড বিজ্ঞাপনে অপেক্ষা করুন।", show_alert=True)
            else:
                bot.answer_callback_query(call.id, text="❌ সেশন ওভার! অনুগ্রহ করে '📋 সাধারণ টাস্ক' বাটনে আবার চাপ দিন।", show_alert=True)

        elif call.data == "final_claim_task":
            current_time = time.time()
            ad_time = config['ads_time']
            reward = config['ads_reward']
            
            if u_id in user_click_timers and user_click_timers[u_id]["status"] == "counting":
                start_time = user_click_timers[u_id]["start_time"]
                elapsed_time = current_time - start_time
                
                if elapsed_time < ad_time:
                    user_click_timers.pop(u_id, None)
                    bot.answer_callback_query(call.id, text=f"🚨 ধোঁকাবাজি সনাক্ত হয়েছে! আপনি সম্পূর্ণ সময় অপেক্ষা করেননি। আপনার চলতি টাস্কটি বাতিল করা হলো! আবার শুরু করুন।", show_alert=True)
                else:
                    user_click_timers.pop(u_id, None)
                    new_balance = user['balance'] + reward
                    with db_lock:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET balance=? WHERE u_id=?", (new_balance, u_id))
                        conn.close()
                    bot.answer_callback_query(call.id, text=f"🎉 অভিনন্দন! আপনি {reward} Rupa Coin বোনাস পেয়েছেন।", show_alert=True)
                    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ **টাস্ক সফলভাবে সম্পূর্ণ!**\n\nআপনার অ্যাকাউন্টে **{reward} Rupa Coin** যোগ করা হয়েছে।")
            else:
                bot.answer_callback_query(call.id, text="❌ কোনো একটিভ টাইমার পাওয়া যায়নি! প্রথমে ২ নম্বর বাটন চেপে টাইমার চালু করুন।", show_alert=True)

        # ================= প্রো টাস্ক ব্লক =================
        elif call.data == "get_pro_link":
            pro_url = config['pro_link']
            if pro_url in user['completed_pro_links']:
                bot.answer_callback_query(call.id, text="⚠️ আপনি ইতিমধ্যে এই টাস্কটি শেষ করেছেন!", show_alert=True)
                return
                
            user_pro_clicks[u_id] = pro_url
            bot.answer_callback_query(call.id, text="✅ আপনার প্রিমিয়াম লিংক নিচে পাঠানো হয়েছে!", show_alert=False)
            
            pro_markup = types.InlineKeyboardMarkup()
            pro_markup.add(types.InlineKeyboardButton(text="🔗 লিংকে প্রবেশ করতে এখানে চাপ দিন", url=pro_url))
            bot.send_message(call.message.chat.id, f"🔥 **আপনার প্রো টাস্ক লিংক রেডি!**\n\n👉 নিচের লিংকে ক্লিক করে টাস্কটি ভিজিট করুন।", reply_markup=pro_markup)

        elif call.data == "claim_pro_task":
            pro_url = config['pro_link']
            pro_reward = config['pro_reward']
            
            if pro_url in user['completed_pro_links']:
                bot.answer_callback_query(call.id, text="❌ আপনি ইতিমধ্যে এই টাস্কের রিওয়ার্ড নিয়ে নিয়েছেন!", show_alert=True)
                return

            if u_id in user_pro_clicks and user_pro_clicks[u_id] == pro_url:
                user_pro_clicks.pop(u_id, None) 
                new_balance = user['balance'] + pro_reward
                user['completed_pro_links'].append(pro_url)
                new_pro_links_str = ",".join([x for x in user['completed_pro_links'] if x])
                
                with db_lock:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("UPDATE users SET balance=?, completed_pro_links=? WHERE u_id=?", (new_balance, new_pro_links_str, u_id))
                    conn.close()
                
                bot.answer_callback_query(call.id, text=f"🎉 অভিনন্দন! অ্যাকাউন্টে {pro_reward} Rupa Coin যোগ করা হয়েছে।", show_alert=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"✅ **PRO টাস্ক সফলভাবে সম্পন্ন!**")
            else:
                bot.answer_callback_query(call.id, text="❌ জاليةতি সনাক্ত হয়েছে! প্রথমে লিংক বাটনে চাপ দিন।", show_alert=True)
                
        # ================= পেমেন্ট সেটেলমেন্ট গেটওয়ে (উইথড্র সিস্টেম) =================
        elif call.data == "set_bkash":
            msg = bot.send_message(call.message.chat.id, "আপনার বিকাশ নম্বরটি লিখুন:")
            bot.register_next_step_handler(msg, lambda m: save_num(m, 'bkash'))
        elif call.data == "set_nagad":
            msg = bot.send_message(call.message.chat.id, "আপনার নগদ নম্বরটি লিখুন:")
            bot.register_next_step_handler(msg, lambda m: save_num(m, 'nagad'))
        
        elif call.data == "do_withdraw":
            # ১. রেস-কন্ডিশন চেক (একই ইউজার একসাথে ডাবল ক্লিক করলে লক করবে)
            if u_id in active_withdrawals:
                bot.answer_callback_query(call.id, text="⚠️ আপনার পূর্বের রিকোয়েস্টটি প্রসেস হচ্ছে, অনুগ্রহ করে অপেক্ষা করুন।", show_alert=True)
                return
                
            if user['balance'] >= 300:
                # সেশন লক এক্টিভেট
                active_withdrawals.add(u_id)
                
                # নাম ক্লিনিং ফিল্টার (টেলিগ্রাম মার্কডাউন ফরম্যাট ক্র্যাশ রোধে)
                clean_name = re.sub(r'[\_*\[\]\(\)~`>#\+\-=|{}.!]', '', user['name'])
                withdraw_msg = f"🚨 *নতুন উইথড্র রিকোয়েস্ট!*\n\n👤 ইউজার: {clean_name}\n🆔 আইডি: {u_id}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 পরিমাণ: {user['balance']} Rupa Coin"
                
                # ২. ডাটাবেজ ব্যালেন্স ফ্ল্যাশ লক (পয়েন্ট আগে জিরো হবে, জালিয়াতি রুখতে)
                with db_lock:
                    try:
                        conn = get_db_connection()
                        cursor = conn.cursor()
                        cursor.execute("UPDATE users SET balance=0.0 WHERE u_id=?", (u_id,))
                        conn.close()
                    except Exception as db_err:
                        active_withdrawals.discard(u_id)
                        bot.answer_callback_query(call.id, text="❌ ডাটাবেজ ব্যস্ত আছে। অনুগ্রহ করে ২ সেকেন্ড পর আবার চেষ্টা করুন।", show_alert=True)
                        return

                # ৩. অ্যাডমিনকে নোটিফিকেশন পাঠানো (সম্পূর্ণ এরর ট্র্যাপ প্রটেকশনসহ)
                msg_sent = False
                try:
                    bot.send_message(ADMIN_ID, withdraw_msg, parse_mode="Markdown")
                    msg_sent = True
                except Exception:
                    try:
                        # ব্যাকআপ প্লেইন টেক্সট মেসেজ (টেলিগ্রাম এরর দিলে এটি কাজ করবে)
                        plain_msg = withdraw_msg.replace('*', '')
                        bot.send_message(ADMIN_ID, plain_msg)
                        msg_sent = True
                    except Exception as admin_err:
                        print(f"Fatal: Could not notify Admin: {admin_err}")

                # উইথড্র লক রিলিজ
                active_withdrawals.discard(u_id)
                
                bot.answer_callback_query(call.id, "✅ উইথড্র রিকোয়েস্ট সফল হয়েছে!", show_alert=True)
                bot.edit_message_text("✅ আপনার রিকোয়েস্টটি অ্যাডমিনের কাছে পাঠানো হয়েছে। খুব শীঘ্রই পেমেন্ট পেয়ে যাবেন।", call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, f"⚠️ সর্বনিম্ন ৩০০ কয়েন প্রয়োজন! আপনার কারেন্ট ব্যালেন্স: {user['balance']} Rupa Coin", show_alert=True)
    except Exception as e:
        print(f"Callback query global handler exception: {e}")

def save_num(msg, key):
    try:
        u_id = str(msg.from_user.id)
        if not msg.text: return
        clean_text = re.sub(r'[<>\'&"\'\*\_]', '', msg.text)
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(f"UPDATE users SET {key}=? WHERE u_id=?", (clean_text, u_id))
            conn.close()
        bot.reply_to(msg, f"✅ আপনার {key} নম্বর সফলভাবে সেভ হয়েছে!")
    except Exception as e:
        print(f"Error saving safe phone number: {e}")

if __name__ == "__main__":
    # মাল্টিপল সাব-প্রসেস জ্যাম এবং রেন্ডার পোর্ট বাইন্ডিং ফিক্স
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000, use_reloader=False, threaded=True)).start()
    run_bot()
