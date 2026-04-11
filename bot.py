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

# ====================== DATABASE ======================
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

# ====================== FUNCTIONS ======================
def get_user(uid, name, ref=None):
    cur.execute("SELECT id FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id, name, ref) VALUES(?,?,?)", (uid, name, ref))
        conn.commit()
        return True
    return False

def time_left(last, seconds):
    if not last:
        return 0
    last = datetime.datetime.fromisoformat(last)
    now = datetime.datetime.now()
    return seconds - (now - last).total_seconds()

def format_time(sec):
    sec = int(sec)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h}:{m:02d}:{s:02d}"

# ====================== KEYBOARDS ======================
def main_kb():
    return ReplyKeyboardMarkup([
        ["❗ خپل حساب معلومات"],
        ["📞 شمېره ثبت کړی"],
        ["💰 افغانۍ زیاتول", "🏦 ایزیلوډ"],
        ["📊 د ربات په اړه"]
    ], resize_keyboard=True)

def invite_kb():
    return ReplyKeyboardMarkup([
        ["🏅 غوره دعوت کوونکي", "✏️ ستا دعوت کوونکي"],
        ["🎁 ورځنۍ بونس", "🎁 اوونیز بونس"],
        ["👥 ملګري دعوت کول", "🎁 Task"],
        ["🔙 وتل"]
    ], resize_keyboard=True)

def phone_kb():
    return ReplyKeyboardMarkup([
        [KeyboardButton("📲 شمېره واستوه", request_contact=True)],
        ["🔙 وتل"]
    ], resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 Broadcast"],
        ["➕ Force Join Add", "➖ Force Join Del"],
        ["➕ Task Add", "➖ Task Del"],
        ["📊 Stats"],
        ["🔙 وتل"]
    ], resize_keyboard=True)

# ====================== INLINE ======================
def force_join_btn(links):
    return InlineKeyboardMarkup([[InlineKeyboardButton("📢 Join Channel", url=l)] for l in links])

def task_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Task Channel", url=link)],
        [InlineKeyboardButton("✅ Done", callback_data=f"done|{link}")]
    ])

# ====================== CHECK JOIN ======================
async def is_joined(user_id, bot, link):
    try:
        if "joinchat" in link or "+" in link:
            return True
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# ====================== START ======================
async def start(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = None
    if context.args:
        try:
            ref = int(context.args[0])
        except:
            pass

    is_new = get_user(uid, name, ref)

    if is_new:
        await context.bot.send_message(ADMIN_ID, f"👤 نوی یوزر:\n{name}\n{uid}")
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?, invites=invites+1 WHERE id=?", 
                       (INVITE_REWARD, ref))
            conn.commit()

    # Force Join Check
    cur.execute("SELECT link FROM forcejoin")
    links = [i[0] for i in cur.fetchall()]
    not_joined = [l for l in links if not await is_joined(uid, context.bot, l)]

    if not_joined:
        await update.message.reply_text("❗ چینلونه جواین کړه", reply_markup=force_join_btn(not_joined))
        return

    await update.message.reply_text("ښه راغلاست 👋", reply_markup=main_kb())

# ====================== MAIN USER HANDLER ======================
async def handler(update, context):
    uid = update.effective_user.id
    name = update.effective_user.first_name
    get_user(uid, name)

    # Contact Handling
    if update.message.contact:
        phone = update.message.contact.phone_number
        cur.execute("UPDATE users SET phone=? WHERE id=?", (phone, uid))
        conn.commit()
        await update.message.reply_text("✅ شمېره ثبت شوه!", reply_markup=main_kb())
        return

    if not update.message.text:
        return

    text = update.message.text

    # Admin Panel
    if uid == ADMIN_ID and text == "/admin":
        await update.message.reply_text("🛠 ادمین پینل", reply_markup=admin_kb())
        return

    # Force Join Check
    cur.execute("SELECT link FROM forcejoin")
    links = [i[0] for i in cur.fetchall()]
    not_joined = [l for l in links if not await is_joined(uid, context.bot, l)]

    if not_joined and uid != ADMIN_ID:
        await update.message.reply_text("❗ مخکې چینل جواین کړه", reply_markup=force_join_btn(not_joined))
        return

    # Fake Balance
    cur.execute("SELECT balance, invites FROM users WHERE id=?", (uid,))
    real_balance, inv = cur.fetchone() or (0, 0)
    fake_balance = int(real_balance * 3 + 20)

    if text == "🔙 وتل":
        await update.message.reply_text("🏠", reply_markup=main_kb())

    elif text == "❗ خپل حساب معلومات":
        await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {fake_balance} افغانۍ
👥 دعوتونه = {inv}"""
        )

    elif text == "📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه", reply_markup=phone_kb())

    elif text == "💰 افغانۍ زیاتول":
        await update.message.reply_text("انتخاب کړه", reply_markup=invite_kb())

    elif text == "👥 ملګري دعوت کول":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"🔗 {link}")

    elif text == "🎁 ورځنۍ بونس":
        cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
        last = cur.fetchone()[0]
        t = time_left(last, 86400)
        if t > 0:
            await update.message.reply_text(f"⏳ {format_time(t)}")
        else:
            cur.execute("UPDATE users SET balance=balance+?, daily=? WHERE id=?",
                        (DAILY_REWARD, datetime.datetime.now().isoformat(), uid))
            conn.commit()
            await update.message.reply_text("🎁 1 افغانۍ درکړل شوه")

    elif text == "🎁 اوونیز بونس":
        cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
        last = cur.fetchone()[0]
        t = time_left(last, 604800)
        if t > 0:
            await update.message.reply_text(f"⏳ {format_time(t)}")
        else:
            cur.execute("UPDATE users SET balance=balance+?, weekly=? WHERE id=?",
                        (WEEKLY_REWARD, datetime.datetime.now().isoformat(), uid))
            conn.commit()
            await update.message.reply_text("🎁 5 افغانۍ درکړل شوه")

    elif text == "🎁 Task":
        cur.execute("SELECT link FROM tasks")
        data = cur.fetchall()
        for t in data[:5]:
            await update.message.reply_text("Task:", reply_markup=task_btn(t[0]))

    elif text == "🏦 ایزیلوډ":
        if real_balance < WITHDRAW_LIMIT:
            await update.message.reply_text("❌ 50 پوره کړه")
        else:
            await update.message.reply_text("✅ درخواست واستول شو")
            await context.bot.send_message(ADMIN_ID, f"💸 Withdraw:\n{uid}\nنام: {name}")

    elif text == "📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]
        fake_users = 200 + real * 3
        await update.message.reply_text(f"""📊 معلومات

👥 کاروونکي: {fake_users}

🔗 {CHANNEL_LINK}""")

# ====================== ADMIN HANDLER ======================
async def admin_handler(update, context):
    if update.effective_user.id != ADMIN_ID:
        return
    text = update.message.text

    if text == "📢 Broadcast":
        await update.message.reply_text("📢 پیغام ولیکئ چې ټولو ته ولیږم:")
        context.user_data['state'] = 'broadcast'

    elif text == "➕ Force Join Add":
        await update.message.reply_text("🔗 Force Join لنک ولیکئ:")
        context.user_data['state'] = 'add_force'

    elif text == "➖ Force Join Del":
        await update.message.reply_text("🔗 Force Join لنک ولیکئ چې حذف کړم:")
        context.user_data['state'] = 'del_force'

    elif text == "➕ Task Add":
        await update.message.reply_text("🔗 Task لنک ولیکئ:")
        context.user_data['state'] = 'add_task'

    elif text == "➖ Task Del":
        await update.message.reply_text("🔗 Task لنک ولیکئ چې حذف کړم:")
        context.user_data['state'] = 'del_task'

    elif text == "📊 Stats":
        cur.execute("SELECT COUNT(*) FROM users")
        total = cur.fetchone()[0]
        cur.execute("SELECT SUM(balance) FROM users")
        bal = cur.fetchone()[0] or 0
        await update.message.reply_text(f"👥 ټول کاروونکي: {total}\n💰 ټول بیلانس: {bal:.2f} افغانۍ")

    elif text == "🔙 وتل":
        await update.message.reply_text("🏠", reply_markup=main_kb())

# ====================== STATE HANDLER (Broadcast etc.) ======================
async def state_handler(update, context):
    if update.effective_user.id != ADMIN_ID:
        return

    state = context.user_data.get('state')
    text = update.message.text

    if state == 'broadcast':
        cur.execute("SELECT id FROM users")
        users = [u[0] for u in cur.fetchall()]
        success = 0
        for u in users:
            try:
                await context.bot.send_message(u, text)
                success += 1
            except:
                pass
        await update.message.reply_text(f"✅ براډکاسټ واستول شو!\n{ success } / { len(users) }")
        context.user_data['state'] = None

    elif state == 'add_force':
        cur.execute("INSERT INTO forcejoin(link) VALUES(?)", (text,))
        conn.commit()
        await update.message.reply_text("✅ Force Join اضافه شو")

    elif state == 'del_force':
        cur.execute("DELETE FROM forcejoin WHERE link=?", (text,))
        conn.commit()
        await update.message.reply_text("✅ Force Join حذف شو")

    elif state == 'add_task':
        cur.execute("INSERT INTO tasks(link) VALUES(?)", (text,))
        conn.commit()
        await update.message.reply_text("✅ Task اضافه شو")

    elif state == 'del_task':
        cur.execute("DELETE FROM tasks WHERE link=?", (text,))
        conn.commit()
        await update.message.reply_text("✅ Task حذف شو")

# ====================== CALLBACK ======================
async def callback(update, context):
    q = update.callback_query
    await q.answer()
    link = q.data.split("|")[1]
    uid = q.from_user.id

    if await is_joined(uid, context.bot, link):
        cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (TASK_REWARD, uid))
        conn.commit()
        await q.message.reply_text("🎉 انعام واخیستل شو")
    else:
        await q.message.reply_text("❌ اول جواین کړه")

# ====================== RUN ======================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", start))   # /admin command

app.add_handler(MessageHandler(filters.CONTACT, handler))
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handler))      # Normal users
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, admin_handler)) # Admin buttons
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, state_handler)) # Broadcast & states

app.add_handler(CallbackQueryHandler(callback))

print("✅ BOT READY")
app.run_polling()
