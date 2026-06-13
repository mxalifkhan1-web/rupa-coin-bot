import telebot
from telebot import types
import json
import os

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
ADMIN_ID = 7817231619  # আপনার আসল টেলিগ্রাম আইডি নম্বর এখানে সেট করা আছে
BOT_USERNAME = 'mdalif268'

bot = telebot.TeleBot(TOKEN)
DATA_FILE = "user_database.json"

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
            'referral_code': f"RUPA{user_id}"
        }
        save_data(user_data)
    return user_data[u_id]

def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add('🏠 Home', '📋 Task (Ads)', '💰 Wallet', '👥 Referral', '💸 Withdraw')
    return m

# 📢 অ্যাডমিন ব্রডকাস্ট কমান্ড
@bot.message_handler(commands=['broadcast'])
def broadcast_to_all(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ আপনি এই বটের অ্যাডমিন নন!")
        return

    command_text = msg.text.split(maxsplit=1)
    if len(command_text) < 2:
        bot.send_message(msg.chat.id, "⚠️ ব্যবহারের নিয়ম: `/broadcast আপনার বিজ্ঞাপনের মেসেজ এখানে লিখুন`")
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
    txt, cid = msg.text, msg.chat.id
    u_id = str(msg.from_user.id)
    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    
    if 'Home' in txt: 
        home_text = (
            f"🏡 **আপনার প্রোফাইল** 🏡\n\n"
            f"👤 নাম: {user['name']}\n"
            f"🆔 আইডি: `{u_id}`\n"
            f"💰 মোট ব্যালেন্স: {user['balance']:.1f} Rupa Coin"
        )
        bot.send_message(cid, home_text, parse_mode="Markdown")
        
    elif 'Task' in txt: 
        user_data[u_id]['balance'] += 0.2
        save_data(user_data)
        
        markup = types.InlineKeyboardMarkup()
        ads_link = "https://telega.in/your-campaign-url-here" 
        ads_button = types.InlineKeyboardButton(text="🎁 বিজ্ঞাপন দেখুন (০.২ Rupa Coin)", url=ads_link)
        markup.add(ads_button)
        
        bot.send_message(cid, "📝 **টাস্ক:** নিচে দেওয়া বাটনে ক্লিক করে বিজ্ঞাপনটি দেখুন এবং কয়েন আর্ন করুন!\n\n*(আপনার অ্যাকাউন্টে ০.২ Rupa Coin যোগ করা হয়েছে)*", reply_markup=markup, parse_mode="Markdown")
        
    elif 'Referral' in txt:
        ref_link = f"https://t.me/{BOT_USERNAME}?start={u_id}"
        ref_text = (
            f"👥 **রেফারেল সেন্টার** 👥\n\n"
            f"আপনার রেফারেল কোড: `{user['referral_code']}`\n\n"
            f"বন্ধুদের ইনভাইট করতে আপনার লিংকটি শেয়ার করুন:\n{ref_link}\n\n"
            f"🎁 প্রতি রেফারে পাবেন **১.০ Rupa Coin** বোনাস!"
        )
        bot.send_message(cid, ref_text, parse_mode="Markdown")
        
    elif 'Wallet' in txt: 
        bot.send_message(cid, f"💰 **আপনার ওয়ালেট** 💰\n\n💵 বর্তমান ব্যালেন্স: {user_data[u_id]['balance']:.1f} Rupa Coin", parse_mode="Markdown")
        
    elif 'Withdraw' in txt:
        if user_data[u_id]['balance'] < 100.0:
            bot.send_message(cid, f"❌ **উইথড্র ব্যর্থ!**\n\nসর্বনিম্ন ১০০ Rupa Coin প্রয়োজন। আপনার বর্তমান ব্যালেন্স: {user_data[u_id]['balance']:.1f} Rupa Coin।", parse_mode="Markdown")
        else:
            markup = types.InlineKeyboardMarkup()
            bkash = types.InlineKeyboardButton(text="বিকাশ (bKash)", callback_data=f"w_bkash")
            nagad = types.InlineKeyboardButton(text="নগদ (Nagad)", callback_data=f"w_nagad")
            markup.add(bkash, nagad)
            bot.send_message(cid, f"💸 **উইথড্র মেথড সিলেক্ট করুন:**", reply_markup=markup, parse_mode="Markdown")
    else: 
        bot.send_message(cid, "দয়া করে মেনু থেকে একটি বাটন চাপুন।", reply_markup=menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('w_'))
def withdraw_callback(call):
    method = call.data.split('_')[1]
    msg = bot.send_message(call.message.chat.id, f"📱 আপনার **{method.upper()}** নাম্বারটি লিখুন:")
    bot.register_next_step_handler(msg, process_number, method)

def process_number(msg, method):
    num = msg.text
    u_id = str(msg.from_user.id)
    
    if not num.isdigit() or len(num) < 11:
        bot.send_message(msg.chat.id, "❌ ভুল নাম্বার! আবার Withdraw বাটনে ক্লিক করে সঠিক নাম্বার দিন।")
        return
        
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

print("Rupa Coin উইথড্র সিস্টেম সহ বট সফলভাবে চালু হয়েছে...")
bot.infinity_polling()
