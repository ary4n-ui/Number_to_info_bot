# ============================================================
# OSINT Telegram Bot - FINAL COMPLETE WORKING CODE (SINGLE FILE)
# Features:
#   ✅ Number Search (/num 9876543210 + menu button)
#   ✅ Credits System + Free Welcome Bonus
#   ✅ QR Payment + Screenshot Approval
#   ✅ Referral System
#   ✅ Admin Panel (Video, QR, Redeem, Broadcast, Stats)
#   ✅ Group Welcome (auto guide for new members)
#   ✅ Group /num support (reply in group + DM full result)
#   ✅ Funny "credits khatam" messages
#   ✅ Feedback System
# ============================================================
import aiohttp
import asyncio
import logging
import sqlite3
import random
from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
)
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)

# ============================================================
# CONFIG
# ============================================================
BOT_TOKEN = "8880226045:AAEq-rVSqxiHdzhXE4RGFrPUAUUmJQr1hss"
ADMIN_IDS = [5239668558]
API_BASE  = "https://geniushacker.vercel.app/api/number/ADITYA-LIFE-@EDITZ-7D23U6L7"
SUPPORT_LINK = "https://t.me/villanchk"

UPI_ID = "niranjan229899@fam"
UPI_NAME = "Niranjan kispota"
QR_IMAGE_URL = ""  # Optional direct URL (admin panel se bhi set kar sakte ho)

FREE_CREDITS = 5
REFERRAL_CREDITS = 1
SEARCH_COST = 1

WELCOME_CAPTION = (
    "🎬 <b>Welcome to OSINT Bot!</b>\n\n"
    "🔍 Number search karo: <code>/num 9876543210</code>\n"
    "💰 Credits kharido\n"
    "👥 Refer karke free credits kamao"
)

DB = "bot.db"

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# ============================================================
# DATABASE
# ============================================================
def init_db():
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        credits INTEGER DEFAULT 0,
        referrer INTEGER DEFAULT NULL,
        referred_by_count INTEGER DEFAULT 0,
        free_claimed INTEGER DEFAULT 0
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS redeem(
        code TEXT PRIMARY KEY,
        credits INTEGER,
        used_by INTEGER DEFAULT NULL
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS payments(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        file_id TEXT,
        amount INTEGER,
        credits INTEGER,
        status TEXT DEFAULT 'pending',
        msg_id INTEGER
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS settings(
        key TEXT PRIMARY KEY,
        value TEXT
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        message TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""")
    con.commit(); con.close()

def set_setting(key, value):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("INSERT OR REPLACE INTO settings(key, value) VALUES(?,?)", (key, value))
    con.commit(); con.close()

def get_setting(key, default=None):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT value FROM settings WHERE key=?", (key,))
    r = cur.fetchone(); con.close()
    return r[0] if r else default

def save_feedback(uid, username, message):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("INSERT INTO feedback(user_id, username, message) VALUES(?,?,?)",
                (uid, username, message))
    fid = cur.lastrowid
    con.commit(); con.close()
    return fid

def add_user(uid, username, referrer=None):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT user_id FROM users WHERE user_id=?", (uid,))
    exists = cur.fetchone()
    if not exists:
        cur.execute(
            "INSERT INTO users(user_id, username, referrer, credits) VALUES(?,?,?,?)",
            (uid, username, referrer, 0)
        )
        if referrer and referrer != uid:
            cur.execute("SELECT user_id FROM users WHERE user_id=?", (referrer,))
            if cur.fetchone():
                cur.execute("UPDATE users SET credits = credits + ? WHERE user_id=?",
                            (REFERRAL_CREDITS, referrer))
                cur.execute("UPDATE users SET referred_by_count = referred_by_count + 1 WHERE user_id=?",
                            (referrer,))
        con.commit()
    con.close()
    return not exists

def get_credits(uid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT credits FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone(); con.close()
    return r[0] if r else 0

def add_credits(uid, amount):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (amount, uid))
    con.commit(); con.close()

def deduct_credit(uid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("UPDATE users SET credits = credits - 1 WHERE user_id=? AND credits > 0", (uid,))
    ok = cur.rowcount > 0
    con.commit(); con.close()
    return ok

def claim_free(uid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT free_claimed FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone()
    if not r:
        con.close(); return False
    if r[0] == 1:
        con.close(); return False
    cur.execute("UPDATE users SET free_claimed=1, credits = credits + ? WHERE user_id=?",
                (FREE_CREDITS, uid))
    con.commit(); con.close()
    return True

def create_redeem(code, credits):
    con = sqlite3.connect(DB); cur = con.cursor()
    try:
        cur.execute("INSERT INTO redeem(code, credits) VALUES(?,?)", (code, credits))
        con.commit(); ok = True
    except sqlite3.IntegrityError:
        ok = False
    con.close(); return ok

def use_redeem(code, uid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT credits, used_by FROM redeem WHERE code=?", (code,))
    r = cur.fetchone()
    if not r or r[1] is not None:
        con.close(); return None
    credits = r[0]
    cur.execute("UPDATE redeem SET used_by=? WHERE code=?", (uid, code))
    cur.execute("UPDATE users SET credits = credits + ? WHERE user_id=?", (credits, uid))
    con.commit(); con.close()
    return credits

def all_users():
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = [r[0] for r in cur.fetchall()]
    con.close(); return rows

def create_payment(uid, file_id, amount, credits):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("INSERT INTO payments(user_id, file_id, amount, credits) VALUES(?,?,?,?)",
                (uid, file_id, amount, credits))
    pid = cur.lastrowid
    con.commit(); con.close()
    return pid

def set_payment_msg(pid, msg_id):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("UPDATE payments SET msg_id=? WHERE id=?", (msg_id, pid))
    con.commit(); con.close()

def get_payment(pid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT user_id, file_id, amount, credits, status FROM payments WHERE id=?", (pid,))
    r = cur.fetchone(); con.close()
    return r

def update_payment_status(pid, status):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("UPDATE payments SET status=? WHERE id=?", (status, pid))
    con.commit(); con.close()

def get_referral_count(uid):
    con = sqlite3.connect(DB); cur = con.cursor()
    cur.execute("SELECT referred_by_count FROM users WHERE user_id=?", (uid,))
    r = cur.fetchone(); con.close()
    return r[0] if r else 0

# ============================================================
# HELPERS
# ============================================================
def is_admin(uid):
    return uid in ADMIN_IDS

def main_menu(uid=None):
    kb = [
        ["🔍 Search Number"],
        ["💰 Buy Credit", "🎁 Redeem"],
        ["👥 Refer & Earn", "🆘 Support"],
        ["📩 Feedback", "ℹ️ Help"]
    ]
    if uid and is_admin(uid):
        kb.append(["🛠 Admin Panel"])
    return ReplyKeyboardMarkup(kb, resize_keyboard=True)

async def fetch_number(number):
    url = f"{API_BASE}?number={number}"
    try:
        async with aiohttp.ClientSession() as s:
            async with s.get(url, timeout=20) as r:
                return await r.json()
    except Exception as e:
        logging.error(f"API error: {e}")
        return None

def get_funny_no_credit_msg(name="bhai"):
    msgs = [
        f"😭 {name}, credits khatam!\n\n"
        "💸 ChatGPT bhi free me nahi deta, hum kya cheez hai 😅\n\n"
        "💰 Buy karo ya 👥 refer karke free credits kamao!",

        f"🚨 {name} ka CREDIT ACCOUNT KHAALI!\n\n"
        "🏦 Itna khaali hai jitna Monday morning ka wallet 😂\n\n"
        "💰 ₹50 me 10 credits — QR scan karo!",

        f"🤡 {name} bhai, credits khatam!\n\n"
        "😭 Google bhi nahi bata raha, hum kya batayenge?\n\n"
        "💰 Buy Credits dabao ya 👥 Refer & Earn karo!",

        f"💀 {name}, credit balance = ₹0\n\n"
        "😂 Itna gareeb feel ho raha hai ki bot bhi ro raha hai\n\n"
        "💰 Buy karo bhai, ₹50 me 10 credits!"
    ]
    return random.choice(msgs)

def format_osint_result(number, data):
    """API response ko sundar format karo"""
    if isinstance(data, dict):
        lines = [f"📱 <b>Number:</b> <code>{number}</code>\n"]
        result = data.get("result") or data.get("data") or data
        if isinstance(result, dict):
            for k, v in result.items():
                if v and str(v).strip() and str(v).lower() not in ("none", "null", ""):
                    key = k.replace("_", " ").title()
                    lines.append(f"• <b>{key}:</b> {v}")
        elif isinstance(result, list):
            for i, item in enumerate(result, 1):
                lines.append(f"{i}. {item}")
        elif isinstance(result, str):
            lines.append(result)
        else:
            lines.append(f"<pre>{data}</pre>")
        return "\n".join(lines)
    return f"📱 <b>{number}</b>\n\n<pre>{data}</pre>"

# ============================================================
# COMMAND HANDLERS
# ============================================================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    args = ctx.args
    referrer = None
    if args and args[0].startswith("ref_"):
        try:
            referrer = int(args[0].replace("ref_", ""))
        except Exception:
            referrer = None

    is_new = add_user(u.id, u.username or "", referrer)

    bonus_msg = ""
    if is_new:
        if claim_free(u.id):
            bonus_msg = f"\n\n🎉 <b>Welcome Bonus:</b> +{FREE_CREDITS} Free Credits!"

    video_id = get_setting("welcome_video")
    if video_id:
        try:
            await update.message.reply_video(
                video=video_id,
                caption=WELCOME_CAPTION,
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"Video send fail: {e}")

    await update.message.reply_text(
        f"👋 Welcome {u.first_name}!{bonus_msg}\n\n"
        f"💳 Credits: {get_credits(u.id)}\n\n"
        "Neeche menu se option chuno\n"
        "🔍 Ya direct: <code>/num 9876543210</code>",
        parse_mode="HTML",
        reply_markup=main_menu(u.id)
    )

async def help_cmd(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "ℹ️ <b>Help</b>\n\n"
        f"🔍 <b>Search:</b> <code>/num 9876543210</code> ({SEARCH_COST} credit)\n"
        "💰 Buy Credit — QR scan karke payment\n"
        "🎁 Redeem — code se free credits\n"
        f"👥 Refer & Earn — har referral pe +{REFERRAL_CREDITS} credits\n"
        "📩 Feedback — suggestion/issue bhejo\n"
        "🆘 Support — admin se baat karo\n\n"
        f"🎁 Naye users ko {FREE_CREDITS} free credits milte hai!\n\n"
        "📖 <b>Group me use:</b> <code>/num 9876543210</code>",
        parse_mode="HTML"
    )

async def buy_credit(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    qr = get_setting("qr_image") or QR_IMAGE_URL or None

    caption = (
        "💰 <b>Buy Credits</b>\n\n"
        "💵 <b>Plans:</b>\n"
        "• 10 credits — ₹50\n"
        "• 50 credits — ₹200\n"
        "• 100 credits — ₹350\n\n"
        f"💳 <b>UPI ID:</b> <code>{UPI_ID}</code>\n"
        f"👤 <b>Name:</b> {UPI_NAME}\n\n"
        "📲 <b>QR scan karke payment karo</b>\n\n"
        "📸 <b>Payment ke baad screenshot yahan bhejo.</b>\n"
        "Admin verify karke credits add karega."
    )

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📞 Contact Admin", url=SUPPORT_LINK)]
    ])

    if qr:
        try:
            await update.message.reply_photo(
                photo=qr, caption=caption, parse_mode="HTML", reply_markup=kb
            )
        except Exception as e:
            logging.error(f"QR send fail: {e}")
            await update.message.reply_text(caption, parse_mode="HTML", reply_markup=kb)
    else:
        await update.message.reply_text(
            caption + "\n\n⚠️ QR abhi set nahi hai. Admin se contact karo.",
            parse_mode="HTML", reply_markup=kb
        )

    ctx.user_data["awaiting"] = "screenshot"

async def referral(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    bot_info = await ctx.bot.get_me()
    link = f"https://t.me/{bot_info.username}?start=ref_{uid}"
    count = get_referral_count(uid)
    await update.message.reply_text(
        f"👥 <b>Refer & Earn</b>\n\n"
        f"Har successful referral pe aapko <b>+{REFERRAL_CREDITS} credits</b> milenge!\n\n"
        f"🔗 <b>Aapka Referral Link:</b>\n<code>{link}</code>\n\n"
        f"📊 <b>Total Referrals:</b> {count}\n"
        f"💳 <b>Credits Earned:</b> {count * REFERRAL_CREDITS}",
        parse_mode="HTML"
    )

async def support(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("💬 Contact", url=SUPPORT_LINK)]])
    await update.message.reply_text("🆘 Support ke liye contact karo:", reply_markup=kb)

async def search_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if get_credits(uid) <= 0:
        await update.message.reply_text(
            get_funny_no_credit_msg(update.effective_user.first_name),
            reply_markup=main_menu(uid)
        )
        return
    ctx.user_data["awaiting"] = "number"
    await update.message.reply_text("📱 10-digit mobile number bhejo:")

async def redeem_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["awaiting"] = "redeem"
    await update.message.reply_text("🎁 Redeem code bhejo:")

async def feedback_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    ctx.user_data["awaiting"] = "feedback"
    await update.message.reply_text(
        "📩 <b>Feedback / Suggestion</b>\n\n"
        "Apni baat, suggestion ya issue likh ke bhejo.\n"
        "Admin tak pahunch jayega ✅",
        parse_mode="HTML"
    )

# ============================================================
# /num COMMAND (Private + Group)
# ============================================================
async def num_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Private chat me /num"""
    uid = update.effective_user.id
    name = update.effective_user.first_name or "bhai"

    if get_credits(uid) <= 0:
        await update.message.reply_text(
            get_funny_no_credit_msg(name),
            reply_markup=main_menu(uid)
        )
        return

    if not ctx.args:
        await update.message.reply_text(
            "📱 <b>Usage:</b> <code>/num 9876543210</code>",
            parse_mode="HTML"
        )
        return

    number = ctx.args[0].strip()
    if not number.isdigit() or len(number) != 10:
        await update.message.reply_text(
            "❌ Invalid number!\n10-digit mobile number bhejo.\n\n"
            "Example: <code>/num 9876543210</code>",
            parse_mode="HTML"
        )
        return

    if not deduct_credit(uid):
        await update.message.reply_text("❌ Credit deduct nahi hua. Try again.")
        return

    msg = await update.message.reply_text(
        f"🔍 <b>Searching:</b> <code>{number}</code>\n⏳ Please wait...",
        parse_mode="HTML"
    )

    data = await fetch_number(number)

    if not data:
        add_credits(uid, 1)
        await msg.edit_text("❌ API se data nahi mila.\n✅ Credit refund kar diya.")
        return

    result = format_osint_result(number, data)
    await msg.edit_text(
        f"{result}\n\n💳 <b>Remaining Credits:</b> {get_credits(uid)}",
        parse_mode="HTML"
    )


async def num_group_command(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Group me /num — short reply in group + full result in DM"""
    if update.effective_chat.type == "private":
        await num_command(update, ctx)
        return

    uid = update.effective_user.id
    name = update.effective_user.first_name or "bhai"
    add_user(uid, update.effective_user.username or "")

    if not ctx.args or not ctx.args[0].isdigit() or len(ctx.args[0]) != 10:
        await update.message.reply_text(
            f"❌ {name}, sahi number bhejo!\n"
            f"Example: <code>/num 9876543210</code>",
            parse_mode="HTML"
        )
        return

    number = ctx.args[0]

    if get_credits(uid) <= 0:
        await update.message.reply_text(get_funny_no_credit_msg(name))
        return

    if not deduct_credit(uid):
        return

    msg = await update.message.reply_text(
        f"🔍 <b>Searching:</b> <code>{number}</code> for {name}...",
        parse_mode="HTML"
    )

    data = await fetch_number(number)

    if not data:
        add_credits(uid, 1)
        await msg.edit_text("❌ Data nahi mila. Credit refund ✅")
        return

    result = format_osint_result(number, data)

    await msg.edit_text(
        f"✅ <b>Result ready for</b> <code>{number}</code>\n\n"
        f"📩 Full details {name} ki DM me bheji gayi!",
        parse_mode="HTML"
    )

    try:
        await ctx.bot.send_message(
            uid,
            f"{result}\n\n💳 <b>Remaining:</b> {get_credits(uid)}",
            parse_mode="HTML"
        )
    except Exception as e:
        logging.error(f"DM fail: {e}")
        await update.message.reply_text(
            f"⚠️ {name}, DM band hai. Yahan result:\n\n{result}",
            parse_mode="HTML"
        )

# ============================================================
# GROUP WELCOME
# ============================================================
GROUP_WELCOME_TEXT = """
🎉 <b>Welcome {name}!</b> 🎉

🤖 Ye hai <b>OSINT Number Search Bot</b>

━━━━━━━━━━━━━━━━━━
🎯 <b>Bot kya karta hai?</b>
━━━━━━━━━━━━━━━━━━
🔍 Kisi bhi mobile number ki info
📍 Owner details, network
📸 Social media profiles

━━━━━━━━━━━━━━━━━━
📖 <b>Kaise use kare?</b>
━━━━━━━━━━━━━━━━━━
1️⃣ Type: <code>/num 9876543210</code>
2️⃣ Result DM me aayega (1 credit)
3️⃣ Naye users ko <b>10 FREE credits</b> 🎁

━━━━━━━━━━━━━━━━━━
💰 <b>Credits khatam?</b>
━━━━━━━━━━━━━━━━━━
• 💰 Buy Credits (QR se ₹50 me 10)
• 👥 Refer & Earn (+1 free)
• 🎁 Redeem codes

👇 <b>Try karo:</b>
<code>/num 9876543210</code>

🆘 Help: /help
"""

async def group_welcome(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    for member in update.message.new_chat_members:
        if member.is_bot:
            continue
        add_user(member.id, member.username or "")
        try:
            await update.message.reply_text(
                GROUP_WELCOME_TEXT.format(name=member.first_name),
                parse_mode="HTML",
                disable_web_page_preview=True
            )
        except Exception as e:
            logging.error(f"Group welcome fail: {e}")

# ============================================================
# TEXT / MEDIA HANDLER
# ============================================================
async def handle_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return
    text = update.message.text.strip()
    uid = update.effective_user.id
    awaiting = ctx.user_data.get("awaiting")

    # Admin inputs
    if is_admin(uid):
        if awaiting == "admin_redeem":
            parts = text.split()
            if len(parts) != 2 or not parts[1].isdigit():
                await update.message.reply_text(
                    "❌ Format: <code>CODE CREDITS</code>", parse_mode="HTML"
                )
                return
            code, credits = parts[0].upper(), int(parts[1])
            if create_redeem(code, credits):
                await update.message.reply_text(
                    f"✅ Redeem code banaya:\n<code>{code}</code> → {credits} credits",
                    parse_mode="HTML"
                )
                ctx.user_data["awaiting"] = None
            else:
                await update.message.reply_text("❌ Ye code already exists.")
            return

        if awaiting == "admin_broadcast":
            ctx.user_data["awaiting"] = None
            users = all_users()
            sent, fail = 0, 0
            msg = await update.message.reply_text(f"📢 Broadcasting to {len(users)} users...")
            for u in users:
                try:
                    await update.message.copy(chat_id=u)
                    sent += 1
                    await asyncio.sleep(0.05)
                except Exception:
                    fail += 1
            await msg.edit_text(f"✅ Broadcast done!\n✔ Sent: {sent}\n✖ Fail: {fail}")
            return

    # Feedback
    if awaiting == "feedback":
        ctx.user_data["awaiting"] = None
        u = update.effective_user
        fid = save_feedback(u.id, u.username or "N/A", text)
        await update.message.reply_text(
            f"✅ Feedback bhej diya!\n🆔 ID: <code>{fid}</code>\n\nThanks 🙏",
            parse_mode="HTML"
        )
        notify = (
            f"📩 <b>New Feedback</b>\n\n"
            f"🆔 #{fid}\n"
            f"👤 {u.first_name} (@{u.username or 'N/A'})\n"
            f"🆔 <code>{u.id}</code>\n\n"
            f"💬 {text}"
        )
        for admin in ADMIN_IDS:
            try:
                await ctx.bot.send_message(admin, notify, parse_mode="HTML")
            except Exception as e:
                logging.error(f"Feedback notify fail: {e}")
        return

    # Redeem code
    if awaiting == "redeem":
        ctx.user_data["awaiting"] = None
        credits = use_redeem(text.upper(), uid)
        if credits:
            await update.message.reply_text(
                f"✅ Redeem successful!\n+{credits} credits added.\n\n"
                f"💳 Balance: {get_credits(uid)}"
            )
        else:
            await update.message.reply_text("❌ Invalid ya already used code.")
        return

    # Number from menu button
    if awaiting == "number":
        ctx.user_data["awaiting"] = None
        if not text.isdigit() or len(text) != 10:
            await update.message.reply_text("❌ 10-digit number bhejo.")
            return
        if get_credits(uid) <= 0:
            await update.message.reply_text(
                get_funny_no_credit_msg(update.effective_user.first_name),
                reply_markup=main_menu(uid)
            )
            return
        if not deduct_credit(uid):
            return
        msg = await update.message.reply_text(f"🔍 Searching <code>{text}</code>...", parse_mode="HTML")
        data = await fetch_number(text)
        if not data:
            add_credits(uid, 1)
            await msg.edit_text("❌ Data nahi mila. Credit refund ✅")
            return
        result = format_osint_result(text, data)
        await msg.edit_text(
            f"{result}\n\n💳 <b>Remaining:</b> {get_credits(uid)}",
            parse_mode="HTML"
        )
        return

async def handle_media(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Admin QR upload + user payment screenshot"""
    if not update.message:
        return
    uid = update.effective_user.id
    awaiting = ctx.user_data.get("awaiting")

    # Admin QR upload
    if is_admin(uid) and awaiting == "admin_qr":
        if not update.message.photo:
            await update.message.reply_text("❌ Photo bhejo QR code ki.")
            return
        file_id = update.message.photo[-1].file_id
        set_setting("qr_image", file_id)
        ctx.user_data["awaiting"] = None
        await update.message.reply_text(
            "✅ QR Code image set ho gaya!\nAb Buy Credit pe QR users ko dikhega."
        )
        return

    # User payment screenshot
    if awaiting == "screenshot" and update.message.photo:
        ctx.user_data["awaiting"] = None
        file_id = update.message.photo[-1].file_id
        pid = create_payment(uid, file_id, 0, 0)

        u = update.effective_user
        admin_caption = (
            f"💳 <b>New Payment Screenshot</b>\n\n"
            f"🆔 Payment ID: <code>{pid}</code>\n"
            f"👤 {u.first_name} (@{u.username or 'N/A'})\n"
            f"🆔 <code>{u.id}</code>\n\n"
            f"Approve karke credits add karo:"
        )
        kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Approve 10", callback_data=f"pay_ok_{pid}_10"),
                InlineKeyboardButton("✅ Approve 50", callback_data=f"pay_ok_{pid}_50")
            ],
            [
                InlineKeyboardButton("✅ Approve 100", callback_data=f"pay_ok_{pid}_100"),
                InlineKeyboardButton("❌ Reject", callback_data=f"pay_no_{pid}")
            ]
        ])

        first_msg_id = None
        for admin in ADMIN_IDS:
            try:
                sent = await ctx.bot.send_photo(
                    chat_id=admin, photo=file_id,
                    caption=admin_caption, parse_mode="HTML",
                    reply_markup=kb
                )
                if first_msg_id is None:
                    first_msg_id = sent.message_id
            except Exception as e:
                logging.error(f"Admin notify fail: {e}")

        if first_msg_id:
            set_payment_msg(pid, first_msg_id)

        await update.message.reply_text(
            f"✅ Screenshot bhej diya!\n🆔 Payment ID: <code>{pid}</code>\n\n"
            "Admin verify karke credits add karega.",
            parse_mode="HTML"
        )
        return

async def handle_admin_video(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    if ctx.user_data.get("awaiting") != "admin_video":
        return
    video = update.message.video
    if not video:
        await update.message.reply_text("❌ Video file bhejo.")
        return
    set_setting("welcome_video", video.file_id)
    ctx.user_data["awaiting"] = None
    await update.message.reply_text(
        "✅ Welcome video set!\nAb har naye user ko /start pe video dikhega."
    )

# ============================================================
# ADMIN PANEL
# ============================================================
async def admin_panel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not is_admin(uid):
        await update.message.reply_text("❌ Sirf admin use kar sakta hai.")
        return
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎥 Set Welcome Video", callback_data="adm_set_video")],
        [InlineKeyboardButton("🗑 Remove Welcome Video", callback_data="adm_del_video")],
        [InlineKeyboardButton("📸 Set QR Code Image", callback_data="adm_set_qr")],
        [InlineKeyboardButton("🗑 Remove QR Image", callback_data="adm_del_qr")],
        [InlineKeyboardButton("🎟 Create Redeem Code", callback_data="adm_gen_redeem")],
        [InlineKeyboardButton("📢 Broadcast Message", callback_data="adm_broadcast")],
        [InlineKeyboardButton("📊 Stats", callback_data="adm_stats")]
    ])
    video_status = "✅ Set" if get_setting("welcome_video") else "❌ Not set"
    qr_status = "✅ Set" if get_setting("qr_image") else "❌ Not set"
    await update.message.reply_text(
        f"🛠 <b>Admin Panel</b>\n\n"
        f"🎥 Welcome Video: {video_status}\n"
        f"📸 QR Code: {qr_status}\n"
        f"👥 Total Users: {len(all_users())}\n\n"
        "Option chuno:",
        parse_mode="HTML",
        reply_markup=kb
    )

async def admin_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Sirf admin.", show_alert=True)
        return

    data = q.data
    if data == "adm_set_video":
        ctx.user_data["awaiting"] = "admin_video"
        await q.edit_message_text("🎥 Ab apna welcome video bhejo (as video).")
        await q.answer()

    elif data == "adm_del_video":
        set_setting("welcome_video", "")
        await q.edit_message_text("🗑 Welcome video remove kar diya.")
        await q.answer("Removed")

    elif data == "adm_set_qr":
        ctx.user_data["awaiting"] = "admin_qr"
        await q.edit_message_text("📸 Ab apna QR code image bhejo (as photo).")
        await q.answer()

    elif data == "adm_del_qr":
        set_setting("qr_image", "")
        await q.edit_message_text("🗑 QR image remove kar di.")
        await q.answer("Removed")

    elif data == "adm_gen_redeem":
        ctx.user_data["awaiting"] = "admin_redeem"
        await q.edit_message_text(
            "🎟 Redeem code bhejo is format me:\n\n"
            "<code>CODE CREDITS</code>\n\n"
            "Example: <code>WELCOME50 50</code>",
            parse_mode="HTML"
        )
        await q.answer()

    elif data == "adm_broadcast":
        ctx.user_data["awaiting"] = "admin_broadcast"
        await q.edit_message_text("📢 Broadcast message bhejo (text/photo/video):")
        await q.answer()

    elif data == "adm_stats":
        total = len(all_users())
        con = sqlite3.connect(DB); cur = con.cursor()
        cur.execute("SELECT COUNT(*) FROM feedback")
        fb = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM payments WHERE status='approved'")
        paid = cur.fetchone()[0]
        con.close()
        await q.edit_message_text(
            f"📊 <b>Bot Stats</b>\n\n"
            f"👥 Users: {total}\n"
            f"📩 Feedback: {fb}\n"
            f"💳 Paid Payments: {paid}",
            parse_mode="HTML"
        )
        await q.answer()

# ============================================================
# PAYMENT CALLBACK
# ============================================================
async def payment_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if not is_admin(q.from_user.id):
        await q.answer("Sirf admin.", show_alert=True)
        return

    data = q.data  # pay_ok_<pid>_<credits>  OR  pay_no_<pid>
    parts = data.split("_")

    if parts[1] == "ok":
        pid = int(parts[2])
        credits = int(parts[3])
        row = get_payment(pid)
        if not row:
            await q.answer("Payment not found.", show_alert=True); return
        user_id, file_id, amount, c, status = row
        if status == "approved":
            await q.answer("Already approved.", show_alert=True); return
        add_credits(user_id, credits)
        update_payment_status(pid, "approved")
        try:
            await ctx.bot.send_message(
                user_id,
                f"✅ <b>Payment Approved!</b>\n\n"
                f"🎁 +{credits} credits added.\n"
                f"💳 Balance: {get_credits(user_id)}",
                parse_mode="HTML"
            )
        except Exception as e:
            logging.error(f"User notify fail: {e}")
        await q.edit_message_caption(
            caption=(q.message.caption or "") + f"\n\n✅ APPROVED (+{credits})"
        )
        await q.answer(f"Approved +{credits}")

    elif parts[1] == "no":
        pid = int(parts[2])
        row = get_payment(pid)
        if not row:
            await q.answer("Not found."); return
        user_id = row[0]
        update_payment_status(pid, "rejected")
        try:
            await ctx.bot.send_message(
                user_id,
                "❌ <b>Payment Rejected</b>\n\n"
                "Screenshot valid nahi tha. Support se contact karo.",
                parse_mode="HTML"
            )
        except Exception:
            pass
        await q.edit_message_caption(
            caption=(q.message.caption or "") + "\n\n❌ REJECTED"
        )
        await q.answer("Rejected")

# ============================================================
# MAIN
# ============================================================
def main():
    init_db()
    app = Application.builder().token(BOT_TOKEN).build()

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("num", num_group_command))   # ✅ /num works everywhere
    app.add_handler(CommandHandler("redeem", redeem_prompt))
    app.add_handler(CommandHandler("feedback", feedback_prompt))
    app.add_handler(CommandHandler("admin", admin_panel))

    # Group new members welcome
    app.add_handler(MessageHandler(
        filters.StatusUpdate.NEW_CHAT_MEMBERS, group_welcome
    ))

    # Callbacks
    app.add_handler(CallbackQueryHandler(admin_callback, pattern="^adm_"))
    app.add_handler(CallbackQueryHandler(payment_callback, pattern="^pay_"))

    # Reply keyboard buttons
    app.add_handler(MessageHandler(filters.Regex("^🔍 Search Number$"), search_prompt))
    app.add_handler(MessageHandler(filters.Regex("^💰 Buy Credit$"), buy_credit))
    app.add_handler(MessageHandler(filters.Regex("^🎁 Redeem$"), redeem_prompt))
    app.add_handler(MessageHandler(filters.Regex("^👥 Refer & Earn$"), referral))
    app.add_handler(MessageHandler(filters.Regex("^🆘 Support$"), support))
    app.add_handler(MessageHandler(filters.Regex("^📩 Feedback$"), feedback_prompt))
    app.add_handler(MessageHandler(filters.Regex("^ℹ️ Help$"), help_cmd))
    app.add_handler(MessageHandler(filters.Regex("^🛠 Admin Panel$"), admin_panel))

    # Media (video / photo)
    app.add_handler(MessageHandler(filters.VIDEO, handle_admin_video))
    app.add_handler(MessageHandler(filters.PHOTO, handle_media))

    # Plain text (last)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 Bot running... Press Ctrl+C to stop.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()