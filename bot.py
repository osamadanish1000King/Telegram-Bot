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

# ===== BACKUP =====
def backup_db():
    try:
        if os.path.exists("bot.db"):
            shutil.copy("bot.db", "backup.db")
    except:
        pass
        
# ===== DB =====
# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

# USERS TABLE
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

# SETTINGS TABLE
cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

# ===== CHECK COLUMN (که مخکې جوړ شوی وي) =====
cur.execute("PRAGMA table_info(users)")
columns = [i[1] for i in cur.fetchall()]

if "task_done" not in columns:
    cur.execute("ALTER TABLE users ADD COLUMN task_done INTEGER DEFAULT 0")

conn.commit()
backup_db()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()
        backup_db()

# ===== SETTINGS =====
def set_setting(key,value):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))
    conn.commit()

def get_setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    d = cur.fetchone()
    return d[0] if d else None

# ===== FORCE JOIN =====
async def is_joined(user_id, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def force_join_btn(link):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=link)]])

# ===== TIME =====
def time_left(last,sec):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    return sec-(datetime.datetime.now()-last).total_seconds()

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
        ["📊 Stats"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = int(context.args[0]) if context.args else None
    get_user(uid,name,ref)

    if ref and ref != uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
        conn.commit()
        backup_db()

    # FORCE JOIN
    link = get_setting("force_join")
    if link and not await is_joined(uid, context.bot, link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    await update.message.reply_text("👇 انتخاب کړه",reply_markup=main_kb())

# ===== TASK DONE =====
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    cur.execute("UPDATE users SET balance=balance+1 WHERE id=?", (uid,))
    conn.commit()
    backup_db()

    await q.edit_message_text("✅ ټاسک مکمل شو +1 افغانۍ")

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text or ""# FORCE JOIN
link = get_setting("force_join")
if link and not await is_joined(uid, context.bot, link):
    await update.message.reply_text(
        "❗ مهرباني وکړه چینل جواین کړه",
        reply_markup=force_join_btn(link)
    )
    return

# 🔙 Back button
if text == "🔙 وتل":
    context.user_data["phone"] = False
    await update.message.reply_text(
        "🏠 اصلي مینو ته لاړې",
        reply_markup=main_kb()
    )
    return   # ✅ ډېر مهم


# ===== HANDLER START =====

elif text == "📢 ټاسک":
    link = get_setting("task")

    if not link:
        await update.message.reply_text("❌ ټاسک نشته")
        return

    # check task status
    cur.execute("SELECT task_done FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    done = data[0] if data else 0

    if done == 1:
    await update.message.reply_text("✅ تا مخکې دا ټاسک مکمل کړی")
    return

await update.message.reply_text(
    "📢 مهرباني وکړه ټاسک ترسره کړه 👇",
    reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 چینل", url=link)],
        [InlineKeyboardButton("✅ Done", callback_data="done_task")]
    ])
)
        
    elif text == "❗ خپل حساب معلومات":
    cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
    b,i = cur.fetchone()
    await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {b} افغانۍ
👥 دعوتونه = {i}"""
    )

elif text=="👥 ملګري دعوت کول":
    cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
    inv = cur.fetchone()[0]
    link = f"https://t.me/{BOT_USERNAME}?start={uid}"

    await update.message.reply_text(
f"""👥 ستا دعوت: {inv}

🔗 لینک:
{link}

🎁 هر دعوت = {INVITE_REWARD} افغانۍ"""
    )

elif text=="🏦 ایزیلوډ":
    cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
    bal = cur.fetchone()[0]

    if bal < 50:
        await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پکار دي")
    else:
        await update.message.reply_text("✅ درخواست واستول شو")
        await context.bot.send_message(ADMIN_ID, f"{name} | {uid} | {bal}")

elif text == "🎁 ورځنۍ بونس":
    cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
    last = cur.fetchone()[0]

    if last and time_left(last, 86400) > 0:
        await update.message.reply_text("⏳ بیا وروسته کوشش وکړه")
    else:
        cur.execute(
            "UPDATE users SET balance=balance+?, daily=? WHERE id=?",
            (DAILY_REWARD, datetime.datetime.now().isoformat(), uid)
        )
        conn.commit()
        backup_db()
        await update.message.reply_text("🎉 1 افغانۍ ترلاسه شوې")

elif text=="📊 د ربات په اړه":
    cur.execute("SELECT COUNT(*) FROM users")
    total = cur.fetchone()[0]
    fake = total + 100

    await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {fake}

🔗 {CHANNEL_LINK}
👤 {ADMIN_ID}"""
    )

elif text=="🏅 غوره دعوت کوونکي":
    cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
    data = cur.fetchall()

    if not data:
        await update.message.reply_text("❌ معلومات نشته")
        return

    msg = "🏆 غوره دعوت کوونکي:\n\n"
    for i, u in enumerate(data, 1):
        msg += f"{i}. {u[0]} - {u[1]}\n"

    await update.message.reply_text(msg)


elif text=="✏️ ستا دعوت کوونکي":
    cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
    inv = cur.fetchone()
    invites = inv[0] if inv else 0

    await update.message.reply_text(f"👥 ستا دعوتونه: {invites}")


elif text == "🎁 ورځنۍ بونس":
    cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    last = data[0] if data else None

    left = time_left(last, 86400)

    if last and left > 0:
        h = int(left//3600)
        m = int((left%3600)//60)
        await update.message.reply_text(f"⏳ پاتې وخت: {h}h {m}m")
    else:
        cur.execute(
            "UPDATE users SET balance=balance+?, daily=? WHERE id=?",
            (DAILY_REWARD, datetime.datetime.now().isoformat(), uid)
        )
        conn.commit()
        backup_db()
        await update.message.reply_text("🎉 1 افغانۍ ترلاسه شوې")


elif text == "🎁 اوونیز بونس":
    cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
    data = cur.fetchone()
    last = data[0] if data else None

    left = time_left(last, 604800)

    if last and left > 0:
        d = int(left//86400)
        h = int((left%86400)//3600)
        await update.message.reply_text(f"⏳ پاتې وخت: {d} ورځې {h} ساعت")
    else:
        cur.execute(
            "UPDATE users SET balance=balance+?, weekly=? WHERE id=?",
            (WEEKLY_REWARD, datetime.datetime.now().isoformat(), uid)
        )
        conn.commit()
        backup_db()
        await update.message.reply_text("🎉 5 افغانۍ ترلاسه شوې")
elif text=="📞 شمېره ثبت کړی":
    await update.message.reply_text("شمېره واستوه", reply_markup=phone_kb())

elif update.message.contact:
    cur.execute("UPDATE users SET phone=? WHERE id=?", (update.message.contact.phone_number,uid))
    conn.commit()
    backup_db()
    await update.message.reply_text("✅ ثبت شوه", reply_markup=main_kb())

elif text=="💰 افغانۍ زیاتول":
    await update.message.reply_text("👇 انتخاب کړه", reply_markup=invite_kb())

elif text=="🔙 وتل":
    await update.message.reply_text("🏠", reply_markup=main_kb())
    # ===== ADMIN =====
    elif text=="🔙 وتل":
    await update.message.reply_text("🏠", reply_markup=main_kb())


# ===== ADMIN =====
# ===== ADMIN =====
    if uid == ADMIN_ID and text == "/admin":
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())

    elif uid == ADMIN_ID and text == "➕ Force Join Add":
        context.user_data["f"] = True
        await update.message.reply_text("🔗 د چینل لینک راکړه")

    elif uid == ADMIN_ID and context.user_data.get("f") and text.startswith("http"):
        set_setting("force_join", text)
        conn.commit()
        backup_db()
        context.user_data["f"] = False
        await update.message.reply_text("✅ Force Join اضافه شو")

    elif uid == ADMIN_ID and text == "➖ Force Join Del":
        set_setting("force_join", "")
        conn.commit()
        backup_db()
        await update.message.reply_text("❌ حذف شو")

    elif uid == ADMIN_ID and text == "➕ Task Add":
        context.user_data["t"] = True
        await update.message.reply_text("🔗 د ټاسک لینک راکړه")

    elif uid == ADMIN_ID and context.user_data.get("t") and text.startswith("http"):
        set_setting("task", text)
        conn.commit()
        backup_db()
        context.user_data["t"] = False
        await update.message.reply_text("✅ Task اضافه شو")

    elif uid == ADMIN_ID and text == "➖ Task Del":
        set_setting("task", "")
        conn.commit()
        backup_db()
        await update.message.reply_text("❌ حذف شو")
# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(done_task, pattern="done_task"))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
