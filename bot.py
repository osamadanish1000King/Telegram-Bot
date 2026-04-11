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

cur.execute("""CREATE TABLE IF NOT EXISTS settings(
key TEXT PRIMARY KEY,
value TEXT)""")

conn.commit()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()

# ===== SETTINGS =====
def set_setting(key,value):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))
    conn.commit()

def get_setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    d = cur.fetchone()
    return d[0] if d else None

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

# ===== TIME =====
def time_left(last,sec):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    return sec-(datetime.datetime.now()-last).total_seconds()

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

    # FORCE JOIN
    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    await update.message.reply_text("👇 انتخاب کړه",reply_markup=main_kb())

# ===== TASK DONE =====
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    cur.execute("UPDATE users SET balance=balance+1 WHERE id=?", (uid,))
    conn.commit()

    await q.edit_message_text("✅ ټاسک مکمل شو +1 افغانۍ")

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text or ""

    # FORCE JOIN
    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    # TASK
    if text=="📢 ټاسک":
        link = get_setting("task")
        if not link:
            await update.message.reply_text("❌ ټاسک نشته")
            return

        await update.message.reply_text("📢 ټاسک ترسره کړه 👇",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 چینل",url=link)],
                [InlineKeyboardButton("✅ Done",callback_data="done_task")]
            ])
        )

    elif text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        b,i = cur.fetchone()
        await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {b} افغانۍ
👥 دعوتونه = {i}"""
        )

    elif text=="👥 ملګري دعوت کول":
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        inv = cur.fetchone()[0]
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(
f"""👥 ستا دعوت: {inv}

🔗 لینک:
{link}

🎁 هر دعوت = {INVITE_REWARD} افغانۍ"""
        )

    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پکار دي")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"{name} | {uid} | {bal}")

    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        fake = total + 100
        await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {fake}

🔗 {CHANNEL_LINK}
👤 {ADMIN_ID}"""
        )

    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه",reply_markup=phone_kb())

    elif update.message.contact:
        cur.execute("UPDATE users SET phone=? WHERE id=?", (update.message.contact.phone_number,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه",reply_markup=main_kb())

    elif text=="💰 افغانۍ زیاتول":
        await update.message.reply_text("👇 انتخاب کړه",reply_markup=invite_kb())

    elif text=="🔙 وتل":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    # ===== ADMIN =====
    elif uid==ADMIN_ID and text=="/admin":
        await update.message.reply_text("👑",reply_markup=admin_kb())

    elif uid==ADMIN_ID and text=="➕ Force Join Add":
        context.user_data["f"]=True
        await update.message.reply_text("لینک راکړه")

    elif uid==ADMIN_ID and context.user_data.get("f"):
        set_setting("force_join",text)
        context.user_data["f"]=False
        await update.message.reply_text("✅")

    elif uid==ADMIN_ID and text=="➖ Force Join Del":
        set_setting("force_join","")
        await update.message.reply_text("❌")

    elif uid==ADMIN_ID and text=="➕ Task Add":
        context.user_data["t"]=True
        await update.message.reply_text("لینک راکړه")

    elif uid==ADMIN_ID and context.user_data.get("t"):
        set_setting("task",text)
        context.user_data["t"]=False
        await update.message.reply_text("✅")

    elif uid==ADMIN_ID and text=="➖ Task Del":
        set_setting("task","")
        await update.message.reply_text("❌")

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(done_task, pattern="done_task"))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
