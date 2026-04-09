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
        ["💼 Set Wallet", "📋 Tasks"],
        ["🎁 Bonus", "📜 Terms"]
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
            if member.status not in ["member", "administrator", "creator"]:
                buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])
        except:
            buttons.append([InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch.replace('@','')}")])

    if buttons:
        buttons.append([InlineKeyboardButton("✅ Joined All", callback_data="check_join")])
        await update.message.reply_text("🚀 Join all required channels:", reply_markup=InlineKeyboardMarkup(buttons))
        return False

    return True

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    args = context.args
    get_user(uid)

    # Referral
    if args:
        try:
            ref = int(args[0])
            if ref != uid:
                cursor.execute("SELECT invited_by FROM users WHERE id=?", (uid,))
                if cursor.fetchone()[0] is None:
                    cursor.execute("UPDATE users SET invited_by=? WHERE id=?", (ref, uid))
                    cursor.execute("UPDATE users SET balance=balance+2 WHERE id=?", (ref,))
                    conn.commit()
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

    if await force_join(query, context):   # force_join works with callback too
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
            if member.status not in ["member", "administrator", "creator"]:
                success = False
        except:
            success = False

    if success:
        cursor.execute("UPDATE users SET balance=balance+0.3 WHERE id=?", (uid,))
        conn.commit()
        await query.message.reply_text("🎉 +0.3 ⭐ added!")
    else:
        await query.message.reply_text("❌ Join all task channels")

# ================= ADMIN PANEL =================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return await update.message.reply_text("❌ Not Admin")
    await update.message.reply_text("⚙️ Admin Panel", reply_markup=admin_kb())

# ================= MAIN HANDLER =================
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    uid = update.effective_user.id

    get_user(uid)

    if uid != ADMIN_ID:
        if not await force_join(update, context):
            return

    # ====================== ADMIN ======================
    if uid == ADMIN_ID:
        # Add Main Channel
        if text == "➕ Add Channel":
            context.user_data["add_channel"] = True
            return await update.message.reply_text("✅ @channel نوم ولیږئ")

        elif context.user_data.get("add_channel"):
            cursor.execute("INSERT INTO channels(username) VALUES(?)", (text,))
            conn.commit()
            context.user_data["add_channel"] = False
            return await update.message.reply_text("✅ Channel اضافه شو!", reply_markup=admin_kb())

        # Delete Main Channel
        elif text == "➖ Delete Channel":
            context.user_data["del_channel"] = True
            return await update.message.reply_text("✅ @channel نوم ولیږئ")

        elif context.user_data.get("del_channel"):
            cursor.execute("DELETE FROM channels WHERE username=?", (text,))
            conn.commit()
            context.user_data["del_channel"] = False
            return await update.message.reply_text("✅ Channel حذف شو!", reply_markup=admin_kb())

        # Add Task Channel
        elif text == "➕ Add Task Channel":
            context.user_data["add_task"] = True
            return await update.message.reply_text("✅ @channel نوم ولیږئ")

        elif context.user_data.get("add_task"):
            cursor.execute("INSERT INTO task_channels(username) VALUES(?)", (text,))
            conn.commit()
            context.user_data["add_task"] = False
            return await update.message.reply_text("✅ Task Channel اضافه شو!", reply_markup=admin_kb())

        # Delete Task Channel
        elif text == "➖ Delete Task Channel":
            context.user_data["del_task"] = True
            return await update.message.reply_text("✅ @channel نوم ولیږئ")

        elif context.user_data.get("del_task"):
            cursor.execute("DELETE FROM task_channels WHERE username=?", (text,))
            conn.commit()
            context.user_data["del_task"] = False
            return await update.message.reply_text("✅ Task Channel حذف شو!", reply_markup=admin_kb())

        # Users
        elif text == "👥 Users":
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            await update.message.reply_text(f"📊 ټول استعمالوونکي: **{total}**", parse_mode='Markdown')

        # Stats
        elif text == "📊 Stats":
            cursor.execute("SELECT COUNT(*), SUM(balance) FROM users")
            data = cursor.fetchone()
            await update.message.reply_text(f"""
📊 **بوټ سټیټس:**
👥 ټول کارونکي: {data[0]}
🌟 ټول سټار: {data[1]:.2f}
""", parse_mode='Markdown')

        # Broadcast
        elif text == "📢 Broadcast":
            context.user_data["broadcast"] = True
            return await update.message.reply_text("📢 پیام ولیږئ چې ټولو ته واستول شي:")

        elif context.user_data.get("broadcast"):
            context.user_data["broadcast"] = False
            cursor.execute("SELECT id FROM users")
            users = cursor.fetchall()
            sent = 0
            for user in users:
                try:
                    await context.bot.send_message(user[0], text)
                    sent += 1
                except:
                    pass
            return await update.message.reply_text(f"✅ پیام {sent} کارونکو ته واستول شو!", reply_markup=admin_kb())

        # Withdraw Requests
        elif text == "💸 Withdraw Requests":
            cursor.execute("SELECT * FROM withdrawals WHERE status='Pending'")
            reqs = cursor.fetchall()
            if not reqs:
                return await update.message.reply_text("✅ هیڅ واپسي درخواست نشته")
            for req in reqs:
                await update.message.reply_text(f"""
🆔 درخواست ID: {req[0]}
👤 User ID: {req[1]}
💰 اندازه: {req[2]} ⭐
📍 والټ: {req[3]}

کېښکاره کړئ: /approve_{req[0]}
""")

        elif text.startswith("/approve_"):
            try:
                wid = int(text.split("_")[1])
                cursor.execute("UPDATE withdrawals SET status='Approved' WHERE id=?", (wid,))
                conn.commit()
                await update.message.reply_text(f"✅ درخواست {wid} منظور شو!")
            except:
                pass

        return   # Admin لپاره دلته پای

    # ====================== USER MENU ======================
    if text == "📊 Statistics":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]
        await update.message.reply_text(f"""
🤵🏻‍♂️ نوم: {update.effective_user.full_name}
💳 ID: {uid}
🌟 بالانس: **{bal:.2f} ⭐**
""", parse_mode='Markdown')

    elif text == "💰 Balance":
        cursor.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cursor.fetchone()[0]
        await update.message.reply_text(f"💰 ستاسو بالانس:\n\n**{bal:.2f} ⭐**", parse_mode='Markdown')

    elif text == "👥 Referral":
        ref_link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"""
👥 ستاسو ريفرل لنک:

{ref_link}

🔹 هر ريفرل = +2 ⭐
""")

    elif text == "💼 Set Wallet":
        context.user_data["set_wallet"] = True
        await update.message.reply_text("💼 خپل USDT (TRC20) والټ آدرس ولیږئ:")

    elif context.user_data.get("set_wallet"):
        cursor.execute("UPDATE users SET wallet=? WHERE id=?", (text.strip(), uid))
        conn.commit()
        context.user_data["set_wallet"] = False
        await update.message.reply_text("✅ والټ په بریالیتوب سره سیټ شو!")

    elif text == "🎁 Bonus":
        today = datetime.date.today().isoformat()
        cursor.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        last = cursor.fetchone()[0]

        if last != today:
            cursor.execute("UPDATE users SET balance = balance + 0.5, last_daily = ? WHERE id=?", (today, uid))
            conn.commit()
            await update.message.reply_text("🎉 تاسو 0.5 ⭐ واخیستل!")
        else:
            await update.message.reply_text("❌ تاسو نن ورځ بونس اخیستی دی")

    elif text == "💸 Withdraw":
        cursor.execute("SELECT balance, wallet FROM users WHERE id=?", (uid,))
        data = cursor.fetchone()
        balance = data[0]
        wallet = data[1]

        if balance < 20:
            await update.message.reply_text("❌ حداقل 20 ⭐ ته اړتیا ده")
        elif not wallet:
            await update.message.reply_text("❌ لومړی والټ سیټ کړئ → 💼 Set Wallet")
        else:
            context.user_data["withdraw_amount"] = True
            await update.message.reply_text(f"""
💸 واپسي درخواست

ستاسو بالانس: **{balance:.2f} ⭐**
والټ: `{wallet}`

د واپسۍ اندازه ولیکئ (حداقل 20):
""", parse_mode='Markdown')

    elif context.user_data.get("withdraw_amount"):
        try:
            amount = float(text)
            if amount < 20:
                return await update.message.reply_text("❌ حداقل 20 ⭐")

            cursor.execute("SELECT balance, wallet FROM users WHERE id=?", (uid,))
            bal, wallet = cursor.fetchone()

            if amount > bal:
                return await update.message.reply_text("❌ کافی بالانس نشته")

            cursor.execute("""
                INSERT INTO withdrawals (user_id, amount, phone, status, date)
                VALUES (?, ?, ?, 'Pending', ?)
            """, (uid, amount, wallet, datetime.datetime.now().isoformat()))
            
            cursor.execute("UPDATE users SET balance = balance - ? WHERE id=?", (amount, uid))
            conn.commit()

            context.user_data["withdraw_amount"] = False
            await update.message.reply_text("✅ ستاسو واپسي درخواست ثبت شو! Admin به ژر چیک کړي.")
        except:
            await update.message.reply_text("❌ سم شمېره ولیکئ")

    elif text == "📋 Tasks":
        cursor.execute("SELECT username FROM task_channels")
        channels = cursor.fetchall()

        if not channels:
            return await update.message.reply_text("❌ اوس مهال کوم ټاسک نشته")

        buttons = [[InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch[0].replace('@','')}")] for ch in channels]
        buttons.append([InlineKeyboardButton("✅ Check Tasks", callback_data="check_tasks")])

        await update.message.reply_text("📋 ټاسکونه بشپړ کړئ:", reply_markup=InlineKeyboardMarkup(buttons))

    elif text == "📜 Terms":
        await update.message.reply_text("📜 Terms & Conditions:\n\n• Minimum withdraw 20 stars\n• Only TRC20 USDT wallet\n• No cheating allowed\n• Admin decision is final")

# ================= RUN BOT =================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", admin_panel))
app.add_handler(CallbackQueryHandler(check_join, pattern="check_join"))
app.add_handler(CallbackQueryHandler(check_tasks, pattern="check_tasks"))
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handler))

print("✅ BOT RUNNING...")
app.run_polling()
