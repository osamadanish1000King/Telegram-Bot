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
DAILY = 0.5
WEEKLY = 5

# ================= DB =================
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY, name TEXT, balance REAL DEFAULT 0, invites INTEGER DEFAULT 0, ref INTEGER, phone TEXT, daily TEXT, weekly TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS done(uid INTEGER, ch TEXT)")
conn.commit()

# ================= USER =================
def get_user(uid, name):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name) VALUES(?,?)",(uid,name))
        conn.commit()

# ================= TIME =================
def time_left(last, seconds):
    if not last:
        return 0
    last = datetime.datetime.fromisoformat(last)
    now = datetime.datetime.now()
    diff = (now - last).total_seconds()
    return seconds - diff

def format_time(sec):
    sec = int(sec)
    d = sec // 86400
    h = (sec % 86400)//3600
    m = (sec % 3600)//60
    s = sec % 60
    if d>0:
        return f"{d} ورځې {h}:{m}:{s}"
    return f"{h}:{m}:{s}"

# ================= START =================
async def start(update,context):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    get_user(uid,name)

    # referral
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+?, invites=invites+1 WHERE id=?", (INVITE_REWARD,ref))
                conn.commit()
                await context.bot.send_message(ref,"🎉 یو کس دې راوست\n💰 4 افغانۍ اضافه شوې")
        except:
            pass

    # admin notify
    await context.bot.send_message(ADMIN_ID,f"👤 نوی یوزر:\n{name}\n{uid}")

    await update.message.reply_text("🌟 ښه راغلاست",reply_markup=main_kb())

# ================= KEYBOARD =================
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
        ["🎁 ورخې ډالۍ","👥 ملګري دعوت کول"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ================= HANDLER =================
async def handler(update,context):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    text = update.message.text

    get_user(uid,name)

    # ================= INFO =================
    if text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv = cur.fetchone()
        await update.message.reply_text(
f"""👤 {name}
🆔 {uid}

💰 {bal} AF
👥 دعوت: {inv}"""
        )

    # ================= PHONE =================
    elif text=="📞 شمېره ثبت کړی":
        cur.execute("SELECT phone FROM users WHERE id=?", (uid,))
        p = cur.fetchone()[0]

        if p:
            await update.message.reply_text(f"📱 ستا شمېره:\n{p}")
        else:
            kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("📲 شمېره ثبت کړه",request_contact=True)]
            ])
            await update.message.reply_text("شمېره نشته",reply_markup=kb)

    # ================= INVITE =================
    elif text=="👥 ملګري دعوت کول":
        link=f"https://t.me/{BOT_USERNAME}?start={uid}"
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        inv=cur.fetchone()[0]

        await update.message.reply_text(
f"""👥 ستا دعوت شوي کسان: {inv}

🔗 لینک:
{link}

🎁 هر دعوت = 4 افغانۍ""",
reply_markup=invite_kb())

    elif text=="✏️ ستا دعوت کوونکي":
        cur.execute("SELECT name FROM users WHERE ref=?", (uid,))
        data=cur.fetchall()
        if not data:
            await update.message.reply_text("❌ هیڅوک نشته")
        else:
            msg="👥 ستا کسان:\n"
            for i in data:
                msg+=f"{i[0]}\n"
            await update.message.reply_text(msg)

    elif text=="🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
        data=cur.fetchall()
        msg="🏅 غوره کسان:\n"
        for i in data:
            msg+=f"{i[0]} - {i[1]}\n"
        await update.message.reply_text(msg)

    # ================= BONUS =================
    elif text=="🎁 ورخې ډالۍ":
        await update.message.reply_text("ورځنۍ یا اوونیز؟")

    # ================= ABOUT =================
    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real=cur.fetchone()[0]

        if uid==ADMIN_ID:
            total=real
        else:
            total=real+100

        await update.message.reply_text(
f"""📊 د ربات معلومات

👥 ټول کاروونکي: {total}

🔗 چینل:
{CHANNEL_LINK}

🆔 {ADMIN_ID}"""
        )

    # ================= EASY LOAD =================
    elif text=="🏦 ایزیلوډ":
        await update.message.reply_text("50 افغانۍ")
        await context.bot.send_message(ADMIN_ID,f"💸 درخواست:\n{uid}")

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT,handler))

print("🔥 BOT READY")
app.run_polling()
