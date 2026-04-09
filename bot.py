import sqlite3
import datetime
import asyncio
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_ID = "@earnFreeafghanibot_channel"

DAILY = 0.5
WEEKLY = 5
INVITE = 2
TASK_REWARD = 0.3

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS withdraw(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER, amount REAL, status TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks(username TEXT)")
conn.commit()

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
        ["📢 Broadcast","💸 Withdraw"],
        ["➕ Add Task"],
        ["🔙 Back"]
    ],resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id) VALUES(?)",(uid,))
        conn.commit()

# ================= START =================
async def start(update,context):
    uid=update.effective_user.id
    get_user(uid)

    if context.args:
        try:
            ref=int(context.args[0])
            if ref!=uid:
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (INVITE,ref))
                conn.commit()

                await context.bot.send_message(ref,"🎉 نوی کس راغی +2 AF")
                await context.bot.send_message(ADMIN_ID,f"👤 New User: {uid}")
        except: pass

    await update.message.reply_text("🌟 ښه راغلاست!",reply_markup=main_kb())

# ================= MAIN =================
async def handler(update,context):
    uid=update.effective_user.id
    text=update.message.text
    get_user(uid)

    # 📊 حالت
    if text=="📊 حالت":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {update.effective_user.first_name}
💳 ID = {uid}
💵 Balance = {bal} AF"""
        )

    # 👥 دعوت
    elif text=="👥 دعوت":
        await update.message.reply_text(
f"https://t.me/{BOT_USERNAME}?start={uid}"
        )

    # 💰 پیسې زیاتول
    elif text=="💰 پیسې زیاتول":
        await update.message.reply_text("انتخاب:",reply_markup=money_kb())

    # 🔙 back
    elif text=="🔙 شاته":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    # ================= TASK =================
    elif text=="📋 ټاسک":
        cur.execute("SELECT username FROM tasks")
        data=cur.fetchall()

        if not data:
            await update.message.reply_text("❌ ټاسک نشته")
            return

        btn=[]
        for t in data:
            btn.append([InlineKeyboardButton("📢 Join",url=f"https://t.me/{t[0].replace('@','')}")])

        btn.append([InlineKeyboardButton("✅ Done",callback_data="task_done")])

        await update.message.reply_text("ټاسک:",reply_markup=InlineKeyboardMarkup(btn))

    # ================= BONUS =================
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
            await update.message.reply_text("✅ ورکړل شو")

    elif text=="🔥 اوونیز بونس":
        week=str(datetime.date.today().isocalendar()[1])
        cur.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        if last==week:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_weekly=? WHERE id=?", (WEEKLY,week,uid))
            conn.commit()
            await update.message.reply_text("✅ ورکړل شو")

    # ================= PHONE =================
    elif text=="📱 شمېره ثبت":
        await update.message.reply_text("شمېره ولیکه:")
        context.user_data["phone"]=True

    elif context.user_data.get("phone"):
        if len(text)>=10:
            cur.execute("UPDATE users SET phone=? WHERE id=?", (text,uid))
            conn.commit()
            await update.message.reply_text("✅ ثبت شو")
        else:
            await update.message.reply_text("❌ نمبر غلط دی")
        context.user_data["phone"]=False

    # ================= WITHDRAW =================
    elif text=="⚡ ایزي لوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ 50 AF پکار دي")
        else:
            cur.execute("INSERT INTO withdraw(user_id,amount,status) VALUES(?,?,?)",(uid,bal,"pending"))
            conn.commit()
            await update.message.reply_text("✅ Request واستول شو")

    # ================= ADMIN =================
    elif text=="/admin":
        if uid==ADMIN_ID:
            await update.message.reply_text("👑 Admin",reply_markup=admin_kb())

    elif text=="📢 Broadcast" and uid==ADMIN_ID:
        await update.message.reply_text("پیغام ولیکه:")
        context.user_data["bc"]=True

    elif context.user_data.get("bc") and uid==ADMIN_ID:
        cur.execute("SELECT id FROM users")
        users=cur.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0],text)
            except: pass

        await update.message.reply_text("✅ واستول شو")
        context.user_data["bc"]=False

    elif text=="➕ Add Task" and uid==ADMIN_ID:
        await update.message.reply_text("username ولیکه:")
        context.user_data["task"]=True

    elif context.user_data.get("task") and uid==ADMIN_ID:
        cur.execute("INSERT INTO tasks(username) VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ اضافه شو")
        context.user_data["task"]=False

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
app.add_handler(CallbackQueryHandler(callback))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 LEVEL 3 PERFECT BOT RUNNING...")
app.run_polling()
