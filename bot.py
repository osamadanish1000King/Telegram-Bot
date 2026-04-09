import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8289491009
BOT_USERNAME = "earn_freeafghani_bot"

DAILY = 0.5
WEEKLY = 5
TASK = 0.3
INVITE = 2

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT, join_date TEXT)")
conn.commit()

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 حالت"],
        ["👥 دعوت", "💰 پیسې زیاتول"],
        ["📱 شمېره ثبت", "⚡ ایزي لوډ"],
        ["🤖 د رباټ په اړه"]
    ], resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        today = str(datetime.date.today())
        cur.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",(uid,0,None,None,None,today))
        conn.commit()
        return True
    return False

# ================= START =================
async def start(update, context):
    uid = update.effective_user.id
    is_new = get_user(uid)

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (INVITE, ref))
                conn.commit()

                # 🎉 congratulation to inviter
                await context.bot.send_message(ref, "🎉 نوی کس راغی! +2 AF")

                # 🔔 notify admin
                await context.bot.send_message(ADMIN_ID, f"👤 نوی یوزر راغی:\nID: {uid}")
        except:
            pass

    # new user message
    if is_new:
        await update.message.reply_text("🎉 ښه راغلاست! دلته پیسې ګټلی شې 💰")

    await update.message.reply_text("👇 مینو:", reply_markup=main_kb())

# ================= HANDLER =================
async def handler(update, context):
    uid = update.effective_user.id
    get_user(uid)
    text = update.message.text

    # 📊 حالت
    if text == "📊 حالت":
        cur.execute("SELECT balance, join_date FROM users WHERE id=?", (uid,))
        data = cur.fetchone()
        bal = data[0]
        join_date = datetime.datetime.strptime(data[1], "%Y-%m-%d").date()

        # fake users growth
        days = (datetime.date.today() - join_date).days
        fake_users = 100 + (days * 20)

        await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {update.effective_user.first_name}
💳 ایډي کارن : {uid}
💵ستاسو پيسو اندازه= {bal} AF

👥 ټول یوزران: {fake_users}

🔗 دعوت:
https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    # 📱 نمبر ثبت
    elif text == "📱 شمېره ثبت":
        await update.message.reply_text("📱 خپل 10 عددي نمبر ولیکئ:")
        context.user_data["phone"] = True

    elif context.user_data.get("phone"):
        if text.isdigit() and len(text) == 10:
            cur.execute("UPDATE users SET phone=? WHERE id=?", (text, uid))
            conn.commit()
            await update.message.reply_text("✅ ستاسو نمبر ثبت شو")
        else:
            await update.message.reply_text("❌ نمبر باید 10 عدده وي")
        context.user_data["phone"] = False

    # ⚡ ایزي لوډ
    elif text == "⚡ ایزي لوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]

        if bal < 50:
            await update.message.reply_text("⚠️ لږ تر لږه 50 AF پکار دي")
        else:
            await update.message.reply_text("✅ ستاسو ایزي لوډ غوښتنه ثبت شوه")

    # 👥 دعوت
    elif text == "👥 دعوت":
        await update.message.reply_text(
f"🔗 لینک:\nhttps://t.me/{BOT_USERNAME}?start={uid}\n👥 هر دعوت = {INVITE} AF"
        )

    # 💰 پیسې زیاتول
    elif text == "💰 پیسې زیاتول":
        await update.message.reply_text("📋 ټاسک یا 🎁 بونس وکاروئ")

    # 🤖 about
    elif text == "🤖 د رباټ په اړه":
        await update.message.reply_text("🤖 دا بوټ د افغانانو د عاید لپاره جوړ شوی ❤️")

    # 👑 ADMIN PANEL
    elif text == "/admin":
        if uid == ADMIN_ID:
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]

            await update.message.reply_text(
f"""👑 Admin Panel

👥 Real Users: {total}

Options:
➕ چینل اضافه کړه
📢 برودکاست"""
            )
        else:
            await update.message.reply_text("❌ ته اډمین نه یې")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

print("🔥 FULL FIXED BOT RUNNING...")
app.run_polling()
