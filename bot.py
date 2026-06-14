import telebot
from telebot import types
import sqlite3
import time
import threading
from flask import Flask

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DB_FILE = "user_database.db"  
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

db_lock = threading.Lock()

user_click_timers = {}
user_pro_clicks = {}

# --- SQLite ডাটাবেজ তৈরি ও সেটআপ ---
def init_db():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
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
            
        conn.commit()
        conn.close()

init_db()

def get_tasks_config():
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT ads_link, ads_reward, ads_time, pro_link, pro_reward FROM tasks WHERE id=1")
        row = cursor.fetchone()
        conn.close()
        return {
            'ads_link': row[0], 'ads_reward': row[1], 'ads_time': row[2],
            'pro_link': row[3], 'pro_reward': row[4]
        }

def get_user(u_id):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT name, balance, bkash, nagad, completed_pro_links FROM users WHERE u_id=?", (str(u_id),))
        row = cursor.fetchone()
        conn.close()
        if row:
            return {
                'name': row[0], 'balance': row[1], 'bkash': row[2], 'nagad': row[3],
                'completed_pro_links': row[4].split(',') if row[4] else []
            }
        return None

def add_user(u_id, name):
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT OR IGNORE INTO users (u_id, name) VALUES (?, ?)", (str(u_id), name))
            conn.commit()
        except Exception as e:
            print(f"Error adding user: {e}")
        finally:
            conn.close()

# --- ব্যাকগ্রাউন্ড ক্যাশ ক্লিনার ---
def cache_cleaner():
    while True:
        time.sleep(1800) 
        now = time.time()
        for uid, t in list(user_click_timers.items()):
            if now - t > 3600: user_click_timers.pop(uid, None)
        for uid, url in list(user_pro_clicks.items()):
            if now - t > 7200: user_pro_clicks.pop(uid, None)

threading.Thread(target=cache_cleaner, daemon=True).start()

# --- ফ্ল্যাস্ক সার্ভার ---
@app.route('/')
def home(): return "Bot is running on SQLite 24/7 Safely!"

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except:
            time.sleep(5)

# --- বটের মেইন লজিক ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    add_user(u_id, msg.from_user.first_name)
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 প্রোফাইল', '📋 সাধারণ টাস্ক', '⚡ প্রো টাস্ক', '💰 ওয়ালেট', '👥 রেফারেল', '👥 কমিউনিটি')
    bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    user = get_user(u_id)
    config = get_tasks_config()
    txt = msg.text

    # --- অ্যাডমিন কমান্ডস ---
    if u_id == str(ADMIN_ID):
        if txt.startswith('/setlink'):
            parts = txt.split()
            if len(parts) == 4:
                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET ads_link=?, ads_time=?, ads_reward=? WHERE id=1", (parts[1], int(parts[2]), float(parts[3])))
                    conn.commit()
                    conn.close()
                bot.reply_to(msg, f"✅ সাধারণ টাস্ক আপডেট হয়েছে!\nলিংক: {parts[1]}\nসময়: {parts[2]} সেকেন্ড\nপয়েন্ট: {parts[3]}")
            return
            
        elif txt.startswith('/setpro'):
            parts = txt.split()
            if len(parts) == 3:
                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor()
                    cursor.execute("UPDATE tasks SET pro_link=?, pro_reward=? WHERE id=1", (parts[1], float(parts[2])))
                    conn.commit()
                    conn.close()
                bot.reply_to(msg, f"🚀 **প্রো টাস্ক আপডেট হয়েছে!**\n\n🔗 নতুন লিংক: {parts[1]}\n💰 রিওয়ার্ড কয়েন: {parts[2]}")
            return

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
        markup = types.InlineKeyboardMarkup(row_width=1)
        button_open = types.InlineKeyboardButton(text="🚀 ১. বিজ্ঞাপন লিংকটি আনুন", callback_data="get_ad_link")
        button_claim = types.InlineKeyboardButton(text="🎁 ২. Claim Reward / ভেরিফাই", callback_data="claim_task1")
        markup.add(button_open, button_claim)
        
        bot.send_message(
            msg.chat.id, 
            f"📋 **Rupa Coin টাস্ক ১**\n\n"
            f"১️⃣ প্রথমে নিচের **'🚀 ১. বিজ্ঞাপন লিংকটি আনুন'** বাটনে চাপ দিন।\n"
            f"২️⃣ লিংক আসলে সেটিতে ক্লিক করে কমপক্ষে **{ad_time} সেকেন্ড** বিজ্ঞাপনটি দেখুন।\n"
            f"৩️⃣ দেখা শেষ হলে বটের এই মেসেজে এসে **'🎁 ২. Claim Reward'** বাটনে চাপ দিন।", 
            reply_markup=markup
        )

    elif txt == '⚡ প্রো টাস্ক':
        pro_url = config['pro_link']
        pro_reward = config['pro_reward']
        
        if pro_url in user['completed_pro_links']:
            bot.send_message(msg.chat.id, "❌ **আপনার জন্য এই মুহূর্তে কোনো টাস্ক নেই!**\n\nআপনি ইতিমধ্যে এই প্রো টাস্কটি সম্পূর্ণ করে ফেলেছেন। অ্যাডমিন নতুন লিংক সেট না করা পর্যন্ত দয়া করে অপেক্ষা করুন।")
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn_get_pro = types.InlineKeyboardButton(text="🚀 ১. প্রো টাস্ক লিংকটি আনুন", callback_data="get_pro_link")
        btn_claim_pro = types.InlineKeyboardButton(text="🎁 ২. Claim Pro Reward", callback_data="claim_pro_task")
        markup.add(btn_get_pro, btn_claim_pro)
        
        bot.send_message(
            msg.chat.id, 
            f"⚡ **Premium Pro Task** ⚡\n\n"
            f"💰 এই টাস্কটি সম্পূর্ণ করলে পাবেন: **{pro_reward} Rupa Coin**\n\n"
            f"👇 **নিয়মাবলী:**\n"
            f"১️⃣ প্রথমে নিচের **'🚀 ১. প্রো টাস্ক লিংকটি আনুন'** বাটনে ক্লিক করুন।\n"
            f"২️⃣ লিংকটি ওপেন করে ঘুরে আসুন (এখানে কোনো টাইম লিমিট নেই)।\n"
            f"৩️⃣ লিংকে ঢোকার পর ব্যাক এসে **'🎁 ২. Claim Pro Reward'** বাটনে চাপ দিন।\n\n"
            f"⚠️ **শর্ত:** লিংকে ক্লিক না করে সরাসরি রিওয়ার্ড ক্লেইম করলে পয়েন্ট অ্যাড হবে না!",
            reply_markup=markup
        )

    elif txt == '👥 রেফারেল':
        bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")

    elif txt == '👥 কমিউনিটি':
        bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")


# --- ইনলাইন বাটন বা কলব্যাক কুয়েরি হ্যান্ডলার ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    user = get_user(u_id)
    config = get_tasks_config()
    if not user: return

    # ================= প্রো টাস্ক লজিক =================
    if call.data == "get_pro_link":
        pro_url = config['pro_link']
        if pro_url in user['completed_pro_links']:
            bot.answer_callback_query(call.id, text="⚠️ আপনি ইতিমধ্যে এই টাস্কটি শেষ করেছেন!", show_alert=True)
            return
            
        user_pro_clicks[u_id] = pro_url
        bot.answer_callback_query(call.id, text="✅ আপনার প্রিমিয়াম লিংক নিচে পাঠানো হয়েছে!", show_alert=False)
        
        pro_markup = types.InlineKeyboardMarkup()
        pro_markup.add(types.InlineKeyboardButton(text="🔗 লিংকে প্রবেশ করতে এখানে চাপ দিন", url=pro_url))
        
        bot.send_message(
            call.message.chat.id,
            f"🔥 **আপনার প্রো টাস্ক লিংক রেডি!**\n\n"
            f"👉 নিচের লিংকে ক্লিক করে টাস্কটি ভিজিট করুন। ভিজিট করা শেষ হলে উপরের মেইন মেসেজের **'Claim Pro Reward'** বাটনে চাপ দিন।",
            reply_markup=pro_markup
        )

    elif call.data == "claim_pro_task":
        pro_url = config['pro_link']
        pro_reward = config['pro_reward']
        
        if pro_url in user['completed_pro_links']:
            bot.answer_callback_query(call.id, text="❌ আপনি ইতিমধ্যে এই টাস্কের রিওয়ার্ড নিয়ে নিয়েছেন!", show_alert=True)
            return

        if u_id in user_pro_clicks and user_pro_clicks[u_id] == pro_url:
            new_balance = user['balance'] + pro_reward
            user['completed_pro_links'].append(pro_url)
            new_pro_links_str = ",".join(user['completed_pro_links'])
            
            with db_lock:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET balance=?, completed_pro_links=? WHERE u_id=?", (new_balance, new_pro_links_str, u_id))
                conn.commit()
                conn.close()
            
            bot.answer_callback_query(call.id, text=f"🎉 অভিনন্দন! অ্যাকাউন্টে {pro_reward} Rupa Coin যোগ করা হয়েছে।", show_alert=True)
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=call.message.message_id, 
                text=f"✅ **PRO টাস্ক সফলভাবে সম্পন্ন!**\n\nআপনি এই টাস্ক থেকে **{pro_reward} Rupa Coin** বোনাস পেয়েছেন। এই টাস্কটি আপনার জন্য চিরতরে লক করা হলো।"
            )
            user_pro_clicks.pop(u_id, None)
        else:
            bot.answer_callback_query(call.id, text="❌ আপনি তো এখনও প্রো লিংকটি আনেননি বা লিংকে ক্লিক করেননি! প্রথমে লিংক বাটনে চাপ দিন।", show_alert=True)
            
    # ================= সাধারণ টাস্ক (Ads) লজিক =================
    elif call.data == "get_ad_link":
        ad_url = config['ads_link']
        user_click_timers[u_id] = time.time()
        bot.answer_callback_query(call.id, text="✅ বিজ্ঞাপন লিংক নিচে পাঠানো হয়েছে!", show_alert=False)
        link_markup = types.InlineKeyboardMarkup()
        link_markup.add(types.InlineKeyboardButton(text="👁️ বিজ্ঞাপন দেখতে এখানে ক্লিক করুন", url=ad_url))
        bot.send_message(call.message.chat.id, f"🔗 **আপনার বিজ্ঞাপন লিংক রেডি!**\n\n👉 নিচের বাটনে ক্লিক করে বিজ্ঞাপনটি ওপেন করুন।", reply_markup=link_markup)

    elif call.data == "claim_task1":
        current_time = time.time()
        ad_time = config['ads_time']
        reward = config['ads_reward']
        
        if u_id in user_click_timers:
            start_time = user_click_timers[u_id]
            elapsed_time = current_time - start_time
            if elapsed_time >= ad_time:
                new_balance = user['balance'] + reward
                with db_lock:
                    conn = sqlite3.connect(DB_FILE)
                    cursor = conn.cursor() # ✅ টাইপোটি এখানে পারফেক্টলি ফিক্স করা হয়েছে
                    cursor.execute("UPDATE users SET balance=? WHERE u_id=?", (new_balance, u_id))
                    conn.commit()
                    conn.close()
                bot.answer_callback_query(call.id, text=f"✅ সফল হয়েছে! আপনি {reward} Coin বোনাস পেয়েছেন।", show_alert=True)
                bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text=f"🎉 **অভিনন্দন!**\n\nআপনার অ্যাকাউন্টে **{reward} Rupa Coin** যোগ করা হয়েছে! ✅")
                user_click_timers.pop(u_id, None)
            else:
                remaining_time = int(ad_time - elapsed_time)
                bot.answer_callback_query(call.id, text=f"⚠️ দয়া করে আরও {remaining_time} সেকেন্ড অপেক্ষা করুন।", show_alert=True)
        else:
            bot.answer_callback_query(call.id, text="❌ প্রথমে '১. বিজ্ঞাপন লিংকটি আনুন' বাটনে চাপ দিন।", show_alert=True)

    # ================= পেমেন্ট ও ওয়ালেট লজিক =================
    elif call.data == "set_bkash":
        msg = bot.send_message(call.message.chat.id, "আপনার বিকাশ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'bkash'))
    elif call.data == "set_nagad":
        msg = bot.send_message(call.message.chat.id, "আপনার নগদ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'nagad'))
    
    elif call.data == "do_withdraw":
        if user['balance'] >= 300:
            withdraw_msg = f"🚨 **নতুন উইথড্র রিকোয়েস্ট!**\n\n👤 ইউজার: {user['name']}\n🆔 আইডি: {u_id}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 পরিমাণ: {user['balance']} Rupa Coin"
            bot.send_message(ADMIN_ID, withdraw_msg, parse_mode="Markdown")
            
            with db_lock:
                conn = sqlite3.connect(DB_FILE)
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET balance=0.0 WHERE u_id=?", (u_id,))
                conn.commit()
                conn.close()
                
            bot.answer_callback_query(call.id, "✅ উইথড্র রিকোয়েস্ট সফল!")
            bot.edit_message_text("✅ রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, f"⚠️ ৩০০ পয়েন্ট প্রয়োজন! আপনার আছে: {user['balance']}")

def save_num(msg, key):
    u_id = str(msg.from_user.id)
    with db_lock:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {key}=? WHERE u_id=?", (msg.text, u_id))
        conn.commit()
        conn.close()
    bot.reply_to(msg, f"✅ আপনার {key} নম্বর সফলভাবে সেভ হয়েছে!")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    run_bot()
