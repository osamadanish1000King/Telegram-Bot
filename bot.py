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
        ["📋 ټاسک"],
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
            await update.message.reply_text("🚨 چینلونه جواین کړه:",reply_markup=InlineKeyboardMarkup(buttons))
        else:
            await update.callback_query.message.reply_text("🚨 چینلونه جواین کړه:",reply_markup=InlineKeyboardMarkup(buttons))

        return False

    return True

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

# ================= TASK SYSTEM =================
async def show_tasks(update,context):
    uid = update.effective_user.id

    cur.execute("SELECT username FROM tasks")
    tasks = cur.fetchall()

    if not tasks:
        await update.message.reply_text("❌ ټاسک نشته")
        return

    buttons = []

    for t in tasks:
        ch = t[0]
        buttons.append([
            InlineKeyboardButton(f"📢 {ch}", url=f"https://t.me/{ch.replace('@','')}"),
            InlineKeyboardButton("✅ واخیستل", callback_data=f"task_{ch}")
        ])

    await update.message.reply_text("📋 ټاسکونه:",reply_markup=InlineKeyboardMarkup(buttons))

async def task_done(update,context):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK_REWARD,uid))
    conn.commit()

    await q.message.reply_text(f"🎉 {TASK_REWARD} AF اضافه شول")

# ================= BROADCAST =================
async def broadcast(update,context):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("✉️ پیغام ولیکه:")
    context.user_data["bc"]=True

async def send_bc(update,context):
    if context.user_data.get("bc"):
        cur.execute("SELECT id FROM users")
        users = cur.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0], update.message.text)
            except:
                pass

        await update.message.reply_text("✅ واستول شو")
        context.user_data["bc"]=False

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
        real = cur.fetchone()[0]

        if uid == ADMIN_ID:
            total = real
        else:
            total = real + 100

        await update.message.reply_text(
f"""💰 {bal} AF
👥 دعوتونه: {inv}
👥 ټول یوزران: {total}

🔗 https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    # 👥 دعوت
    elif text=="👥 دعوت":
        await update.message.reply_text(f"https://t.me/{BOT_USERNAME}?start={uid}")

    # 📋 TASK
    elif text=="📋 ټاسک":
        await show_tasks(update,context)

    # ================= ADMIN =================
    elif uid==ADMIN_ID:

        if text=="👥 ټول یوزران":
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            await update.message.reply_text(f"👥 Real Users: {count}")

        elif text=="📢 برودکاست":
            await broadcast(update,context)

        elif context.user_data.get("bc"):
            await send_bc(update,context)

        elif text=="➕ فورس چینل":
            await update.message.reply_text("یوزرنیم:")
            context.user_data["add_f"]=True

        elif context.user_data.get("add_f"):
            cur.execute("INSERT INTO channels VALUES(?)",(text,))
            conn.commit()
            await update.message.reply_text("✅ اضافه شو")
            context.user_data["add_f"]=False

        elif text=="➖ فورس چینل":
            await update.message.reply_text("یوزرنیم:")
            context.user_data["del_f"]=True

        elif context.user_data.get("del_f"):
            cur.execute("DELETE FROM channels WHERE username=?",(text,))
            conn.commit()
            await update.message.reply_text("❌ حذف شو")
            context.user_data["del_f"]=False

        elif text=="➕ ټاسک چینل":
            await update.message.reply_text("Task چینل:")
            context.user_data["add_t"]=True

        elif context.user_data.get("add_t"):
            cur.execute("INSERT INTO tasks VALUES(?)",(text,))
            conn.commit()
            await update.message.reply_text("✅ اضافه شو")
            context.user_data["add_t"]=False

        elif text=="➖ ټاسک چینل":
            await update.message.reply_text("یوزرنیم:")
            context.user_data["del_t"]=True

        elif context.user_data.get("del_t"):
            cur.execute("DELETE FROM tasks WHERE username=?",(text,))
            conn.commit()
            await update.message.reply_text("❌ حذف شو")
            context.user_data["del_t"]=False

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
app.add_handler(CallbackQueryHandler(task_done,pattern="task_"))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 LEVEL 10 FULL BOT READY")
app.run_polling()
