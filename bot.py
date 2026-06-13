import telebot
from telebot import types
import json
import os

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619  # আপনার আসল টেলিগ্রাম আইডি
BOT_USERNAME = 'mdalif268'

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "user_database.json"

# গলোবাল ভেরিয়াবল (অ্যাডমিন যেকোনো সময় এটি পরিবর্তন করতে পারবেন)
current_ad_link = "https://telega.in"  
current_ad_text = "📝 নিচে দেওয়া বাটনে ক্লিক করে বিজ্ঞাপনটি দেখুন এবং কয়েন আর্ন করুন!"
COMMUNITY_LINK = "https://t.me/rupacoin27bd"  # আপনার গ্রুপের লিংক

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

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

# 🎛️ কিবোর্ড মেনু (এখানে '👥 Community' বাটনটি যোগ করা হয়েছে)
def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add('🏠 Home', '📋 Task (Ads)', '💰 Wallet')
    m.add('👥 Referral', '💸 Withdraw', '👥 Community')  # নতুন বাটন এখানে যুক্ত
    return m

# 📢 ১. বটের ভেতর থেকেই বিজ্ঞাপন বা লিংক পরিবর্তন করার স্পেশাল কমান্ড
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
    bot.send_message(msg.chat.id, f"✅ বিজ্ঞাপনের লিংক সফলভাবে আপডেট হয়েছে!\n\n🔗 বর্তমান লিংক: {current_ad_link}")

# 📢 ২. বটের ভেতর থেকে বিজ্ঞাপনের লেখার বিবরণ পরিবর্তন করার কমান্ড
@bot.message_handler(commands=['settext'])
def set_ad_text(msg):
    global current_ad_text
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return
        
    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: /settext আপনার নতুন বিজ্ঞাপনের বিবরণ এখানে লিখুন")
        return
        
    current_ad_text = command_text[1]
    bot.send_message(msg.chat.id, f"✅ বিজ্ঞাপনের বিবরণ সফলভাবে আপডেট হয়েছে!\n\n📝 বর্তমান লেখা: {current_ad_text}")

# 📢 ৩. সব ইউজারের কাছে এক ক্লিকে নোটিফিকেশন বা মেসেজ পাঠানোর ব্রডকাস্ট কমান্ড
@bot.message_handler(commands=['broadcast'])
def broadcast_to_all(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return

    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: /broadcast আপনার বিজ্ঞাপনের মেসেজ এখানে লিখুন")
        return

    ad_message = command_text[1]
    bot.send_message(msg.chat.id, "⏳ বিজ্ঞাপনটি সব ইউজারের কাছে পাঠানো শুরু হচ্ছে...")

    success_count = 0
    fail_count = 0

    for u_id in user_data.keys():
        try:
            bot.send_message(int(u_id), ad_message)
            success_count += 1
        except Exception:
            fail_count += 1

    bot.send_message(msg.chat.id, f"✅ ব্রডকাস্ট সম্পন্ন হয়েছে!\n\n🚀 সফলভাবে পাঠানো হয়েছে: {success_count} জনের কাছে\n❌ ব্যর্থ হয়েছে: {fail_count} জন।")

@bot.message_handler(commands=['start'])
def start(msg):
    u_id = str(msg.from_user.id)
    command = msg.text.split()
    
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if len(command) > 1:
        referrer_id = command[1]
        if referrer_id in user_data and referrer_id != u_id:
            if 'referred_by' not in user_data[u_id]:
                user_data[referrer_id]['balance'] += 1.0
                user_data[u_id]['referred_by'] = referrer_id
                save_data(user_data)
                try:
                    bot.send_message(int(referrer_id), "🎉 অভিনন্দন! কেউ আপনার রেফারেল লিংকে জয়েন করেছে। আপনি ১.০ Rupa Coin বোনাস পেয়েছেন!")
                except:
                    pass

    bot.send_message(msg.chat.id, f"স্বাগতম {user['name']}! Rupa Coin আর্নিং বতে আপনাকে সতত স্বাগত।", reply_markup=menu())

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    global current_ad_link, current_ad_text, COMMUNITY_LINK
    txt, cid = msg.text, msg.chat.id
    u_id = str(msg.from_user.id)
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if 'Home' in txt: 
        home_text = (
            f"🏡 আপনার প্রোফাইল 🏡\n\n"
            f"👤 নাম: {user['name']}\n"
            f"🆔 আইডি: {u_id}\n"
            f"💰 মোট ব্যালেন্স: {user['balance']:.1f} Rupa Coin"
        )
        bot.send_message(cid, home_text, parse_mode="Markdown")
        
    elif 'Task' in txt: 
        user_data[u_id]['balance'] += 0.2
        save_data(user_data)
        
        markup = types.InlineKeyboardMarkup()
        ads_button = types.InlineKeyboardButton(text="🎁 বিজ্ঞাপন দেখুন (০.২ Rupa Coin)", url=current_ad_link)
        markup.add(ads_button)
        
        bot.send_message(cid, f"{current_ad_text}\n\n*(আপনার অ্যাকাউন্টে ০.২ Rupa Coin যোগ করা হয়েছে)*", reply_markup=markup, parse_mode="Markdown")
        
    elif 'Referral' in txt:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
        ref_text = (
            f"👥 রেফারেল সেন্টার 👥\n\n"
            f"আপনার রেফারেল কোড: {user['referral_code']}\n\n"
            f"বন্ধুদের ইনভাইট করতে আপনার লিংকটি শেয়ার করুন:\n{ref_link}\n\n"
            f"🎁 প্রতি রেফারে পাবেন ১.০ Rupa Coin বোনাস!"
        )
        bot.send_message(cid, ref_text, parse_mode="Markdown")
        
    elif 'Wallet' in txt: 
        wallet_text = (
            f"💰 **আপনার ওয়ালেট** 💰\n\n"
            f"💵 বর্তমান ব্যালেন্স: {user_data[u_id]['balance']:.1f} Rupa Coin\n"
            f"📱 বিকাশ নাম্বার: {user_data[u_id]['bkash_num']}\n"
            f"📱 নগদ নাম্বার: {user_data[u_id]['nagad_num']}\n\n"
            f"ℹ️ ব্যালেন্স ১০০ কয়েন হওয়ার আগেই আপনি নিচে ক্লিক করে নাম্বার সেভ করে রাখতে পারেন।"
        )
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("⚙️ সেভ/পরিবর্তন নাম্বার", callback_data="manage_nums"))
        bot.send_message(cid, wallet_text, reply_markup=markup, parse_mode="Markdown")
        
    elif 'Withdraw' in txt:
        if user_data[u_id]['balance'] < 100.0:
            bot.send_message(cid, f"❌ উইথড্র ব্যর্থ!\n\nসর্বনিম্ন ১০০ Rupa Coin প্রয়োজন। আপনার বর্তমান ব্যালেন্স: {user_data[u_id]['balance']:.1f} Rupa Coin।", parse_mode="Markdown")
        else:
            markup = types.InlineKeyboardMarkup()
            bkash = types.InlineKeyboardButton(text="বিকাশ (bKash)", callback_data=f"w_bkash")
            nagad = types.InlineKeyboardButton(text="নগদ (Nagad)", callback_data=f"w_nagad")
            markup.add(bkash, nagad)
            bot.send_message(cid, f"💸 উইথড্র মেথড সিলেক্ট করুন:", reply_markup=markup, parse_mode="Markdown")
            
    # 👥 নতুন 'Community' বাটনের লজিক
    elif 'Community' in txt:
        community_text = (
            f"👥 **Rupa Coin অফিসিয়াল কমিউনিটি** 👥\n\n"
            f"আমাদের গ্রুপে জয়েন করুন! এখানে নতুন সব আপডেট, পেমেন্ট প্রুফ এবং অন্যান্য মেম্বারদের সাথে আলোচনা করতে পারবেন।"
        )
        markup = types.InlineKeyboardMarkup()
        group_button = types.InlineKeyboardButton(text="💬 গ্রুপে জয়েন করুন", url=COMMUNITY_LINK)
        markup.add(group_button)
        bot.send_message(cid, community_text, reply_markup=markup)
        
    else: 
        bot.send_message(cid, "দয়া করে মেনু থেকে একটি বাটন চাপুন।", reply_markup=menu())

# ⚙️ নম্বর সেভ এবং উইথড্র ম্যানেজমেন্টের জন্য ইনলাইন বাটন রেসপন্স
@bot.callback_query_handler(func=lambda call: call.data.startswith('w_') or call.data in ['manage_nums', 'save_b', 'save_n'])
def withdraw_callback(call):
    u_id = str(call.from_user.id)
    
    if call.data == 'manage_nums':
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("বিকাশ (bKash)", callback_data="save_b"),
                   types.InlineKeyboardButton("নগদ (Nagad)", callback_data="save_n"))
        bot.edit_message_text("কোন নাম্বারটি সেট বা পরিবর্তন করতে চান সিলেক্ট করুন:", call.message.chat.id, call.message.message_id, reply_markup=markup)
        
    elif call.data == 'save_b':
        msg = bot.send_message(call.message.chat.id, "📱 আপনার **বিকাশ পার্সোনাল নাম্বারটি** লিখে সেন্ড করুন:")
        bot.register_next_step_handler(msg, save_number_db, "bkash")
        
    elif call.data == 'save_n':
        msg = bot.send_message(call.message.chat.id, "📱 আপনার **নগদ পার্সোনাল নাম্বারটি** লিখে সেন্ড করুন:")
        bot.register_next_step_handler(msg, save_number_db, "nagad")

    elif call.data.startswith('w_'):
        method = call.data.split('_')[1]
        db_key = 'bkash_num' if method == 'bkash' else 'nagad_num'
        
        if user_data[u_id][db_key] != 'Not Set':
            num = user_data[u_id][db_key]
            m = bot.send_message(call.message.chat.id, f"💵 কত Rupa Coin উইথড্র করতে চান লিখুন (আপনার ব্যালেন্স: {user_data[u_id]['balance']:.1f}):")
            bot.register_next_step_handler(m, process_amount, method, num)
        else:
            msg = bot.send_message(call.message.chat.id, f"📱 আপনার {method.upper()} নাম্বারটি লিখুন:")
            bot.register_next_step_handler(msg, process_number, method)

def save_number_db(msg, method):
    num = msg.text
    u_id = str(msg.from_user.id)
    
    if not num.isdigit() or len(num) < 11:
        bot.send_message(msg.chat.id, "❌ ভুল নাম্বার! শুধুমাত্র ১১ ডিজিটের সঠিক নাম্বারটি দিন।")
        return
        
    if method == "bkash":
        user_data[u_id]['bkash_num'] = num
    else:
        user_data[u_id]['nagad_num'] = num
        
    save_data(user_data)
    bot.send_message(msg.chat.id, f"✅ আপনার {method.upper()} নাম্বারটি সফলভাবে প্রোফাইলে সেভ করা হয়েছে!")

def process_number(msg, method):
    num = msg.text
    u_id = str(msg.from_user.id)
    
    if not num.isdigit() or len(num) < 11:
        bot.send_message(msg.chat.id, "❌ ভুল নাম্বার! আবার Withdraw বাটনে ক্লিক করে সঠিক নাম্বার দিন।")
        return
    
    if method == "bkash":
        user_data[u_id]['bkash_num'] = num
    else:
        user_data[u_id]['nagad_num'] = num
    save_data(user_data)
        
    m = bot.send_message(msg.chat.id, f"💵 কত Rupa Coin উইথড্র করতে চান লিখুন (আপনার ব্যালেন্স: {user_data[u_id]['balance']:.1f}):")
    bot.register_next_step_handler(m, process_amount, method, num)

def process_amount(msg, method, num):
    u_id = str(msg.from_user.id)
    amount_text = msg.text
    
    try:
        amount = float(amount_text)
    except ValueError:
        bot.send_message(msg.chat.id, "❌ ভুল অ্যামাউন্ট! শুধুমাত্র সংখ্যা লিখুন। আবার চেষ্টা করুন।")
        return
        
    if amount < 100.0:
        bot.send_message(msg.chat.id, "❌ সর্বনিম্ন উইথড্র ১০০ Rupa Coin!")
        return
        
    if user_data[u_id]['balance'] < amount:
        bot.send_message(msg.chat.id, f"❌ আপনার পর্যাপ্ত ব্যালেন্স নেই! বর্তমান ব্যালেন্স: {user_data[u_id]['balance']:.1f}")
        return
        
    user_data[u_id]['balance'] -= amount
    save_data(user_data)
    
    admin_msg = (
        f"🚨 **নতুন উইথড্র রিকোয়েস্ট!** 🚨\n\n"
        f"👤 নাম: {msg.from_user.first_name}\n"
        f"🆔 ইউজার আইডি: `{u_id}`\n"
        f"💵 মেথড: {method.upper()}\n"
        f"📱 নাম্বার: `{num}`\n"
        f"💰 পরিমাণ: {amount} Rupa Coin"
    )
    
    try:
        bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
        bot.send_message(msg.chat.id, f"✅ আপনার উইথড্র রিকোয়েস্ট সফলভাবে অ্যাডমিনের কাছে পাঠানো হয়েছে!\n\n📱 মেথড: {method.upper()}\n📱 নাম্বার: {num}\n💰 পরিমাণ: {amount} Rupa Coin\n\nঅ্যাডমিন চেক করে খুব দ্রুত আপনার নাম্বারে টাকা পাঠিয়ে দেবেন।")
    except Exception:
        bot.send_message(msg.chat.id, f"❌ সাময়িক ত্রুটি! অনুগ্রহ করে সরাসরি অ্যাডমিনের সাথে যোগাযোগ করুন।")


# ==========================================
# RENDER SERVER & THREADING INTEGRATION (রেন্ডার ফিক্স কোড)
# ==========================================

print("Rupa Coin মাস্টার কন্ট্রোল ও উইথড্র সিস্টেম সহ বট সফলভাবে চালু হয়েছে।")

from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return "Bot is running!"

if __name__ == "__main__":
    # Render-এর পোর্ট হ্যান্ডেল করার জন্য Flask চালু করা
    port = int(os.environ.get("PORT", 5000))
    
    # ব্যাকগ্রাউন্ডে ফ্ল্যাস্ক রান হবে যেন রেন্ডার টাইম আউট না দেয়
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False)).start()
    
    # আপনার বটের মেইন পোলিং রান হবে এখানে
    bot.infinity_polling()
