import sqlite3
import datetime
from telegram import *
from telegram.ext import *
import asyncio

# ================= CONFIG =================
TOKEN = "8279973060:AAGp9bxREyPd29xzv85mcWvTA33WIltyi3A"
ADMIN_ID = 8279973060
BOT_USERNAME = "Afghan_starbot"

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
balance REAL DEFAULT 0,
invited_by INTEGER,
phone TEXT,
last_daily TEXT,
last_weekly TEXT,
join_date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT
)
""")

conn.commit()

# ================= KEYBOARD =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 حالت"],
        ["👥 دعوت", "💰 پیسې زیاتول"],
        ["📋 ټاسک", "🎁 بونس"],
        ["📱 شمېره ثبت", "⚡ ایزي لوډ"],
        ["🤖 د رباټ په اړه"]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 ټول یوزران", "📊 احصایه"],
        ["📢 برودکاست"],
        ["💰 ریوارد کنټرول"],
        ["📣 آټو پوسټ"],
        ["➕ فورس چینل", "➖ حذف چینل"],
        ["🔙 شاته"]
    ], resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cursor.fetchone():
        today = str(datetime.date.today())
        cursor.execute("INSERT INTO users(id, join_date) VALUES(?,?)", (uid, today))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update, context):
    cursor.execute("SELECT username FROM channels LIMIT 3")
    channels = cursor.fetchall()

    if not channels:
        return True

    uid = update.effective_user.id
    buttons = []

    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member", "administrator", "creator"]:
                buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ تایید", callback_data="check_join")])

        if update.message:
            await update.message.reply_text("🚨 لومړی چینلونه جواین کړئ:", reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.callback_query.message.reply_text("🚨 چینلونه جواین کړئ:", reply_markup=InlineKeyboardMarkup(buttons))

        return False

    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    if not await force_join(update, context):
        return

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cursor.execute("UPDATE users SET balance=balance+2 WHERE id=?", (ref,))
                conn.commit()
        except:
            pass

    await update.message.reply_text("🎉 ښه راغلاست!", reply_markup=main_kb())

# ================= MAIN =================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id
    get_user(uid)

    if not await force_join(update, context):
        return

    # 📊 حالت
    if text == "📊 حالت":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]

        name = update.effective_user.first_name

        await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {name}

💳 ایډي کارن : {uid}
💵ستاسو پيسو اندازه= {bal} AF"""
        )

    # 👥 دعوت
    elif text == "👥 دعوت":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"🔗 لینک:\n{link}\nهر کس = 2 AF")

    # 🎁 بونس
    elif text == "🎁 ورځنی بونس":
        today = str(datetime.date.today())
        cursor.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        last = cursor.fetchone()[0]

        if last == today:
            await update.message.reply_text("❌ نن مو اخیستی")
        else:
            cursor.execute("UPDATE users SET balance=balance+0.5, last_daily=? WHERE id=?", (today, uid))
            conn.commit()
            await update.message.reply_text("✅ 0.5 AF اضافه شول")

    elif text == "🔥 اوونیز بونس":
        week = str(datetime.date.today().isocalendar()[1])
        cursor.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
        last = cursor.fetchone()[0]

        if last == week:
            await update.message.reply_text("❌ دا هفته مو اخیستی")
        else:
            cursor.execute("UPDATE users SET balance=balance+5, last_weekly=? WHERE id=?", (week, uid))
            conn.commit()
            await update.message.reply_text("✅ 5 AF اضافه شول")

    # 📱 نمبر
    elif text == "📱 شمېره ثبت":
        await update.message.reply_text("10 رقمي نمبر داخل کړئ:")

    elif text.isdigit():
        if len(text) == 10:
            cursor.execute("UPDATE users SET phone=? WHERE id=?", (text, uid))
            conn.commit()
            await update.message.reply_text("✅ ثبت شو")
        else:
            await update.message.reply_text("❌ باید 10 عدد وي")

    # ⚡ ایزي لوډ
    elif text == "⚡ ایزي لوډ":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bal < 50:
            await update.message.reply_text("⚠️ لږ تر لږه 50 افغانۍ باید ولرئ")

    # 🤖 about
    elif text == "🤖 د رباټ په اړه":
        await update.message.reply_text("🤖 دا بوټ د افغانانو لپاره جوړ شوی ❤️")

# ================= ADMIN =================
async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    cursor.execute("SELECT COUNT(*) FROM users")
    total = cursor.fetchone()[0]

    today = str(datetime.date.today())
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date=?", (today,))
    daily = cursor.fetchone()[0]

    month = today[:7]
    cursor.execute("SELECT COUNT(*) FROM users WHERE join_date LIKE ?", (f"{month}%",))
    monthly = cursor.fetchone()[0]

    await update.message.reply_text(
f"""👑 Admin Panel

👥 ټول یوزران: {total}
📅 ورځني یوزران: {daily}
📆 میاشتني یوزران: {monthly}""",
        reply_markup=admin_kb()
    )

# ================= BROADCAST =================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    cursor.execute("SELECT id FROM users")
    users = cursor.fetchall()

    for u in users:
        try:
            await context.bot.send_message(u[0], msg)
        except:
            pass

    await update.message.reply_text("✅ واستول شو")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin))
app.add_handler(CommandHandler("broadcast", broadcast))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

print("✅ BOT RUNNING...")
app.run_polling()
