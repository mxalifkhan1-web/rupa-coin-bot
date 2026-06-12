import telebot
from telebot import types

TOKEN = '8895342557:AAF08qNX-3yWm2vZyXp3K2fA7-Yrul6D1hw'
bot = telebot.TeleBot(TOKEN)

# ডেটাবেস: ইউজারদের তথ্য জমা রাখার জন্য
user_data = {}

def get_or_create_user(user_id, first_name):
    if user_id not in user_data:
        user_data[user_id] = {
            'name': first_name,
            'balance': 0.0,
            'referral_code': f"RUPA{user_id}"
        }
    return user_data[user_id]

def menu():
    m = types.ReplyKeyboardMarkup(resize_keyboard=True)
    m.add('🏠 Home', '📋 Task (Ads)', '💰 Wallet', '👥 Referral', '💸 Withdraw')
    return m

@bot.message_handler(commands=['start'])
def start(msg):
    command = msg.text.split()
    if len(command) > 1:
        referrer_id = int(command[1])
        if referrer_id in user_data and referrer_id != msg.from_user.id:
            # রেফার বোনাস হিসেবে ১ Rupa Coin দেওয়া হচ্ছে
            user_data[referrer_id]['balance'] += 1.0 
            bot.send_message(referrer_id, "🎉 অভিনন্দন! কেউ আপনার রেফারেল লিংকে জয়েন করেছে। আপনি ১.০ Rupa Coin বোনাস পেয়েছেন!")

    user = get_or_create_user(msg.from_user.id, msg.from_user.first_name)
    bot.send_message(msg.chat.id, f"স্বাগতম {user['name']}! Rupa Coin আর্নিং বতে আপনাকে স্বাগতম।", reply_markup=menu())

@bot.message_handler(func=lambda msg: True)
def reply(msg):
    txt, cid = msg.text, msg.chat.id
    user_id = msg.from_user.id
    user = get_or_create_user(user_id, msg.from_user.first_name)
    
    if 'Home' in txt: 
        home_text = (
            f"🏡 **আপনার প্রোফাইল** 🏡\n\n"
            f"👤 নাম: {user['name']}\n"
            f"🆔 আইডি: `{user_id}`\n"
            f"💰 মোট ব্যালেন্স: {user['balance']:.1f} Rupa Coin"
        )
        bot.send_message(cid, home_text, parse_mode="Markdown")
        
    elif 'Task' in txt: 
        # প্রতি অ্যাড ক্লিকে ০.২ Rupa Coin যোগ হবে
        user['balance'] += 0.2
        
        markup = types.InlineKeyboardMarkup()
        # এখানে আপনার আসল অ্যাডের লিংকটি বসাবেন
        ad_button = types.InlineKeyboardButton(text="🔗 বিজ্ঞাপন দেখুন (০.২ Rupa Coin)", url="https://www.google.com")
        markup.add(ad_button)
        
        bot.send_message(cid, "📝 **টাস্ক:** নিচের লিংকে ক্লিক করে বিজ্ঞাপনটি সম্পূর্ণ দেখুন।\n🎁 আপনার অ্যাকাউন্টে **০.২ Rupa Coin** যোগ করা হয়েছে!", reply_markup=markup, parse_mode="Markdown")
        
    elif 'Referral' in txt:
        ref_link = f"https://t.me/{(bot.get_me()).username}?start={user_id}"
        ref_text = (
            f"👥 **রেফারেল সেন্টার** 👥\n\n"
            f"আপনার রেফারেল কোড: `{user['referral_code']}`\n\n"
            f"বন্ধুদের ইনভাইট করতে আপনার লিংকটি শেয়ার করুন:\n{ref_link}\n\n"
            f"🎁 প্রতি রেফারে পাবেন **১.০ Rupa Coin** বোনাস!"
        )
        bot.send_message(cid, ref_text, parse_mode="Markdown")
        
    elif 'Wallet' in txt: 
        bot.send_message(cid, f"💰 **আপনার ওয়ালেট** 💰\n\n💵 বর্তমান ব্যালেন্স: {user['balance']:.1f} Rupa Coin", parse_mode="Markdown")
        
    elif 'Withdraw' in txt:
        if user['balance'] < 100.0:
            bot.send_message(cid, f"❌ **উইথড্র ব্যর্থ!**\n\nসর্বনিম্ন ১০০ Rupa Coin প্রয়োজন। আপনার বর্তমান ব্যালেন্স: {user['balance']:.1f} Rupa Coin। আরও কাজ করুন!", parse_mode="Markdown")
        else:
            markup = types.InlineKeyboardMarkup()
            bkash = types.InlineKeyboardButton(text="বিকাশ (bKash)", callback_data="w_bkash")
            nagad = types.InlineKeyboardButton(text="নগদ (Nagad)", callback_data="w_nagad")
            markup.add(bkash, nagad)
            bot.send_message(cid, f"💸 **উইথড্র মেথড সিলেক্ট করুন:**\n(আপনার ব্যালেন্স: {user['balance']:.1f} Rupa Coin)", reply_markup=markup, parse_mode="Markdown")
    else: 
        bot.send_message(cid, "দয়া করে মেনু থেকে একটি বাটন চাপুন।", reply_markup=menu())

@bot.callback_query_handler(func=lambda call: call.data.startswith('w_'))
def withdraw_callback(call):
    user_id = call.from_user.id
    user = user_data.get(user_id, {'balance': 0})
    
    if call.data == "w_bkash":
        bot.send_message(call.message.chat.id, f"✅ আপনার বিকাশ নাম্বার এবং কত Rupa Coin উইথড্র করতে চান তা অ্যাডমিনকে জানান।")
    elif call.data == "w_nagad":
        bot.send_message(call.message.chat.id, f"✅ আপনার নগদ নাম্বার এবং কত Rupa Coin উইথড্র করতে চান তা অ্যাডমিনকে জানান।")

print("Rupa Coin আর্নিং বট সফলভাবে চালু হয়েছে...")
bot.infinity_polling()
