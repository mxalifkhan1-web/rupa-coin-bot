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
current_ad_text = "📝 নিচে দেওয়া বাটনে ক্লিক করে বিজ্ঞাপনটি দেখুন এবং কয়েন আর্ন করুন!"
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

# ইমোজি ও বাংলা ফিক্স করার জন্য এনকোডিং যোগ করা হয়েছে
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
        user_data[u_id] = {
            'name': first_name,
            'balance': 0.0,
            'referral_code': f"RUPA{user_id}",
            'bkash_num': 'Not Set',  
            'nagad_num': 'Not Set'   
        }
    if 'bkash_num' not in user_data[u_id]:
        user_data[u_id]['bkash_num'] = 'Not Set'
    if 'nagad_num' not in user_data[u_id]:
        user_data[u_id]['nagad_num'] = 'Not Set'
    save_data(user_data)
    return user_data[u_id]

def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add('🏠 Home', '📋 Task (Ads)', '💰 Wallet')
    m.add('👥 Referral', '💸 Withdraw', '👥 Community')
    return m

@bot.message_handler(commands=['setlink'])
def set_ad_link(msg):
    global current_ad_link
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return
    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: /setlink https://নতুন-অ্যাড-লিংক.com")
        return
    current_ad_link = command_text[1].strip()
    bot.send_message(msg.chat.id, f"✅ বিজ্ঞাপনের লিংক সফলভাবে আপডেট হয়েছে!")

@bot.message_handler(commands=['settext'])
def set_ad_text(msg):
    global current_ad_text
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return
    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: /settext আপনার নতুন বিজ্ঞাপনের বিবরণ")
        return
    current_ad_text = command_text[1]
    bot.send_message(msg.chat.id, f"✅ বিজ্ঞাপনের বিবরণ সফলভাবে আপডেট হয়েছে!")

@bot.message_handler(commands=['broadcast'])
def broadcast_to_all(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return
    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: /broadcast আপনার মেসেজ")
        return
    ad_message = command_text[1]
    for u_id in user_data.keys():
        try: bot.send_message(int(u_id), ad_message)
        except: pass
    bot.send_message(msg.chat.id, "✅ ব্রডকাস্ট সম্পন্ন হয়েছে!")

@bot.message_handler(commands=['start'])
def start(msg):
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, f"স্বাগতম {user['name']}! Rupa Coin আর্নিং বতে আপনাকে স্বাগতম।", reply_markup=menu())

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    global current_ad_link, current_ad_text
    txt, cid = msg.text, msg.chat.id
    u_id = str(msg.from_user.id)
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if 'Home' in txt: 
        bot.send_message(cid, f"🏡 প্রোফাইল:\n👤 নাম: {user['name']}\n💰 ব্যালেন্স: {user['balance']:.1f} Rupa Coin")
    elif 'Task' in txt: 
        user_data[u_id]['balance'] += 0.2
        save_data(user_data)
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="🎁 বিজ্ঞাপন দেখুন", url=current_ad_link))
        bot.send_message(cid, f"{current_ad_text}\n\n*(০.২ কয়েন যোগ হয়েছে)*", reply_markup=markup)
    elif 'Wallet' in txt: 
        bot.send_message(cid, f"💰 ব্যালেন্স: {user_data[u_id]['balance']:.1f}\n📱 বিকাশ: {user_data[u_id]['bkash_num']}\n📱 নগদ: {user_data[u_id]['nagad_num']}")
    elif 'Community' in txt:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text="💬 গ্রুপে জয়েন করুন", url=COMMUNITY_LINK))
        bot.send_message(cid, "আমাদের অফিসিয়াল কমিউনিটি:", reply_markup=markup)
    else: 
        bot.send_message(cid, "দয়া করে মেনু থেকে বাটন চাপুন।", reply_markup=menu())

# --- রেন্ডার সার্ভার ---
print("Bot running...")
from flask import Flask
import threading
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()
    bot.infinity_polling()
