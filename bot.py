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

# --- শক্তিশালী ডেটাবেস লোডার ---
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {'users': {}, 'tasks': {'ads': 'https://telega.in', 'pro': 'https://google.com'}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# --- মেইন বট লুপ (সবসময় একটিভ রাখার জন্য) ---
def run_bot():
    while True:
        try:
            print("বট চালু হচ্ছে...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"বট ক্র্যাশ করেছে, ৫ সেকেন্ড পর রিস্টার্ট হচ্ছে: {e}")
            time.sleep(5) # অটো রিস্টার্টের জন্য অপেক্ষা

# --- ফ্লাস্ক সার্ভার (রেন্ডারে বটকে জাগিয়ে রাখার জন্য) ---
@app.route('/')
def home():
    return "Bot is running 24/7!"

def start_server():
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

# --- বট ফিচারসমূহ ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']:
        data['users'][u_id] = {'name': msg.from_user.first_name, 'balance': 0.0, 'bkash': 'Not Set', 'nagad': 'Not Set'}
        save_data(data)
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '💸 Withdraw', '👥 Community')
    bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}! কাজ শুরু করুন।", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']: return
    user = data['users'][u_id]
    txt = msg.text

    if txt == '💰 Wallet':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📱 বিকাশ সেট", callback_data="set_bkash"),
                   types.InlineKeyboardButton("📱 নগদ সেট", callback_data="set_nagad"))
        bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {user['balance']} Rupa Coin\n\nপেমেন্ট নম্বর সেট করুন:", reply_markup=markup)
    
    elif txt == '📋 Task (Ads)':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 লিংকে যান", callback_data="click_ads"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন, পয়েন্ট অটো যোগ হবে:", reply_markup=markup)

    elif txt == '⚡ Pro Task':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 প্রো-লিংকে যান", callback_data="click_pro"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন, পয়েন্ট অটো যোগ হবে:", reply_markup=markup)

    elif txt == '💸 Withdraw':
        if user['balance'] >= 300:
            bot.send_message(ADMIN_ID, f"🔔 উইথড্র রিকোয়েস্ট!\n👤 নাম: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 ব্যালেন্স: {user['balance']}")
            user['balance'] = 0.0
            save_data(data)
            bot.send_message(msg.chat.id, "✅ উইথড্র রিকোয়েস্ট সফল!")
        else:
            bot.send_message(msg.chat.id, f"⚠️ ৩০০ পয়েন্ট প্রয়োজন। বর্তমান: {user['balance']}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    if call.data == "set_bkash":
        msg = bot.send_message(call.message.chat.id, "আপনার বিকাশ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'bkash'))
    elif call.data == "set_nagad":
        msg = bot.send_message(call.message.chat.id, "আপনার নগদ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'nagad'))
    elif call.data == "click_ads":
        data['users'][u_id]['balance'] += 0.2
        save_data(data)
        bot.answer_callback_query(call.id, "✅ ০.২ পয়েন্ট যোগ হয়েছে!")
        bot.edit_message_text(f"লিংকে যান: {data['tasks']['ads']}", call.message.chat.id, call.message.message_id)
    elif call.data == "click_pro":
        data['users'][u_id]['balance'] += 0.4
        save_data(data)
        bot.answer_callback_query(call.id, "✅ ০.৪ পয়েন্ট যোগ হয়েছে!")
        bot.edit_message_text(f"লিংকে যান: {data['tasks']['pro']}", call.message.chat.id, call.message.message_id)

def save_num(msg, key):
    data['users'][str(msg.from_user.id)][key] = msg.text
    save_data(data)
    bot.reply_to(msg, f"✅ আপনার {key} নম্বর সেভ হয়েছে!")

# --- বট ও ফ্লাস্ক একসাথে চালানো ---
if __name__ == "__main__":
    threading.Thread(target=start_server).start() # ফ্লাস্ক সার্ভার চালু
    run_bot() # বট চালু

