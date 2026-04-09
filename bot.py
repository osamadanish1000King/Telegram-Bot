import sqlite3
import datetime
from telegram import *
from telegram.ext import *

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
phone TEXT,
wallet TEXT,
invited_by INTEGER,
last_daily TEXT,
last_weekly TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdrawals(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
amount REAL,
phone TEXT,
status TEXT,
date TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT
)
""")

# ✅ NEW TASK CHANNEL TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS task_channels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT
)
""")

conn.commit()

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 Statistics"],
        ["👥 Referral", "💰 Balance", "🎁 Bonus"],
        ["💼 Set Wallet", "💸 Withdraw"],
        ["📋 Tasks", "📜 Terms"]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 Users", "📊 Stats"],
        ["📢 Broadcast", "💸 Withdraw Requests"],
        ["➕ Add Channel", "➖ Delete Channel"],
        ["➕ Add Task Channel", "➖ Delete Task Channel"],
        ["🔙 Back"]
    ], resize_keyboard=True)

# ================= USER =================
def get_user(uid):
    cursor.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO users(id) VALUES(?)", (uid,))
        conn.commit()

# ================= FORCE JOIN =================
async def force_join(update, context):
    cursor.execute("SELECT username FROM channels")
    channels = cursor.fetchall()

    if not channels:
        return True

    uid = update.effective_user.id
    buttons = []

    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member","administrator","creator"]:
                buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ Joined All", callback_data="check_join")])
        await update.message.reply_text(
            "🚀 Join all required channels:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        return False

    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    get_user(uid)

    # Referral
    if args:
        ref = int(args[0])
        if ref != uid:
            cursor.execute("SELECT invited_by FROM users WHERE id=?", (uid,))
            if cursor.fetchone()[0] is None:
                cursor.execute("UPDATE users SET invited_by=? WHERE id=?", (ref, uid))
                cursor.execute("UPDATE users SET balance=balance+2 WHERE id=?", (ref,))
                conn.commit()
                try:
                    await context.bot.send_message(ref, "🎉 New referral joined! +2 ⭐")
                except:
                    pass

    if not await force_join(update, context):
        return

    await update.message.reply_text(
"""🎉 Earn Stars Easily!

💰 Invite = 2 ⭐
🎁 Daily = 0.5 ⭐
🔥 Weekly = 2 ⭐
💸 Withdraw = 20 ⭐

👇 Use menu:""",
        reply_markup=main_kb()
    )

# ================= CHECK JOIN =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await force_join(query, context):
        await query.message.reply_text("✅ Verified!", reply_markup=main_kb())

# ================= TASK SYSTEM =================
async def check_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    cursor.execute("SELECT username FROM task_channels")
    channels = cursor.fetchall()

    success = True

    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member","administrator","creator"]:
                success = False
        except:
            success = False

    if success:
        cursor.execute("UPDATE users SET balance=balance+0.3 WHERE id=?", (uid,))
        conn.commit()
        await query.message.reply_text("🎉 +0.3 ⭐ added!")
    else:
        await query.message.reply_text("❌ Join all task channels")

# ================= ADMIN =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not Admin")
    await update.message.reply_text("⚙️ Admin Panel", reply_markup=admin_kb())

# ================= HANDLER =================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    get_user(uid)

    if uid != ADMIN_ID:
        if not await force_join(update, context):
            return

    # ===== ADMIN =====
    if uid == ADMIN_ID:

        if text == "➕ Add Task Channel":
            context.user_data["add_task"] = True
            await update.message.reply_text("Send @channel")

        elif context.user_data.get("add_task"):
            cursor.execute("INSERT INTO task_channels(username) VALUES(?)", (text,))
            conn.commit()
            context.user_data["add_task"] = False
            await update.message.reply_text("✅ Added", reply_markup=admin_kb())

        elif text == "➖ Delete Task Channel":
            context.user_data["del_task"] = True
            await update.message.reply_text("Send channel")

        elif context.user_data.get("del_task"):
            cursor.execute("DELETE FROM task_channels WHERE username=?", (text,))
            conn.commit()
            context.user_data["del_task"] = False
            await update.message.reply_text("✅ Deleted", reply_markup=admin_kb())

    # ===== USER =====
    if text == "📋 Tasks":
        cursor.execute("SELECT username FROM task_channels")
        channels = cursor.fetchall()

        if not channels:
            await update.message.reply_text("❌ No tasks available")
            return

        buttons = []
        for ch in channels:
            ch = ch[0]
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])

        buttons.append([InlineKeyboardButton("✅ Check Tasks", callback_data="check_tasks")])

        await update.message.reply_text(
            "📋 Complete tasks:",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    if text == "📊 Statistics":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        row = cursor.fetchone()
        balance = row[0] if row else 0
        name = update.effective_user.first_name or "User"
        await update.message.reply_text(
f"""🤵🏻‍♂️استعمالوونکی = {name}

💳 ایډي کارن : {uid}
🌟ستاسو دسټاراندازه= {balance}

🔗 د بیلانس زیاتولو لپاره  [ 👫 کسان ] دعوت کړی،""",
            reply_markup=main_kb()
        )

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(CallbackQueryHandler(check_tasks, pattern="check_tasks"))
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handler))

print("✅ BOT RUNNING...")
app.run_polling()
