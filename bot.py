import telebot
from telebot import types
import json
import os
import threading
import time
from flask import Flask

# কনফিগারেশন
TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DATA_FILE = "user_database.json"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ডাটাবেস হ্যান্ডলার
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {'users': {}, 'tasks': {'ads': 'https://telega.in', 'pro': 'https://google.com'}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# --- বট স্ট্যাবিলিটি ও অটো-রিস্টার্ট ---
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"বট রিস্টার্ট নিচ্ছে... এরর: {e}")
            time.sleep(5)

# --- অ্যাডমিন কন্ট্রোল ---
@bot.message_handler(commands=['setlink'])
def set_links(msg):
    if msg.from_user.id != ADMIN_ID: return
    parts = msg.text.split()
    if len(parts) >= 3:
        data['tasks'][parts[1]] = parts[2]
        save_data(data)
        bot.reply_to(msg, f"✅ {parts[1]} লিংক সফলভাবে আপডেট করা হয়েছে।")

# --- মেনু ও প্রোফাইল ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']:
        data['users'][u_id] = {'name': msg.from_user.first_name, 'balance': 0.0, 'bkash': 'Not Set', 'nagad': 'Not Set'}
        save_data(data)
    
    # রেফারেল বোনাস
    args = msg.text.split()
    if len(args) > 1 and args[1] != u_id and args[1] in data['users']:
        data['users'][args[1]]['balance'] += 5.0
        save_data(data)

    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '💸 Withdraw', '👥 Community')
    bot.send_message(msg.chat.id, f"স্বাগতম {msg.from_user.first_name}! Rupa Coin এ কাজ করে আয় করুন।", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    user = data['users'].get(u_id)
    if not user: return

    if msg.text == '👤 Profile':
        bot.send_message(msg.chat.id, f"👤 প্রোফাইল:\nID: {u_id}\nনাম: {user['name']}\nবিকাশ: {user['bkash']}\nনগদ: {user['nagad']}\n\nআপনার নাম্বার সেট করতে লিখুন:\n/setbkash [নাম্বার]\n/setnagad [নাম্বার]")
    
    elif msg.text.startswith(('/setbkash', '/setnagad')):
        parts = msg.text.split()
        if len(parts) > 1:
            key = 'bkash' if 'bkash' in msg.text else 'nagad'
            user[key] = parts[1]
            save_data(data)
            bot.reply_to(msg, f"✅ আপনার {key} নাম্বার আপডেট হয়েছে।")

    elif msg.text == '💸 Withdraw':
        if user['balance'] >= 300:
            bot.send_message(ADMIN_ID, f"🔔 উইথড্র রিকোয়েস্ট!\n👤 ইউজার: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 ব্যালেন্স: {user['balance']} কয়েন")
            user['balance'] = 0.0  # ব্যালেন্স রিসেট
            save_data(data)
            bot.send_message(msg.chat.id, "✅ উইথড্র সফল! আপনার ব্যালেন্স জিরো হয়েছে এবং অ্যাডমিনকে জানানো হয়েছে।")
        else:
            bot.send_message(msg.chat.id, f"⚠️ ৩০০ কয়েন হলে উইথড্র দিতে পারবেন। বর্তমান: {user['balance']}")

    elif msg.text == '📋 Task (Ads)':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 লিংকে যান", url=data['tasks']['ads']),
                   types.InlineKeyboardButton("✅ কয়েন নিন", callback_data="add_ads"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করে ব্যাক এসে কয়েন নিন:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    if call.data == "add_ads":
        data['users'][u_id]['balance'] += 0.2
        save_data(data)
        bot.answer_callback_query(call.id, "✅ ০.২ কয়েন যোগ হয়েছে!")

@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    run_bot() # অটো-রিস্টার্ট ফাংশন চালু
