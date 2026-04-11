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
cur.execute("CREATE TABLE IF NOT EXISTS tasks(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS channels(username TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS stats(day TEXT, fake INTEGER)")
conn.commit()

# ================= FAKE USERS =================
def fake_users():
    today = str(datetime.date.today())
    cur.execute("SELECT fake FROM stats WHERE day=?", (today,))
    row = cur.fetchone()

    if not row:
        cur.execute("INSERT INTO stats VALUES(?,?)", (today, 100))
        conn.commit()
        return 100
    return row[0]

# ================= KEYBOARDS =================
def main_kb():
    return ReplyKeyboardMarkup([
        ["📊 حالت"],
        ["👥 دعوت","💰 پیسې زیاتول"],
        ["📱 شمېره ثبت","⚡ ایزي لوډ"],
        ["🤖 د رباټ په اړه"]
    ],resize_keyboard=True)

def money_kb():
    return ReplyKeyboardMarkup([
        ["📋 ټاسک","🎁 بونس"],
        ["🔙 شاته"]
    ],resize_keyboard=True)

def bonus_kb():
    return ReplyKeyboardMarkup([
        ["🎁 ورځنی بونس","🔥 اوونیز بونس"],
        ["🔙 شاته"]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["👥 ټول یوزران"],
        ["📢 برودکاست"],
        ["➕ ټاسک چینل","➖ ټاسک چینل"],
        ["➕ فورس چینل","➖ فورس چینل"],
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
    cur.execute("SELECT username FROM channels")
    channels = cur.fetchall()

    if not channels:
        return True

    uid = update.effective_user.id
    for ch in channels:
        ch = ch[0]
        try:
            member = await context.bot.get_chat_member(ch, uid)
            if member.status not in ["member","administrator","creator"]:
                await update.message.reply_text(f"❗ لطفاً دا چینل جواین کړه:\nhttps://t.me/{ch.replace('@','')}")
                return False
        except:
            await update.message.reply_text(f"❗ دا چینل جواین کړه:\nhttps://t.me/{ch.replace('@','')}")
            return False

    return True

# ================= START =================
async def start(update,context):
    uid = update.effective_user.id
    get_user(uid)

    # referral system
    if context.args:
        try:
            ref = int(context.args[0])
            if ref != uid:
                cur.execute("UPDATE users SET balance=balance+?, invites=invites+1 WHERE id=?", (INVITE,ref))
                conn.commit()
        except:
            pass

    if not await force_join(update,context):
        return

    await update.message.reply_text("🌟 ښه راغلاست!",reply_markup=main_kb())

# ================= ADMIN =================
async def admin_cmd(update, context):
    uid = update.effective_user.id

    if uid == ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel", reply_markup=admin_kb())
    else:
        await update.message.reply_text(f"❌ له اډمين سره اړيکه:\n{ADMIN_USERNAME}")

# ================= HELP =================
async def help_cmd(update, context):
    await update.message.reply_text(
"""ℹ️ د رباټ مکمل معلومات:

💰 عاید لارې:
👥 دعوت = پیسې
📋 ټاسک = انعام
🎁 بونس = ورځنی + اوونیز

📊 حالت = بیلانس + یوزران
📱 شمېره ثبت = خپل نمبر
⚡ ایزي لوډ = ریچارج

🚀 هرڅومره زیات دعوت وکړئ، همغومره زیات عاید!"""
    )

# ================= MAIN =================
async def handler(update,context):

    if not update.message:
        return

    uid = update.effective_user.id
    text = update.message.text.strip()

    get_user(uid)

    if not await force_join(update,context):
        return

    # حالت
    if text=="📊 حالت":
        cur.execute("SELECT balance, invites FROM users WHERE id=?", (uid,))
        bal,inv = cur.fetchone()

        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]

        total = real + fake_users()

        await update.message.reply_text(
f"""👤 {update.effective_user.first_name}
💰 {bal} AF
👥 ټول یوزران: {total}
👥 ستا دعوتونه: {inv}

https://t.me/{BOT_USERNAME}?start={uid}"""
        )

    # دعوت
    elif text=="👥 دعوت":
        await update.message.reply_text(f"🔗 لینک:\nhttps://t.me/{BOT_USERNAME}?start={uid}")

    # پیسې زیاتول
    elif text=="💰 پیسې زیاتول":
        await update.message.reply_text("انتخاب:",reply_markup=money_kb())

    elif text=="🔙 شاته":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    # بونس
    elif text=="🎁 بونس":
        await update.message.reply_text("🎁",reply_markup=bonus_kb())

    elif text=="🎁 ورځنی بونس":
        today=str(datetime.date.today())
        cur.execute("SELECT last_daily FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        if last==today:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_daily=? WHERE id=?", (DAILY,today,uid))
            conn.commit()
            await update.message.reply_text(f"✅ {DAILY} AF")

    elif text=="🔥 اوونیز بونس":
        week=str(datetime.date.today().isocalendar()[1])
        cur.execute("SELECT last_weekly FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]

        if last==week:
            await update.message.reply_text("❌ اخیستل شوی")
        else:
            cur.execute("UPDATE users SET balance=balance+?, last_weekly=? WHERE id=?", (WEEKLY,week,uid))
            conn.commit()
            await update.message.reply_text(f"✅ {WEEKLY} AF")

    # 📱 نمبر
    elif text=="📱 شمېره ثبت":
        await update.message.reply_text("شمېره ولیکه:")
        context.user_data["phone"]=True

    elif context.user_data.get("phone"):
        if text.isdigit():
            cur.execute("UPDATE users SET phone=? WHERE id=?", (text,uid))
            conn.commit()
            await update.message.reply_text("✅ ثبت شوه")
        else:
            await update.message.reply_text("❌ غلط نمبر")
        context.user_data["phone"]=False

    # ⚡ ایزي لوډ
    elif text=="⚡ ایزي لوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ 50 AF پکار دي")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")

    # 🤖 ABOUT
    elif text=="🤖 د رباټ په اړه":
        await update.message.reply_text(
"""🤖 Afghan Earn Bot 🇦🇫

💰 دلته تاسو کولی شئ پیسې وګټئ:
👥 دعوت له لارې
📋 ټاسکونو سره
🎁 بونس اخیستلو سره

⚡ ایزي لوډ هم شته

🚀 دا یو ریښتینی عاید سیستم دی!
"""
        )

    # ================= ADMIN BUTTONS =================
    elif uid==ADMIN_ID:

        if text=="👥 ټول یوزران":
            cur.execute("SELECT COUNT(*) FROM users")
            count = cur.fetchone()[0]
            await update.message.reply_text(f"👥 Users: {count}")

        elif text=="➕ فورس چینل":
            await update.message.reply_text("چینل یوزرنیم ولیکه (@channel):")
            context.user_data["add_channel"]=True

        elif context.user_data.get("add_channel"):
            cur.execute("INSERT INTO channels VALUES(?)",(text,))
            conn.commit()
            await update.message.reply_text("✅ اضافه شو")
            context.user_data["add_channel"]=False

        elif text=="➖ فورس چینل":
            await update.message.reply_text("چینل یوزرنیم ولیکه:")
            context.user_data["del_channel"]=True

        elif context.user_data.get("del_channel"):
            cur.execute("DELETE FROM channels WHERE username=?",(text,))
            conn.commit()
            await update.message.reply_text("❌ حذف شو")
            context.user_data["del_channel"]=False

# ================= RUN =================
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CommandHandler("admin",admin_cmd))
app.add_handler(CommandHandler("help",help_cmd))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND,handler))

print("🔥 FINAL BOT READY")
app.run_polling()
