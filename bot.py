import sqlite3
import datetime
import shutil
import os
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
DAILY_REWARD = 1
WEEKLY_REWARD = 5

# ===== AUTO RESTORE =====
if not os.path.exists("bot.db") and os.path.exists("backup.db"):
    shutil.copy("backup.db", "bot.db")

def backup_db():
    try:
        shutil.copy("bot.db", "backup.db")
    except:
        pass

# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 0,
    invites INTEGER DEFAULT 0,
    ref INTEGER,
    phone TEXT,
    daily TEXT,
    weekly TEXT,
    task_done INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# ===== USER =====
def get_user(uid, name, ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)", (uid, name, ref))
        conn.commit()

# ===== SETTINGS =====
def set_setting(k, v):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
    conn.commit()

def get_setting(k):
    cur.execute("SELECT value FROM settings WHERE key=?", (k,))
    d = cur.fetchone()
    return d[0] if d else None

# ===== TIME =====
def time_left(last, sec):
    if not last:
        return 0
    last = datetime.datetime.fromisoformat(last)
    return sec - (datetime.datetime.now() - last).total_seconds()

# ===== FORCE JOIN =====
async def is_joined(uid, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, uid)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def force_join_btn(link):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=link)]])

# ===== KEYBOARDS =====
def main_kb():
    return ReplyKeyboardMarkup([
        ["❗ خپل حساب معلومات"],
        ["📞 شمېره ثبت کړی"],
        ["💰 افغانۍ زیاتول","🏦 ایزیلوډ"],
        ["📊 د ربات په اړه"]
    ],resize_keyboard=True)

def invite_kb():
    return ReplyKeyboardMarkup([
        ["🏅 غوره دعوت کوونکي","✏️ ستا دعوت کوونکي"],
        ["🎁 ورځنۍ بونس","🎁 اوونیز بونس"],
        ["👥 ملګري دعوت کول"],
        ["📢 ټاسک"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

def phone_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📲 شمېره واستوه",request_contact=True)],
        ["🔙 وتل"]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 Broadcast"],
        ["➕ Force Join Add","➖ Force Join Del"],
        ["➕ Task Add","➖ Task Del"],
        ["♻️ Task Reset"],
        ["📊 Stats"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = int(context.args[0]) if context.args else None
    get_user(uid, name, ref)

    if ref and ref != uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?", (INVITE_REWARD, ref))
        conn.commit()

    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    await update.message.reply_text("""🌟 ښه راغلاست ګرانه کاروونکي! 👋

💸 دلته ته کولی شې ډېري په اسانۍ سره افغانۍ وګټې!

🎯 څنګه کار کوي؟
👥 ملګري دعوت کړه
🎁 بونسونه ترلاسه کړه
📢 ټاسکونه ترسره کړه

💰 هر دعوت = جایزه
🎁 ورځنۍ او اوونیز بونس هم شته!

🚀 همدا اوس پیل کړه او عاید جوړ کړه 👇

👇 له مینو څخه یو انتخاب وکړه""",reply_markup=main_kb())

# ===== TASK DONE =====
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    cur.execute("UPDATE users SET balance=balance+1, task_done=1 WHERE id=?", (uid,))
    conn.commit()

    await q.edit_message_text("✅ ټاسک مکمل شو +1 افغانۍ")

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text or ""

    # BACK
    if text == "🔙 وتل":
        await update.message.reply_text("🏠 اصلي مینو ته لاړې", reply_markup=main_kb())
        return

    # ===== ADMIN PANEL =====
    if uid == ADMIN_ID and text == "/admin":
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())
        return

    # FORCE JOIN ADD
    if uid == ADMIN_ID and text == "➕ Force Join Add":
        context.user_data["f"] = True
        await update.message.reply_text("🔗 د چینل لینک راکړه")
        return

    if uid == ADMIN_ID and context.user_data.get("f") and text.startswith("http"):
        set_setting("force_join", text)
        context.user_data["f"] = False
        await update.message.reply_text("✅ Force Join اضافه شو")
        return

    if uid == ADMIN_ID and text == "➖ Force Join Del":
        set_setting("force_join", "")
        await update.message.reply_text("❌ حذف شو")
        return

    # TASK ADD
    if uid == ADMIN_ID and text == "➕ Task Add":
        context.user_data["t"] = True
        await update.message.reply_text("🔗 د ټاسک لینک راکړه")
        return

    if uid == ADMIN_ID and context.user_data.get("t") and text.startswith("http"):
        set_setting("task", text)
        context.user_data["t"] = False
        await update.message.reply_text("✅ Task اضافه شو")
        return

    if uid == ADMIN_ID and text == "➖ Task Del":
        set_setting("task", "")
        await update.message.reply_text("❌ حذف شو")
        return

    # TASK RESET
    if uid == ADMIN_ID and text == "♻️ Task Reset":
        cur.execute("UPDATE users SET task_done=0")
        conn.commit()
        await update.message.reply_text("✅ ټول ټاسکونه ریست شول")
        return

    # BROADCAST
    if uid == ADMIN_ID and text == "📢 Broadcast":
        context.user_data["broadcast"] = True
        await update.message.reply_text("✉️ مسيج راولیږه")
        return

    if uid == ADMIN_ID and context.user_data.get("broadcast"):
        msg = text
        context.user_data["broadcast"] = False

        cur.execute("SELECT id FROM users")
        users = cur.fetchall()

        sent = 0
        for u in users:
            try:
                await context.bot.send_message(u[0], msg)
                sent += 1
            except:
                pass

        await update.message.reply_text(f"✅ واستول شو: {sent}")
        return

    # FORCE JOIN CHECK
    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    # ===== USER SECTION =====
    if text == "📢 ټاسک":
    ...

elif text == "❗ خپل حساب معلومات":
    ...

elif text == "💰 افغانۍ زیاتول":
    await update.message.reply_text("👇 انتخاب کړه", reply_markup=invite_kb())

elif text == "🏅 غوره دعوت کوونکي":
    cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
    data = cur.fetchall()

    if not data:
        await update.message.reply_text("❌ معلومات نشته")
        return

    msg = "🏆 غوره دعوت کوونکي:\n\n"
    for i, u in enumerate(data, 1):
        msg += f"{i}. {u[0]} - {u[1]}\n"

    await update.message.reply_text(msg)

elif text == "✏️ ستا دعوت کوونکي":
    cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    invites = data[0] if data else 0

    await update.message.reply_text(f"👥 ستا دعوتونه: {invites}")

elif text == "🎁 ورځنۍ بونس":
    cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    last = data[0] if data else None

    left = time_left(last, 86400)

    if last and left > 0:
        h = int(left // 3600)
        m = int((left % 3600) // 60)
        await update.message.reply_text(f"⏳ پاتې وخت: {h}h {m}m")
    else:
        cur.execute(
            "UPDATE users SET balance=balance+?, daily=? WHERE id=?",
            (DAILY_REWARD, datetime.datetime.now().isoformat(), uid)
        )
        conn.commit()
        await update.message.reply_text("🎉 1 افغانۍ ترلاسه شوې")

elif text == "🎁 اوونیز بونس":
    cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    last = data[0] if data else None

    left = time_left(last, 604800)

    if last and left > 0:
        d = int(left // 86400)
        h = int((left % 86400) // 3600)
        await update.message.reply_text(f"⏳ پاتې وخت: {d} ورځې {h} ساعت")
    else:
        cur.execute(
            "UPDATE users SET balance=balance+?, weekly=? WHERE id=?",
            (WEEKLY_REWARD, datetime.datetime.now().isoformat(), uid)
        )
        conn.commit()
        await update.message.reply_text("🎉 5 افغانۍ ترلاسه شوې")

elif text == "📊 د ربات په اړه":
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]

    await update.message.reply_text(f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}
👤 {ADMIN_ID}""")

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(done_task, pattern="done_task"))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
