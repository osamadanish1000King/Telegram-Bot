import sqlite3
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
DAILY_REWARD = 1
WEEKLY_REWARD = 5

# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
balance REAL DEFAULT 0,
invites INTEGER DEFAULT 0,
ref INTEGER,
phone TEXT,
daily TEXT,
weekly TEXT)""")
conn.commit()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()

# ===== TIME =====
def time_left(last,seconds):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    now=datetime.datetime.now()
    return seconds-(now-last).total_seconds()

def format_time(sec):
    sec=int(sec)
    h=sec//3600
    m=(sec%3600)//60
    s=sec%60
    return f"{h}:{m}:{s}"

# ===== KEYBOARD =====
def main_kb():
    return ReplyKeyboardMarkup([
        ["❗ خپل حساب معلومات"],
        ["📞 شمېره ثبت کړی"],
        ["💰 افغانۍ زیاتول","🏦 ایزیلوډ"],
        ["📊 د ربات په اړه"]
    ],resize_keyboard=True)

def invite_kb():
    return ReplyKeyboardMarkup([
        ["🏅 غوره دعوت کوونکي","✏️ ستا دعوت کوونکي"],
        ["🎁 ورځنۍ بونس","🎁 اوونیز بونس"],
        ["👥 ملګري دعوت کول"],
        ["📢 ټاسک"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

def phone_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📲 شمېره واستوه",request_contact=True)],
        ["🔙 وتل"]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 Broadcast"],
        ["➕ Force Join Add","➖ Force Join Del"],
        ["➕ Task Add","➖ Task Del"],
        ["📊 Stats"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== INLINE =====
def force_join_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 چینل جواین", url=link)]
    ])

def task_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Task Channel", url=link)],
        [InlineKeyboardButton("✅ Done", callback_data="done_task")]
    ])

# ===== CHECK JOIN =====
async def is_joined(user_id, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except:
            ref = None

    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    exists = cur.fetchone()

    if not exists:
        get_user(uid, name, ref)

        if ref and ref != uid:
            cur.execute(
                "UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",
                (INVITE_REWARD, ref)
            )
            conn.commit()

            await context.bot.send_message(
                ref,
                "🎉 یو کس دې راوست\n💰 4 افغانۍ اضافه شوه"
            )

    await context.bot.send_message(
        ADMIN_ID,
        f"👤 نوی یوزر:\n{name}\n{uid}"
    )

    link = context.bot_data.get("force_join")
    if link:
        joined = await is_joined(uid, context.bot, link)
        if not joined:
            await update.message.reply_text(
                "❗ مهرباني وکړه چینل جواین کړه",
                reply_markup=force_join_btn(link)
            )
            return

    await update.message.reply_text(
        """🌟 ښه راغلاست ګرانه کاروونکي! 👋

💸 دلته ته کولی شې ډېري په اسانۍ سره افغانۍ وګټې!

🎯 څنګه کار کوي؟
👥 ملګري دعوت کړه
🎁 بونسونه ترلاسه کړه
📢 ټاسکونه ترسره کړه

💰 هر دعوت = جایزه
🎁 ورځنۍ او اوونیز بونس هم شته!

🚀 همدا اوس پیل کړه او عاید جوړ کړه 👇

👇 له مینو څخه یو انتخاب وکړه""",
        reply_markup=main_kb()
    )

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return
        
    uid=update.effective_user.id
    name=update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text if update.message.text else ""

    if text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel",reply_markup=admin_kb())

    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real_total = cur.fetchone()[0]

        total = (real_total * 2) + 100

        await update.message.reply_text(
            f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}
👤 {ADMIN_ID}
"""
        )

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))

print("BOT RUNNING...")
app.run_polling()
