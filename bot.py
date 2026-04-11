import sqlite3
import datetime
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

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

# ===== INLINE =====

def force_join_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 چینل جواین", url=link)]
    ])


def task_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Task Channel", url=link)],
        [InlineKeyboardButton("✅ Done", callback_data="done_task")]
    ])
# ===== CHECK JOIN =====
async def is_joined(user_id, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    ref=None
    if context.args:
        try:
            ref=int(context.args[0])
        except:
            pass

    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    exists = cur.fetchone()

    if not exists:
        get_user(uid,name,ref)

        if ref and ref!=uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
            conn.commit()
            await context.bot.send_message(ref,"🎉 یو کس دې راوست\n💰 4 افغانۍ اضافه شوه")

    await context.bot.send_message(ADMIN_ID,f"👤 نوی یوزر:\n{name}\n{uid}")

    link = context.bot_data.get("force_join")
    if link:
        joined = await is_joined(uid, context.bot, link)
        if not joined:
            await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
            return

    await update.message.reply_text("ښه راغلاست 👋",reply_markup=main_kb())

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid=update.effective_user.id
    name=update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text if update.message.text else ""

    # ===== ADMIN PANEL =====
    if text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel",reply_markup=admin_kb())

    elif text=="📢 Broadcast" and uid==ADMIN_ID:
        context.user_data["bc"]=True
        await update.message.reply_text("پیغام ولیکه")

    elif context.user_data.get("bc") and uid==ADMIN_ID:
        context.user_data["bc"]=False
        cur.execute("SELECT id FROM users")
        users = cur.fetchall()
        for u in users:
            try:
                await context.bot.send_message(u[0], text)
            except:
                pass
        await update.message.reply_text("✅ ټولو ته واستول شو")

    elif text=="➕ Force Join Add" and uid==ADMIN_ID:
        context.user_data["fjoin"]=True
        await update.message.reply_text("لینک ولیکه")

    elif context.user_data.get("fjoin") and uid==ADMIN_ID:
        context.user_data["fjoin"]=False
        context.bot_data["force_join"]=text
        await update.message.reply_text("✅ Force Join فعال شو")

    elif text=="➖ Force Join Del" and uid==ADMIN_ID:
        context.bot_data["force_join"]=None
        await update.message.reply_text("❌ حذف شو")

    elif text=="➕ Task Add" and uid==ADMIN_ID:
        context.user_data["task"]=True
        await update.message.reply_text("د چینل لینک ولیکه")

    elif context.user_data.get("task") and uid==ADMIN_ID:
        context.user_data["task"]=False
        context.bot_data["task"]=text
        await update.message.reply_text("✅ Task اضافه شو")

    elif text=="➖ Task Del" and uid==ADMIN_ID:
        context.bot_data["task"]=None
        await update.message.reply_text("❌ Task حذف شو")

    elif text=="📊 Stats" and uid==ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total=cur.fetchone()[0]
        cur.execute("SELECT SUM(balance) FROM users")
        bal=cur.fetchone()[0]
        await update.message.reply_text(f"👥 Users: {total}\n💰 Total: {bal}")

    # ===== USER =====
    elif text=="🔙 وتل":
        await update.message.reply_text("🏠 اصلي مېنو",reply_markup=main_kb())

    elif text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        await update.message.reply_text(
f"""💳 کارن = {name}

💡  ایډي کارن : {uid}

🛣ستاسو دپيسو اندازه= {int(bal)}

🔗 د بیلانس زیاتولو لپاره  [ 👫 کسان ] دعوت کړی"""
        )

    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه 👇",reply_markup=phone_kb())

    elif update.message.contact:
        phone=update.message.contact.phone_number
        cur.execute("UPDATE users SET phone=? WHERE id=?", (phone,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه",reply_markup=main_kb())

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

    elif text=="🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
        data = cur.fetchall()
        msg="🏅 غوره دعوت کوونکي:\n\n"
        for i,row in enumerate(data,1):
            msg+=f"{i}. {row[0]} - {row[1]}\n"
        await update.message.reply_text(msg)

    elif text=="✏️ ستا دعوت کوونکي":
        cur.execute("SELECT ref FROM users WHERE id=?", (uid,))
        ref=cur.fetchone()[0]
        if ref:
            await update.message.reply_text(f"👤 ته د دې له خوا راغلی یې:\n{ref}")
        else:
            await update.message.reply_text("❌ تا څوک نه دی دعوت کړی")

    elif text=="🎁 ورځنۍ بونس":
        cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]
        t=time_left(last,86400)
        if t>0:
            await update.message.reply_text(f"⏳ {format_time(t)}")
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
            await update.message.reply_text(f"⏳ {format_time(t)}")
        else:
            cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",
                        (WEEKLY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎁 5 افغانۍ درکړل شوه")

    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پوره کړه")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"💸 درخواست:\n{uid}")

    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        total=cur.fetchone()[0]

        await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}

🆔 {ADMIN_ID}"""
        )

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))

print("BOT RUNNING...")
app.run_polling()
