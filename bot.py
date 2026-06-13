import telebot
from telebot import types
import json
import os

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'mdalif268'

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "user_database.json"

current_ad_link = "https://telega.in"  
pro_task_link = "https://google.com" 
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_data(data):
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
    m.add('🏠 Home', '📋 Task (Ads)', '⭐ Pro Task', '💰 Wallet', '👥 Referral', '💸 Withdraw', '👥 Community')
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, "✨ **Rupa Coin বতে স্বাগতম!**", parse_mode="Markdown", reply_markup=menu())

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    global current_ad_link, pro_task_link
    txt, cid = msg.text, msg.chat.id
    u_id = str(msg.from_user.id)
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if txt == '🏠 Home': 
        bot.send_message(cid, f"👤 **ব্যবহারকারী:** {user['name']}\n💰 **ব্যালেন্স:** {user['balance']:.1f} Rupa Coin", parse_mode="Markdown")
    
    elif txt == '📋 Task (Ads)': 
        user_data[u_id]['balance'] += 0.2
        save_data(user_data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="🎁 ভিজিট করুন", url=current_ad_link))
        bot.send_message(cid, "✅ বিজ্ঞাপন ভিজিট সম্পন্ন! ০.২ কয়েন যোগ হয়েছে।", reply_markup=markup)
        
    elif txt == '⭐ Pro Task': 
        user_data[u_id]['balance'] += 0.5
        save_data(user_data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="⭐ Pro Task ভিজিট", url=pro_task_link))
        bot.send_message(cid, "✅ প্রো টাস্ক সম্পন্ন! ০.৫ কয়েন যোগ হয়েছে।", reply_markup=markup)
        
    elif txt == '💰 Wallet': 
        bot.send_message(cid, f"💰 **আপনার ওয়ালেট:**\nমোট ব্যালেন্স: {user_data[u_id]['balance']:.1f} Rupa Coin", parse_mode="Markdown")
        
    elif txt == '💸 Withdraw':
        # এডমিনের কাছে নোটিফিকেশন পাঠানো
        admin_message = f"🔔 **নতুন উইথড্র রিকোয়েস্ট!**\n\n👤 **ইউজার:** {user['name']}\n🆔 **ID:** {u_id}\n💰 **ব্যালেন্স:** {user['balance']:.1f}\n📱 **বিকাশ:** {user.get('bkash', 'Not Set')}\n📱 **নগদ:** {user.get('nagad', 'Not Set')}"
        bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
        
        # ইউজারকে রিপ্লাই দেওয়া
        bot.send_message(cid, f"💸 **উইথড্র রিকোয়েস্ট পাঠানো হয়েছে!**\n\nঅ্যাডমিন আপনার রিকোয়েস্টটি চেক করে পেমেন্ট পাঠিয়ে দেবে।\n\n📱 আপনার সেট করা নম্বর:\nবিকাশ: {user.get('bkash', 'Not Set')}\nনগদ: {user.get('nagad', 'Not Set')}", parse_mode="Markdown")
        
    elif txt == '👥 Referral':
        ref_link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
        bot.send_message(cid, f"👥 **আপনার রেফারেল লিংক:**\n`{ref_link}`", parse_mode="Markdown")

    elif txt == '👥 Community':
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="💬 অফিসিয়াল গ্রুপে জয়েন করুন", url=COMMUNITY_LINK))
        bot.send_message(cid, "আমাদের কমিউনিটিতে জয়েন করতে নিচে ক্লিক করুন:", reply_markup=markup)
        
    else: 
        bot.send_message(cid, "দয়া করে মেনু থেকে সঠিক বাটনটি চাপুন।", reply_markup=menu())

@bot.message_handler(commands=['setbkash', 'setnagad'])
def set_payment(msg):
    u_id = str(msg.from_user.id)
    cmd = msg.text.split()
    if len(cmd) < 2:
        bot.send_message(msg.chat.id, "⚠️ ভুল ফরম্যাট! লিখুন: /setbkash 017xxxxxxxx")
        return
    val = cmd[1]
    if 'bkash' in msg.text:
        user_data[u_id]['bkash'] = val
        bot.send_message(msg.chat.id, f"✅ বিকাশ নম্বর সেট হয়েছে: {val}")
    else:
        user_data[u_id]['nagad'] = val
        bot.send_message(msg.chat.id, f"✅ নগদ নম্বর সেট হয়েছে: {val}")
    save_data(user_data)

from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    bot.infinity_polling()
