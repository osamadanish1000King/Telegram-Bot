import sqlite3
import datetime
import shutil
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
DAILY_REWARD = 1
WEEKLY_REWARD = 5

# ===== AUTO RESTORE =====
if not os.path.exists("bot.db") and os.path.exists("backup.db"):
    shutil.copy("backup.db", "bot.db")

# ===== BACKUP =====
def backup_db():
    try:
        if os.path.exists("bot.db"):
            shutil.copy("bot.db", "backup.db")
    except:
        pass

# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 0,
    invites INTEGER DEFAULT 0,
    ref INTEGER,
    phone TEXT,
    daily TEXT,
    weekly TEXT,
    task_done INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()
backup_db()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()
        backup_db()

# ===== SETTINGS =====
def set_setting(key,value):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))
    conn.commit()

def get_setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    d = cur.fetchone()
    return d[0] if d else None

# ===== TIME =====
def time_left(last,sec):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    return sec-(datetime.datetime.now()-last).total_seconds()

# ===== FORCE JOIN =====
async def is_joined(user_id, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def force_join_btn(link):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=link)]])

# ===== KEYBOARDS =====
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

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = int(context.args[0]) if context.args else None
    get_user(uid,name,ref)

    if ref and ref != uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
        conn.commit()
        backup_db()

    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    # ✅ NEW WELCOME MESSAGE
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

# ===== TASK DONE =====
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    cur.execute("UPDATE users SET balance=balance+1, task_done=1 WHERE id=?", (uid,))
    conn.commit()
    backup_db()

    await q.edit_message_text("✅ ټاسک مکمل شو +1 افغانۍ")

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid, name)

    text = update.message.text or ""

    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    🔙 BACK
if text == "🔙 وتل":
    await update.message.reply_text(
        "🏠 اصلي مینو ته لاړې",
        reply_markup=main_kb()
    )
    return

# ===== BROADCAST START =====
if uid == ADMIN_ID and text == "📢 Broadcast":
    context.user_data["broadcast"] = True
    await update.message.reply_text("✉️ مسيج راولیږه")
    return

# ===== BROADCAST SEND =====
if uid == ADMIN_ID and context.user_data.get("broadcast"):
    msg = text
    context.user_data["broadcast"] = False

    cur.execute("SELECT id FROM users")
    users = cur.fetchall()

    sent = 0

    for u in users:
        try:
            await context.bot.send_message(u[0], msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"✅ واستول شو: {sent}")
    if text == "📢 ټاسک":
        link = get_setting("task")
        if not link:
            await update.message.reply_text("❌ ټاسک نشته")
            return

        cur.execute("SELECT task_done FROM users WHERE id=?", (uid,))
        done = cur.fetchone()[0]

        if done == 1:
            await update.message.reply_text("✅ تا مخکې دا ټاسک مکمل کړی")
            return

        await update.message.reply_text(
            "📢 مهرباني وکړه ټاسک ترسره کړه 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 چینل", url=link)],
                [InlineKeyboardButton("✅ Done", callback_data="done_task")]
            ])
        )

    elif text == "❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        b,i = cur.fetchone()

        await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {b} افغانۍ
👥 دعوتونه = {i}"""
        )

    elif text == "💰 افغانۍ زیاتول":
        await update.message.reply_text("👇 انتخاب کړه", reply_markup=invite_kb())

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(done_task, pattern="done_task"))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
