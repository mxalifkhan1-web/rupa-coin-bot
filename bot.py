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

# --- ডেটাবেস হ্যান্ডলার ---
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

# --- শক্তিশালী ২৪/৭ বট রানিং ফিচার ---
def run_bot():
    while True:
        try:
            print("Bot is starting...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"Error occurred: {e}. Restarting in 5 seconds...")
            time.sleep(5)

@app.route('/')
def home():
    return "Bot is running 24/7!"

# --- মেইন বট লজিক ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']:
        data['users'][u_id] = {'name': msg.from_user.first_name, 'balance': 0.0, 'bkash': 'Not Set', 'nagad': 'Not Set'}
        save_data(data)
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '👥 Community')
    bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']: return
    user = data['users'][u_id]
    txt = msg.text

    if txt == '👤 Profile':
        bot.send_message(msg.chat.id, f"👤 প্রোফাইল:\n\n🆔 আইডি: {u_id}\n👤 নাম: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}")
    
    elif txt == '💰 Wallet':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📱 বিকাশ সেট", callback_data="set_bkash"),
                   types.InlineKeyboardButton("📱 নগদ সেট", callback_data="set_nagad"))
        markup.add(types.InlineKeyboardButton("💸 উইথড্র করুন", callback_data="do_withdraw"))
        bot.send_message(msg.chat.id, f"💰 ব্যালেন্স: {user['balance']} Rupa Coin\n\nপেমেন্ট মেথড সেট করুন বা উইথড্র করুন:", reply_markup=markup)
    
    elif txt == '📋 Task (Ads)':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 লিংকে প্রবেশ করুন", callback_data="click_ads"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন:", reply_markup=markup)

    elif txt == '⚡ Pro Task':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔗 প্রো-লিংকে প্রবেশ করুন", callback_data="click_pro"))
        bot.send_message(msg.chat.id, "লিংকে ক্লিক করুন:", reply_markup=markup)

    elif txt == '👥 Referral':
        bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")

    elif txt == '👥 Community':
        bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    user = data['users'][u_id]

    if call.data == "set_bkash":
        msg = bot.send_message(call.message.chat.id, "আপনার বিকাশ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'bkash'))
    elif call.data == "set_nagad":
        msg = bot.send_message(call.message.chat.id, "আপনার নগদ নম্বরটি লিখুন:")
        bot.register_next_step_handler(msg, lambda m: save_num(m, 'nagad'))
    
    elif call.data == "do_withdraw":
        if user['balance'] >= 300:
            bot.send_message(ADMIN_ID, f"🔔 উইথড্র রিকোয়েস্ট!\n👤 নাম: {user['name']}\n📱 বিকাশ: {user['bkash']}\n📱 নগদ: {user['nagad']}\n💰 ব্যালেন্স: {user['balance']}")
            user['balance'] = 0.0
            save_data(data)
            bot.answer_callback_query(call.id, "✅ উইথড্র রিকোয়েস্ট সফল!")
            bot.edit_message_text("✅ রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, f"⚠️ ৩০০ পয়েন্ট প্রয়োজন! আপনার: {user['balance']}")
    
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

# --- বট ও সার্ভার একসাথে চালানো ---
if __name__ == "__main__":
    # Flask ওয়েব সার্ভার আলাদা থ্রেডে চালু
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    # বট মেইন থ্রেডে চালু
    run_bot()
