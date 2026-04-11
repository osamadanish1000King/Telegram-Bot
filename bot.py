import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"
ADMIN_ID = 8289491009
BOT_USERNAME = "earn_freeafghani_bot"

DAILY = 0.5
WEEKLY = 5
INVITE = 2
TASK_REWARD = 0.3

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, invites INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS done(uid INTEGER, channel TEXT)")
conn.commit()

# ================= USER =================
def get_user(uid):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id) VALUES(?)",(uid,))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update,context):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        return True

    cur.execute("SELECT username FROM channels")
    channels = cur.fetchall()

    if not channels:
        return True

    buttons = []

    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member","administrator","creator"]:
                buttons.append([InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ چک کول", callback_data="check_join")])
        await update.message.reply_text("🚨 چینلونه جواین کړه:",reply_markup=InlineKeyboardMarkup(buttons))
        return False

    return True

async def check_join(update,context):
    q = update.callback_query
    await q.answer()

    if await force_join(update,context):
        await q.message.reply_text("✅ تایید شو")

# ================= START =================
async def start(update,context):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    get_user(uid)

    if not await force_join(update,context):
        return

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+?, invites=invites+1 WHERE id=?", (INVITE,ref))
                conn.commit()

                # ✅ message to inviter
                try:
                    await context.bot.send_message(ref, f"🎉 مبارک! یو نوی یوزر دې راوست\n💰 {INVITE} AF اضافه شول")
                except:
                    pass
        except:
            pass

    # ✅ message to admin
    try:
        await context.bot.send_message(ADMIN_ID, f"👤 نوی یوزر راغی:\n🆔 {uid}\n👤 {name}")
    except:
        pass

    await update.message.reply_text("🌟 ښه راغلاست!")

# ================= TASK =================
async def show_tasks(update,context):
    cur.execute("SELECT username FROM tasks")
    tasks = cur.fetchall()

    if not tasks:
        await update.message.reply_text("❌ ټاسک نشته")
        return

    buttons=[]

    for t in tasks:
        ch=t[0]
        buttons.append([
            InlineKeyboardButton(ch, url=f"https://t.me/{ch.replace('@','')}"),
            InlineKeyboardButton("✅ واخیستل", callback_data=f"task_{ch}")
        ])

    await update.message.reply_text("📋 ټاسک:",reply_markup=InlineKeyboardMarkup(buttons))

async def task_done(update,context):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    ch = q.data.replace("task_","")

    cur.execute("SELECT * FROM done WHERE uid=? AND channel=?", (uid,ch))
    if cur.fetchone():
        await q.message.reply_text("❌ مخکې اخیستل شوی")
        return

    cur.execute("INSERT INTO done VALUES(?,?)",(uid,ch))
    cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK_REWARD,uid))
    conn.commit()

    await q.message.reply_text(f"✅ {TASK_REWARD} AF اضافه شول")

# ================= ADMIN =================
async def admin(update,context):
    if update.effective_user.id != ADMIN_ID:
        return

    text = update.message.text.strip()
    text = text.replace("https://t.me/","@")

    if context.user_data.get("add_f"):
        cur.execute("INSERT INTO channels VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ اضافه شو")
        context.user_data["add_f"]=False

    elif context.user_data.get("add_t"):
        cur.execute("INSERT INTO tasks VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ ټاسک اضافه شو")
        context.user_data["add_t"]=False

# ================= MAIN =================
async def handler(update,context):

    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid)

    if not await force_join(update,context):
        return

    if text=="📊 حالت":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]

        fake = real + 100

        if uid == ADMIN_ID:
            total = real
        else:
            total = fake

        await update.message.reply_text(f"💰 {bal}\n👥 {total}\n👥 دعوت: {inv}")

    elif text=="📋 ټاسک":
        await show_tasks(update,context)

    if uid == ADMIN_ID:

        if text=="➕ فورس چینل":
            context.user_data["add_f"]=True
            await update.message.reply_text("چینل ولیکه")

        elif text=="➕ ټاسک چینل":
            context.user_data["add_t"]=True
            await update.message.reply_text("ټاسک ولیکه")

        elif text=="📋 چینلونه":
            cur.execute("SELECT username FROM channels")
            f=cur.fetchall()

            cur.execute("SELECT username FROM tasks")
            t=cur.fetchall()

            msg="Force:\n"
            for i in f:
                msg+=i[0]+"\n"

            msg+="\nTask:\n"
            for i in t:
                msg+=i[0]+"\n"

            await update.message.reply_text(msg)

        await admin(update,context)

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(check_join,pattern="check_join"))
app.add_handler(CallbackQueryHandler(task_done,pattern="task_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 FINAL 100% WORKING")
app.run_polling()
