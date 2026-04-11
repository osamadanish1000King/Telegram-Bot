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
WITHDRAW_LIMIT = 50

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

cur.execute("CREATE TABLE IF NOT EXISTS forcejoin(link TEXT)")
cur.execute("CREATE TABLE IF NOT EXISTS tasks(link TEXT)")
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
        ["👥 ملګري دعوت کول","🎁 Task"],
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
        ["💸 Withdraw Requests"],
        ["📊 Stats"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== INLINE =====
def force_join_btn(links):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("📢 Join Channel", url=l)] for l in links]
    )

def task_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Task Channel", url=link)],
        [InlineKeyboardButton("✅ Done", callback_data=f"done|{link}")]
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
        try: ref=int(context.args[0])
        except: pass

    get_user(uid,name,ref)

    if ref and ref!=uid:
        cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
        conn.commit()

    await context.bot.send_message(ADMIN_ID,f"👤 نوی یوزر:\n{name}\n{uid}")

    cur.execute("SELECT link FROM forcejoin")
    links=[i[0] for i in cur.fetchall()]

    if links:
        for link in links:
            if not await is_joined(uid,context.bot,link):
                await update.message.reply_text(
                    "❗ ټول چینلونه جواین کړه",
                    reply_markup=force_join_btn(links)
                )
                return

    await update.message.reply_text("ښه راغلاست 👋",reply_markup=main_kb())

# ===== HANDLER =====
async def handler(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    get_user(uid,name)

    # FORCE JOIN CHECK
    cur.execute("SELECT link FROM forcejoin")
    links=[i[0] for i in cur.fetchall()]

    if links:
        for link in links:
            if not await is_joined(uid,context.bot,link):
                await update.message.reply_text(
                    "❗ مخکې چینل جواین کړه",
                    reply_markup=force_join_btn(links)
                )
                return

    # BROADCAST
    if context.user_data.get("broadcast"):
        context.user_data["broadcast"]=False

        cur.execute("SELECT id FROM users")
        users=cur.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0], update.message.text)
            except:
                pass

        await update.message.reply_text("✅ Broadcast واستول شو")
        return

    if update.message.contact:
        cur.execute("UPDATE users SET phone=? WHERE id=?", (update.message.contact.phone_number,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه",reply_markup=main_kb())
        return

    text=update.message.text

    if text=="🔙 وتل":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    elif text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv=cur.fetchone()
        await update.message.reply_text(
f"""💳 کارن = {name}

💡 ایډي کارن : {uid}

💰 بیلانس = {bal} افغانۍ
👥 دعوتونه = {inv}

🔗 د بیلانس زیاتولو لپاره ملګري دعوت کړه"""
        )

    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه",reply_markup=phone_kb())

    elif text=="💰 افغانۍ زیاتول":
        await update.message.reply_text("انتخاب کړه",reply_markup=invite_kb())

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

    # TASK FIX (NO SPAM)
    elif text=="🎁 Task":
        cur.execute("SELECT link FROM tasks")
        data=cur.fetchall()

        if not data:
            await update.message.reply_text("❌ Task نشته")
        else:
            for t in data[:5]:   # limit
                await update.message.reply_text("Task:",reply_markup=task_btn(t[0]))

    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal=cur.fetchone()[0]

        if bal<WITHDRAW_LIMIT:
            await update.message.reply_text("❌ 50 پوره کړه")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"💸 Withdraw:\n{uid}")

    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real=cur.fetchone()[0]

        total = real if uid==ADMIN_ID else 100 + (real*2)

        await update.message.reply_text(
f"""📊 معلومات

👥 کاروونکي: {total}

🔗 {CHANNEL_LINK}

🆔 {ADMIN_ID}"""
        )

    # ADMIN
    elif text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("👑",reply_markup=admin_kb())

    elif text=="📢 Broadcast" and uid==ADMIN_ID:
        context.user_data["broadcast"]=True
        await update.message.reply_text("✍️ پیغام ولیکه")

    elif text=="➕ Force Join Add" and uid==ADMIN_ID:
        context.user_data["fjoin"]=True
        await update.message.reply_text("لینک ولیکه")

    elif context.user_data.get("fjoin"):
        context.user_data["fjoin"]=False
        cur.execute("INSERT INTO forcejoin(link) VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ ثبت شو")

    elif text=="➕ Task Add" and uid==ADMIN_ID:
        context.user_data["task"]=True
        await update.message.reply_text("Task لینک ولیکه")

    elif context.user_data.get("task"):
        context.user_data["task"]=False
        cur.execute("INSERT INTO tasks(link) VALUES(?)",(text,))
        conn.commit()
        await update.message.reply_text("✅ Task ثبت شو")

# ===== CALLBACK =====
async def callback(update,context):
    q=update.callback_query
    await q.answer()

    data=q.data
    if data.startswith("done|"):
        link=data.split("|")[1]
        uid=q.from_user.id

        if await is_joined(uid,context.bot,link):
            cur.execute("UPDATE users SET balance=balance+? WHERE id=?",(TASK_REWARD,uid))
            conn.commit()
            await q.message.reply_text("🎉 انعام واخیستل شو")
        else:
            await q.message.reply_text("❌ اول جواین کړه")

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))
app.add_handler(CallbackQueryHandler(callback))

print("BOT READY")
app.run_polling()
