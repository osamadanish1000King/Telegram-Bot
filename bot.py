import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8414495176
BOT_USERNAME = "Earn_FreeAfghani_Bot"

# rewards
DAILY = 0.5
WEEKLY = 5
TASK = 0.3
INVITE = 2

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS task_channels(id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT)")
conn.commit()

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 حالت"],
        ["👥 دعوت", "💰 پیسې زیاتول"],
        ["📱 شمېره ثبت", "⚡ ایزي لوډ"],
        ["🤖 د رباټ په اړه"]
    ], resize_keyboard=True)

def money_kb():
    return ReplyKeyboardMarkup([
        ["📋 ټاسک", "🎁 بونس"],
        ["🔙 شاته"]
    ], resize_keyboard=True)

def bonus_kb():
    return ReplyKeyboardMarkup([
        ["🎁 ورځنی بونس", "🔥 اوونیز بونس"],
        ["🔙 شاته"]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 ټول یوزران"],
        ["📢 برودکاست"],
        ["➕ ټاسک چینل"],
        ["➕ فورس چینل"],
        ["🔙 شاته"]
    ], resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id) VALUES(?)", (uid,))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update, context):
    cur.execute("SELECT username FROM channels LIMIT 3")
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
                buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ تایید", callback_data="check_join")])
        await update.effective_message.reply_text(
            "🚨 مهرباني وکړئ چینلونه جواین کړئ:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False

    return True

async def check_join(update, context):
    query = update.callback_query
    await query.answer()
    if await force_join(update, context):
        await query.message.reply_text("✅ تایید شو", reply_markup=main_kb())

# ================= TASK =================
async def task_done(update, context):
    query = update.callback_query
    await query.answer()
    uid = query.from_user.id

    cur.execute("SELECT username FROM task_channels")
    channels = cur.fetchall()

    ok = True
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch[0], uid)
            if member.status not in ["member","administrator","creator"]:
                ok = False
        except:
            ok = False

    if ok:
        cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK, uid))
        conn.commit()
        await query.message.reply_text("🎉 0.3 AF اضافه شول")
    else:
        await query.message.reply_text("❌ ټول چینلونه جواین کړئ")

# ================= START =================
async def start(update, context):
    uid = update.effective_user.id
    get_user(uid)

    if not await force_join(update, context):
        return

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (INVITE, ref))
                conn.commit()
        except:
            pass

    await update.message.reply_text("🌟 ښه راغلاست!", reply_markup=main_kb())

# ================= MAIN HANDLER =================
async def handler(update, context):
    uid = update.effective_user.id
    get_user(uid)

    text = update.message.text if update.message else ""

    if update.message:
        if not await force_join(update, context):
            return

        # 📊 حالت
        if text == "📊 حالت":
            cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
            bal = cur.fetchone()[0]
            name = update.effective_user.first_name

            await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {name}
💳 ایډي کارن : {uid}
💵ستاسو پيسو اندازه= {bal} AF

🔗 دعوت:
https://t.me/{BOT_USERNAME}?start={uid}"""
            )

        # 👥 دعوت
        elif text == "👥 دعوت":
            await update.message.reply_text(
f"🔗 خپل لینک:\nhttps://t.me/{BOT_USERNAME}?start={uid}\n\n👥 هر دعوت = {INVITE} AF"
            )

        # 💰 پیسې زیاتول
        elif text == "💰 پیسې زیاتول":
            await update.message.reply_text("انتخاب کړئ:", reply_markup=money_kb())

        # 📋 ټاسک
        elif text == "📋 ټاسک":
            cur.execute("SELECT username FROM task_channels")
            channels = cur.fetchall()

            if not channels:
                await update.message.reply_text("❌ ټاسک نشته")
                return

            buttons = []
            for ch in channels:
                buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch[0].replace('@','')}")])

            buttons.append([InlineKeyboardButton("✅ Done", callback_data="task_done")])

            await update.message.reply_text(
                "📋 چینلونه جواین کړئ:",
                reply_markup=InlineKeyboardMarkup(buttons)
            )

        # 🎁 بونس
        elif text == "🎁 بونس":
            await update.message.reply_text("🎁 بونس:", reply_markup=bonus_kb())

        elif text == "🎁 ورځنی بونس":
            today = str(datetime.date.today())
            cur.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
            last = cur.fetchone()[0]

            if last == today:
                await update.message.reply_text("❌ نن اخیستل شوی")
            else:
                cur.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE id=?", (DAILY, today, uid))
                conn.commit()
                await update.message.reply_text(f"✅ {DAILY} AF اضافه شول")

        elif text == "🔥 اوونیز بونس":
            week = str(datetime.date.today().isocalendar()[1])
            cur.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
            last = cur.fetchone()[0]

            if last == week:
                await update.message.reply_text("❌ دا هفته اخیستل شوی")
            else:
                cur.execute("UPDATE users SET balance=balance+?, last_weekly=? WHERE id=?", (WEEKLY, week, uid))
                conn.commit()
                await update.message.reply_text(f"✅ {WEEKLY} AF اضافه شول")

        # 🔙 back
        elif text == "🔙 شاته":
            await update.message.reply_text("🏠 اصلي مینو", reply_markup=main_kb())

        # 🤖 about
        elif text == "🤖 د رباټ په اړه":
            await update.message.reply_text("🤖 دا بوټ د افغانانو د ګټې لپاره جوړ شوی ❤️")

        # 👑 ADMIN
        elif text == "/admin":
            if uid == ADMIN_ID:
                await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())
            else:
                await update.message.reply_text("❌ ته اډمین نه یې")

        # ➕ ټاسک چینل
        elif text == "➕ ټاسک چینل" and uid == ADMIN_ID:
            await update.message.reply_text("username ولیکئ:")
            context.user_data["add_task"] = True

        elif context.user_data.get("add_task") and uid == ADMIN_ID:
            cur.execute("INSERT INTO task_channels(username) VALUES(?)", (text,))
            conn.commit()
            await update.message.reply_text("✅ اضافه شو")
            context.user_data["add_task"] = False

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(CallbackQueryHandler(task_done, pattern="task_done"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

print("🚀 BOT RUNNING PERFECT...")
app.run_polling()
