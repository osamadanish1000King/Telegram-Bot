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
    else:
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

    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (INVITE,ref))
                conn.commit()

                await context.bot.send_message(ref,"🎉 نوی یوزر راغی +2 AF")
                await context.bot.send_message(ADMIN_ID,f"👤 New User: {uid}")
        except:
            pass

    await update.message.reply_text(
"""🌟 ښه راغلاست!

💰 دلته تاسو کولای شئ پیسې وګټئ:
👥 د دعوت له لارې
📋 ټاسک ترسره کولو سره
🎁 بونس اخیستلو سره

👇 پیل وکړئ""",
reply_markup=main_kb()
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

    # 📊 حالت
    if text=="📊 حالت":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]

        fake = fake_users()
        total = real + fake

        await update.message.reply_text(
f"""🤵🏻‍♂️ {update.effective_user.first_name}
🆔 {uid}

💰 بیلانس: {bal} AF

👥 ټول یوزران: {total}

🔗 لینک:
https://t.me/{BOT_USERNAME}?start={uid}

💸 هر دعوت = {INVITE} AF"""
        )

    elif text=="👥 دعوت":
        await update.message.reply_text(f"https://t.me/{BOT_USERNAME}?start={uid}")

    elif text=="💰 پیسې زیاتول":
        await update.message.reply_text("انتخاب:",reply_markup=money_kb())

    elif text=="📱 شمېره ثبت":
        await update.message.reply_text("شمېره ولیکه:")
        context.user_data["phone"]=True

    elif context.user_data.get("phone",False):
        cur.execute("UPDATE users SET phone=? WHERE id=?", (text,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه")
        context.user_data["phone"]=False

    elif text=="⚡ ایزي لوډ":
        await update.message.reply_text("✅ ثبت شو")

    elif text=="🤖 د رباټ په اړه":
        await update.message.reply_text("🤖")

    elif text=="📋 ټاسک":
        cur.execute("SELECT username FROM tasks")
        data = cur.fetchall()

        btn=[]
        for t in data:
            btn.append([InlineKeyboardButton("Join",url=f"https://t.me/{t[0].replace('@','')}")])

        btn.append([InlineKeyboardButton("Done",callback_data="task_done")])
        await update.message.reply_text("ټاسک:",reply_markup=InlineKeyboardMarkup(btn))

    elif text=="🎁 بونس":
        await update.message.reply_text("🎁",reply_markup=bonus_kb())

    # ================= ADMIN =================
    elif text=="/admin":
        if uid==ADMIN_ID:
            await update.message.reply_text("👑 Admin Panel",reply_markup=admin_kb())

    elif text=="➕ فورس چینل" and uid==ADMIN_ID:
        await update.message.reply_text("username:")
        context.user_data["add_force"]=True

    elif context.user_data.get("add_force",False):
        cur.execute("INSERT INTO channels(username) VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ اضافه شو")
        context.user_data["add_force"]=False

    elif text=="➖ فورس چینل" and uid==ADMIN_ID:
        await update.message.reply_text("username:")
        context.user_data["del_force"]=True

    elif context.user_data.get("del_force",False):
        cur.execute("DELETE FROM channels WHERE username=?", (text,))
        conn.commit()
        await update.message.reply_text("❌ حذف شو")
        context.user_data["del_force"]=False

    elif text=="➕ ټاسک چینل" and uid==ADMIN_ID:
        await update.message.reply_text("username:")
        context.user_data["add_task"]=True

    elif context.user_data.get("add_task",False):
        cur.execute("INSERT INTO tasks(username) VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ اضافه شو")
        context.user_data["add_task"]=False

    elif text=="➖ ټاسک چینل" and uid==ADMIN_ID:
        await update.message.reply_text("username:")
        context.user_data["del_task"]=True

    elif context.user_data.get("del_task",False):
        cur.execute("DELETE FROM tasks WHERE username=?", (text,))
        conn.commit()
        await update.message.reply_text("❌ حذف شو")
        context.user_data["del_task"]=False

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
app.add_handler(CallbackQueryHandler(check_join,pattern="check_join"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 FINAL ADMIN SYSTEM READY...")
app.run_polling()
