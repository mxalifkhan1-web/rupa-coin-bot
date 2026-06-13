import telebot
from telebot import types
import json
import os
import threading
import time
from flask import Flask

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DATA_FILE = "user_database.json"
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {'users': {}, 'tasks': {'ads': 'https://telega.in', 'pro': 'https://google.com'}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except:
            time.sleep(5)

@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']:
        data['users'][u_id] = {'name': msg.from_user.first_name, 'balance': 0.0, 'bkash': 'Not Set', 'nagad': 'Not Set'}
        save_data(data)
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '💸 Withdraw', '👥 Community')
    bot.send_message(msg.chat.id, "✨ স্বাগতম! কাজ শুরু করতে নিচের বাটন চাপুন।", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']: return
    txt = msg.text

    if txt == '👤 Profile':
        bot.send_message(msg.chat.id, f"👤 আইডি: {u_id}\nবিকাশ: {data['users'][u_id]['bkash']}\nনগদ: {data['users'][u_id]['nagad']}")
    
    elif txt.startswith(('/setbkash', '/setnagad')):
        parts = txt.split()
        if len(parts) > 1:
            key = 'bkash' if 'bkash' in txt else 'nagad'
            data['users'][u_id][key] = parts[1]
            save_data(data)
            bot.reply_to(msg, f"✅ {key} নাম্বার সেট হয়েছে।")

    elif txt == '💰 Wallet':
        bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {data['users'][u_id]['balance']} Rupa Coin")

    elif txt == '📋 Task (Ads)':
        markup = types.InlineKeyboardMarkup()
        # এখানে ক্লিক করলে callback 'click_ads' কল হবে
        markup.add(types.InlineKeyboardButton("🔗 লিংকে প্রবেশ করুন", callback_data="click_ads"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন, সাথে সাথে পয়েন্ট যোগ হবে:", reply_markup=markup)

    elif txt == '⚡ Pro Task':
        markup = types.InlineKeyboardMarkup()
        # এখানে ক্লিক করলে callback 'click_pro' কল হবে
        markup.add(types.InlineKeyboardButton("🔗 প্রো-লিংকে প্রবেশ করুন", callback_data="click_pro"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন, সাথে সাথে পয়েন্ট যোগ হবে:", reply_markup=markup)

    elif txt == '💸 Withdraw':
        if data['users'][u_id]['balance'] >= 300:
            bot.send_message(ADMIN_ID, f"🔔 উইথড্র রিকোয়েস্ট!\n👤 ইউজার: {data['users'][u_id]['name']}\n📱 বিকাশ: {data['users'][u_id]['bkash']}\n💰 ব্যালেন্স: {data['users'][u_id]['balance']}")
            data['users'][u_id]['balance'] = 0.0
            save_data(data)
            bot.send_message(msg.chat.id, "✅ উইথড্র সফল!")
        else:
            bot.send_message(msg.chat.id, "⚠️ ৩০০ পয়েন্ট প্রয়োজন।")

    elif txt == '👥 Referral':
        bot.send_message(msg.chat.id, f"রেফার লিংক: https://t.me/{BOT_USERNAME}?start={u_id}")

    elif txt == '👥 Community':
        bot.send_message(msg.chat.id, f"গ্রুপ: {COMMUNITY_LINK}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    if call.data == "click_ads":
        data['users'][u_id]['balance'] += 0.2
        save_data(data)
        bot.answer_callback_query(call.id, "✅ ০.২ পয়েন্ট যোগ হয়েছে!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"লিংকে যান: {data['tasks']['ads']}")
    
    elif call.data == "click_pro":
        data['users'][u_id]['balance'] += 0.4
        save_data(data)
        bot.answer_callback_query(call.id, "✅ ০.৪ পয়েন্ট যোগ হয়েছে!")
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, 
                              text=f"প্রো-লিংকে যান: {data['tasks']['pro']}")

@app.route('/')
def home(): return "Bot is running!"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    run_bot()
