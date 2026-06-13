import telebot
from telebot import types
import json
import os

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "user_database.json"

COMMUNITY_LINK = "https://t.me/rupacoin27bd"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
    if not isinstance(data, dict): return
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

user_data = load_data()

def get_or_create_user(user_id, first_name):
    u_id = str(user_id)
    if u_id not in user_data:
        user_data[u_id] = {'name': first_name, 'balance': 0.0, 'bkash': 'Not Set', 'nagad': 'Not Set'}
    save_data(user_data)
    return user_data[u_id]

def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('🏠 Home', '💰 Wallet', '👥 Referral', '⚡ Pro Task', '💸 Withdraw', '👥 Community')
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    args = msg.text.split()
    if len(args) > 1:
        ref_id = args[1]
        if ref_id != u_id and ref_id in user_data:
            user_data[ref_id]['balance'] += 5.0
            save_data(user_data)
            bot.send_message(ref_id, "🎉 নতুন রেফারেল জয়েন করায় আপনি ৫ কয়েন পেয়েছেন!")
    
    get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, "স্বাগতম! কাজ শুরু করতে মেনু ব্যবহার করুন।", reply_markup=menu())

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    txt, cid = msg.text, msg.chat.id
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if txt == '🏠 Home': 
        bot.send_message(cid, "🏠 হোমে স্বাগতম!")
    
    elif txt == '💰 Wallet': 
        bot.send_message(cid, f"💰 আপনার বর্তমান ব্যালেন্স: {user['balance']} Rupa Coin")
        
    elif txt == '👥 Referral':
        ref_link = f"https://t.me/{BOT_USERNAME}?start={str(msg.from_user.id)}"
        bot.send_message(cid, f"👥 আপনার রেফারেল লিংক:\n`{ref_link}`\n\nপ্রতি নতুন জয়েনিংয়ে ৫ কয়েন!")

    elif txt == '⚡ Pro Task':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="⚡ টাস্ক সম্পন্ন করে ০.৪ কয়েন নিন", callback_data="pro_task"))
        bot.send_message(cid, "লিংকে ক্লিক করে টাস্ক পূর্ণ করুন এবং নিচে বাটনে চাপুন:", reply_markup=markup)
        
    elif txt == '💸 Withdraw':
        if user['balance'] >= 200:
            bot.send_message(cid, "✅ উইথড্র রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।")
            bot.send_message(ADMIN_ID, f"🔔 উইথড্র রিকোয়েস্ট: {user['name']} (ব্যালেন্স: {user['balance']})")
        else:
            bot.send_message(cid, f"⚠️ দুঃখিত, উইথড্র করতে ২০০ কয়েন প্রয়োজন। বর্তমান ব্যালেন্স: {user['balance']}")
            
    elif txt == '👥 Community':
        bot.send_message(cid, f"আমাদের গ্রুপ লিংক: {COMMUNITY_LINK}")

@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    u_id = str(call.from_user.id)
    if call.data == "pro_task":
        user_data[u_id]['balance'] += 0.4
        save_data(user_data)
        bot.answer_callback_query(call.id, "✅ ০.৪ কয়েন সফলভাবে যোগ হয়েছে!")
        bot.send_message(call.message.chat.id, "✅ আপনার ব্যালেন্সে ০.৪ কয়েন যোগ হয়েছে।")

from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    bot.infinity_polling()
