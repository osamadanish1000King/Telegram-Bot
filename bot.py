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

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, balance REAL DEFAULT 0, phone TEXT, last_daily TEXT, last_weekly TEXT, invites INTEGER DEFAULT 0)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT)")
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

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 ټول یوزران"],
        ["📢 برودکاست"],
        ["➕ فورس چینل","➖ فورس چینل"],
        ["➕ ټاسک چینل","➖ ټاسک چینل"],
        ["📋 چینلونه"],
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
    uid = update.effective_user.id

    # ❗ اډمین ته شرط نشته
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
                buttons.append([InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ چک کول", callback_data="check_join")])

        if update.message:
            await update.message.reply_text("🚨 مهرباني وکړئ ټول چینلونه جواین کړئ:",reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.callback_query.message.reply_text("🚨 چینلونه جواین کړئ:",reply_markup=InlineKeyboardMarkup(buttons))

        return False

    return True

# ================= CHECK BUTTON =================
async def check_join(update,context):
    q = update.callback_query
    await q.answer()

    if await force_join(update,context):
        await q.message.reply_text("✅ تایید شو",reply_markup=main_kb())

# ================= START =================
async def start(update,context):
    uid = update.effective_user.id
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
        except:
            pass

    await update.message.reply_text("🌟 ښه راغلاست!",reply_markup=main_kb())

# ================= ADMIN =================
async def admin_cmd(update, context):
    if update.effective_user.id == ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())
    else:
        await update.message.reply_text(f"❌ {ADMIN_USERNAME}")

# ================= MAIN =================
async def handler(update,context):

    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid)

    if not await force_join(update,context):
        return

    # 📊 حالت
    if text=="📊 حالت":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]

        await update.message.reply_text(
f"""💰 {bal} AF
👥 دعوتونه: {inv}

🔗 https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    # ================= ADMIN BUTTONS =================
    elif uid==ADMIN_ID:

        # ➕ فورس چینل
        if text=="➕ فورس چینل":
            await update.message.reply_text("یوزرنیم ولیکه (@channel):")
            context.user_data["add_f"]=True

        elif context.user_data.get("add_f"):
            cur.execute("INSERT INTO channels VALUES(?)",(text,))
            conn.commit()
            await update.message.reply_text("✅ اضافه شو")
            context.user_data["add_f"]=False

        # ➖ فورس چینل
        elif text=="➖ فورس چینل":
            cur.execute("SELECT username FROM channels")
            data = cur.fetchall()

            msg="❌ د حذف لپاره انتخاب کړه:\n"
            for i in data:
                msg+=f"{i[0]}\n"

            await update.message.reply_text(msg)
            context.user_data["del_f"]=True

        elif context.user_data.get("del_f"):
            cur.execute("DELETE FROM channels WHERE username=?",(text,))
            conn.commit()
            await update.message.reply_text("❌ حذف شو")
            context.user_data["del_f"]=False

        # ➕ ټاسک چینل
        elif text=="➕ ټاسک چینل":
            await update.message.reply_text("Task چینل ولیکه:")
            context.user_data["add_t"]=True

        elif context.user_data.get("add_t"):
            cur.execute("INSERT INTO tasks VALUES(?)",(text,))
            conn.commit()
            await update.message.reply_text("✅ Task اضافه شو")
            context.user_data["add_t"]=False

        # ➖ ټاسک چینل
        elif text=="➖ ټاسک چینل":
            cur.execute("SELECT username FROM tasks")
            data = cur.fetchall()

            msg="❌ د حذف لپاره انتخاب کړه:\n"
            for i in data:
                msg+=f"{i[0]}\n"

            await update.message.reply_text(msg)
            context.user_data["del_t"]=True

        elif context.user_data.get("del_t"):
            cur.execute("DELETE FROM tasks WHERE username=?",(text,))
            conn.commit()
            await update.message.reply_text("❌ حذف شو")
            context.user_data["del_t"]=False

        # 📋 لیست
        elif text=="📋 چینلونه":
            cur.execute("SELECT username FROM channels")
            f = cur.fetchall()

            cur.execute("SELECT username FROM tasks")
            t = cur.fetchall()

            msg="📢 Force Join:\n"
            for i in f:
                msg+=f"{i[0]}\n"

            msg+="\n📋 Task:\n"
            for i in t:
                msg+=f"{i[0]}\n"

            await update.message.reply_text(msg)

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin_cmd))
app.add_handler(CallbackQueryHandler(check_join,pattern="check_join"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 FINAL ULTRA 100% WORKING")
app.run_polling()
