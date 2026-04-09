import sqlite3
import datetime
import asyncio
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_freeafghani_Bot"

# rewards
DAILY = 0.5
WEEKLY = 5
TASK = 0.3
INVITE = 2

conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT, join_date TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(id INTEGER PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS task_channels(id INTEGER PRIMARY KEY, username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS withdraw(id INTEGER PRIMARY KEY, user_id INTEGER, amount REAL, status TEXT)")
conn.commit()

# ================= KEYBOARD =================
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

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        today = str(datetime.date.today())
        cur.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",(uid,0,None,None,None,today))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update, context):
    cur.execute("SELECT username FROM channels LIMIT 3")
    chs = cur.fetchall()
    if not chs: return True

    uid = update.effective_user.id
    btn = []
    for c in chs:
        c=c[0]
        try:
            m=await context.bot.get_chat_member(c,uid)
            if m.status not in ["member","administrator","creator"]:
                btn.append([InlineKeyboardButton("📢 Join",url=f"https://t.me/{c.replace('@','')}")])
        except:
            btn.append([InlineKeyboardButton("📢 Join",url=f"https://t.me/{c.replace('@','')}")])

    if btn:
        btn.append([InlineKeyboardButton("✅ تایید",callback_data="join")])
        await update.effective_message.reply_text("🚨 چینلونه جواین کړئ:",reply_markup=InlineKeyboardMarkup(btn))
        return False
    return True

async def check_join(update,context):
    q=update.callback_query
    await q.answer()
    if await force_join(update,context):
        await q.message.reply_text("✅ تایید شو",reply_markup=main_kb())

# ================= START =================
async def start(update,context):
    uid=update.effective_user.id
    get_user(uid)

    if not await force_join(update,context): return

    if context.args:
        try:
            ref=int(context.args[0])
            if ref!=uid:
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (INVITE,ref))
                conn.commit()
        except: pass

    await update.message.reply_text("🌟 ښه راغلاست!",reply_markup=main_kb())

# ================= MAIN =================
async def handler(update,context):
    if not update.message: return
    uid=update.effective_user.id
    text=update.message.text
    get_user(uid)

    if not await force_join(update,context): return

    # حالت
    if text=="📊 حالت":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]
        name=update.effective_user.first_name

        await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {name}
💳 ایډي کارن : {uid}
💵ستاسو پيسو اندازه= {bal} AF

🔗 دعوت:
https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    # پیسې زیاتول
    elif text=="💰 پیسې زیاتول":
        await update.message.reply_text("انتخاب کړئ:",reply_markup=money_kb())

    # ټاسک
    elif text=="📋 ټاسک":
        cur.execute("SELECT username FROM task_channels")
        ch=cur.fetchall()
        if not ch:
            await update.message.reply_text("❌ نشته")
            return

        btn=[]
        for c in ch:
            btn.append([InlineKeyboardButton("Join",url=f"https://t.me/{c[0].replace('@','')}")])
        btn.append([InlineKeyboardButton("Done",callback_data="task")])

        await update.message.reply_text("ټاسک:",reply_markup=InlineKeyboardMarkup(btn))

    # بونس
    elif text=="🎁 بونس":
        await update.message.reply_text("انتخاب:",reply_markup=ReplyKeyboardMarkup([
            ["🎁 ورځنی بونس","🔥 اوونیز بونس"],["🔙 شاته"]
        ],resize_keyboard=True))

    elif text=="🎁 ورځنی بونس":
        today=str(datetime.date.today())
        cur.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        if cur.fetchone()[0]==today:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE id=?", (DAILY,today,uid))
            conn.commit()
            await update.message.reply_text("✅ ورکړل شو")

    elif text=="🔥 اوونیز بونس":
        w=str(datetime.date.today().isocalendar()[1])
        cur.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
        if cur.fetchone()[0]==w:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_weekly=? WHERE id=?", (WEEKLY,w,uid))
            conn.commit()
            await update.message.reply_text("✅ ورکړل شو")

    # ================= ADMIN =================
    elif text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel")

# ================= TASK CALLBACK =================
async def task_done(update,context):
    q=update.callback_query
    await q.answer()
    uid=q.from_user.id

    cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK,uid))
    conn.commit()
    await q.message.reply_text("🎉 reward ورکړل شو")

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(check_join,pattern="join"))
app.add_handler(CallbackQueryHandler(task_done,pattern="task"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 FINAL BOSS RUNNING...")
app.run_polling()
