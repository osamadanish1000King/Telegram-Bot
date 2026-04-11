import sqlite3
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
DAILY_REWARD = 1
WEEKLY_REWARD = 5

# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
balance REAL DEFAULT 0,
invites INTEGER DEFAULT 0,
ref INTEGER,
phone TEXT,
daily TEXT,
weekly TEXT)""")

cur.execute("""CREATE TABLE IF NOT EXISTS settings(
key TEXT PRIMARY KEY,
value TEXT)""")

conn.commit()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()

# ===== SETTINGS =====
def set_setting(key,value):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)",(key,value))
    conn.commit()

def get_setting(key):
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    data = cur.fetchone()
    return data[0] if data else None

# ===== TIME =====
def time_left(last,seconds):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    now=datetime.datetime.now()
    return seconds-(now-last).total_seconds()

def format_time(sec):
    sec=int(sec)
    h=sec//3600
    m=(sec%3600)//60
    s=sec%60
    return f"{h}:{m}:{s}"

# ===== KEYBOARD =====
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

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except:
            ref = None

    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    exists = cur.fetchone()

    if not exists:
        get_user(uid, name, ref)

        if ref and ref != uid:
            cur.execute(
                "UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",
                (INVITE_REWARD, ref)
            )
            conn.commit()

            await context.bot.send_message(
                ref,
                "🎉 یو کس دې راوست\n💰 4 افغانۍ اضافه شوه"
            )

    await context.bot.send_message(
        ADMIN_ID,
        f"👤 نوی یوزر:\n{name}\n{uid}"
    )

    await update.message.reply_text(
        "👇 له مینو څخه یو انتخاب وکړه",
        reply_markup=main_kb()
    )

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid, name)

    text = update.message.text if update.message.text else ""

    # ===== FORCE JOIN CHECK =====
    link = get_setting("force_join") 
    if link:
        joined = await is_joined(uid, context.bot, link)
        if not joined:
            await update.message.reply_text(
                "❗ مهرباني وکړه چینل جواین کړه",
                reply_markup=force_join_btn(link)
            )
            return

# ===== TASK =====
if text == "📢 ټاسک":
    link = get_setting("task")

    if not link:
        await update.message.reply_text("❌ ټاسک نشته")
        return

    await update.message.reply_text(
        "📢 مهرباني وکړه ټاسک ترسره کړه 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 چینل", url=link)],
            [InlineKeyboardButton("✅ Done", callback_data="done_task")]
        ])
    )

# ===== USER INFO =====
    # ===== USER INFO =====
    elif text == "❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        data = cur.fetchone()

        balance = data[0] if data else 0
        invites = data[1] if data else 0

        await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {balance} افغانۍ
👥 دعوتونه = {invites}"""
        )

    
    # ===== INVITE =====
    elif text == "👥 ملګري دعوت کول":
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        invites = cur.fetchone()[0]

        link = f"https://t.me/{BOT_USERNAME}?start={uid}"

        await update.message.reply_text(
f"""👥 ستا دعوت: {invites}

🔗 لینک:
{link}

🎁 هر دعوت = {INVITE_REWARD} افغانۍ"""
        )

    # ===== EASYLOAD =====
    elif text == "🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        balance = cur.fetchone()[0]

        if balance < 50:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پکار دي")
        else:
            await update.message.reply_text(
f"""💳 د ایزیلوډ غوښتنه ثبت شوه

👤 {name}
🆔 {uid}
💰 {balance} AFN

⏳ مهرباني وکړئ انتظار وباسئ"""
            )

            await context.bot.send_message(
                ADMIN_ID,
f"""💳 نوی ایزیلوډ درخواست

👤 {name}
🆔 {uid}
💰 {balance} AFN"""
)

    # ===== ADMIN =====
    if text == "/admin" and uid == ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())

    elif text == "📢 Broadcast" and uid == ADMIN_ID:
        context.user_data["broadcast"] = True
        await update.message.reply_text("✉️ مسیج ولیکه")

    elif context.user_data.get("broadcast") and uid == ADMIN_ID:
        cur.execute("SELECT id FROM users")
        users = cur.fetchall()
        for u in users:
            try:
                await context.bot.send_message(u[0], text)
            except:
                pass
        context.user_data["broadcast"] = False
        await update.message.reply_text("✅ واستول شو")

    elif text == "➕ Force Join Add" and uid == ADMIN_ID:
        context.user_data["fjoin"] = True
        await update.message.reply_text("🔗 لینک ولیکه")

    elif context.user_data.get("fjoin") and uid == ADMIN_ID:
        set_setting("force_join", text)
        context.user_data["fjoin"] = False
        await update.message.reply_text("✅ اضافه شو")

    elif text == "➖ Force Join Del" and uid == ADMIN_ID:
        set_setting("force_join", "")
        await update.message.reply_text("❌ حذف شو")

    elif text == "📊 Stats" and uid == ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        fake = total + 100
        await update.message.reply_text(f"👥 Users: {fake}")

    # ===== USER =====
    elif text == "📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        fake = total + 100

        await update.message.reply_text(
            f"👥 کاروونکي: {fake}\n🔗 {CHANNEL_LINK}"
        )

        link = f"https://t.me/{BOT_USERNAME}?start={uid}"

        await update.message.reply_text(
            f"💰 {balance}\n👥 {invites}\n🔗 {link}"
        )

    elif text == "📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه", reply_markup=phone_kb())

    elif update.message.contact:
        cur.execute("UPDATE users SET phone=? WHERE id=?", (update.message.contact.phone_number, uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه", reply_markup=main_kb())

    elif text == "💰 افغانۍ زیاتول":
        await update.message.reply_text("👇 انتخاب کړه", reply_markup=invite_kb())

    elif text == "🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
        data = cur.fetchall()
        msg = "🏆\n"
        for i,u in enumerate(data,1):
            msg += f"{i}. {u[0]} - {u[1]}\n"
        await update.message.reply_text(msg)

    elif text == "✏️ ستا دعوت کوونکي":
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        inv = cur.fetchone()[0]
        await update.message.reply_text(f"👥 {inv}")

    elif text == "🎁 ورځنۍ بونس":
        cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
        last = cur.fetchone()[0]

        if time_left(last,86400)>0:
            await update.message.reply_text("⏳ صبر")
        else:
            cur.execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?",
                        (DAILY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎉 1 AFN")

    elif text == "🎁 اوونیز بونس":
        cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
        last = cur.fetchone()[0]

        if time_left(last,604800)>0:
            await update.message.reply_text("⏳ صبر")
        else:
            cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",
                        (WEEKLY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎉 5 AFN")

    elif text == "📢 ټاسک":
        await update.message.reply_text("📢 Task نشته")

    elif text == "🔙 وتل":
        await update.message.reply_text("🏠", reply_markup=main_kb())

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
