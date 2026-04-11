import sqlite3
import datetime
from telegram import *
from telegram.ext import *

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"

INVITE_REWARD = 4

# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY,
name TEXT,
balance REAL DEFAULT 0,
invites INTEGER DEFAULT 0,
ref INTEGER
)""")

conn.commit()

# ===== USER =====
def get_user(uid,name,ref=None):
    cur.execute("SELECT id FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()
        return True
    return False

# ===== KEYBOARD =====
def main_kb():
    return ReplyKeyboardMarkup([
        ["❗ خپل حساب معلومات"],
        ["👥 ملګري دعوت کول"],
        ["🏅 غوره دعوت کوونکي","✏️ ستا دعوت کوونکي"]
    ],resize_keyboard=True)

def admin_kb():
    return ReplyKeyboardMarkup([
        ["📢 Broadcast"],
        ["📊 Stats"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== START =====
async def start(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    ref=None
    if context.args:
        try: ref=int(context.args[0])
        except: pass

    is_new = get_user(uid,name,ref)

    if is_new:
        if ref and ref!=uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
            conn.commit()

    await update.message.reply_text("ښه راغلاست 👋",reply_markup=main_kb())

# ===== HANDLER =====
async def handler(update,context):
    uid=update.effective_user.id
    name=update.effective_user.first_name
    text=update.message.text

    get_user(uid,name)

    # ===== ADMIN =====
    if text=="/admin" and uid==ADMIN_ID:
        await update.message.reply_text("🛠 ادمین پینل",reply_markup=admin_kb())
        return

    # ===== BACK =====
    if text=="🔙 وتل":
        await update.message.reply_text("🏠",reply_markup=main_kb())
        return

    # ===== ACCOUNT =====
    if text=="❗ خپل حساب معلومات":
        cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
        bal,inv=cur.fetchone()

        await update.message.reply_text(
f"""👤 {name}

💰 بیلانس: {bal}
👥 دعوتونه: {inv}"""
        )

    # ===== INVITE LINK =====
    elif text=="👥 ملګري دعوت کول":
        link=f"https://t.me/{BOT_USERNAME}?start={uid}"
        await update.message.reply_text(f"🔗 ستا لینک:\n{link}")

    # ===== MY REFERRALS =====
    elif text=="✏️ ستا دعوت کوونکي":
        cur.execute("SELECT name FROM users WHERE ref=?", (uid,))
        data=cur.fetchall()

        if not data:
            await update.message.reply_text("❌ هیڅ څوک دې نه دي دعوت کړي")
        else:
            msg="👥 ستا دعوت کوونکي:\n\n"
            for i,x in enumerate(data,1):
                msg+=f"{i}- {x[0]}\n"

            await update.message.reply_text(msg)

    # ===== TOP REFERRALS =====
    elif text=="🏅 غوره دعوت کوونکي":
        cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 10")
        data=cur.fetchall()

        msg="🏆 غوره دعوت کوونکي:\n\n"
        for i,(name,inv) in enumerate(data,1):
            msg+=f"{i}- {name} ({inv})\n"

        await update.message.reply_text(msg)

    # ===== ADMIN BROADCAST =====
    elif text=="📢 Broadcast" and uid==ADMIN_ID:
        await update.message.reply_text("✉️ مسیج ولیکه:")
        context.user_data["broadcast"]=True

    elif context.user_data.get("broadcast") and uid==ADMIN_ID:
        msg=text
        cur.execute("SELECT id FROM users")
        users=cur.fetchall()

        for u in users:
            try:
                await context.bot.send_message(u[0],msg)
            except:
                pass

        context.user_data["broadcast"]=False
        await update.message.reply_text("✅ واستول شو")

    # ===== STATS =====
    elif text=="📊 Stats" and uid==ADMIN_ID:
        cur.execute("SELECT COUNT(*) FROM users")
        total=cur.fetchone()[0]

        await update.message.reply_text(f"👥 ټول یوزران: {total}")

# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(MessageHandler(filters.TEXT,handler))

print("BOT READY")
app.run_polling()
