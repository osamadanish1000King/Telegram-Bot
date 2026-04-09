import sqlite3
import datetime
from telegram import *
from telegram.ext import *

# ================= CONFIG =================
TOKEN = "8279973060:AAGp9bxREyPd29xzv85mcWvTA33WIltyi3A"
ADMIN_ID = 8289491009
BOT_USERNAME = "Afghan_starbot"

# ================= DATABASE =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
balance REAL DEFAULT 0,
invited_by INTEGER,
last_daily TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS channels(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT
)
""")

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
        ["📊 Statistics", "💸 Withdraw"],
        ["👥 Referral", "💰 Balance"],
        ["💼 Wallet", "📋 Tasks"],
        ["🎁 Bonus", "📜 Terms"]
    ], resize_keyboard=True)

# ================= HELPER =================
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
            if member.status not in ["member", "administrator", "creator"]:
                buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ Joined", callback_data="check_join")])

        if update.message:
            await update.message.reply_text("🚀 Join channels first:", reply_markup=InlineKeyboardMarkup(buttons))
        elif update.callback_query:
            await update.callback_query.message.reply_text("🚀 Join channels first:", reply_markup=InlineKeyboardMarkup(buttons))

        return False

    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    get_user(uid)

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cursor.execute("SELECT invited_by FROM users WHERE id=?", (uid,))
                if cursor.fetchone()[0] is None:
                    cursor.execute("UPDATE users SET invited_by=? WHERE id=?", (ref, uid))
                    cursor.execute("UPDATE users SET balance=balance+2 WHERE id=?", (ref,))
                    conn.commit()
        except:
            pass

    if not await force_join(update, context):
        return

    await update.message.reply_text("🎉 Welcome!\nEarn stars easily ⭐", reply_markup=main_kb())

# ================= CALLBACK =================
async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if await force_join(update, context):
        await query.message.reply_text("✅ Verified!", reply_markup=main_kb())

# ================= MAIN HANDLER =================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    text = update.message.text
    uid = update.effective_user.id
    get_user(uid)

    if not await force_join(update, context):
        return

    # ================= BUTTONS =================
    if text == "📊 Statistics":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]
        await update.message.reply_text(f"⭐ Balance: {bal:.2f}")

    elif text == "💰 Balance":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]
        await update.message.reply_text(f"💰 {bal:.2f} ⭐")

    elif text == "👥 Referral":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"Invite link:\n{link}\n\n+2⭐ per user")

    elif text == "💸 Withdraw":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]

        if bal < 20:
            await update.message.reply_text("❌ Minimum 20⭐ required")
        else:
            await update.message.reply_text("✅ Withdraw request sent (demo)")

    elif text == "📋 Tasks":
        cursor.execute("SELECT username FROM task_channels")
        channels = cursor.fetchall()

        if not channels:
            await update.message.reply_text("No tasks now")
            return

        buttons = []
        for ch in channels:
            buttons.append([InlineKeyboardButton("Join Task", url=f"https://t.me/{ch[0].replace('@','')}")])

        buttons.append([InlineKeyboardButton("✅ Done", callback_data="task_done")])

        await update.message.reply_text("📋 Complete tasks:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "🎁 Bonus":
        today = str(datetime.date.today())

        cursor.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        last = cursor.fetchone()[0]

        if last == today:
            await update.message.reply_text("❌ Already claimed today")
        else:
            cursor.execute("UPDATE users SET balance=balance+0.5, last_daily=? WHERE id=?", (today, uid))
            conn.commit()
            await update.message.reply_text("🎁 +0.5⭐ added")

    elif text == "💼 Wallet":
        await update.message.reply_text("Send your wallet address (demo)")

    elif text == "📜 Terms":
        await update.message.reply_text("📜 Basic rules: no spam, real users only")

# ================= TASK CHECK =================
async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id

    cursor.execute("SELECT username FROM task_channels")
    channels = cursor.fetchall()

    ok = True
    for ch in channels:
        try:
            member = await context.bot.get_chat_member(ch[0], uid)
            if member.status not in ["member", "administrator", "creator"]:
                ok = False
        except:
            ok = False

    if ok:
        cursor.execute("UPDATE users SET balance=balance+0.3 WHERE id=?", (uid,))
        conn.commit()
        await query.message.reply_text("🎉 +0.3⭐ added")
    else:
        await query.message.reply_text("❌ Join all first")

# ================= RUN =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(CallbackQueryHandler(task_done, pattern="task_done"))

# ✅ FIXED LINE (NO ERROR)
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handler))

print("✅ BOT RUNNING...")
app.run_polling()
