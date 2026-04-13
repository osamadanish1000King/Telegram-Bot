import sqlite3
import datetime
import os
import shutil

TOKEN = "8414495176:AAHt30wZaH4ScvdJG4L7Oi6NNJ0pDP_NmcU"

ADMIN_ID = 8289491009
BOT_USERNAME = "Earn_FreeAfghani_Bot"
CHANNEL_LINK = "https://t.me/Afghani_Earn_Bank"

INVITE_REWARD = 4
DAILY_REWARD = 1
WEEKLY_REWARD = 5

# ===== RESTORE DB =====
if not os.path.exists("bot.db") and os.path.exists("backup.db"):
    shutil.copy("backup.db", "bot.db")
import json 
from telegram import *
from telegram.ext import *
# ===== DB =====
# ===== DB =====
conn = sqlite3.connect("bot.db", check_same_thread=False)
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY,
    name TEXT,
    balance REAL DEFAULT 0,
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
import shutil

def backup_db():
    try:
        shutil.copy("bot.db", "backup.db")
    except:
        pass

# ===== FORCE JOIN ====
def get_user(uid, name, ref=None):
    cur.execute("SELECT * FROM users WHERE id=?", (uid,))
    user = cur.fetchone()   # 👈 اول value واخله

    if not user:
        cur.execute("INSERT INTO users(id,name,ref) VALUES(?,?,?)", (uid, name, ref))
        conn.commit()
        

        # ✅ invite reward only first time
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?", (INVITE_REWARD, ref))
            conn.commit()
        
        # ✅ invite abuse fix
        if ref and ref != uid:
            cur.execute("UPDATE users SET balance=balance+?,invites=invites+1 WHERE id=?", (INVITE_REWARD, ref))
            conn.commit()
            

def set_setting(k, v):
    cur.execute("REPLACE INTO settings(key,value) VALUES(?,?)", (k, v))
    conn.commit()
    

def get_setting(k):
    cur.execute("SELECT value FROM settings WHERE key=?", (k,))
    d = cur.fetchone()
    return d[0] if d else None

def time_left(last, sec):
    if not last:
        return 0
    last = datetime.datetime.fromisoformat(last)
    return sec - (datetime.datetime.now() - last).total_seconds()


# ===== FORCE JOIN =====
# ===== MULTI FORCE JOIN (څو چینلونه) =====
def get_force_channels():
    data = get_setting("force_channels")
    if data:
        try:
            return json.loads(data)
        except:
            return []
    return []

def set_force_channels(channels):
    set_setting("force_channels", json.dumps(channels))

async def is_joined(uid, bot, link):
    try:
        chat = link.replace("https://t.me/", "@")
        member = await bot.get_chat_member(chat, uid)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

async def is_joined_all(uid, bot):
    channels = get_force_channels()
    if not channels:
        return True
    for link in channels:
        if not await is_joined(uid, bot, link):
            return False
    return True

def force_join_keyboard():
    channels = get_force_channels()
    if not channels:
        return None
    buttons = []
    for link in channels:
        channel_name = link.replace("https://t.me/", "").replace("@", "")
        buttons.append([InlineKeyboardButton(f"📢 {channel_name}", url=link)])
    buttons.append([InlineKeyboardButton("✅ چک کړم - ټول جواین شوي", callback_data="check_force")])
    return InlineKeyboardMarkup(buttons)
# ===== KEYBOARDS =====
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
        ["👥 ملګري دعوت کول"],
        ["📢 ټاسک"],
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
        ["♻️ Task Reset"],
        ["📊 Stats", "📋 Users"],
        ["💰 Add Balance"],
        ["🔙 وتل"]
    ], resize_keyboard=True)

# ===== START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    name = update.effective_user.first_name

    ref = int(context.args[0]) if context.args else None
    get_user(uid, name, ref)

    # ===== FORCE JOIN =====
    if not await is_joined_all(uid, context.bot):
        await update.message.reply_text(
            "<b>❗ مهرباني وکړه ټول چینلونه جواین کړه</b>",
            reply_markup=force_join_keyboard(),
            parse_mode='HTML'
        )
        return

    # ===== MAIN MENU =====
    await update.message.reply_text(
        "<b>✅ ربات ته ښه راغلاست</b>",
        reply_markup=main_kb(),
        parse_mode='HTML'
    )
    # ===== START MESSAGE =====
    msg = """
<b>🌟 ښه راغلاست ګرانه کاروونکي! 👋

💸 دلته ته کولی شې ډېري په اسانۍ سره افغانۍ وګټې!

🎯 څنګه کار کوي؟
👥 ملګري دعوت کړه
🎁 بونسونه ترلاسه کړه
📢 ټاسکونه ترسره کړه

💰 هر دعوت = جایزه
🎁 ورځنۍ او اوونیز بونس هم شته!

🚀 همدا اوس پیل کړه او عاید جوړ کړه 👇

👇 له مینو څخه یو انتخاب وکړه</b>
"""

    await update.message.reply_text(
        msg,
        reply_markup=main_kb(),
        parse_mode='HTML'
    )
# ===== CALLBACK =====
# ===== CALLBACK (TASK DONE) =====
async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # ✅ task abuse fix
    cur.execute("SELECT task_done FROM users WHERE id=?", (uid,))
    row = cur.fetchone()

    if row and row[0] == 1:
        await q.answer("❌ مخکې دې اخیستی", show_alert=True)
        return

    cur.execute("UPDATE users SET balance=balance+1,task_done=1 WHERE id=?", (uid,))
    conn.commit()
    backup_db()

    await q.edit_message_text("<b>✅ Done +1</b>", parse_mode='HTML')

# ===== FORCE JOIN CHECK BUTTON =====
async def check_force(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    # چک کوي چې ټول چینلونه جواین شوي که نه
    if await is_joined_all(uid, context.bot):
        await q.message.delete()

        await context.bot.send_message(
            chat_id=uid,
            text="<b>✅ ته ټول چینلونه جواین کړي! ربات شروع شو 🎉</b>",
            reply_markup=main_kb(),
            parse_mode='HTML'
        )
    else:
        await q.answer("❌ لا هم ټول چینلونه نه دي جواین شوي!", show_alert=True)
#handler
async def handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if not update.message:
            return

        uid = update.effective_user.id
        name = update.effective_user.first_name

        # ✅ user فقط یو ځل create شي
        cur.execute("SELECT id FROM users WHERE id=?", (uid,))
        if not cur.fetchone():
            get_user(uid, name)

        text = update.message.text or ""
        # ✅ MULTI FORCE JOIN CHECK
        if not await is_joined_all(uid, context.bot):
            await update.message.reply_text(
                "<b>❗ مهرباني وکړه ټول چینلونه جواین کړه</b>",
                reply_markup=force_join_keyboard(),
                parse_mode='HTML'
            )
            return


        # BACK
        if text == "🔙 وتل":
            await update.message.reply_text(
                "<b>🏠 اصلي مینو ته لاړې</b>",
                reply_markup=main_kb(),
                parse_mode='HTML'
            )
            return

        # ===== ADMIN =====
        if uid == ADMIN_ID and text == "/admin":
            await update.message.reply_text("<b>👑 Admin Panel</b>", reply_markup=admin_kb(), parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "📊 Stats":
            cur.execute("SELECT COUNT(*) FROM users")
            total = cur.fetchone()[0]
            await update.message.reply_text(f"<b>👥 ټول یوزر: {total}</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "📋 Users":
            cur.execute("SELECT id,name FROM users LIMIT 50")
            data = cur.fetchall()
            msg = "👥 Users:\n\n"
            for u in data:
                msg += f"{u[1]} - {u[0]}\n"
            await update.message.reply_text(f"<b>{msg}</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "💰 Add Balance":
            context.user_data["bal"] = True
            await update.message.reply_text("<b>uid او amount ولیکه\nمثال:\n123456 50</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and context.user_data.get("bal"):
            try:
                uid2, amount = text.split()
                cur.execute("UPDATE users SET balance=balance+? WHERE id=?", (float(amount), int(uid2)))
                conn.commit()
                backup_db()
                await update.message.reply_text("<b>✅ اضافه شو</b>", parse_mode='HTML')
            except:
                await update.message.reply_text("<b>❌ غلط format</b>", parse_mode='HTML')
            context.user_data["bal"] = False
            return

        if uid == ADMIN_ID and text == "📢 Broadcast":
            context.user_data["b"] = True
            await update.message.reply_text("<b>✉️ مسيج راولیږه</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and context.user_data.get("b"):
            context.user_data["b"] = False
            cur.execute("SELECT id FROM users")
            for u in cur.fetchall():
                try:
                    await context.bot.send_message(u[0], text)   # ادمین مسيج هماغه شان استول کیږي
                except:
                    pass
            await update.message.reply_text("<b>✅ واستول شو</b>", parse_mode='HTML')
            return

        # ➕ Force Join Add
        if uid == ADMIN_ID and text == "➕ Force Join Add":
            context.user_data["f"] = True
            await update.message.reply_text("<b>🔗 لینک راکړه</b>", parse_mode='HTML')
            return

        # 📥 Force Join لینک save کول (Multi)
        if uid == ADMIN_ID and context.user_data.get("f") and text.startswith("http"):
            channels = get_force_channels()

            if text not in channels:
                channels.append(text)

            set_force_channels(channels)

            context.user_data["f"] = False
            await update.message.reply_text("<b>✅ چینل اضافه شو</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "➖ Force Join Del":
            set_setting("force_join", "")
            await update.message.reply_text("<b>❌ حذف شو</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "➕ Task Add":
            context.user_data["t"] = True
            await update.message.reply_text("<b>🔗 لینک راکړه</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and context.user_data.get("t") and text.startswith("http"):
            set_setting("task", text)
            context.user_data["t"] = False
            await update.message.reply_text("<b>✅ Task اضافه شو</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "➖ Task Del":
            set_setting("task", "")
            await update.message.reply_text("<b>❌ حذف شو</b>", parse_mode='HTML')
            return

        if uid == ADMIN_ID and text == "♻️ Task Reset":
            cur.execute("UPDATE users SET task_done=0")
            conn.commit()
            backup_db()
            await update.message.reply_text("<b>✅ ریست شو</b>", parse_mode='HTML')
            return

        # ===== FORCE JOIN CHECK =====
        

        # ===== USER COMMANDS =====
        if update.message.contact:
            phone = update.message.contact.phone_number
            cur.execute("UPDATE users SET phone=? WHERE id=?", (phone, uid))
            conn.commit()
            backup_db()
            await update.message.reply_text("<b>✅ شمېره ثبت شوه</b>", reply_markup=main_kb(), parse_mode='HTML')

        elif text == "📞 شمېره ثبت کړی":
            await update.message.reply_text("<b>📲 خپله شمېره واستوه</b>", reply_markup=phone_kb(), parse_mode='HTML')

        elif text == "🏅 غوره دعوت کوونکي":
            cur.execute("SELECT name,invites FROM users ORDER BY invites DESC LIMIT 5")
            data = cur.fetchall()
            if not data:
                await update.message.reply_text("<b>❌ معلومات نشته</b>", parse_mode='HTML')
                return
            msg = "🏆 غوره دعوت کوونکي:\n\n"
            for i, u in enumerate(data, 1):
                msg += f"{i}. {u[0]} - {u[1]}\n"
            await update.message.reply_text(f"<b>{msg}</b>", parse_mode='HTML')

        elif text == "✏️ ستا دعوت کوونکي":
            cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            invites = row[0] if row else 0
            await update.message.reply_text(f"<b>👥 ستا دعوتونه: {invites}</b>", parse_mode='HTML')

        elif text == "🎁 ورځنۍ بونس":
            cur.execute("SELECT daily FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            last = row[0] if row else None
            left = time_left(last, 86400)

            if last and left > 0:
                h = int(left // 3600)
                m = int((left % 3600) // 60)
                await update.message.reply_text(f"<b>⏳ پاتې وخت: {h}h {m}m</b>", parse_mode='HTML')
            else:
                cur.execute("UPDATE users SET balance=balance+?,daily=? WHERE id=?",
                            (DAILY_REWARD, datetime.datetime.now().isoformat(), uid))
                conn.commit()
                backup_db()
                await update.message.reply_text("<b>🎉 1 افغانۍ ترلاسه شوې</b>", parse_mode='HTML')

        elif text == "🎁 اوونیز بونس":
            cur.execute("SELECT weekly FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            last = row[0] if row else None
            left = time_left(last, 604800)

            if last and left > 0:
                await update.message.reply_text("<b>⏳ وروسته بیا هڅه وکړه</b>", parse_mode='HTML')
            else:
                cur.execute("UPDATE users SET balance=balance+?,weekly=? WHERE id=?",
                            (WEEKLY_REWARD, datetime.datetime.now().isoformat(), uid))
                conn.commit()
                backup_db()
                await update.message.reply_text("<b>🎉 5 افغانۍ ترلاسه شوې</b>", parse_mode='HTML')

        elif text == "💰 افغانۍ زیاتول":
            await update.message.reply_text("<b>👇 انتخاب کړه</b>", reply_markup=invite_kb(), parse_mode='HTML')

        elif text == "👥 ملګري دعوت کول":
            cur.execute("SELECT invites FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            invites = row[0] if row else 0
            link = f"https://t.me/{BOT_USERNAME}?start={uid}"
            await update.message.reply_text(
                f"<b>👥 ستا دعوت: {invites}\n\n🔗 لینک:\n{link}\n\n🎁 هر دعوت = {INVITE_REWARD} افغانۍ</b>",
                parse_mode='HTML'
            )

        elif text == "🏦 ایزیلوډ":
            await update.message.reply_text("<b>⚠️ لږ تر لږه 50 افغانۍ پکار دي</b>", parse_mode='HTML')

        elif text == "📢 ټاسک":
            link = get_setting("task")
            if not link:
                await update.message.reply_text("<b>❌ ټاسک نشته</b>", parse_mode='HTML')
                return
            await update.message.reply_text(
                "<b>📢 ټاسک ترسره کړه 👇</b>",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("📢 چینل", url=link)],
                    [InlineKeyboardButton("✅ Done", callback_data="done")]
                ]),
                parse_mode='HTML'
            )

        elif text == "❗ خپل حساب معلومات":
            cur.execute("SELECT balance,invites FROM users WHERE id=?", (uid,))
            row = cur.fetchone()
            b, i = row if row else (0, 0)
            await update.message.reply_text(
                f"<b>💳 کارن = {name}\n\n🆔 {uid}\n\n💰 بیلانس = {b}\n👥 دعوتونه = {i}</b>",
                parse_mode='HTML'
            )

        elif text == "📊 د ربات په اړه":
            await update.message.reply_text(
                "<b>📊 د ربات په اړه:\n\n"
                "دا ربات تاسو ته اجازه درکوي چې د ملګرو دعوتولو، ورځني او اوونیز بونس، "
                "او ټاسکونو له لارې افغانۍ وګټئ!\n\n"
                "ډیر ښه وخت ولرئ! 🎉</b>",
                parse_mode='HTML'
            )

    except Exception as e:
        print("ERROR:", e)

# ===== RUN =====
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))

# ✅ TASK DONE BUTTON
app.add_handler(CallbackQueryHandler(done, pattern="done"))

# ✅ FORCE JOIN CHECK BUTTON
app.add_handler(CallbackQueryHandler(check_force, pattern="check_force"))

# ✅ MAIN HANDLER
app.add_handler(MessageHandler(filters.TEXT | filters.CONTACT, handler))

print("BOT RUNNING...")
backup_db()
app.run_polling()
