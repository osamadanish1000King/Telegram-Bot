import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
TASK_REWARD = 1
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
conn.commit()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()

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
        ["🔙 وتل"]
    ],resize_keyboard=True)

def phone_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📲 شمېره واستوه",request_contact=True)]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 نشر پیغام"],
        ["💰 پیسې زیاتول"],
        ["📊 احصایه"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== START =====
async def start(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    ref=None
    if context.args:
        try:
            ref=int(context.args[0])
        except:
            pass

    get_user(uid,name,ref)

    if ref and ref!=uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
        conn.commit()

    await context.bot.send_message(ADMIN_ID,f"👤 نوی یوزر:\n{name}\n{uid}")
    await update.message.reply_text("ښه راغلاست 👋",reply_markup=main_kb())

# ===== HANDLER =====
async def handler(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name
    text=update.message.text

    get_user(uid,name)

    # ===== INFO =====
    if text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv=cur.fetchone()

        await update.message.reply_text(
f"""👤 {name}
🆔 {uid}

💰 {bal} افغانۍ
👥 دعوت: {inv}"""
        )

    # ===== PHONE =====
    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه 👇",reply_markup=phone_kb())

    elif update.message.contact:
        phone=update.message.contact.phone_number
        cur.execute("UPDATE users SET phone=? WHERE id=?", (phone,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه")

    # ===== INVITE MENU =====
    elif text=="💰 افغانۍ زیاتول":
        await update.message.reply_text("انتخاب کړه 👇",reply_markup=invite_kb())

    elif text=="👥 ملګري دعوت کول":
        link=f"https://t.me/{BOT_USERNAME}?start={uid}"
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        inv=cur.fetchone()[0]

        await update.message.reply_text(
f"""👥 ستا دعوت: {inv}

🔗 لینک:
{link}

🎁 هر دعوت = 4 افغانۍ"""
        )

    elif text=="✏️ ستا دعوت کوونکي":
        cur.execute("SELECT name FROM users WHERE ref=?", (uid,))
        data=cur.fetchall()
        if not data:
            await update.message.reply_text("❌ نشته")
        else:
            msg="👥 کسان:\n"
            for i in data:
                msg+=f"{i[0]}\n"
            await update.message.reply_text(msg)

    elif text=="🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
        data=cur.fetchall()
        msg="🏆 TOP:\n"
        for i in data:
            msg+=f"{i[0]} - {i[1]}\n"
        await update.message.reply_text(msg)

    # ===== BONUS =====
    elif text=="🎁 ورځنۍ بونس":
        cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        t=time_left(last,86400)
        if t>0:
            await update.message.reply_text(f"⏳ پاتې:\n{format_time(t)}")
        else:
            cur.execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?",
                        (DAILY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎁 1 افغانۍ درکړل شوه")

    elif text=="🎁 اوونیز بونس":
        cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        t=time_left(last,604800)
        if t>0:
            await update.message.reply_text(f"⏳ پاتې:\n{format_time(t)}")
        else:
            cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",
                        (WEEKLY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎁 5 افغانۍ درکړل شوه")

    # ===== EASYLOAD =====
    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پوره کړه")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"💸 درخواست:\n{uid}")

    # ===== ABOUT =====
    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real=cur.fetchone()[0]

        total=real if uid==ADMIN_ID else real+100

        await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}

🆔 {ADMIN_ID}"""
        )

    # ===== ADMIN =====
    elif text=="/admin":
        if uid==ADMIN_ID:
            await update.message.reply_text("Admin Panel 👑",reply_markup=admin_kb())

    elif text=="📊 احصایه" and uid==ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        users=cur.fetchone()[0]
        await update.message.reply_text(f"👥 ټول یوزران: {users}")

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))

print("BOT RUNNING...")
app.run_polling()
