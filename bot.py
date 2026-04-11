import sqlite3
import datetime
from telegram import *
from telegram.ext import *

# ====================== TOKEN ======================
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
    try:
        last = datetime.datetime.fromisoformat(last)
        return seconds - (datetime.datetime.now() - last).total_seconds()
    except:
        return 0

def format_time(sec):
    sec = int(sec)
    h = sec // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    return f"{h:02d}:{m:02d}:{s:02d}"

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

    ref = int(context.args[0]) if context.args else None
    get_user(uid, name, ref)

    cur.execute("SELECT link FROM forcejoin")
    not_joined = [l[0] for l in cur.fetchall() if not await is_joined(uid, context.bot, l[0])]

    if not_joined:
        await update.message.reply_text("❗ چینلونه جواین کړه", reply_markup=force_join_btn(not_joined))
        return

    await update.message.reply_text("ښه راغلاست 👋", reply_markup=main_kb())

# ====================== MAIN HANDLER ======================
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

    text = update.message.text
    if not text:
        return

    # Admin Panel
    if uid == ADMIN_ID and text == "/admin":
        await update.message.reply_text("🛠 ادمین پینل", reply_markup=admin_kb())
        return

    # ==================== ADMIN SECTION ====================
    if uid == ADMIN_ID:
        if text == "📢 Broadcast":
            context.user_data["broadcast"] = True
            await update.message.reply_text("✉️ پیغام ولیکئ چې ټولو ته واستول شي:")
            return

        if context.user_data.get("broadcast"):
            cur.execute("SELECT id FROM users")
            success = 0
            for (user_id,) in cur.fetchall():
                try:
                    await context.bot.send_message(user_id, text)
                    success += 1
                except:
                    pass
            context.user_data["broadcast"] = False
            await update.message.reply_text(f"✅ براډکاسټ واستول شو!\n{success} یوزر ته")
            return

        if text == "📊 Stats":
            cur.execute("SELECT COUNT(*), SUM(balance) FROM users")
            total, bal = cur.fetchone() or (0, 0)
            await update.message.reply_text(f"👥 ټول کاروونکي: {total}\n💰 ټول بیلانس: {bal:.2f} افغانۍ")
            return

    # Force Join Check
    cur.execute("SELECT link FROM forcejoin")
    not_joined = [l[0] for l in cur.fetchall() if not await is_joined(uid, context.bot, l[0])]
    if not_joined and uid != ADMIN_ID:
        await update.message.reply_text("❗ مخکې چینل جواین کړه", reply_markup=force_join_btn(not_joined))
        return

    # Fake Balance
    cur.execute("SELECT balance, invites FROM users WHERE id=?", (uid,))
    real_balance, invites = cur.fetchone() or (0, 0)
    fake_balance = int(real_balance * 3 + 20)

    # ==================== USER COMMANDS ====================
    if text == "🔙 وتل":
        await update.message.reply_text("🏠", reply_markup=main_kb())

    elif text == "❗ خپل حساب معلومات":
        await update.message.reply_text(
f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {fake_balance} افغانۍ
👥 دعوتونه = {invites}"""
        )

    elif text == "📞 شمېره ثبت کړی":
        await update.message.reply_text("شمېره واستوه", reply_markup=phone_kb())

    elif text == "💰 افغانۍ زیاتول":
        await update.message.reply_text("انتخاب کړه", reply_markup=invite_kb())

    elif text == "👥 ملګري دعوت کول":
        link = f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"🔗 {link}")

    elif text == "✏️ ستا دعوت کوونکي":
        cur.execute("SELECT name FROM users WHERE ref=?", (uid,))
        data = cur.fetchall()
        if not data:
            await update.message.reply_text("❌ تر اوسه هیڅوک نه دي دعوت کړي")
        else:
            msg = "👥 ستا دعوت کوونکي:\n\n" + "\n".join(f"{i}- {x[0]}" for i, x in enumerate(data, 1))
            await update.message.reply_text(msg)

    elif text == "🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name, invites FROM users ORDER BY invites DESC LIMIT 10")
        data = cur.fetchall()
        msg = "🏆 غوره دعوت کوونکي:\n\n" + "\n".join(f"{i}- {n} ({v})" for i, (n, v) in enumerate(data, 1))
        await update.message.reply_text(msg or "تر اوسه هیڅوک نشته")

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
        if not data:
            await update.message.reply_text("❌ تر اوسه هیڅ ټاسک نشته")
        else:
            for t in data[:5]:
                await update.message.reply_text("📌 Task", reply_markup=task_btn(t[0]))

    elif text == "🏦 ایزیلوډ":
        if real_balance < WITHDRAW_LIMIT:
            await update.message.reply_text("❌ لږ تر لږه 50 افغانۍ پوره کړئ")
        else:
            await update.message.reply_text("✅ درخواست ادمین ته واستول شو")
            await context.bot.send_message(ADMIN_ID, f"💸 واپس درخواست:\nID: {uid}\nName: {name}")

    elif text == "📊 د ربات په اړه":
        cur.execute("SELECT COUNT(*) FROM users")
        real = cur.fetchone()[0]
        fake_users = 200 + real * 3
        await update.message.reply_text(f"""📊 معلومات

👥 کاروونکي: {fake_users}

🔗 {CHANNEL_LINK}""")

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
        await q.message.reply_text("❌ لومړی چینل جواین کړئ")

# ====================== RUN ======================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("admin", start))
app.add_handler(MessageHandler(filters.CONTACT, handler))
app.add_handler(MessageHandler(filters.TEXT & \~filters.COMMAND, handler))
app.add_handler(CallbackQueryHandler(callback))

print("✅ BOT READY - Token Added Successfully")
app.run_polling()
