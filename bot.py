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
    return {
        'users': {}, 
        'tasks': {
            'ads_link': 'https://telega.in', 
            'ads_reward': 0.2,
            'ads_time': 15, 
            'channel_username': '@rupacoin27bd', 
            'channel_reward': 2.0 
        }
    }

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

data = load_data()

# ডাটাবেস সেফটি চেক
if 'ads_link' not in data['tasks']: data['tasks']['ads_link'] = 'https://telega.in'
if 'ads_reward' not in data['tasks']: data['tasks']['ads_reward'] = 0.2
if 'ads_time' not in data['tasks']: data['tasks']['ads_time'] = 15
if 'channel_username' not in data['tasks']: data['tasks']['channel_username'] = '@rupacoin27bd'
if 'channel_reward' not in data['tasks']: data['tasks']['channel_reward'] = 2.0

# --- বট রানার ---
def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except:
            time.sleep(5)

@app.route('/')
def home(): return "Bot is running 24/7!"

# --- বট লজিক ---
@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    if u_id not in data['users']:
        data['users'][u_id] = {
            'name': msg.from_user.first_name, 
            'balance': 0.0, 
            'bkash': 'Not Set', 
            'nagad': 'Not Set',
            'joined_channels': [],
            'last_ad_click': 0 
        }
        save_data(data)
    
    if 'joined_channels' not in data['users'][u_id]:
        data['users'][u_id]['joined_channels'] = []
        save_data(data)
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '👥 Community')
    bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    u_id = str(msg.from_user.id)
    
    # --- অ্যাডমিন কমান্ডস ---
    if u_id == str(ADMIN_ID):
        if msg.text.startswith('/setlink'):
            parts = msg.text.split()
            if len(parts) == 4:
                data['tasks']['ads_link'] = parts[1]
                data['tasks']['ads_time'] = int(parts[2])
                data['tasks']['ads_reward'] = float(parts[3])
                save_data(data)
                bot.reply_to(msg, f"✅ টাস্ক অ্যাড আপডেট হয়েছে!\nলিংক: {parts[1]}\nসময়: {parts[2]} সেকেন্ড\nপয়েন্ট: {parts[3]}")
            return
        
        elif msg.text.startswith('/setpro'):
            parts = msg.text.split()
            if len(parts) == 3:
                data['tasks']['channel_username'] = parts[1]
                data['tasks']['channel_reward'] = float(parts[2])
                save_data(data)
                bot.reply_to(msg, f"⚡ প্রো টাস্ক চ্যানেল সেট হয়েছে!\nচ্যানেল: {parts[1]}\nপয়েন্ট: {parts[2]}")
            return

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
    
    # টেলিগ্রাম অ্যাপের ভেতরে অ্যাড দেখা এবং রিয়েল-টাইম লাইভ কাউন্টডাউন টাইমার
    elif txt == '📋 Task (Ads)':
        ad_time = data['tasks']['ads_time']
        reward = data['tasks']['ads_reward']
        ad_url = data['tasks']['ads_link']
        
        markup = types.InlineKeyboardMarkup()
        # WebApp ব্যবহার করায় ওয়েবসাইটটি আলাদা ব্রাউজারে না গিয়ে টেলিগ্রামের ভেতরেই পপ-আপ আকারে খুলবে
        markup.add(types.InlineKeyboardButton("👁️ এড টি দেখুন", web_app=types.WebAppInfo(url=ad_url)))
        
        sent_msg = bot.send_message(msg.chat.id, f"📋 **টাস্ক অ্যাড!**\n\n👉 **এড টি দেখুন**\n\n⚠️ নিচের বাটনে চাপ দিয়ে অ্যাডটি ওপেন করুন এবং টেলিগ্রামের ভেতরেই অপেক্ষা করুন।\n\n⏳ **সময় বাকি: {ad_time} সেকেন্ড**", reply_markup=markup)
        
        # ব্যাকগ্রাউন্ডে টাইমার থ্রেড চালানো (মেসেজ লাইভ এডিট হয়ে সময় কমবে)
        threading.Thread(target=countdown_timer, args=(msg.chat.id, sent_msg.message_id, ad_time, reward, u_id, ad_url)).start()

    elif txt == '⚡ Pro Task':
        target_channel = data['tasks']['channel_username']
        reward = data['tasks']['channel_reward']
        
        if target_channel in user.get('joined_channels', []):
            bot.send_message(msg.chat.id, "⚠️ আপনি ইতিমধ্যে এই প্রো টাস্কটি সম্পূর্ণ করেছেন!")
            return
            
        clean_username = target_channel.replace("@", "")
        channel_url = f"https://t.me/{clean_username}"
        
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("📢 চ্যানেলে জয়েন করুন", url=channel_url))
        markup.add(types.InlineKeyboardButton("✅ Check / Claim Reward", callback_data="check_pro_join"))
        
        bot.send_message(msg.chat.id, f"⚡ **প্রো টাস্ক (চ্যানেল জয়েন)!**\n\nনিচের চ্যানেলে জয়েন করুন এবং 'Check / Claim Reward' বাটনে ক্লিক করে **{reward} Rupa Coin** ফ্রিতে বুঝে নিন।\n\n⚠️ জয়েন না করলে কোনো কয়েন পাবেন না!", reply_markup=markup)

    elif txt == '👥 Referral':
        bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")

    elif txt == '👥 Community':
        bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")

# লাইভ টাইমার কাউন্টডাউন ফাংশন
def countdown_timer(chat_id, message_id, remaining_time, reward, u_id, ad_url):
    while remaining_time > 0:
        time.sleep(1)
        remaining_time -= 1
        try:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("👁️ এড টি দেখুন", web_app=types.WebAppInfo(url=ad_url)))
            
            # প্রতি সেকেন্ডে মেসেজ আপডেট করে টাইমার কমানো হবে
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"📋 **টাস্ক অ্যাড!**\n\n👉 **এড টি দেখুন**\n\n⚠️ নিচের বাটনে চাপ দিয়ে অ্যাডটি ওপেন করুন এবং টেলিগ্রামের ভেতরেই অপেক্ষা করুন।\n\n⏳ **সময় বাকি: {remaining_time} সেকেন্ড**",
                reply_markup=markup
            )
        except:
            # ইউজার চ্যাট ডিলিট বা ক্লিয়ার করলে এরর এড়ানোর জন্য
            return
            
    # সময় শেষ হলে অটোমেটিক কয়েন যোগ হয়ে মেসেজ বদলে যাবে
    try:
        global data
        data['users'][u_id]['balance'] += reward
        save_data(data)
        
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=f"🎉 **অভিনন্দন!**\n\nআপনি সফলভাবে পুরো সময় এড টি দেখেছেন। আপনার অ্যাকাউন্টে **{reward} Rupa Coin** যোগ করা হয়েছে! ✅"
        )
    except:
        pass

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
            withdraw_msg = (
                f"🚨 **নতুন উইথড্র রিকোয়েস্ট!**\n\n"
                f"👤 ইউজার: {user['name']}\n"
                f"🆔 আইডি: {u_id}\n"
                f"📱 বিকাশ নম্বর: {user['bkash']}\n"
                f"📱 নগদ নম্বর: {user['nagad']}\n"
                f"💰 পরিমাণ: {user['balance']} Rupa Coin"
            )
            bot.send_message(ADMIN_ID, withdraw_msg, parse_mode="Markdown")
            
            user['balance'] = 0.0
            save_data(data)
            bot.answer_callback_query(call.id, "✅ উইথড্র রিকোয়েস্ট সফল!")
            bot.edit_message_text("✅ রিকোয়েস্ট অ্যাডমিনের কাছে পাঠানো হয়েছে।", call.message.chat.id, call.message.message_id)
        else:
            bot.answer_callback_query(call.id, f"⚠️ ৩০০ পয়েন্ট প্রয়োজন! আপনার আছে: {user['balance']}")

    elif call.data == "check_pro_join":
        target_channel = data['tasks']['channel_username']
        reward = data['tasks']['channel_reward']
        
        if target_channel in user.get('joined_channels', []):
            bot.answer_callback_query(call.id, "⚠️ ইতিমধ্যে ক্লেইম করেছেন!", show_alert=True)
            return
            
        try:
            member = bot.get_chat_member(target_channel, call.from_user.id)
            if member.status in ['member', 'administrator', 'creator']:
                data['users'][u_id]['balance'] += reward
                if 'joined_channels' not in data['users'][u_id]:
                    data['users'][u_id]['joined_channels'] = []
                data['users'][u_id]['joined_channels'].append(target_channel)
                save_data(data)
                
                bot.answer_callback_query(call.id, f"✅ সফল! {reward} Rupa Coin যোগ হয়েছে।", show_alert=True)
                bot.edit_message_text(f"🎉 অভিনন্দন! আপনি সফলভাবে হয়েছেন এবং {reward} Rupa Coin জিতে নিয়েছেন।", call.message.chat.id, call.message.message_id)
            else:
                bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেলে জয়েন করেননি! আগে জয়েন করুন তবেই কয়েন পাবেন।", show_alert=True)
        except Exception as e:
            bot.answer_callback_query(call.id, "⚠️ বটটি ওই চ্যানেলে অ্যাডমিন নেই! অ্যাডমিনকে জানান।", show_alert=True)

def save_num(msg, key):
    u_id = str(msg.from_user.id)
    if u_id in data['users']:
        data['users'][u_id][key] = msg.text
        save_data(data)
        bot.reply_to(msg, f"✅ আপনার {key} নম্বর সেভ হয়েছে!")

if __name__ == "__main__":
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    run_bot()
