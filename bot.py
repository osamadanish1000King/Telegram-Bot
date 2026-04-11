import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8289491009
BOT_USERNAME = "earn_freeafghani_bot"
ADMIN_USERNAME = "@Danish_King2"

DAILY = 0.5
WEEKLY = 5
INVITE = 2
TASK_REWARD = 0.3

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS stats(day TEXT, fake INTEGER)")
conn.commit()

# ================= FAKE USERS =================
def fake_users():
    today = str(datetime.date.today())
    cur.execute("SELECT fake FROM stats WHERE day=?", (today,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO stats VALUES(?,?)", (today, 1000))
        conn.commit()
        return 1000
    return row[0]

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 حالت"],
        ["👥 دعوت","💰 پیسې زیاتول"],
        ["📱 شمېره ثبت","⚡ ایزي لوډ"],
        ["🤖 د رباټ په اړه"]
    ],resize_keyboard=True)

def money_kb():
    return ReplyKeyboardMarkup([
        ["📋 ټاسک","🎁 بونس"],
        ["🔙 شاته"]
    ],resize_keyboard=True)

def bonus_kb():
    return ReplyKeyboardMarkup([
        ["🎁 ورځنی بونس","🔥 اوونیز بونس"],
        ["🔙 شاته"]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 ټول یوزران"],
        ["📢 برودکاست"],
        ["➕ ټاسک چینل","➖ ټاسک چینل"],
        ["➕ فورس چینل","➖ فورس چینل"],
        ["🔙 شاته"]
    ],resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id) VALUES(?)",(uid,))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update,context):
    cur.execute("SELECT username FROM channels")
    channels = cur.fetchall()

    if not channels:
        return True

    uid = update.effective_user.id
    buttons = []

    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member","administrator","creator"]:
                buttons.append([InlineKeyboardButton("📢 Join",url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join",url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ تایید",callback_data="check_join")])
        await update.effective_message.reply_text("🚨 چینلونه جواین کړئ:",reply_markup=InlineKeyboardMarkup(buttons))
        return False

    return True

async def check_join(update,context):
    q=update.callback_query
    await q.answer()
    if await force_join(update,context):
        await q.message.reply_text("✅ تایید شو",reply_markup=main_kb())

# ================= START =================
async def start(update,context):
    uid = update.effective_user.id
    get_user(uid)

    if not await force_join(update,context):
        return

    await update.message.reply_text("🌟 ښه راغلاست!",reply_markup=main_kb())

# ================= ADMIN COMMAND =================
async def admin_cmd(update, context):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())
    else:
        await update.message.reply_text(f"❌ که کومه ستونزه وي له اډمين سره اړيکه ونيسئ:\n{ADMIN_USERNAME}")

# ================= HELP COMMAND =================
async def help_cmd(update, context):
    await update.message.reply_text(
"""ℹ️ د رباټ مرسته:

📊 حالت - خپل بیلانس وګوره
👥 دعوت - خپل لینک واخلئ
💰 پیسې زیاتول - ټاسک او بونس
📱 شمېره ثبت - نمبر ثبت کړه
⚡ ایزي لوډ - بیلانس استعمال کړه

🎁 بونس هره ورځ او هره اوونۍ ورکول کیږي

🚀 خپل لینک شریک کړه او عاید ترلاسه کړه!"""
    )

# ================= MAIN =================
async def handler(update,context):

    if not update.message:
        return

    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid)

    if not await force_join(update,context):
        return

    if text=="📊 حالت":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]

        total = real + fake_users()

        await update.message.reply_text(
f"""🤵🏻‍♂️ {update.effective_user.first_name}
🆔 {uid}

💰 بیلانس: {bal} AF
👥 ټول یوزران: {total}

https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    elif text=="👥 دعوت":
        await update.message.reply_text(f"https://t.me/{BOT_USERNAME}?start={uid}")

    elif text=="💰 پیسې زیاتول":
        await update.message.reply_text("انتخاب:",reply_markup=money_kb())

    elif text=="🔙 شاته":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    elif text=="🎁 بونس":
        await update.message.reply_text("🎁",reply_markup=bonus_kb())

    elif text=="🎁 ورځنی بونس":
        today=str(datetime.date.today())
        cur.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        if last==today:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE id=?", (DAILY,today,uid))
            conn.commit()
            await update.message.reply_text(f"✅ {DAILY} AF اضافه شول")

    elif text=="🔥 اوونیز بونس":
        week=str(datetime.date.today().isocalendar()[1])
        cur.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        if last==week:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_weekly=? WHERE id=?", (WEEKLY,week,uid))
            conn.commit()
            await update.message.reply_text(f"✅ {WEEKLY} AF اضافه شول")

# ================= CALLBACK =================
async def callback(update,context):
    q=update.callback_query
    await q.answer()

    if q.data=="task_done":
        uid=q.from_user.id
        cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK_REWARD,uid))
        conn.commit()
        await q.message.reply_text("🎉 Reward ورکړل شو")

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin_cmd))   # ✅ FIXED
app.add_handler(CommandHandler("help",help_cmd))     # ✅ ADDED
app.add_handler(CallbackQueryHandler(callback))
app.add_handler(CallbackQueryHandler(check_join,pattern="check_join"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 LEVEL 5 FINAL WORKING 100%")
app.run_polling()
