import logging
import random
import sqlite3
import os
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, Filters

# লগিং সেটআপ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# এডমিন কনফিগ - আপনার ডিটেইলস দিন
ADMIN_USERNAME = "@Mathtoearnadmin"
ADMIN_EMAIL = "বিকল্প email@gmail.com"  #
ADMIN_ID =   বিকল্প #

# পেমেন্ট ডিটেইলস - আপনার দেওয়া নাম্বার
PAYMENT_DETAILS = {
    'bkash': "01873115394",
    'nagad': "01873115394", 
    'rocket': "015772133478",
    'upay': "01873115394"
}

# ডাটাবেস সেটআপ
def init_db():
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY,
                  username TEXT,
                  first_name TEXT,
                  referred_by INTEGER,
                  is_premium INTEGER DEFAULT 0,
                  tax_balance INTEGER DEFAULT 0,
                  referral_balance INTEGER DEFAULT 0,
                  premium_balance INTEGER DEFAULT 0,
                  total_balance INTEGER DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS referrals
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  referrer_id INTEGER,
                  referred_id INTEGER,
                  level INTEGER,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    conn.commit()
    conn.close()

init_db()

# ডাটাবেস ফাংশন
def get_user_data(user_id):
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def get_all_users():
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users ORDER BY total_balance DESC")
    users = c.fetchall()
    conn.close()
    return users

def create_user(user_id, username, first_name, referred_by=None):
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    c.execute('''INSERT OR IGNORE INTO users 
                 (user_id, username, first_name, referred_by) 
                 VALUES (?, ?, ?, ?)''',
              (user_id, username, first_name, referred_by))
    conn.commit()
    conn.close()

def update_user_balance(user_id, tax_points=0, referral_points=0, premium_points=0):
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    
    user = get_user_data(user_id)
    if user:
        c.execute('''UPDATE users SET 
                     tax_balance = tax_balance + ?,
                     referral_balance = referral_balance + ?,
                     premium_balance = premium_balance + ?,
                     total_balance = tax_balance + referral_balance + premium_balance
                     WHERE user_id = ?''',
                 (tax_points, referral_points, premium_points, user_id))
        
        # রেফারেল বোনাস
        if referred_by := user[3]:
            if tax_points > 0:
                # Level 1: 30 points
                c.execute("UPDATE users SET referral_balance = referral_balance + 30 WHERE user_id = ?", 
                         (referred_by,))
    conn.commit()
    conn.close()

def activate_premium(user_id):
    conn = sqlite3.connect('math_game.db')
    c = conn.cursor()
    c.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

# গেম ফাংশন
def generate_math_problem():
    operations = ['+', '-', '×', '÷']
    operation = random.choice(operations)
    
    if operation == '+':
        a, b = random.randint(1, 50), random.randint(1, 50)
        answer = a + b
        problem = f"{a} + {b} = ?"
    elif operation == '-':
        a, b = random.randint(20, 100), random.randint(1, 19)
        answer = a - b
        problem = f"{a} - {b} = ?"
    elif operation == '×':
        a, b = random.randint(1, 12), random.randint(1, 12)
        answer = a * b
        problem = f"{a} × {b} = ?"
    else:  # ÷
        b = random.randint(1, 10)
        a = b * random.randint(1, 10)
        answer = a // b
        problem = f"{a} ÷ {b} = ?"
    
    return problem, answer, operation

# মেনু সিস্টেম
def main_menu(update: Update, context: CallbackContext):
    keyboard = [
        [InlineKeyboardButton("📖 About", callback_data="about")],
        [InlineKeyboardButton("🧮 Tax Game", callback_data="tax_game")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 Our Channel", callback_data="channel")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        update.message.reply_text(
            "🎮 **গণিত গেম মেনু**\n\nনিচ থেকে অপশন সিলেক্ট করুন:",
            reply_markup=reply_markup
        )
    else:
        update.callback_query.edit_message_text(
            "🎮 **গণিত গেম মেনু**\n\nনিচ থেকে অপশন সিলেক্ট করুন:",
            reply_markup=reply_markup
        )

def start(update: Update, context: CallbackContext):
    user = update.message.from_user
    referred_by = context.args[0] if context.args else None
    
    create_user(user.id, user.username, user.first_name, referred_by)
    
    welcome_text = f"""
🌟 **স্বাগতম {user.first_name}!** 🌟

🎯 **গণিত শিখুন, আয় করুন!**
• গণিত সমস্যা সমাধান করে ইনকাম করুন
• বন্ধুদের রেফার করে এক্সট্রা ইনকাম করুন
• আনলিমিটেড গেম খেলার সুযোগ

🚀 **শুরু করতে মেনু থেকে 'Tax Game' সিলেক্ট করুন**
    """
    
    update.message.reply_text(welcome_text)
    main_menu(update, context)

# এবাউট সেকশন (আপডেটেড)
def show_about(query, context):
    about_text = f"""
📖 **About MathToEarn Bot** 📖

🎯 **গণিত শিখুন, আয় করুন!**
• গণিত সমস্যা সমাধান করে ইনকাম করুন
• বন্ধুদের রেফার করে এক্সট্রা ইনকাম করুন
• দৈনিক আনলিমিটেড গেম করার সুযোগ

💰 **ইনকাম সিস্টেম:**
• সঠিক উত্তর: +২ পয়েন্ট
• ভুল উত্তর: -২ পয়েন্ট  
• 💎 **প্রিমিয়াম নিলে বেশি ইনকাম的机会!**

👥 **রেফারেল সিস্টেম:**
• লেভেল ১: ৩০ পয়েন্ট
• লেভেল ২: ১০ পয়েন্ট  
• লেভেল ৩: ৪ পয়েন্ট
• লেভেল ৪: ১ পয়েন্ট

📞 **কন্টাক্ট:**
এডমিন: {Mathtoearnadmin}
ইমেইল: {বিকল্প}

💡 **মোটিভেশন:** 
"প্রতিদিন কিছুক্ষণ গণিত চর্চা করুন, মস্তিষ্কের ব্যায়াম করুন এবং আয় করুন!"
    """
    query.edit_message_text(about_text, reply_markup=main_menu_keyboard())

# কলব্যাক হ্যান্ডলার
def handle_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    user_id = query.from_user.id
    
    if query.data == "about":
        show_about(query, context)
    
    elif query.data == "tax_game":
        start_tax_game(query, context)
    
    elif query.data == "balance":
        show_balance(query, context)
    
    elif query.data == "channel":
        query.edit_message_text(
            "📊 **আমাদের অফিসিয়াল চ্যানেল:**\n\n"
            "👉 "
            "সব আপডেট পেতে এখনই জয়েন করুন!",
            reply_markup=main_menu_keyboard()
        )
    
    elif query.data == "withdraw":
        handle_withdraw(query, context)
    
    elif query.data == "referral":
        show_referral_link(query, context)
    
    elif query.data == "deposit":
        show_deposit_options(query, context)
    
    elif query.data == "back_to_menu":
        main_menu(update, context)

def main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📖 About", callback_data="about")],
        [InlineKeyboardButton("🧮 Tax Game", callback_data="tax_game")],
        [InlineKeyboardButton("💰 Balance", callback_data="balance")],
        [InlineKeyboardButton("📊 Our Channel", callback_data="channel")],
        [InlineKeyboardButton("💸 Withdraw", callback_data="withdraw")],
        [InlineKeyboardButton("👥 Referral", callback_data="referral")]
    ]
    return InlineKeyboardMarkup(keyboard)

def start_tax_game(query, context):
    problem, answer, operation = generate_math_problem()
    
    context.user_data['current_answer'] = answer
    context.user_data['current_operation'] = operation
    
    motivational_text = """
💡 **গুরুত্বপূর্ণ নিয়ম:**
✅ সঠিক উত্তর দিলে: +২ পয়েন্ট  
❌ ভুল উত্তর দিলে: -২ পয়েন্ট

🎯 **প্রিমিয়াম ইউজাররা বেশি ইনকাম的机会 পাবেন!**
    """
    
    query.edit_message_text(
        f"{motivational_text}\n\n"
        f"🧮 **গণিত সমস্যা:**\n{problem}\n\n"
        f"📝 **আপনার উত্তর টাইপ করুন:**",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 মেনু", callback_data="back_to_menu")]])
    )

def show_balance(query, context):
    user_id = query.from_user.id
    user = get_user_data(user_id)
    
    if user:
        balance_text = f"""
💰 **আপনার ব্যালেন্স:**

• 🧮 Tax Balance: {user[5]} পয়েন্ট
• 👥 Referral Balance: {user[6]} পয়েন্ট  
• 💎 Premium Balance: {user[7]} পয়েন্ট
• 📊 Total Balance: {user[8]} পয়েন্ট

💡 **প্রিমিয়াম ইউজাররা বেশি ইনকাম的机会 পান!**
        """
    else:
        balance_text = "❌ ডাটা লোড করতে সমস্যা হচ্ছে!"
    
    query.edit_message_text(balance_text, reply_markup=main_menu_keyboard())

def handle_withdraw(query, context):
    user_id = query.from_user.id
    user = get_user_data(user_id)
    
    if not user:
        query.edit_message_text("❌ ইউজার ডাটা পাওয়া যায়নি!", reply_markup=main_menu_keyboard())
        return
    
    if user[8] < 500:
        query.edit_message_text(
            f"❌ **ন্যূনতম ৫০০ পয়েন্ট প্রয়োজন!**\n\n"
            f"💰 আপনার মোট ব্যালেন্স: {user[8]} পয়েন্ট\n"
            f"🎯 আরও {500 - user[8]} পয়েন্ট প্রয়োজন",
            reply_markup=main_menu_keyboard()
        )
        return
    
    show_withdraw_amounts(query, context)

def show_deposit_options(query, context):
    deposit_text = f"""
💰💎 🌟✨ **অফিসিয়াল পেমেন্ট ডিটেইলস** ✨🌟 💎💰

💖 **পেমেন্ট নাম্বারসমূহ:**
📱💸 বিকাশ: {PAYMENT_DETAILS['bkash']}
📱💸 নগদ: {PAYMENT_DETAILS['nagad']}
📱💸 রকেট: {PAYMENT_DETAILS['rocket']}
📱💸 উপায়: {PAYMENT_DETAILS['upay']}

💰 **পরিমাণ:** ১২৫ টাকা

📋 **ইনস্ট্রাকশন:**
1. উপরের যেকোনো নাম্বারে ১২৫ টাকা সেন্ড মানি করুন
2. ট্রানজেকশন আইডি ও স্ক্রিনশট সেভ করুন  
3. অ্যাডমিনকে ট্রানজেকশন আইডি ও স্ক্রিনশট পাঠান
4. ২৪ ঘন্টার মধ্যে আপনার একাউন্ট একটিভ হবে

👨‍💼 **অ্যাডমিন:** {ADMIN_USERNAME}
📧 **ইমেইল:** {ADMIN_EMAIL}
    """
    query.edit_message_text(deposit_text, reply_markup=main_menu_keyboard())

def show_withdraw_amounts(query, context):
    keyboard = [
        [InlineKeyboardButton("২০০ পয়েন্ট", callback_data="withdraw_200")],
        [InlineKeyboardButton("৫০০ পয়েন্ট", callback_data="withdraw_500")],
        [InlineKeyboardButton("১০০০ পয়েন্ট", callback_data="withdraw_1000")],
        [InlineKeyboardButton("১৫০০ পয়েন্ট", callback_data="withdraw_1500")],
        [InlineKeyboardButton("🔙 মেনু", callback_data="back_to_menu")]
    ]
    query.edit_message_text(
        "💰 **উইথড্র পরিমাণ সিলেক্ট করুন:**\n\n"
        "নিচ থেকে আপনার পছন্দের পরিমাণ সিলেক্ট করুন:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

def show_referral_link(query, context):
    user_id = query.from_user.id
    referral_link = f"https://t.me/Mathtoearn_bot?start={user_id}"
    
    referral_text = f"""
👥 **রেফারেল সিস্টেম:**

🔗 **আপনার রেফারেল লিংক:**
`{referral_link}`

📊 **রেফারেল বোনাস:**
• লেভেল ১: ৩০ পয়েন্ট
• লেভেল ২: ১০ পয়েন্ট
• লেভেল ৩: ৪ পয়েন্ট  
• লেভেল ৪: ১ পয়েন্ট

💡 **বন্ধুদের মাঝে শেয়ার করুন এবং এক্সট্রা ইনকাম করুন!**
💎 **প্রিমিয়াম ইউজাররা বেশি বোনাস পান!**
    """
    query.edit_message_text(
        referral_text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 লিংক কপি করুন", callback_data="copy_link")],
            [InlineKeyboardButton("🔙 মেনু", callback_data="back_to_menu")]
        ])
    )

# মেসেজ হ্যান্ডলার
def handle_message(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    
    if 'current_answer' in context.user_data:
        try:
            user_answer = int(update.message.text.strip())
            correct_answer = context.user_data['current_answer']
            
            if user_answer == correct_answer:
                update_user_balance(user_id, tax_points=2)
                update.message.reply_text(
                    "✅ **সঠিক উত্তর!** 🎉\n\n"
                    "➕ **২ পয়েন্ট যোগ করা হয়েছে!**\n\n"
                    "💎 **প্রিমিয়াম ইউজাররা বেশি ইনকাম করতে পান!**",
                    reply_markup=main_menu_keyboard()
                )
            else:
                user = get_user_data(user_id)
                if user and user[5] >= 2:
                    update_user_balance(user_id, tax_points=-2)
                    update.message.reply_text(
                        "❌ **ভুল উত্তর!**\n\n"
                        "➖ **২ পয়েন্ট কাটা হয়েছে!**\n\n"
                        "💡 আবার চেষ্টা করুন!",
                        reply_markup=main_menu_keyboard()
                    )
                else:
                    update.message.reply_text(
                        "❌ **ভুল উত্তর!**\n\n"
                        "⚠️ **পর্যাপ্ত পয়েন্ট নেই!**\n\n"
                        "💡 আবার চেষ্টা করুন!",
                        reply_markup=main_menu_keyboard()
                    )
            
            context.user_data.pop('current_answer', None)
            context.user_data.pop('current_operation', None)
            
        except ValueError:
            update.message.reply_text(
                "❌ দয়া করে শুধুমাত্র সংখ্যা ইনপুট করুন!",
                reply_markup=main_menu_keyboard()
            )
    else:
        main_menu(update, context)

def main():
    BOT_TOKEN = "8217748761:AAFSDp4pYLx1e1NMvhCxhY5X9RHbO_0vxmI"
    
    updater = Updater(BOT_TOKEN)
    dispatcher = updater.dispatcher
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("menu", main_menu))
    dispatcher.add_handler(CallbackQueryHandler(handle_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    updater.start_polling()
    print("✅ MathToEarn Bot Started Successfully!")
    updater.idle()

if __name__ == '__main__':
    main()
