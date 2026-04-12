import sqlite3
import datetime
import os
from telegram import *
from telegram.ext import *

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

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 100,
    invites INTEGER DEFAULT 0,
    ref INTEGER,
    phone TEXT,
    daily TEXT,
    weekly TEXT,
    task_done INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS settings(
    key TEXT PRIMARY KEY,
    value TEXT
)
""")

conn.commit()

# ===== FUNCTIONS =====
def get_user(uid, name, ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    if not cur.fetchone():
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)",(uid,name,ref))
        conn.commit()

        # ✅ invite abuse fix
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?",(INVITE_REWARD,ref))
            conn.commit()

def set_setting(k,v):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)",(k,v))
    conn.commit()

def get_setting(k):
    cur.execute("SELECT value FROM settings WHERE key=?",(k,))
    d=cur.fetchone()
    return d[0] if d else None

def time_left(last,sec):
    if not last:
        return 0
    last=datetime.datetime.fromisoformat(last)
    return sec-(datetime.datetime.now()-last).total_seconds()

# ===== FORCE JOIN =====
async def is_joined(uid, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, uid)
        return member.status in ["member","administrator","creator"]
    except:
        return False

def force_join_btn(link):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Join Channel", url=link)]
    ])

# ===== KEYBOARDS =====
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
        ["♻️ Task Reset"],
        ["📊 Stats","📋 Users"],
        ["💰 Add Balance"],
        ["🔙 وتل"]
    ],resize_keyboard=True)

# ===== START =====
async def start(update:Update,context:ContextTypes.DEFAULT_TYPE):
    uid=update.effective_user.id
    name=update.effective_user.first_name

    ref=int(context.args[0]) if context.args else None
    get_user(uid,name,ref)

    link=get_setting("force_join")
    if link and not await is_joined(uid,context.bot,link):
        await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
        return

    await update.message.reply_text("👇 له مینو څخه یو انتخاب وکړه",reply_markup=main_kb())

# ===== CALLBACK =====
async def done(update:Update,context:ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    await q.answer()

    uid=q.from_user.id

    # ✅ task abuse fix
    cur.execute("SELECT task_done FROM users WHERE id=?",(uid,))
    if cur.fetchone()[0] == 1:
        await q.answer("❌ مخکې دې اخیستی", show_alert=True)
        return

    cur.execute("UPDATE users SET balance=balance+1,task_done=1 WHERE id=?",(uid,))
    conn.commit()

    await q.edit_message_text("✅ Done +1")

# ===== HANDLER =====
async def handler(update:Update,context:ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

        uid=update.effective_user.id
        name=update.effective_user.first_name
        get_user(uid,name)

        text=update.message.text or ""

        # BACK
        if text=="🔙 وتل":
            await update.message.reply_text("🏠 اصلي مینو ته لاړې",reply_markup=main_kb())
            return

        # ===== ADMIN =====
        if uid==ADMIN_ID and text=="/admin":
            await update.message.reply_text("👑 Admin Panel",reply_markup=admin_kb())
            return

        if uid==ADMIN_ID and text=="📊 Stats":
            cur.execute("SELECT COUNT(*) FROM users")
            total=cur.fetchone()[0]
            await update.message.reply_text(f"👥 ټول یوزر: {total}")
            return

        if uid==ADMIN_ID and text=="📋 Users":
            cur.execute("SELECT id,name FROM users LIMIT 50")
            data=cur.fetchall()
            msg="👥 Users:\n\n"
            for u in data:
                msg+=f"{u[1]} - {u[0]}\n"
            await update.message.reply_text(msg)
            return

        if uid==ADMIN_ID and text=="💰 Add Balance":
            context.user_data["bal"]=True
            await update.message.reply_text("uid او amount ولیکه\nمثال:\n123456 50")
            return

        if uid==ADMIN_ID and context.user_data.get("bal"):
            try:
                uid2,amount=text.split()
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?",(float(amount),int(uid2)))
                conn.commit()
                await update.message.reply_text("✅ اضافه شو")
            except:
                await update.message.reply_text("❌ غلط format")
            context.user_data["bal"]=False
            return

        if uid==ADMIN_ID and text=="📢 Broadcast":
            context.user_data["b"]=True
            await update.message.reply_text("✉️ مسيج راولیږه")
            return

        if uid==ADMIN_ID and context.user_data.get("b"):
            context.user_data["b"]=False
            cur.execute("SELECT id FROM users")
            for u in cur.fetchall():
                try:
                    await context.bot.send_message(u[0],text)
                except:
                    pass
            await update.message.reply_text("✅ واستول شو")
            return

        if uid==ADMIN_ID and text=="➕ Force Join Add":
            context.user_data["f"]=True
            await update.message.reply_text("🔗 لینک راکړه")
            return

        if uid==ADMIN_ID and context.user_data.get("f") and text.startswith("http"):
            set_setting("force_join",text)
            context.user_data["f"]=False
            await update.message.reply_text("✅ Force Join اضافه شو")
            return

        if uid==ADMIN_ID and text=="➖ Force Join Del":
            set_setting("force_join","")
            await update.message.reply_text("❌ حذف شو")
            return

        if uid==ADMIN_ID and text=="➕ Task Add":
            context.user_data["t"]=True
            await update.message.reply_text("🔗 لینک راکړه")
            return

        if uid==ADMIN_ID and context.user_data.get("t") and text.startswith("http"):
            set_setting("task",text)
            context.user_data["t"]=False
            await update.message.reply_text("✅ Task اضافه شو")
            return

        if uid==ADMIN_ID and text=="➖ Task Del":
            set_setting("task","")
            await update.message.reply_text("❌ حذف شو")
            return

        if uid==ADMIN_ID and text=="♻️ Task Reset":
            cur.execute("UPDATE users SET task_done=0")
            conn.commit()
            await update.message.reply_text("✅ ریست شو")
            return

        # FORCE JOIN
        link=get_setting("force_join")
        if link and not await is_joined(uid,context.bot,link):
            await update.message.reply_text("❗ مهرباني وکړه چینل جواین کړه",reply_markup=force_join_btn(link))
            return

        # ===== USER =====
       # ===== USER =====
if text=="📞 شمېره ثبت کړی":
    await update.message.reply_text("📲 خپله شمېره واستوه",reply_markup=phone_kb())

elif update.message.contact:
    phone=update.message.contact.phone_number
    cur.execute("UPDATE users SET phone=? WHERE id=?",(phone,uid))
    conn.commit()
    await update.message.reply_text("✅ شمېره ثبت شوه",reply_markup=main_kb())

elif text=="🏅 غوره دعوت کوونکي":
    cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
    data=cur.fetchall()

    if not data:
        await update.message.reply_text("❌ معلومات نشته")
        return

    msg="🏆 غوره دعوت کوونکي:\n\n"
    for i,u in enumerate(data,1):
        msg+=f"{i}. {u[0]} - {u[1]}\n"

    await update.message.reply_text(msg)

elif text=="✏️ ستا دعوت کوونکي":
    cur.execute("SELECT invites FROM users WHERE id=?",(uid,))
    invites=cur.fetchone()[0]
    await update.message.reply_text(f"👥 ستا دعوتونه: {invites}")

elif text=="🎁 ورځنۍ بونس":
    cur.execute("SELECT daily FROM users WHERE id=?",(uid,))
    last=cur.fetchone()[0]
    left=time_left(last,86400)

    if last and left>0:
        h=int(left//3600)
        m=int((left%3600)//60)
        await update.message.reply_text(f"⏳ پاتې وخت: {h}h {m}m")
    else:
        cur.execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?",
                    (DAILY_REWARD,datetime.datetime.now().isoformat(),uid))
        conn.commit()
        await update.message.reply_text("🎉 1 افغانۍ ترلاسه شوې")

elif text=="🎁 اوونیز بونس":
    cur.execute("SELECT weekly FROM users WHERE id=?",(uid,))
    last=cur.fetchone()[0]
    left=time_left(last,604800)

    if last and left>0:
        await update.message.reply_text("⏳ وروسته بیا هڅه وکړه")
    else:
        cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",
                    (WEEKLY_REWARD,datetime.datetime.now().isoformat(),uid))
        conn.commit()
        await update.message.reply_text("🎉 5 افغانۍ ترلاسه شوې")

elif text=="💰 افغانۍ زیاتول":
    await update.message.reply_text("👇 انتخاب کړه",reply_markup=invite_kb())

elif text=="👥 ملګري دعوت کول":
    cur.execute("SELECT invites FROM users WHERE id=?",(uid,))
    invites=cur.fetchone()[0]
    link=f"https://t.me/{BOT_USERNAME}?start={uid}"

    await update.message.reply_text(f"""👥 ستا دعوت: {invites}

🔗 لینک:
{link}

🎁 هر دعوت = {INVITE_REWARD} افغانۍ""")

elif text=="🏦 ایزیلوډ":
    await update.message.reply_text("""⚠️

د ایزیلوډ ترلاسه کولو لپاره:

💰 باید لږ تر لږه 50 افغانۍ پوره کړې

👥 ملګري دعوت کړه
🎁 بونسونه واخله

کله چې 50 افغانۍ پوره کړې،
نو بیا ایزیلوډ درکول کېږي ✅""")

elif text=="📢 ټاسک":
    link=get_setting("task")
    if not link:
        await update.message.reply_text("❌ ټاسک نشته")
        return

    await update.message.reply_text(
        "📢 ټاسک ترسره کړه 👇",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📢 چینل",url=link)],
            [InlineKeyboardButton("✅ Done",callback_data="done")]
        ])
    )

elif text=="❗ خپل حساب معلومات":
    cur.execute("SELECT balance,invites FROM users WHERE id=?",(uid,))
    b,i=cur.fetchone()

    await update.message.reply_text(f"""💳 کارن = {name}

🆔 {uid}

💰 بیلانس = {b}
👥 دعوتونه = {i}""")
# ===== RUN =====
app=Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start",start))
app.add_handler(CallbackQueryHandler(done))
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT,handler))

print("BOT RUNNING...")
app.run_polling()
