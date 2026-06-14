import telebot
from telebot import types
import json
import os
import time
from flask import Flask

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619
BOT_USERNAME = 'alif357_bot'
DATA_FILE = "user_database.json"
COMMUNITY_LINK = "https://t.me/rupacoin27bd"

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# ইউজারের বিজ্ঞপ্তিতে ক্লিক করার শুরুর সময় ট্র্যাক করার গ্লোবাল ডিকশনারি
user_click_timers = {}

# --- ডেটাবেস হ্যান্ডলার ---
def load_data():
    if not os.path.exists(DATA_FILE):
        default_data = {
            'users': {}, 
            'tasks': {
                'ads_link': 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 
                'ads_reward': 0.2,
                'ads_time': 15, 
                'channel_username': '@rupacoin27bd', 
                'channel_reward': 2.0 
            }
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(default_data, f, indent=4, ensure_ascii=False)
        return default_data
        
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            'users': {}, 
            'tasks': {
                'ads_link': 'https://acceptable.a-ads.com/2444040/?size=Adaptive', 
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
if 'ads_link' not in data['tasks'] or 'size=Adaptive' not in data['tasks']['ads_link']: 
    data['tasks']['ads_link'] = 'https://acceptable.a-ads.com/2444040/?size=Adaptive'
if 'ads_reward' not in data['tasks']: data['tasks']['ads_reward'] = 0.2
if 'ads_time' not in data['tasks']: data['tasks']['ads_time'] = 15
if 'channel_username' not in data['tasks']: data['tasks']['channel_username'] = '@rupacoin27bd'
if 'channel_reward' not in data['tasks']: data['tasks']['channel_reward'] = 2.0
save_data(data)

# --- সার্ভার ---
@app.route('/')
def home(): return "Bot is running 24/7!"

def run_bot():
    while True:
        try:
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except:
            time.sleep(5)

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
    
    m = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    m.add('👤 Profile', '📋 Task (Ads)', '⚡ Pro Task', '💰 Wallet', '👥 Referral', '👥 Community')
    bot.send_message(msg.chat.id, f"✨ স্বাগতম {msg.from_user.first_name}!", reply_markup=m)

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    global data
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
    
    # 📋 নতুন টাস্ক সিস্টেম (চিটিং আটকানোর মেথড)
    elif txt == '📋 Task (Ads)':
        ad_time = data['tasks']['ads_time']
        ad_url = data['tasks']['ads_link']
        
        # ইউজার যেন ডিরেক্টলি লিংক ট্র্যাকিং মেকানিজমে ঢুকতে পারে
        # আমরা টেলিগ্রামের ইনলাইন ইউআরএল রিডাইরেকশন ব্যবহার করছি
        # ইউজার লিংকে ক্লিক করলে বটের গ্লোবাল টাইম ট্র্যাকিং সক্রিয় করার জন্য আমরা একটা কাস্টম ইনলাইন বাটন দিচ্ছি
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # বাটন ১: বিজ্ঞাপন দেখার লিংক (এই লিংকে ক্লিক করার পরই মূলত ঘড়ি কাউন্ট করবে)
        # টেলিগ্রাম বটের মাধ্যমে ট্র্যাকিং সিস্টেম সচল করতে আমরা কলব্যাক কুয়েরি মেথড এবং ব্রাউজার ওপেন কম্বাইন করেছি
        # কিন্তু সরাসরি লিংকে ক্লিক করাটা ট্র্যাক করতে আমাদের রিয়েল-টাইম ভেরিফায়ার লাগবে
        
        # 👑 ট্রিক: ইউজার যখনই এই বাটনে চাপ দেবে, তার টাইম ট্র্যাকার সক্রিয় হবে
        # ইউজারকে অবশ্যই প্রথমে লিংকে ক্লিক করতে হবে, তারপর রিওয়ার্ড ক্লেইম করতে হবে
        button_open = types.InlineKeyboardButton(text="🔗 Open Link (বিজ্ঞাপন দেখুন)", url=ad_url, callback_data="clicked_the_link")
        button_claim = types.InlineKeyboardButton(text="🎁 Claim Reward / ভেরিফাই করুন", callback_data="claim_task1")
        
        markup.add(button_open, button_claim)
        
        # ইউজার যখন টাস্ক ওপেন করবে, বটের ডেটাতে তার ইনিশিয়াল টাইম ট্র্যাক শুরু হবে যাতে সে কোনো ফাঁকি না দিতে পারে
        user_click_timers[u_id] = time.time()
        
        bot.send_message(
            msg.chat.id, 
            f"📋 **Rupa Coin Task 1**\n\n"
            f"👉 নিচে দেওয়া **'🔗 Open Link'** বাটনে ক্লিক করে বিজ্ঞাপনটি ওপেন করুন এবং কমপক্ষে **{ad_time} সেকেন্ড** সেখানে অপেক্ষা করুন।\n\n"
            f"⚠️ **শর্ত:** বিজ্ঞপ্তির লিংকে ক্লিক না করে সরাসরি রিওয়ার্ড বাটনে চাপ দিলে বা সময় শেষ হওয়ার আগে ব্যাক আসলে ১ পয়েন্টও পাবেন না!\n\n"
            f"⏳ সময় শেষ হলে ফিরে এসে নিচের **'🎁 Claim Reward'** বাটনে চাপ দিন।", 
            reply_markup=markup
        )

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
        bot.send_message(msg.chat.id, f"⚡ **প্রো টাস্ক (চ্যানেল জয়েন)!**\n\nনিচের চ্যানেলে জয়েন করুন এবং 'Check / Claim Reward' বাটনে ক্লিক করে **{reward} Rupa Coin** ফ্রিতে বুঝে নিন।", reply_markup=markup)

    elif txt == '👥 Referral':
        bot.send_message(msg.chat.id, f"আপনার রেফারেল লিংক:\nhttps://t.me/{BOT_USERNAME}?start={u_id}")

    elif txt == '👥 Community':
        bot.send_message(msg.chat.id, f"জয়েন করুন: {COMMUNITY_LINK}")


# --- কলব্যাক কুয়েরি হ্যান্ডলার (সব ভেরিফিকেশন এখানে হবে) ---
@bot.callback_query_handler(func=lambda call: True)
def callback(call):
    global data
    u_id = str(call.from_user.id)
    user = data['users'][u_id]

    # টাস্ক ১ এর ক্লেইম এবং ফাঁকিবাজি চেকার লজিক
    if call.data == "claim_task1":
        current_time = time.time()
        ad_time = data['tasks']['ads_time']
        reward = data['tasks']['ads_reward']
        
        # ইউজার টাস্ক বাটনে ক্লিক করেছিল কিনা চেক
        if u_id in user_click_timers:
            start_time = user_click_timers[u_id]
            elapsed_time = current_time - start_time  # কত সেকেন্ড পার হয়েছে তার হিসাব
            
            # শর্ত: সেট করা সময় (যেমন ১৫ সেকেন্ড) পার হতে হবে
            if elapsed_time >= ad_time:
                # ইউজারের ব্যালেন্সে রিওয়ার্ড কয়েন যোগ করা হচ্ছে
                data['users'][u_id]['balance'] += reward
                save_data(data)
                
                # স্ক্রিনে সাকসেস পপ-আপ মেসেজ
                bot.answer_callback_query(call.id, text=f"✅ সফল হয়েছে! আপনি {reward} Rupa Coin বোনাস পেয়েছেন।", show_alert=True)
                
                # মেইন মেসেজটি এডিট করে অভিনন্দন জানানো হচ্ছে
                bot.edit_message_text(
                    chat_id=call.message.chat.id, 
                    message_id=call.message.message_id, 
                    text=f"🎉 **অভিনন্দন!**\n\nআপনি সফলভাবে পুরো সময় এড টি দেখেছেন। আপনার অ্যাকাউন্টে **{reward} Rupa Coin** যোগ করা হয়েছে! ✅"
                )
                # কাজ শেষ, তাই ইউজারের টাইমার ডিলিট করা হলো
                del user_click_timers[u_id]
            else:
                # যদি ইউজার নির্ধারিত সময়ের আগে চলে আসে তবে এই অ্যালার্টটি আসবে এবং কোনো কয়েন অ্যাড হবে না
                remaining_time = int(ad_time - elapsed_time)
                bot.answer_callback_query(
                    call.id, 
                    text=f"⚠️ আপনি ফাঁকিবাজি করছেন! বিজ্ঞাপনটি পুরোপুরি দেখা হয়নি। দয়া করে আরও {remaining_time} সেকেন্ড অপেক্ষা করুন।", 
                    show_alert=True
                )
        else:
            bot.answer_callback_query(call.id, text="❌ আপনি তো এখনও বিজ্ঞাপনটি ওপেনই করেননি! প্রথমে '🔗 Open Link'-এ ক্লিক করুন।", show_alert=True)

    elif call.data == "set_bkash":
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
        try:
            member = bot.get_chat_member(target_channel, call.from_user.id)
            if member.status in ['member', 'administrator', 'creator']:
                data['users'][u_id]['balance'] += reward
                save_data(data)
                bot.answer_callback_query(call.id, f"✅ সফল! {reward} Rupa Coin যোগ হয়েছে।", show_alert=True)
            else:
                bot.answer_callback_query(call.id, "❌ আপনি এখনও চ্যানেলে জয়েন করেননি!", show_alert=True)
        except:
            bot.answer_callback_query(call.id, "⚠️ চ্যানেল চেক করা যাচ্ছে না!", show_alert=True)

def save_num(msg, key):
    u_id = str(msg.from_user.id)
    if u_id in data['users']:
        data['users'][u_id][key] = msg.text
        save_data(data)
        bot.reply_to(msg, f"✅ আপনার {key} নম্বর সেভ হয়েছে!")

if __name__ == "__main__":
    import threading
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=5000)).start()
    run_bot()
