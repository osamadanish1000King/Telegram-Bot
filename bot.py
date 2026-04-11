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

# ===== FORCE JOIN =====
async def is_joined(user_id, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def force_join_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=link)]
    ])

# ===== TIME =====
def time_left(last,seconds):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    now=datetime.datetime.now()
    return seconds-(now-last).total_seconds()

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

    ref = int(context.args[0]) if context.args else None

    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        get_user(uid,name,ref)

        if ref and ref!=uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
            conn.commit()

    await update.message.reply_text("👇 انتخاب کړه",reply_markup=main_kb())

# ===== TASK DONE =====
async def done_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    uid = query.from_user.id
    cur.execute("UPDATE users SET balance=balance+1 WHERE id=?", (uid,))
    conn.commit()

    await query.edit_message_text("✅ ټاسک مکمل شو +1 افغانۍ")

# ===== HANDLER =====
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message:
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid,name)

    text = update.message.text or ""

    # FORCE JOIN
    link = get_setting("force_join")
    if link:
        if not await is_joined(uid,context.bot,link):
            await update.message.reply_text("❗ چینل جواین کړه",reply_markup=force_join_btn(link))
            return

    # TASK
    if text=="📢 ټاسک":
        link = get_setting("task")
        if not link:
            await update.message.reply_text("❌ ټاسک نشته")
            return

        await update.message.reply_text("📢 ټاسک ترسره کړه",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 چینل",url=link)],
                [InlineKeyboardButton("✅ Done",callback_data="done_task")]
            ])
        )

    elif text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        b,i = cur.fetchone()
        await update.message.reply_text(f"💳 {name}\n🆔 {uid}\n💰 {b}\n👥 {i}")

    elif text=="👥 ملګري دعوت کول":
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        inv = cur.fetchone()[0]
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"👥 {inv}\n🔗 {link}\n🎁 {INVITE_REWARD}")

    elif text=="🏦 ایزیلوډ":
        cur.execute("SELECT balance FROM users WHERE id=?", (uid,))
        bal = cur.fetchone()[0]

        if bal<50:
            await update.message.reply_text("❌ 50 ته اړتیا ده")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID,f"{name} {uid} {bal}")

    elif text=="📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه",reply_markup=phone_kb())

    elif update.message.contact:
        cur.execute("UPDATE users SET phone=? WHERE id=?",(update.message.contact.phone_number,uid))
        conn.commit()
        await update.message.reply_text("✅ ثبت شوه",reply_markup=main_kb())

    elif text=="💰 افغانۍ زیاتول":
        await update.message.reply_text("👇 انتخاب کړه",reply_markup=invite_kb())

    elif text=="🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
        data = cur.fetchall()
        msg="🏆\n"
        for i,u in enumerate(data,1):
            msg+=f"{i}. {u[0]} - {u[1]}\n"
        await update.message.reply_text(msg)

    elif text=="✏️ ستا دعوت کوونکي":
        cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
        await update.message.reply_text(str(cur.fetchone()[0]))

    elif text=="🎁 ورځنۍ بونس":
        cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]
        if time_left(last,86400)>0:
            await update.message.reply_text("⏳ صبر")
        else:
            cur.execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?",(DAILY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎉 1 AFN")

    elif text=="🎁 اوونیز بونس":
        cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
        last=cur.fetchone()[0]
        if time_left(last,604800)>0:
            await update.message.reply_text("⏳ صبر")
        else:
            cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",(WEEKLY_REWARD,datetime.datetime.now().isoformat(),uid))
            conn.commit()
            await update.message.reply_text("🎉 5 AFN")

    elif text=="📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        total=cur.fetchone()[0]
        await update.message.reply_text(f"👥 {total}\n🔗 {CHANNEL_LINK}")

    elif text=="🔙 وتل":
        await update.message.reply_text("🏠",reply_markup=main_kb())

    # ADMIN
    elif uid==ADMIN_ID and text=="/admin":
        await update.message.reply_text("👑",reply_markup=admin_kb())

    elif uid==ADMIN_ID and text=="➕ Force Join Add":
        context.user_data["fjoin"]=True
        await update.message.reply_text("لینک راکړه")

    elif uid==ADMIN_ID and context.user_data.get("fjoin"):
        set_setting("force_join",text)
        context.user_data["fjoin"]=False
        await update.message.reply_text("✅")

    elif uid==ADMIN_ID and text=="➖ Force Join Del":
        set_setting("force_join","")
        await update.message.reply_text("❌")

    elif uid==ADMIN_ID and text=="➕ Task Add":
        context.user_data["task"]=True
        await update.message.reply_text("لینک راکړه")

    elif uid==ADMIN_ID and context.user_data.get("task"):
        set_setting("task",text)
        context.user_data["task"]=False
        await update.message.reply_text("✅")

    elif uid==ADMIN_ID and text=="➖ Task Del":
        set_setting("task","")
        await update.message.reply_text("❌")

    elif uid==ADMIN_ID and text=="📊 Stats":
        cur.execute("SELECT COUNT(*) FROM users")
        total=cur.fetchone()[0]
        await update.message.reply_text(f"👥 {total}")

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(done_task, pattern="done_task"))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
app.run_polling()
