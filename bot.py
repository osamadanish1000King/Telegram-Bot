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
        [KeyboardButton("📲 شمېره واستوه",request_contact=True)],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== ADMIN KEYBOARD =====
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

    # invite reward
    if ref and ref!=uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
        conn.commit()
        await context.bot.send_message(ref,"🎉 یو کس دې راوست\n💰 4 افغانۍ اضافه شوه")

    # admin notify
    await context.bot.send_message(ADMIN_ID,f"👤 نوی یوزر:\n{name}\n{uid}")

    # force join
    link = context.bot_data.get("force_join")
    if link:
        joined = await is_joined(uid, context.bot, link)
        if not joined:
            await update.message.reply_text(
                "❗ مهرباني وکړه چینل جواین کړه",
                reply_markup=force_join_btn(link)
            )
            return

    await update.message.reply_text("ښه راغلاست 👋",reply_markup=main_kb())

# ===== HANDLER =====
async def handler(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    get_user(uid,name)

    # force join check for all messages
    link = context.bot_data.get("force_join")
    if link:
        joined = await is_joined(uid, context.bot, link)
        if not joined:
            await update.message.reply_text(
                "❗ مخکې چینل جواین کړه",
                reply_markup=force_join_btn(link)
            )
            return

    # contact save
    if update.message.contact:
        phone=update.message.contact.phone_number
        cur.execute("UPDATE users SET phone=? WHERE id=?", (phone,uid))
        conn.commit()
        await update.message.reply_text("✅ شمېره ثبت شوه",reply_markup=main_kb())
        return

    text=update.message.text

    # BACK
    if text=="🔙 وتل":
        await update.message.reply_text("🏠 اصلي مېنو",reply_markup=main_kb())

    # INFO
    elif text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv=cur.fetchone()

        await update.message.reply_text(
f"""👤 {name}
🆔 {uid}

💰 {bal} افغانۍ
👥 دعوت: {inv}"""
        )

    # PHONE
    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه 👇 یا ولیکه",reply_markup=phone_kb())

    elif text.startswith("07") or text.startswith("+93"):
        cur.execute("UPDATE users SET phone=? WHERE id=?", (text,uid))
        conn.commit()
        await update.message.reply_text("✅ شمېره ثبت شوه",reply_markup=main_kb())

    # INVITE
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

    # BONUS
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

    # EASYLOAD
    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پوره کړه")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"💸 درخواست:\n{uid}")

    # ABOUT
    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real=cur.fetchone()[0]

        if uid==ADMIN_ID:
            total = real
        else:
            total = 100 + (real * 2)

        await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}

🆔 {ADMIN_ID}"""
        )

    # ADMIN
    elif text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("👑 Admin Panel",reply_markup=admin_kb())

    elif text=="➕ Force Join Add" and uid==ADMIN_ID:
        context.user_data["fjoin"]=True
        await update.message.reply_text("لینک ولیکه")

    elif context.user_data.get("fjoin"):
        context.user_data["fjoin"]=False
        context.bot_data["force_join"]=text
        await update.message.reply_text("✅ Force Join فعال شو")

    elif text=="➖ Force Join Del" and uid==ADMIN_ID:
        context.bot_data["force_join"]=None
        await update.message.reply_text("❌ حذف شو")

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))

print("BOT RUNNING...")
app.run_polling()
