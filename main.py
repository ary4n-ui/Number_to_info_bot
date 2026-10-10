# ═══════════════════════════════════════════════
# 🚀 Hosted By - @FreeHostingX1Bot ( 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏𝙄𝙉𝙂 𝙓𝟭 𝘽𝙊𝙏 🔥 )
# 🔥 Powered By 𝙁𝙍𝙀𝙀 𝙃𝙊𝙎𝙏𝙄𝙉𝙂 𝙓𝟭 𝘽𝙊𝙏 🔥
# 🌐 24/7 Premium Cloud Hosting Service
# ═══════════════════════════════════════════════

# ═══════════════════════════════════════
# IMPORTS
# ═══════════════════════════════════════
import asyncio
import json
import logging
import os
import random
import re
import secrets
import time
import warnings
from datetime import datetime
from pyrogram import Client, filters
from pyrogram.errors import (
    FloodWait,
    PhoneCodeExpired,
    PhoneCodeInvalid,
    SessionPasswordNeeded,
)
from pyrogram.raw.functions.messages import GetMessagesViews
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

# Suppress warnings
warnings.filterwarnings("ignore", message="TgCrypto is missing!")
logging.basicConfig(level=logging.ERROR)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

# Event loop fix
try:
    loop = asyncio.get_event_loop()
except RuntimeError:
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

try:
    import uvloop
    uvloop.install()
except ImportError:
    pass

# ═══════════════════════════════════════
# COLOUR BUTTON PATCH (Works with regular pyrogram)
# ═══════════════════════════════════════
_original_init = InlineKeyboardButton.__init__
_original_write = InlineKeyboardButton.write


def _patched_init(self, text, callback_data=None, url=None, **kwargs):
    style = kwargs.pop("style", None)
    _original_init(self, text=text, callback_data=callback_data, url=url, **kwargs)
    if style:
        self._button_style = style


def _patched_write(self):
    data = _original_write(self)
    style = getattr(self, "_button_style", None)
    if style:
        data["style"] = style
    return data


InlineKeyboardButton.__init__ = _patched_init
InlineKeyboardButton.write = _patched_write

# ═══════════════════════════════════════
# FOLDER SETUP
# ═══════════════════════════════════════
os.makedirs("data", exist_ok=True)

# ----------------- CONFIGURATION -----------------
API_ID = int(os.getenv("API_ID", "34035552"))
API_HASH = os.getenv("API_HASH", "ae6642cc552c9e01c9a2ca791593bfae")
BOT_TOKEN = os.getenv("BOT_TOKEN", "8852490910:AAHWOP1wNPn1T0C_hY8LLOg9Mth5MS34YBk")

DB_FILE = "data/user_database.json"
SETTINGS_FILE = "data/bot_settings.json"
ADV_USERS_FILE = "data/adv_users.json"
FROZEN_FILE = "data/frozen_accounts.json"
LOG_FILE = "data/bot_log.txt"
SQL_BACKUP_FILE = "data/db_backup.sql"
SQL_FILE = "old_database.sql"

OWNER_ID = int(os.getenv("OWNER_ID", "5954012829"))
USERS_PER_PAGE = 20
# -------------------------------------------------

# ========== PREMIUM CUSTOM EMOJI IDs ==========
PREMIUM_EMOJIS = {
    "heart_fire": "5042225965518816316",
    "lightning": "5042334757040423886",
    "location": "5039775669496579510",
    "flower": "6073117703965511893",
    "check": "6147460667281511517",
    "crown": "6235252066554484059",
    "kiss": "6116282026506065674",
    "skull": "6089128873893563936",
    "xmas": "6267071898702583835",
    "monkey": "6273627839862411998",
    "gift": "5893175870096414393",
    "angel": "5893411041030707544",
    "devil": "5893079628469246474",
}


# Dynamic Button Formatter (Colourful)
def styled_button(text, callback_data=None, url=None, style="primary", emoji_key=None):
    kwargs = {"text": text, "callback_data": callback_data, "url": url}
    if emoji_key and emoji_key in PREMIUM_EMOJIS:
        kwargs["icon_custom_emoji_id"] = PREMIUM_EMOJIS[emoji_key]
    if style:
        kwargs["style"] = style
    try:
        return InlineKeyboardButton(**kwargs)
    except Exception:
        return InlineKeyboardButton(text=text, callback_data=callback_data, url=url)


# Keyboards
add_account_keyboard = InlineKeyboardMarkup([
    [styled_button("Phone + OTP", callback_data="add_phone_otp", style="success", emoji_key="location")],
    [styled_button("Session String", callback_data="add_session_string", style="primary", emoji_key="lightning")],
    [styled_button("Bulk Sessions", callback_data="add_bulk_sessions", style="primary", emoji_key="gift")],
    [styled_button("Upload ZIP", callback_data="add_zip", style="primary", emoji_key="gift")],
    [styled_button("CANCEL", callback_data="cancel_action", style="danger", emoji_key="skull")],
])

owner_accounts_keyboard = InlineKeyboardMarkup([
    [
        styled_button("✅ Live", callback_data="admin_view_live", style="success", emoji_key="check"),
        styled_button("❌ Expired", callback_data="admin_view_expired", style="danger", emoji_key="skull"),
    ],
    [
        styled_button("🗑️ Remove", callback_data="admin_remove_prompt", style="danger", emoji_key="skull"),
        styled_button("⚠️ REMOVE ALL", callback_data="admin_remove_all_prompt", style="danger", emoji_key="skull"),
    ],
    [styled_button("➕ Add Another", callback_data="add_account", style="success", emoji_key="gift")],
    [styled_button("❌ CANCEL", callback_data="cancel_action", style="danger", emoji_key="skull")],
])


bot = Client("MarcoAutoVotingBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

user_sessions = {}
user_db = {}
user_settings = {}
user_campaign_counter = {}
allowed_adv_users = {}
banned_users = set()
frozen_accounts = {}
campaign_history = []
log_gc_id = None

bot_settings = {
    "maintenance": False,
    "fsub_channel": "Not Set",
    "paid_mode": False,
    "owner_username": "@MarcoEraXD",
    "extra_owners": [],
    "account_limit": 0,
    "global_cooldown": 0,
    "notifications": True,
    "log_gc_id": None,
}

TOTAL_ACTIONS_DONE = 0
ACTIVE_RUNNING_CAMPAIGNS = 0

RANDOM_EMOJIS = ["👍", "❤️", "🔥", "🥰", "👏", "😁", "🎉", "🙏", "💯", "😎", "🤣"]


def is_owner(user_id):
    return user_id == OWNER_ID or user_id in bot_settings.get("extra_owners", [])


# ----------------- DATABASE HELPERS -----------------
def load_db():
    global user_db, bot_settings, allowed_adv_users, frozen_accounts, log_gc_id

    # Auto SQL import if DB not present
    if not os.path.exists(DB_FILE) and os.path.exists(SQL_FILE):
        import_from_sql()

    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                user_db = json.load(f)
        except Exception as e:
            logging.error(f"Error loading database: {e}")
            user_db = {}
    else:
        user_db = {}

    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                bot_settings.update(loaded)
                log_gc_id = loaded.get("log_gc_id", None)
        except Exception as e:
            logging.error(f"Error loading settings: {e}")

    if os.path.exists(ADV_USERS_FILE):
        try:
            with open(ADV_USERS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                allowed_adv_users = {int(k): v for k, v in data.items()}
        except Exception as e:
            logging.error(f"Error loading adv users: {e}")
            allowed_adv_users = {}

    if os.path.exists(FROZEN_FILE):
        try:
            with open(FROZEN_FILE, "r", encoding="utf-8") as f:
                frozen_accounts = json.load(f)
        except Exception:
            frozen_accounts = {}


def save_db():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(user_db, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving database: {e}")


def save_bot_settings():
    try:
        bot_settings["log_gc_id"] = log_gc_id
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(bot_settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving settings: {e}")


def save_adv_users():
    try:
        with open(ADV_USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in allowed_adv_users.items()}, f, indent=4)
    except Exception as e:
        logging.error(f"Error saving adv users: {e}")


def save_frozen():
    try:
        with open(FROZEN_FILE, "w", encoding="utf-8") as f:
            json.dump(frozen_accounts, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logging.error(f"Error saving frozen: {e}")


# ----------------- SQL BACKUP / IMPORT -----------------
def create_sql_backup(reason="manual"):
    try:
        def esc(s):
            return str(s).replace("'", "''")

        lines = [
            "-- ═══════════════════════════════════════════════",
            f"-- Marco Auto Voting Bot — DB Backup",
            f"-- Reason : {reason}",
            f"-- Generated : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"-- Total Users : {len(user_db)}",
            f"-- Total Accounts : {sum(len(v) for v in user_db.values())}",
            "-- ═══════════════════════════════════════════════\n",
            "CREATE TABLE IF NOT EXISTS users (user_id BIGINT PRIMARY KEY, accounts TEXT, campaigns INT DEFAULT 0);\n",
            "CREATE TABLE IF NOT EXISTS adv_users (user_id BIGINT PRIMARY KEY, acc_limit INT);\n",
            "CREATE TABLE IF NOT EXISTS bot_settings (key TEXT PRIMARY KEY, value TEXT);\n",
        ]

        for u_s, accs in user_db.items():
            a_str = ",".join(accs) if accs else ""
            c = user_campaign_counter.get(int(u_s), 0)
            lines.append(f"INSERT OR REPLACE INTO users (user_id, accounts, campaigns) VALUES ({u_s}, '{esc(a_str)}', {c});")

        for u, lim in allowed_adv_users.items():
            lines.append(f"INSERT OR REPLACE INTO adv_users (user_id, acc_limit) VALUES ({u}, {lim});")

        settings_blob = dict(bot_settings)
        settings_blob["log_gc_id"] = log_gc_id
        lines.append(f"INSERT OR REPLACE INTO bot_settings (key, value) VALUES ('global', '{esc(json.dumps(settings_blob))}');")
        lines.append("\n-- End of Backup")

        with open(SQL_BACKUP_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return True
    except Exception as e:
        print(f"❌ Backup error: {e}")
        return False


def import_from_sql():
    global user_db, user_campaign_counter, allowed_adv_users, bot_settings, log_gc_id

    if not os.path.exists(SQL_FILE):
        return False

    print(f"📥 SQL file mili: {SQL_FILE}")
    print("⏳ Import kar raha hun...")

    tmp_user_db = {}
    tmp_adv_users = {}
    tmp_settings = {}
    tmp_counter = {}

    try:
        with open(SQL_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue

                if line.startswith('INSERT INTO public."bot_settings"'):
                    m = re.search(r"VALUES \('([^']+)', '(.*)'\) ON CONFLICT", line)
                    if m:
                        try:
                            tmp_settings[m.group(1)] = json.loads(m.group(2))
                        except Exception:
                            pass

                elif line.startswith('INSERT INTO public."user_data"'):
                    m = re.search(r"VALUES \((\d+), '(.*)'\) ON CONFLICT DO NOTHING;", line)
                    if m:
                        uid = m.group(1)
                        data_str = m.group(2).replace("''", "'")
                        try:
                            data = json.loads(data_str)
                        except Exception:
                            continue

                        sessions = []
                        for acc in data.get("accounts", []):
                            ident = str(acc.get("identifier", "")).strip()
                            if ident:
                                sessions.append(ident)
                        if sessions:
                            tmp_user_db[uid] = sessions

                        camps = data.get("campaigns", [])
                        if camps:
                            tmp_counter[int(uid)] = len(camps)

        global_s = tmp_settings.get("global", {})
        for adv_uid, limit in global_s.get("adv_access", {}).items():
            tmp_adv_users[int(adv_uid)] = limit

        extra_owners = [o for o in global_s.get("owner_ids", []) if o != OWNER_ID]
        log_channel = global_s.get("log_channel", None)

        user_db = tmp_user_db
        user_campaign_counter = tmp_counter
        allowed_adv_users = tmp_adv_users
        bot_settings["maintenance"] = global_s.get("maintenance_mode", False)
        bot_settings["paid_mode"] = global_s.get("paid_mode", False)
        bot_settings["owner_username"] = "@MarcoEraXD"
        bot_settings["extra_owners"] = extra_owners
        log_gc_id = log_channel

        save_db()
        save_adv_users()
        save_bot_settings()
        create_sql_backup("auto-import")

        total = sum(len(v) for v in user_db.values())
        print("═" * 40)
        print("✅ SQL IMPORT SUCCESSFUL!")
        print(f"👥 Users       : {len(user_db)}")
        print(f"📱 Accounts    : {total}")
        print(f"📌 Adv Users   : {len(allowed_adv_users)}")
        print(f"👑 Extra Owners: {len(extra_owners)}")
        print(f"📝 Log Channel : {log_channel}")
        print("═" * 40)
        return True
    except Exception as e:
        print(f"❌ SQL import failed: {e}")
        return False


def register_user_if_not_exists(user_id):
    uid_str = str(user_id)
    if uid_str not in user_db:
        user_db[uid_str] = []
        save_db()


def get_user_accounts(user_id):
    uid_str = str(user_id)
    return user_db.get(uid_str, [])


def get_all_bot_accounts():
    all_sessions = []
    for uid_str in user_db:
        all_sessions.extend(user_db[uid_str])
    return all_sessions


def add_user_account(user_id, session_str):
    uid_str = str(user_id)
    if uid_str not in user_db:
        user_db[uid_str] = []
    if session_str not in user_db[uid_str]:
        user_db[uid_str].append(session_str)
        save_db()


def get_user_delay(user_id):
    speed = user_settings.get(user_id, "Normal (200ms)")
    base = 0.2
    if "Slow" in speed:
        base = 0.5
    elif "Fast" in speed:
        base = 0.05
    return base + bot_settings.get("global_cooldown", 0)


async def send_log(text):
    if log_gc_id:
        try:
            await bot.send_message(log_gc_id, text)
        except Exception:
            pass


# ----------------- CAMPAIGN SUMMARY -----------------
def generate_campaign_summary_text(session_data, user_id):
    action_disp = session_data.get("action_display", "Custom Campaign")
    target_post = session_data.get("target_link", "N/A")

    emoji = session_data.get("chosen_emoji", "None")
    if isinstance(emoji, list):
        emoji_str = " ".join(emoji) if emoji else "None"
    elif emoji == "auto":
        emoji_str = "Auto (Premium)"
    else:
        emoji_str = str(emoji) if emoji else "None"

    button_disp = session_data.get("button_option", "None")
    join_link = session_data.get("join_link", "Skipped")
    accounts_count = len(session_data.get("accounts_to_use", []))

    user_limit = (
        allowed_adv_users.get(user_id, len(get_all_bot_accounts()))
        if (is_owner(user_id) or user_id in allowed_adv_users)
        else len(get_user_accounts(user_id))
    )

    return (
        "📋 **Campaign Summary**\n"
        "--------------------------------------------------\n"
        "-------\n\n"
        "```\n"
        f"🎯 Action: 🔥 {action_disp}\n"
        f"🔗 Post: {target_post}\n"
        f"😀 Reaction: {emoji_str}\n"
        f"🗳 Button: {button_disp}\n"
        f"🔗 Auto-join: {join_link}\n"
        f"📱 Accounts: {accounts_count} will run (your limit: {user_limit})\n"
        "```\n\n"
        "_Tap Run to start the campaign._"
    )


# ----------------- OWNER DASHBOARD -----------------
def get_owner_dashboard_text():
    total_users = len(user_db)
    all_accounts = get_all_bot_accounts()
    total_accounts = len(all_accounts)
    active_accounts = total_accounts - len(frozen_accounts)
    total_campaigns = sum(user_campaign_counter.values())
    up = int(time.time() - time.time())  # Uptime placeholder

    return (
        "👑 **— -𝐌ᴀʀᴄᴏ ꪜᴏᴛɪɴɢ 𝕭ᴏᴛ  **\n"
        "-----------------------------------\n\n"
        "```\n"
        f"👥 Users: {total_users}\n"
        f"📱 Accounts: {total_accounts} · Active: {active_accounts}\n"
        f"📋 Campaigns: {total_campaigns} · Running: {ACTIVE_RUNNING_CAMPAIGNS}\n"
        f"⚡ Total Actions: {TOTAL_ACTIONS_DONE}\n"
        "```\n\n"
        "**Select an operation below:**"
    )


def get_admin_settings_text():
    m_status = "ON 🟢" if bot_settings.get("maintenance") else "OFF 🔴"
    p_status = "ON 🟢" if bot_settings.get("paid_mode") else "OFF 🔴"
    n_status = "ON 🟢" if bot_settings.get("notifications", True) else "OFF 🔴"
    fsub = bot_settings.get("fsub_channel", "Not Set")
    owner = bot_settings.get("owner_username", "@MarcoEraXD")

    return (
        "👑 **— -𝐌ᴀʀᴄᴏ ꪜᴏᴛɪɴɢ 𝕭ᴏᴛ  **\n"
        "--------------------------------------------------\n"
        "-------\n\n"
        "⚙️ **Bot Settings**\n\n"
        "```\n"
        f"🔧 Maintenance: {m_status}\n"
        f"📡 FSub Channel: {fsub}\n"
        f"💎 Paid Mode: {p_status}\n"
        f"👤 Owner: {owner}\n"
        f"🔔 Notifications: {n_status}\n"
        "```\n\n"
        "_Paid Mode ON → free users see a purchase popup on action buttons._"
    )


def get_admin_settings_keyboard():
    m_btn = "⚡ Maintenance: ON 🟢" if bot_settings.get("maintenance") else "⚡ Maintenance: OFF 🔴"
    p_btn = "🎉 Paid Mode: ON 🟢" if bot_settings.get("paid_mode") else "🎉 Paid Mode: OFF 🔴"
    n_btn = "🔔 Notifications: ON 🟢" if bot_settings.get("notifications", True) else "🔔 Notifications: OFF 🔴"
    fsub_btn = f"📣 FSub Channels: {bot_settings.get('fsub_channel', 'Not Set')}"
    owner_btn = f"🐸 Owner: {bot_settings.get('owner_username', '@MarcoEraXD')}"

    return InlineKeyboardMarkup([
        [styled_button(m_btn, callback_data="toggle_maintenance", style="danger", emoji_key="lightning")],
        [styled_button(p_btn, callback_data="toggle_paid_mode", style="success", emoji_key="crown")],
        [styled_button(n_btn, callback_data="toggle_notifications", style="primary", emoji_key="lightning")],
        [styled_button(fsub_btn, callback_data="set_fsub_channel", style="primary", emoji_key="flower")],
        [styled_button(owner_btn, callback_data="set_owner_username", style="primary", emoji_key="monkey")],
        [styled_button("📝 Set Log GC", callback_data="set_log_gc", style="primary", emoji_key="gift")],
        [styled_button("🏥 Health Report", callback_data="admin_session_health", style="success", emoji_key="check")],
        [styled_button("🗑 Clear Log GC", callback_data="admin_clear_log_gc", style="danger", emoji_key="skull")],
        [styled_button("⬅️ Back", callback_data="owner_menu", style="danger", emoji_key="skull")],
    ])


def get_adv_access_menu_text():
    auth_users_count = len(allowed_adv_users)
    total_bot_ids = len(get_all_bot_accounts())

    return (
        "👑 **ADV CAMPAIGN ACCESS CONTROL**\n"
        "====================================\n\n"
        f"👥 **Authorized Users:** {auth_users_count}\n"
        f"📱 **IDs currently in bot:** {total_bot_ids}\n\n"
        "When granting access, the admin enters a User ID and the maximum number of bot account IDs that user may use."
    )


def get_adv_access_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("➕ Grant Adv Access", callback_data="adv_grant_access", style="success", emoji_key="check")],
        [styled_button("➖ Revoke Adv Access", callback_data="adv_revoke_access", style="danger", emoji_key="skull")],
        [styled_button("👥 Authorized Users", callback_data="adv_authorized_users", style="primary", emoji_key="crown")],
        [styled_button("🔙 Back", callback_data="owner_menu", style="primary", emoji_key="skull")],
    ])


# ----------------- UI TEXT & KEYBOARDS -----------------
MAIN_TEXT = (
    "-----------------------------------\n"
    "**Auto Voter**\n"
    "_Telegram Automation Bot_\n"
    "-----------------------------------\n\n"
    "**React • Vote • View • Join • DM**\n"
    "Fast, reliable & smart Telegram automation\n\n"
    "**Choose an option:**\n\n"
    "---- -𝐌ᴀʀᴄᴏ ꪜᴏᴛɪɴɢ 𝕭ᴏᴛ (@MarcoAutoVotingBot)"
)

HELP_TEXT = (
    "📖 **HOW TO USE**\n"
    "======================\n\n"
    "➕ **ADD ACCOUNTS (3 WAYS)**\n"
    "• **Phone + OTP** — Manual login\n"
    "• **Session String** — Telethon/Pyrogram session\n"
    "• **Bulk Sessions** — Add multiple at once\n\n"
    "🚀 **RUN CAMPAIGN**\n"
    "1. Click 'New Campaign'\n"
    "2. Select action\n"
    "3. Send Target Link\n"
    "4. Tap 'Run Campaign'\n\n"
    "---- -𝐌ᴀʀᴄᴏ ꪜᴏᴛɪɴɢ 𝕭ᴏᴛ (@MarcoAutoVotingBot)"
)

SUPPORT_TEXT = (
    "🎧 **SUPPORT**\n"
    "👾 ---- Support: @MarcoEraXd\n\n"
    "👨‍💻 Developer: - 𝐌ᴀʀᴄᴏ (@MarcoEraXd)\n\n"
    "Need help? Contact the developer."
)


def get_account_added_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("➕ Add Another Account", callback_data="add_account", style="success", emoji_key="gift")],
        [styled_button("🏠 Main Menu", callback_data="back_to_menu", style="primary", emoji_key="crown")],
    ])


def get_otp_retry_keyboard():
    return InlineKeyboardMarkup([
        [
            styled_button("🔄 Retry OTP", callback_data="retry_otp_input", style="primary", emoji_key="lightning"),
            styled_button("❌ Cancel Login", callback_data="cancel_login_process", style="danger", emoji_key="skull"),
        ]
    ])


def get_login_cancel_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("👑 Cancel", callback_data="cancel_login_process", style="danger", emoji_key="skull")]
    ])


async def get_user_profile_text(client, user):
    user_id = user.id
    name = user.first_name + (f" {user.last_name}" if user.last_name else "")
    username = f"@{user.username}" if user.username else "None"

    accounts = get_user_accounts(user_id)
    acc_count = len(accounts)
    campaign_count = user_campaign_counter.get(user_id, 0)
    speed = user_settings.get(user_id, "Normal (200ms)")
    date_str = datetime.now().strftime("%Y-%m-%d")

    return (
        "👤  **PROFILE**    👤 **USER**\n"
        "------------------------\n\n"
        f"🆔  `{user_id}`\n"
        f"📛  **{name}**\n"
        f"💬  {username}\n"
        f"📅  `{date_str}`\n"
        f"🎭  **Accounts:** `{acc_count}`\n"
        f"🚀  **Campaigns:** `{campaign_count}`\n"
        f"⚡  **Speed:** `{speed}`"
    )


def get_settings_text(user_id):
    speed_val = user_settings.get(user_id, "Normal (200ms)")
    return (
        "⚙️ **SETTINGS**\n\n"
        "⚡ **Campaign Speed Control**\n\n"
        "Choose how fast accounts should perform actions:\n\n"
        "🐢 **Slow:** 500ms delay (safer)\n"
        "⚡ **Normal:** 200ms delay (balanced)\n"
        "🚀 **Fast:** 50ms delay (aggressive)\n\n"
        f"Current setting: **{speed_val}**\n\n"
        "_Current setting affects all running campaigns._"
    )


def get_main_keyboard(user_id=None):
    keyboard = [
        [
            styled_button("  Add Account", callback_data="add_account", style="success", emoji_key="location"),
            styled_button("✅ My Accounts", callback_data="my_accounts", style="primary", emoji_key="check"),
        ],
        [
            styled_button("⭐ New Campaign", callback_data="new_campaign", style="success", emoji_key="crown"),
            styled_button("❤️‍🔥 My Campaigns", callback_data="my_campaigns", style="primary", emoji_key="heart_fire"),
        ],
        [
            styled_button("👑 Scheduled", callback_data="scheduled_campaigns_menu", style="primary", emoji_key="crown"),
            styled_button("❤️‍🔥 My Stats", callback_data="stats", style="primary", emoji_key="heart_fire"),
        ],
        [
            styled_button("⚡ Settings", callback_data="settings", style="primary", emoji_key="lightning"),
            styled_button("🐸 My Profile", callback_data="my_profile", style="primary", emoji_key="monkey"),
        ],
        [
            styled_button("🥊 Help & Guide", callback_data="help_guide", style="primary", emoji_key="flower"),
            styled_button("🥊 Support", callback_data="support", style="primary", emoji_key="kiss"),
        ],
    ]
    if is_owner(user_id) or user_id in allowed_adv_users:
        keyboard.append([styled_button("📌 Adv Campaign", callback_data="user_adv_campaign", style="success", emoji_key="crown")])
    if is_owner(user_id):
        keyboard.append([styled_button("👑 Owner Panel", callback_data="owner_menu", style="danger", emoji_key="crown")])
    return InlineKeyboardMarkup(keyboard)


def get_adv_campaign_keyboard():
    return InlineKeyboardMarkup([
        [
            styled_button("⭐ React Only", callback_data="camp_react_only", style="success", emoji_key="flower"),
            styled_button("❤️‍🔥 Vote Only", callback_data="camp_vote_only", style="primary", emoji_key="heart_fire"),
        ],
        [
            styled_button("🍾 React + Vote", callback_data="camp_react_vote", style="primary", emoji_key="kiss"),
            styled_button("👑 View Only", callback_data="camp_view_only", style="success", emoji_key="crown"),
        ],
        [
            styled_button("⭐ React + View", callback_data="camp_react_view", style="primary", emoji_key="lightning"),
            styled_button("❤️‍🔥 Vote + View", callback_data="camp_vote_view", style="primary", emoji_key="heart_fire"),
        ],
        [
            styled_button("🍾 React + Vote + View", callback_data="camp_react_vote_view", style="success", emoji_key="crown")
        ],
        [
            styled_button("⚡ Join Channel", callback_data="camp_join_channel", style="success", emoji_key="lightning"),
            styled_button("🐸🚪 Leave Channel", callback_data="camp_leave_channel_menu", style="danger", emoji_key="skull"),
        ],
        [styled_button("🔗 Bot Referral", callback_data="camp_bot_referral", style="success", emoji_key="gift")],
        [styled_button("🥊 Bulk DM", callback_data="camp_bulk_dm", style="primary", emoji_key="gift")],
        [styled_button("⚡ Speed", callback_data="settings", style="primary", emoji_key="lightning")],
        [styled_button("👑 Cancel", callback_data="back_to_menu", style="danger", emoji_key="skull")],
    ])


def get_leave_channel_sub_keyboard():
    return InlineKeyboardMarkup([
        [
            styled_button("🐸 🚪 Leave Specific", callback_data="camp_leave_specific_channel", style="danger", emoji_key="skull"),
            styled_button("❤️ 🚪 Leave All", callback_data="camp_leave_all_channels", style="danger", emoji_key="heart_fire"),
        ],
        [styled_button("❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")],
    ])


def get_settings_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("🐢 Slow (500ms)", callback_data="set_speed_Slow (500ms)", style="primary", emoji_key="flower")],
        [styled_button("⚡ Normal (200ms)", callback_data="set_speed_Normal (200ms)", style="success", emoji_key="lightning")],
        [styled_button("🚀 Fast (50ms)", callback_data="set_speed_Fast (50ms)", style="primary", emoji_key="crown")],
        [styled_button("❌ CANCEL", callback_data="back_to_menu", style="danger", emoji_key="skull")],
    ])



# ═══════════════════════════════════════
# OWNER KEYBOARD (Screenshot Style)
# ═══════════════════════════════════════
def get_owner_keyboard():
    return InlineKeyboardMarkup([
        [
            styled_button("🧟 Users List", callback_data="admin_users_list", style="primary", emoji_key="monkey"),
            styled_button("✅ All Sessions", callback_data="admin_all_sessions", style="success", emoji_key="check"),
        ],
        [
            styled_button("💎 Broadcast", callback_data="admin_broadcast", style="success", emoji_key="lightning"),
            styled_button("⚡ Settings", callback_data="admin_settings", style="primary", emoji_key="lightning"),
        ],
        [
            styled_button("🎉 Ban/Unban", callback_data="admin_ban_unban", style="danger", emoji_key="skull"),
            styled_button("❤️‍🔥 Log GC", callback_data="admin_log_gc", style="primary", emoji_key="heart_fire"),
        ],
        [
            styled_button("📣 FSub Check", callback_data="admin_fsub_check", style="primary", emoji_key="flower"),
            styled_button("📌 Adv Campaign", callback_data="user_adv_campaign", style="success", emoji_key="crown"),
        ],
        [
            styled_button("🔬 Session Health", callback_data="admin_session_health", style="danger", emoji_key="check"),
            styled_button("📌 Adv Access", callback_data="admin_adv_access", style="primary", emoji_key="crown"),
        ],
        [
            styled_button("❤️ Manage Owners", callback_data="admin_manage_owners", style="danger", emoji_key="heart_fire"),
            styled_button("📱 Add Session (OTP)", callback_data="add_account", style="success", emoji_key="location"),
        ],
        [
            styled_button("🔍 Campaign Info", callback_data="admin_campaign_info", style="primary", emoji_key="flower"),
            styled_button("💾 DB Stats", callback_data="admin_db_stats", style="primary", emoji_key="monkey"),
        ],
        [
            styled_button("🧟 DB Diagnostics", callback_data="admin_db_diagnostics", style="success", emoji_key="monkey"),
            styled_button("❄️ Frozen Accounts", callback_data="admin_frozen_accounts", style="danger", emoji_key="skull"),
        ],
        [
            styled_button("📊 Account Health", callback_data="admin_account_health", style="primary", emoji_key="check"),
            styled_button("📈 Analytics", callback_data="admin_analytics", style="primary", emoji_key="crown"),
        ],
        [
            styled_button("⚡ Rotation", callback_data="admin_rotation", style="primary", emoji_key="lightning"),
            styled_button("🔔 Notifications", callback_data="admin_notifications", style="primary", emoji_key="kiss"),
        ],
        [styled_button("📥 Import (.sql)", callback_data="admin_import_db", style="success", emoji_key="gift")],
        [styled_button("💾 Extract DB Backup.sql", callback_data="admin_export_db", style="primary", emoji_key="monkey")],
        [styled_button("🦚 Main Menu", callback_data="back_to_menu", style="primary", emoji_key="crown")],
    ])


def get_normal_emoji_keyboard(selected_list=None):
    if selected_list is None:
        selected_list = []

    def get_btn_text(emoji):
        return f"✅ {emoji}" if emoji in selected_list else f"⭐ {emoji}"

    selected_text = " ".join(selected_list) if selected_list else "None"

    keyboard = [
        [
            styled_button(get_btn_text("👍"), callback_data="select_emoji_👍", style="success"),
            styled_button(get_btn_text("❤️"), callback_data="select_emoji_❤️", style="primary"),
            styled_button(get_btn_text("🔥"), callback_data="select_emoji_🔥", style="primary"),
            styled_button(get_btn_text("🥰"), callback_data="select_emoji_🥰", style="primary"),
            styled_button(get_btn_text("👏"), callback_data="select_emoji_👏", style="primary"),
        ],
        [
            styled_button(get_btn_text("😁"), callback_data="select_emoji_😁", style="primary"),
            styled_button(get_btn_text("🤩"), callback_data="select_emoji_🤩", style="primary"),
            styled_button(get_btn_text("🎉"), callback_data="select_emoji_🎉", style="success"),
            styled_button(get_btn_text("🙏"), callback_data="select_emoji_🙏", style="success"),
            styled_button(get_btn_text("💯"), callback_data="select_emoji_💯", style="primary"),
        ],
        [
            styled_button(get_btn_text("😎"), callback_data="select_emoji_😎", style="primary"),
            styled_button(get_btn_text("🤣"), callback_data="select_emoji_🤣", style="primary"),
            styled_button(get_btn_text("😢"), callback_data="select_emoji_😢", style="primary"),
            styled_button(get_btn_text("👎"), callback_data="select_emoji_👎", style="danger"),
            styled_button(get_btn_text("💩"), callback_data="select_emoji_💩", style="danger"),
        ],
        [styled_button("✅ Confirm Multi Selection", callback_data="confirm_multi_emoji", style="success", emoji_key="check")],
        [styled_button("🪶 ✏️ Custom emoji (single)", callback_data="custom_emoji_single", style="primary", emoji_key="flower")],
        [styled_button("👑 ❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull")],
    ]

    text = (
        "😀 **Normal Emoji Mode**\n\n"
        "Step **4️⃣** — 😀 **Choose reaction(s)**\n\n"
        "> Tap one or more emojis to select them.\n"
        "> Accounts will be split evenly across your selections.\n"
        f"> **Selected:** `{selected_text}`"
    )

    return text, InlineKeyboardMarkup(keyboard)


PREMIUM_EMOJI_TEXT = (
    "💎 **Premium Emoji Mode**\n\n"
    "⚠️ **INSTRUCTIONS:**\n\n"
    "1️⃣ Go to the post/message\n"
    "2️⃣ Right-click and manually react with the premium emoji **ONCE**\n"
    "3️⃣ Come back here and tap 'Ready'\n"
    "4️⃣ Bot will automatically react with **ALL** emojis on the message\n\n"
    "> Bot will find all reactions on the message and react with each one multiple times."
)


def get_premium_emoji_keyboard():
    return InlineKeyboardMarkup([
        [styled_button("📣 ✅ Ready - Start Reacting", callback_data="premium_ready_start", style="success", emoji_key="check")],
        [styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull")],
    ])


emoji_type_keyboard = InlineKeyboardMarkup([
    [
        styled_button("😀 Normal Emoji Mode", callback_data="emoji_type_normal", style="success", emoji_key="flower"),
        styled_button("💎 Premium Emoji", callback_data="emoji_type_premium", style="primary", emoji_key="crown"),
    ],
    [styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull")],
])


def get_back_keyboard():
    return InlineKeyboardMarkup([[styled_button("⬅️ BACK", callback_data="back_to_menu", style="danger", emoji_key="skull")]])


def get_owner_back_keyboard():
    return InlineKeyboardMarkup([[styled_button("Back to Owner Panel", callback_data="owner_menu", style="primary", emoji_key="crown")]])


# ═══════════════════════════════════════
# WORKER ENGINE
# ═══════════════════════════════════════
async def worker_single_account(session_str, chat_peer, msg_id, action, emoji, option_id, semaphore, delay, extra_text="", join_link="Skipped"):
    global TOTAL_ACTIONS_DONE
    async with semaphore:
        try:
            async def task_operations():
                global TOTAL_ACTIONS_DONE
                async with Client("session_client", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as user_client:
                    try:
                        async for _ in user_client.get_dialogs(limit=50):
                            pass
                    except Exception:
                        pass

                    # BOT REFERRAL LOGIC
                    if join_link and join_link != "Skipped":
                        try:
                            if "start=" in join_link or action == "camp_bot_referral":
                                bot_username = join_link.split("t.me/")[-1].split("?")[0] if "t.me/" in join_link else None
                                start_param = None
                                if "start=" in join_link:
                                    start_param = join_link.split("start=")[-1].split("&")[0]
                                if bot_username:
                                    await user_client.send_message(bot_username, f"/start {start_param}" if start_param else "/start")
                                    TOTAL_ACTIONS_DONE += 1
                                    await asyncio.sleep(1)
                            else:
                                await user_client.join_chat(join_link)
                                await asyncio.sleep(1)
                        except Exception:
                            pass
                    elif action in [
                        "camp_join_channel",
                        "camp_auto_diff_react_view",
                        "camp_react_vote_view",
                        "camp_react_view",
                        "camp_vote_view",
                        "camp_react_vote",
                    ]:
                        try:
                            if chat_peer and not isinstance(chat_peer, int):
                                await user_client.join_chat(chat_peer)
                                await asyncio.sleep(1)
                        except Exception:
                            pass

                    if action == "camp_bulk_dm":
                        try:
                            await user_client.send_message(chat_peer, extra_text)
                            TOTAL_ACTIONS_DONE += 1
                        except Exception as e:
                            raise e

                    if msg_id:
                        if "view" in action or action == "camp_view_only":
                            try:
                                peer = await user_client.resolve_peer(chat_peer)
                                await user_client.invoke(GetMessagesViews(peer=peer, id=[msg_id], increment=True))
                                TOTAL_ACTIONS_DONE += 1
                            except Exception:
                                try:
                                    await user_client.get_messages(chat_peer, msg_id)
                                    TOTAL_ACTIONS_DONE += 1
                                except Exception as e:
                                    raise e

                        if "react" in action or action in ["camp_react_only", "camp_auto_react"]:
                            if "auto" in action:
                                target_emoji = random.choice(RANDOM_EMOJIS)
                            elif isinstance(emoji, list) and emoji:
                                target_emoji = random.choice(emoji)
                            else:
                                target_emoji = emoji

                            try:
                                await user_client.send_reaction(chat_peer, msg_id, target_emoji)
                                TOTAL_ACTIONS_DONE += 1
                            except Exception:
                                try:
                                    await user_client.send_reaction(chat_peer, msg_id, None)
                                    await asyncio.sleep(0.3)
                                    await user_client.send_reaction(chat_peer, msg_id, target_emoji)
                                    TOTAL_ACTIONS_DONE += 1
                                except Exception as e:
                                    raise e

                        if "vote" in action or action in [
                            "camp_vote_only",
                            "camp_react_vote",
                            "camp_vote_view",
                            "camp_react_vote_view",
                        ]:
                            try:
                                opt = option_id if isinstance(option_id, list) else [0]
                                await user_client.vote_poll(chat_peer, msg_id, opt)
                                TOTAL_ACTIONS_DONE += 1
                            except Exception:
                                try:
                                    msg = await user_client.get_messages(chat_peer, msg_id)
                                    if msg and msg.reply_markup and msg.reply_markup.inline_keyboard:
                                        button = msg.reply_markup.inline_keyboard[0][0]
                                        await user_client.request_callback_answer(
                                            chat_id=chat_peer, message_id=msg_id, callback_data=button.callback_data
                                        )
                                        TOTAL_ACTIONS_DONE += 1
                                except Exception as e:
                                    raise e

                    if action == "camp_leave_specific_channel":
                        try:
                            await user_client.leave_chat(chat_peer)
                            TOTAL_ACTIONS_DONE += 1
                        except Exception as e:
                            raise e
                    elif action == "camp_leave_all_channels":
                        try:
                            async for dialog in user_client.get_dialogs():
                                if dialog.chat.type in ["channel", "group", "supergroup"]:
                                    try:
                                        await user_client.leave_chat(dialog.chat.id)
                                        await asyncio.sleep(0.5)
                                    except Exception:
                                        pass
                            TOTAL_ACTIONS_DONE += 1
                        except Exception as e:
                            raise e

                if delay > 0:
                    await asyncio.sleep(delay)

            await asyncio.wait_for(task_operations(), timeout=35)
            return True, None

        except asyncio.TimeoutError:
            return False, "Request timed out"
        except FloodWait as fw:
            await asyncio.sleep(fw.value)
            return False, f"FloodWait {fw.value}s"
        except Exception as e:
            err_str = str(e).split(":")[-1].strip() or "Unknown error"
            return False, err_str


async def execute_background_campaign(client, user_id, target_link, action, accounts, emoji="👍", option_id=0, extra_text="", launch_msg_id=None, campaign_id="", join_link="Skipped"):
    global ACTIVE_RUNNING_CAMPAIGNS
    ACTIVE_RUNNING_CAMPAIGNS += 1
    start_time = datetime.now()

    chat_peer = None
    msg_id = None

    if target_link and target_link != "ALL":
        try:
            if "t.me/" in target_link:
                parts = target_link.split("t.me/")[1].split("/")
                if parts[0] == "c":
                    chat_peer = int("-100" + parts[1])
                    msg_id = int(parts[2]) if len(parts) > 2 else None
                else:
                    chat_peer = parts[0]
                    msg_id = int(parts[1]) if len(parts) > 1 else None
            else:
                chat_peer = target_link
        except Exception:
            pass

    delay = get_user_delay(user_id)
    semaphore = asyncio.Semaphore(5)

    async def task_wrapper(session_str, idx):
        acc_label = f"+91{secrets.randbits(28)}"
        current_emoji = emoji
        if isinstance(emoji, list) and emoji:
            current_emoji = emoji[idx % len(emoji)]

        success, err_reason = await worker_single_account(
            session_str, chat_peer, msg_id, action, current_emoji, option_id, semaphore, delay, extra_text, join_link,
        )
        return success, err_reason, acc_label

    results = await asyncio.gather(*[task_wrapper(session_str, idx) for idx, session_str in enumerate(accounts)])

    ACTIVE_RUNNING_CAMPAIGNS = max(0, ACTIVE_RUNNING_CAMPAIGNS - 1)
    end_time = datetime.now()
    elapsed = end_time - start_time
    minutes = int(elapsed.total_seconds() // 60)
    seconds = int(elapsed.total_seconds() % 60)
    time_taken_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    success_count = sum(1 for r in results if r[0])
    failed_count = len(accounts) - success_count
    success_percentage = int((success_count / len(accounts)) * 100) if accounts else 0

    filled_blocks = int(success_percentage / 10)
    bar_str = "█" * filled_blocks + "░" * (10 - filled_blocks)

    failure_reasons_dict = {}
    for success, err_reason, label in results:
        if not success:
            failure_reasons_dict[err_reason] = failure_reasons_dict.get(err_reason, 0) + 1

    failure_lines = []
    for reason, count in list(failure_reasons_dict.items())[:5]:
        failure_lines.append(f"• {reason} ({count} accounts)")

    failures_block = ""
    if failure_lines:
        failures_block = "\n❌ **Failure reasons:**\n" + "\n".join(failure_lines)

    report_text = (
        f"✅ **Campaign Finished!**\n\n"
        f"`{bar_str}` `{success_percentage}%`\n\n"
        f"📊 **Total:** `{len(accounts)}`\n"
        f"✅ **Success:** `{success_count}`\n"
        f"❌ **Failed:** `{failed_count}`\n"
        f"⏱️ **Time taken:** `{time_taken_str}`"
        f"{failures_block}"
    )

    report_keyboard = InlineKeyboardMarkup([
        [styled_button("🚀 New Campaign", callback_data="new_campaign", style="success", emoji_key="crown")],
        [styled_button("🦚 🏠 Main Menu", callback_data="back_to_menu", style="primary", emoji_key="crown")],
    ])

    try:
        if launch_msg_id:
            await client.edit_message_text(chat_id=user_id, message_id=launch_msg_id, text=report_text, reply_markup=report_keyboard)
        else:
            await client.send_message(chat_id=user_id, text=report_text, reply_markup=report_keyboard)
    except Exception as e:
        logging.error(f"Error sending campaign report: {e}")

    if bot_settings.get("notifications", True):
        await send_log(f"✅ Campaign done for `{user_id}` — {success_count}/{len(accounts)}")


# ═══════════════════════════════════════
# COMMAND HANDLERS
# ═══════════════════════════════════════
@bot.on_message(filters.command(["start", "menu"]) & filters.private)
async def start_cmd(client, message):
    user_id = message.from_user.id
    if user_id in banned_users:
        await message.reply_text("❌ You are banned from using this bot.")
        return
    if bot_settings.get("maintenance") and not is_owner(user_id):
        await message.reply_text("⚠️ **Bot is currently under maintenance. Please try again later!**")
        return

    register_user_if_not_exists(user_id)
    await message.reply_text(MAIN_TEXT, reply_markup=get_main_keyboard(user_id))


@bot.on_message(filters.command("help") & filters.private)
async def help_cmd(client, message):
    await message.reply_text(HELP_TEXT, reply_markup=get_back_keyboard())


@bot.on_message(filters.command("me") & filters.private)
async def me_cmd(client, message):
    profile_text = await get_user_profile_text(client, message.from_user)
    await message.reply_text(profile_text, reply_markup=get_back_keyboard())


@bot.on_message(filters.command(["owner", "admin"]) & filters.private)
async def owner_panel_cmd(client, message):
    if not is_owner(message.from_user.id):
        await message.reply_text("Access Denied.")
        return
    await message.reply_text(get_owner_dashboard_text(), reply_markup=get_owner_keyboard())


@bot.on_message(filters.command("user") & filters.private)
async def user_info_cmd(client, message):
    if not is_owner(message.from_user.id):
        await message.reply_text("Access Denied.")
        return

    parts = message.text.strip().split()
    if len(parts) < 2:
        await message.reply_text("❌ **Usage:** `/user [user_id]`")
        return

    try:
        target_uid = int(parts[1])
        uid_str = str(target_uid)

        acc_count = len(user_db.get(uid_str, []))
        camp_count = user_campaign_counter.get(target_uid, 0)
        is_banned = "Yes 🚫" if target_uid in banned_users else "No ✅"
        adv_limit = allowed_adv_users.get(target_uid, "No Access")

        display_name = "Unknown"
        username_str = "None"

        try:
            target_obj = await client.get_users(target_uid)
            if target_obj:
                display_name = target_obj.first_name + (f" {target_obj.last_name}" if target_obj.last_name else "")
                if target_obj.username:
                    username_str = f"@{target_obj.username}"
        except Exception:
            pass

        info_text = (
            "👤 **USER INFORMATION SUMMARY**\n"
            "-----------------------------------\n\n"
            f"🆔 **User ID:** `{target_uid}`\n"
            f"📛 **Name:** `{display_name}`\n"
            f"💬 **Username:** {username_str}\n"
            f"📱 **Accounts:** `{acc_count}`\n"
            f"📋 **Campaigns:** `{camp_count}`\n"
            f"🚫 **Banned:** `{is_banned}`\n"
            f"📌 **Adv Access:** `{adv_limit}`"
        )
        await message.reply_text(info_text, reply_markup=get_owner_back_keyboard())
    except ValueError:
        await message.reply_text("❌ Send a valid numeric User ID.")


# ═══════════════════════════════════════
# TEXT INPUT HANDLER
# ═══════════════════════════════════════
@bot.on_message(filters.private & ~filters.command(["start", "menu", "help", "me", "owner", "admin", "user"]) & ~filters.document)
async def handle_user_inputs(client, message):
    user_id = message.from_user.id
    if user_id in banned_users or user_id not in user_sessions:
        return

    session = user_sessions[user_id]
    step = session.get("step")
    text = message.text.strip() if message.text else ""

    if step == "input_fsub_channel":
        bot_settings["fsub_channel"] = text
        save_bot_settings()
        user_sessions.pop(user_id, None)
        await message.reply_text(f"✅ **FSub Channel Updated to:** `{text}`", reply_markup=get_admin_settings_keyboard())

    elif step == "input_owner_username":
        bot_settings["owner_username"] = text
        save_bot_settings()
        user_sessions.pop(user_id, None)
        await message.reply_text(f"✅ **Owner Username Updated to:** `{text}`", reply_markup=get_admin_settings_keyboard())

    elif step == "input_log_gc":
        try:
            gc_id = int(text)
            global log_gc_id
            log_gc_id = gc_id
            save_bot_settings()
            user_sessions.pop(user_id, None)
            await message.reply_text(f"✅ **Log GC set to** `{gc_id}`", reply_markup=get_admin_settings_keyboard())
        except ValueError:
            await message.reply_text("❌ Send a valid Chat ID.")

    elif step == "input_acc_limit":
        try:
            limit = int(text)
            bot_settings["account_limit"] = limit
            save_bot_settings()
            user_sessions.pop(user_id, None)
            await message.reply_text(f"✅ **Account Limit set to** `{limit}`", reply_markup=get_admin_settings_keyboard())
        except ValueError:
            await message.reply_text("❌ Send a number.")

    elif step == "input_cooldown":
        try:
            cd = float(text)
            bot_settings["global_cooldown"] = cd
            save_bot_settings()
            user_sessions.pop(user_id, None)
            await message.reply_text(f"✅ **Global Cooldown:** `{cd}s`", reply_markup=get_admin_settings_keyboard())
        except ValueError:
            await message.reply_text("❌ Send a number.")

    elif step == "admin_broadcast_input":
        user_sessions.pop(user_id, None)
        all_users = list(user_db.keys())
        total_users = len(all_users)

        if total_users == 0:
            await message.reply_text("❌ No registered users found.", reply_markup=get_owner_back_keyboard())
            return

        status_msg = await message.reply_text(f"⏳ **Broadcasting started...**\nTargeting `{total_users}` users.")
        success, failed = 0, 0

        for uid_str in all_users:
            try:
                target_id = int(uid_str)
                await message.copy(chat_id=target_id)
                success += 1
                await asyncio.sleep(0.05)
            except FloodWait as fw:
                await asyncio.sleep(fw.value)
                try:
                    await message.copy(chat_id=target_id)
                    success += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1

        report_text = (
            "✅ **Broadcast Completed!**\n"
            "-----------------------------------\n\n"
            f"📊 **Total Users:** `{total_users}`\n"
            f"✅ **Delivered:** `{success}`\n"
            f"❌ **Failed:** `{failed}`"
        )
        await status_msg.edit_text(report_text, reply_markup=get_owner_back_keyboard())
        await send_log(f"📢 Broadcast done — {success}/{total_users}")

    elif step == "admin_ban_unban_step":
        try:
            target_id = int(text)
            if target_id in banned_users:
                banned_users.remove(target_id)
                msg = f"✅ User `{target_id}` has been Unbanned!"
            else:
                banned_users.add(target_id)
                msg = f"🚫 User `{target_id}` has been Banned!"
            user_sessions.pop(user_id, None)
            await message.reply_text(msg, reply_markup=get_owner_back_keyboard())
        except ValueError:
            await message.reply_text("❌ Invalid ID format. Send a valid numeric User ID.")

    elif step == "admin_manage_owners_step":
        try:
            target_id = int(text)
            if target_id == OWNER_ID:
                await message.reply_text("❌ Cannot remove main owner.")
                return
            ol = bot_settings.get("extra_owners", [])
            if target_id in ol:
                ol.remove(target_id)
                msg = f"✅ User `{target_id}` removed from Owners."
            else:
                ol.append(target_id)
                msg = f"✅ User `{target_id}` added as Owner."
            bot_settings["extra_owners"] = ol
            save_bot_settings()
            user_sessions.pop(user_id, None)
            await message.reply_text(msg, reply_markup=get_owner_back_keyboard())
        except ValueError:
            await message.reply_text("❌ Send numeric User ID.")

    elif step == "remove_single_acc":
        try:
            idx = int(text) - 1
            accounts = get_user_accounts(user_id)
            if 0 <= idx < len(accounts):
                accounts.pop(idx)
                user_db[str(user_id)] = accounts
                save_db()
                await message.reply_text("✅ Account removed successfully!", reply_markup=get_back_keyboard())
            else:
                await message.reply_text(f"❌ Invalid index! Choose between 1 and {len(accounts)}.")
            user_sessions.pop(user_id, None)
        except ValueError:
            await message.reply_text("❌ Send a valid index number.")

    elif step == "adv_revoke_input_uid":
        try:
            target_uid = int(text)
            if target_uid in allowed_adv_users:
                allowed_adv_users.pop(target_uid, None)
                save_adv_users()
                user_sessions.pop(user_id, None)
                await message.reply_text(
                    f"✅ **Adv Access Revoked!**\nUser `{target_uid}` is no longer allowed to run Adv Campaigns.",
                    reply_markup=get_adv_access_keyboard()
                )
            else:
                await message.reply_text("❌ This user does not have Adv Access.")
        except ValueError:
            await message.reply_text("❌ Send a valid numeric User ID.")

    elif step == "adv_access_step1":
        try:
            target_uid = int(text)
            all_accounts = get_all_bot_accounts()
            total_active = len(all_accounts)

            user_sessions[user_id] = {
                "step": "adv_access_step2",
                "target_uid": target_uid,
                "total_active": total_active,
            }

            msg_text = (
                "🔑 **SET ADV ID LIMIT**\n"
                "-----------------------------------\n\n"
                f"👤 **User ID:** `{target_uid}`\n"
                f"📦 **IDs in bot:** `{total_active}`\n\n"
                "How many accounts should this user be allowed to use?"
            )

            kbd = InlineKeyboardMarkup([
                [styled_button(f"📣 ✅ All ({total_active})", callback_data=f"set_adv_all_{target_uid}_{total_active}", style="success", emoji_key="check")],
                [styled_button("❌ Cancel", callback_data="cancel_adv_process", style="danger", emoji_key="skull")],
            ])
            await message.reply_text(msg_text, reply_markup=kbd)
        except ValueError:
            await message.reply_text("❌ Send a valid numeric User ID.")

    elif step == "adv_access_step2":
        try:
            count = int(text)
            target_uid = session.get("target_uid")
            total_active = session.get("total_active")

            if 1 <= count <= total_active:
                allowed_adv_users[target_uid] = count
                save_adv_users()
                user_sessions.pop(user_id, None)
                await message.reply_text(
                    f"✅ Success! Access granted to `{target_uid}` for `{count}` accounts.",
                    reply_markup=get_adv_access_keyboard(),
                )
            else:
                await message.reply_text(f"❌ Send a number between 1 and {total_active}.")
        except ValueError:
            await message.reply_text("❌ Send a valid number.")

    elif step == "phone":
        phone_number = text.replace(" ", "")
        status_msg = await message.reply_text("⏳ Sending OTP to Telegram...")

        temp_client = Client(f"temp_{user_id}", api_id=API_ID, api_hash=API_HASH, in_memory=True)
        try:
            await temp_client.connect()
            code_info = await temp_client.send_code(phone_number)

            user_sessions[user_id] = {
                "step": "otp",
                "phone": phone_number,
                "phone_code_hash": code_info.phone_code_hash,
                "temp_client": temp_client,
            }
            await status_msg.edit_text(
                f"✅ **OTP Sent Successfully!**\n\n"
                f"📱 **Phone:** `{phone_number}`\n"
                f"📩 Reply below with your 5-digit code:",
                reply_markup=get_login_cancel_keyboard(),
            )
        except Exception as e:
            await status_msg.edit_text(f"❌ **Failed to send OTP:** `{str(e)}`", reply_markup=get_login_cancel_keyboard())
            user_sessions.pop(user_id, None)

    elif step == "otp":
        otp_code = text.replace(" ", "").strip()
        temp_client = session.get("temp_client")
        phone = session.get("phone")
        phone_code_hash = session.get("phone_code_hash")

        if not temp_client or not phone_code_hash:
            await message.reply_text("❌ Session lost. Please try logging in again.", reply_markup=get_back_keyboard())
            user_sessions.pop(user_id, None)
            return

        try:
            await temp_client.sign_in(phone, phone_code_hash, otp_code)
            session_str = await temp_client.export_session_string()
            await temp_client.disconnect()

            add_user_account(user_id, session_str)
            user_sessions.pop(user_id, None)
            await message.reply_text("🎉 **ACCOUNT ADDED SUCCESSFULLY!** 😊", reply_markup=get_account_added_keyboard())

        except PhoneCodeInvalid:
            await message.reply_text("❌ **Invalid OTP Code!**", reply_markup=get_otp_retry_keyboard())
        except PhoneCodeExpired:
            await message.reply_text("⚠️ **OTP Expired!**", reply_markup=get_login_cancel_keyboard())
            if temp_client:
                await temp_client.disconnect()
            user_sessions.pop(user_id, None)
        except SessionPasswordNeeded:
            user_sessions[user_id]["step"] = "2fa"
            await message.reply_text("🔐 **2FA Password Required**", reply_markup=get_login_cancel_keyboard())
        except Exception as e:
            await message.reply_text(f"❌ Error: `{str(e)}`", reply_markup=get_otp_retry_keyboard())

    elif step == "2fa":
        password = text
        temp_client = session.get("temp_client")

        try:
            await temp_client.check_password(password)
            session_str = await temp_client.export_session_string()
            await temp_client.disconnect()

            add_user_account(user_id, session_str)
            user_sessions.pop(user_id, None)
            await message.reply_text("🎉 **ACCOUNT ADDED SUCCESSFULLY!** 😊", reply_markup=get_account_added_keyboard())
        except Exception as e:
            await message.reply_text(f"❌ Error: `{str(e)}`", reply_markup=get_login_cancel_keyboard())
            if temp_client and temp_client.is_connected:
                await temp_client.disconnect()
            user_sessions.pop(user_id, None)

    elif step == "input_session_string":
        add_user_account(user_id, text)
        user_sessions.pop(user_id, None)
        await message.reply_text("ACCOUNT ADDED SUCCESSFULLY 😊", reply_markup=get_account_added_keyboard())

    elif step == "input_bulk_sessions":
        sessions_list = text.split("\n")
        for s_str in sessions_list:
            s_clean = s_str.strip()
            if s_clean:
                add_user_account(user_id, s_clean)
        user_sessions.pop(user_id, None)
        await message.reply_text("ACCOUNT ADDED SUCCESSFULLY 😊", reply_markup=get_account_added_keyboard())

    elif step == "collect_custom_emoji":
        selected_emoji = text
        user_sessions[user_id]["chosen_emoji"] = [selected_emoji]
        session_key = secrets.token_hex(8)
        user_sessions[user_id].update({"key": session_key})

        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)

        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await message.reply_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif step == "collect_referral_link":
        ref_link = text.strip()
        if not ref_link.startswith("http") and "t.me" not in ref_link:
            await message.reply_text(
                "❌ **Invalid Referral Link!**\n\n"
                "**> 💡 Format :**\n"
                "> `https://t.me/YourBot?start=ref_XXXX`",
                reply_markup=get_login_cancel_keyboard()
            )
            return

        if is_owner(user_id) or user_id in allowed_adv_users:
            acc_limit = allowed_adv_users.get(user_id, len(get_all_bot_accounts()))
            accounts_to_use = get_all_bot_accounts()[:acc_limit]
        else:
            accounts_to_use = get_user_accounts(user_id)

        session_key = secrets.token_hex(8)
        user_sessions[user_id].update({
            "target_link": ref_link,
            "accounts_to_use": accounts_to_use,
            "key": session_key,
            "chosen_emoji": "None",
            "join_link": ref_link,
        })

        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await message.reply_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif step == "collect_link":
        target_link = text
        if is_owner(user_id) or user_id in allowed_adv_users:
            acc_limit = allowed_adv_users.get(user_id, len(get_all_bot_accounts()))
            accounts_to_use = get_all_bot_accounts()[:acc_limit]
        else:
            accounts_to_use = get_user_accounts(user_id)

        lim = bot_settings.get("account_limit", 0)
        if lim and not is_owner(user_id):
            accounts_to_use = accounts_to_use[:lim]

        user_sessions[user_id].update({"target_link": target_link, "accounts_to_use": accounts_to_use})

        if session.get("action") in ["camp_join_channel", "camp_leave_specific_channel"]:
            session_key = secrets.token_hex(8)
            user_sessions[user_id].update({"key": session_key, "chosen_emoji": "None", "join_link": target_link})
            summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
            confirm_keyboard = InlineKeyboardMarkup([
                [
                    styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                    styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
                ]
            ])
            await message.reply_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)
            return

        if session["action"] == "camp_bulk_dm":
            user_sessions[user_id]["step"] = "collect_bulk_dm_text"
            await message.reply_text("Send the message text you want to DM:")
        else:
            user_sessions[user_id]["step"] = "collect_join_link"
            step_three_kb = InlineKeyboardMarkup([
                [styled_button("⏭️ Skip (already joined)", callback_data="skip_join_link", style="primary", emoji_key="lightning")],
                [styled_button("👑 ❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")],
            ])
            await message.reply_text(
                f"✅ **Channel link saved!**\n🔗 `{target_link}`\n\nStep 2 — **Paste channel join link or tap Skip:**",
                reply_markup=step_three_kb,
                disable_web_page_preview=True
            )

    elif step == "collect_bulk_dm_text":
        user_sessions[user_id]["extra_text"] = text
        session_key = secrets.token_hex(8)
        user_sessions[user_id].update({"key": session_key, "chosen_emoji": "None", "join_link": "Skipped"})
        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await message.reply_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif step == "collect_join_link":
        join_link = text
        user_sessions[user_id]["join_link"] = join_link
        action = session.get("action")

        if "react" in action:
            user_sessions[user_id]["step"] = "choose_emoji_type"
            step_4_text = (
                f"✅ **Action: 😀+👁 {session.get('action_display', 'React')}**\n\n"
                "**Step 4️⃣ — 😀 Choose emoji type**\n\n"
                "> Select whether you want to use regular emojis or premium emojis."
            )
            await message.reply_text(step_4_text, reply_markup=emoji_type_keyboard)
        else:
            session_key = secrets.token_hex(8)
            user_sessions[user_id].update({"key": session_key})
            summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
            confirm_keyboard = InlineKeyboardMarkup([
                [
                    styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                    styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
                ]
            ])
            await message.reply_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

# ═══════════════════════════════════════
# SQL DOCUMENT HANDLER (Import)
# ═══════════════════════════════════════
@bot.on_message(filters.private & filters.document)
async def handle_sql_import(client, message):
    user_id = message.from_user.id
    if not is_owner(user_id):
        return
    if user_sessions.get(user_id, {}).get("step") != "admin_import_db_input":
        return
    doc = message.document
    if not (doc.file_name or "").endswith(".sql"):
        await message.reply_text("❌ Only .sql files!", reply_markup=get_owner_back_keyboard())
        return
    st = await message.reply_text("⏳ Parsing SQL...")
    path = f"import_{int(time.time())}.sql"
    try:
        await message.download(file_name=path)
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        u_imp = a_imp = s_imp = 0
        for line in content.splitlines():
            line = line.strip()
            if not line.upper().startswith("INSERT"):
                continue
            if "into users" in line.lower():
                m = re.search(r"VALUES\s*\(\s*(\d+)\s*,\s*'(.*?)'\s*,\s*(\d+)\s*\)", line, re.IGNORECASE)
                if m:
                    u = m.group(1)
                    accs = [a for a in m.group(2).replace("''", "'").split(",") if a.strip()]
                    user_db[u] = accs
                    user_campaign_counter[int(u)] = int(m.group(3))
                    u_imp += 1
            elif "into adv_users" in line.lower():
                m = re.search(r"VALUES\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", line, re.IGNORECASE)
                if m:
                    allowed_adv_users[int(m.group(1))] = int(m.group(2))
                    a_imp += 1
            elif "into bot_settings" in line.lower():
                m = re.search(r"VALUES\s*\(\s*'(.*?)'\s*,\s*'(.*?)'\s*\)", line, re.IGNORECASE)
                if m:
                    k = m.group(1).replace("''", "'")
                    v = m.group(2).replace("''", "'")
                    try:
                        parsed = json.loads(v)
                        if k == "global" and isinstance(parsed, dict):
                            bot_settings.update(parsed)
                        else:
                            bot_settings[k] = parsed
                    except Exception:
                        bot_settings[k] = v
                    s_imp += 1

        save_db()
        save_bot_settings()
        save_adv_users()
        user_sessions.pop(user_id, None)
        create_sql_backup("after-import")

        await st.edit_text(
            f"✅ **Import OK!**\n\n> 👥 Users: `{u_imp}`\n> 📌 Adv: `{a_imp}`\n> ⚙️ Settings: `{s_imp}`\n> 💾 Auto-backup: `{SQL_BACKUP_FILE}`",
            reply_markup=get_owner_back_keyboard()
        )
    except Exception as e:
        await st.edit_text(f"❌ Import failed: `{str(e)}`", reply_markup=get_owner_back_keyboard())
    finally:
        if os.path.exists(path):
            os.remove(path)

# ═══════════════════════════════════════
# CALLBACK ROUTER
# ═══════════════════════════════════════
@bot.on_callback_query()
async def callback_handler(client, query):
    await query.answer()

    user_id = query.from_user.id
    if user_id in banned_users:
        await query.answer("🚫 You are banned from using this bot.", show_alert=True)
        return

    if bot_settings.get("maintenance") and not is_owner(user_id):
        await query.answer("⚠️ Bot is under maintenance!", show_alert=True)
        return

    data = query.data
    accounts = get_user_accounts(user_id)

    if bot_settings.get("paid_mode") and not is_owner(user_id):
        if data in ["new_campaign", "user_adv_campaign", "add_account"]:
            await query.answer("💎 Paid Mode is Active! Please purchase access from owner.", show_alert=True)
            return

    # SETTINGS
    if data == "admin_settings":
        if not is_owner(user_id):
            return
        await query.message.edit_text(get_admin_settings_text(), reply_markup=get_admin_settings_keyboard())

    elif data == "toggle_maintenance":
        if not is_owner(user_id):
            return
        bot_settings["maintenance"] = not bot_settings.get("maintenance", False)
        save_bot_settings()
        await query.message.edit_text(get_admin_settings_text(), reply_markup=get_admin_settings_keyboard())

    elif data == "toggle_paid_mode":
        if not is_owner(user_id):
            return
        bot_settings["paid_mode"] = not bot_settings.get("paid_mode", False)
        save_bot_settings()
        await query.message.edit_text(get_admin_settings_text(), reply_markup=get_admin_settings_keyboard())

    elif data == "toggle_notifications":
        if not is_owner(user_id):
            return
        bot_settings["notifications"] = not bot_settings.get("notifications", True)
        save_bot_settings()
        await query.message.edit_text(get_admin_settings_text(), reply_markup=get_admin_settings_keyboard())

    elif data == "set_fsub_channel":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "input_fsub_channel"}
        await query.message.reply_text("📢 Send FSub Channel Username or ID:")

    elif data == "set_owner_username":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "input_owner_username"}
        await query.message.reply_text("👤 Send Owner Username:")

    elif data == "set_log_gc":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "input_log_gc"}
        await query.message.reply_text("📝 Send Log Group/Channel ID:")

    elif data == "admin_acc_limit":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "input_acc_limit"}
        await query.message.reply_text("📊 Send Account Limit (0 = unlimited):")

    elif data == "admin_cooldown":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "input_cooldown"}
        await query.message.reply_text("⏱ Send Global Cooldown (in seconds):")

    elif data == "admin_clear_log_gc":
        if not is_owner(user_id):
            return
        if os.path.exists(LOG_FILE):
            os.remove(LOG_FILE)
        await query.answer("✅ Log cleared!", show_alert=True)

    elif data == "add_account":
        user_accs = get_user_accounts(user_id)
        add_text = f"**Add Telegram Account**\n-----------------------------------\n\nConnected: **{len(user_accs)}**\n\nSelect method:"
        await query.message.edit_text(add_text, reply_markup=add_account_keyboard)

    elif data == "add_phone_otp":
        user_sessions[user_id] = {"step": "phone"}
        await query.message.edit_text("Send Phone Number in international format (+12345678900):", reply_markup=get_login_cancel_keyboard())

    elif data == "add_session_string":
        user_sessions[user_id] = {"step": "input_session_string"}
        await query.message.edit_text("Send Pyrogram / Telethon Session String:", reply_markup=get_login_cancel_keyboard())

    elif data == "add_bulk_sessions":
        user_sessions[user_id] = {"step": "input_bulk_sessions"}
        await query.message.edit_text("Send multiple session strings (one per line):", reply_markup=get_login_cancel_keyboard())

    elif data == "add_zip":
        await query.message.edit_text("📦 Please send your .zip file containing session files directly to the chat.")

    elif data == "admin_view_live":
        user_accs = get_user_accounts(user_id)
        if not user_accs:
            await query.answer("No Live accounts!", show_alert=True)
            return
        txt = f"✅ **Live Accounts ({len(user_accs)})**\n\n"
        for idx in range(len(user_accs)):
            txt += f"• Account {idx+1} — Active\n"
        await query.message.edit_text(txt, reply_markup=get_back_keyboard())

    elif data == "admin_view_expired":
        await query.answer("No expired sessions!", show_alert=True)

    elif data == "admin_remove_prompt":
        user_sessions[user_id] = {"step": "remove_single_acc"}
        await query.message.reply_text("Send index number of account to remove (e.g. 1):")

    elif data == "admin_remove_all_prompt":
        confirm_kbd = InlineKeyboardMarkup([
            [styled_button("⚠️ Yes, Delete All", callback_data="confirm_acc_remove_all", style="danger", emoji_key="skull")],
            [styled_button("👑 Cancel", callback_data="my_accounts", style="primary", emoji_key="crown")],
        ])
        await query.message.edit_text("⚠️ **Remove ALL accounts?**", reply_markup=confirm_kbd)

    elif data.startswith("admin_users_list") or data.startswith("userlist_page_"):
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        page = 1
        if "_" in data:
            try:
                page = int(data.split("_")[-1])
            except ValueError:
                page = 1
        all_uids = list(user_db.keys())
        total_users = len(all_uids)
        if not total_users:
            await query.message.edit_text("👥 Users List — Page 0/0\n\nNo users.", reply_markup=get_owner_back_keyboard())
            return
        total_pages = (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE
        page = max(1, min(page, total_pages))
        start_idx = (page - 1) * USERS_PER_PAGE
        end_idx = start_idx + USERS_PER_PAGE
        current_page_uids = all_uids[start_idx:end_idx]
        blocks = []
        header_text = f"------\n👥 **Users List — Page {page}/{total_pages}**\n\n"
        for uid_str in current_page_uids:
            try:
                uid = int(uid_str)
                acc_count = len(user_db.get(uid_str, []))
                camp_count = user_campaign_counter.get(uid, 0)
                display_name = "UNKNOWN"
                username_str = ""
                try:
                    user_obj = await client.get_users(uid)
                    if user_obj:
                        if user_obj.first_name:
                            display_name = user_obj.first_name + (f" {user_obj.last_name}" if user_obj.last_name else "")
                        if user_obj.username:
                            username_str = f"@{user_obj.username}"
                except Exception:
                    pass
                if username_str:
                    blocks.append(f"`{uid}` · **{display_name}** · {username_str}\n📱 `{acc_count}` accs · 📋 `{camp_count}` camps")
                else:
                    blocks.append(f"`{uid}` · **{display_name}**\n📱 `{acc_count}` accs · 📋 `{camp_count}` camps")
            except Exception:
                continue
        final_text = header_text + "\n\n".join(blocks)
        final_text += "\n\n--------------------------------------------------------\n------\n🔍 **Manage a user:**\n`/user [id]` — **full user info**"
        nav = [
            styled_button("📊 ◀️ Prev", callback_data=f"userlist_page_{max(1, page - 1)}", style="primary", emoji_key="lightning"),
            styled_button("📊 Next ▶️", callback_data=f"userlist_page_{min(total_pages, page + 1)}", style="primary", emoji_key="lightning"),
        ]
        rows = [
            nav,
            [styled_button("❤️‍🔥 📥 Export All Users Data", callback_data="export_users_data", style="primary", emoji_key="heart_fire")],
            [styled_button("💟 ◀️ Owner Panel", callback_data="owner_menu", style="primary", emoji_key="crown")],
        ]
        try:
            await query.message.edit_text(final_text, reply_markup=InlineKeyboardMarkup(rows), disable_web_page_preview=True)
        except Exception as e:
            logging.error(f"Error rendering user list UI: {e}")

    elif data == "export_users_data":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        status_msg = await query.message.reply_text("⏳ Generating users export...")
        export_filename = "all_users_export.txt"
        all_uids = list(user_db.keys())
        export_lines = [f"All Users Export — {len(all_uids)} users", "=" * 50 + "\n"]
        for uid_str in all_uids:
            try:
                uid = int(uid_str)
                acc_count = len(user_db.get(uid_str, []))
                camp_count = user_campaign_counter.get(uid, 0)
                display_name = "UNKNOWN"
                username_str = "None"
                try:
                    user_obj = await client.get_users(uid)
                    if user_obj:
                        if user_obj.first_name:
                            display_name = user_obj.first_name + (f" {user_obj.last_name}" if user_obj.last_name else "")
                        if user_obj.username:
                            username_str = f"@{user_obj.username}"
                except Exception:
                    pass
                export_lines.append(f"ID: {uid} | Name: {display_name} | Username: {username_str} | Accounts: {acc_count} | Campaigns: {camp_count}")
            except Exception:
                continue
        with open(export_filename, "w", encoding="utf-8") as f:
            f.write("\n".join(export_lines))
        await client.send_document(
            chat_id=user_id, document=export_filename,
            caption=f"📥 **All Users Export — {len(all_uids)} users**"
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
        if os.path.exists(export_filename):
            os.remove(export_filename)

    elif data in ["cancel_login_process", "cancel_login"]:
        session = user_sessions.get(user_id, {})
        temp_cli = session.get("temp_client")
        if temp_cli:
            try:
                await temp_cli.disconnect()
            except Exception:
                pass
        user_sessions.pop(user_id, None)
        await query.message.edit_text("❌ Login process cancelled.", reply_markup=get_back_keyboard())

    elif data == "retry_otp_input":
        session = user_sessions.get(user_id, {})
        if not session or "phone" not in session:
            user_sessions[user_id] = {"step": "phone"}
            await query.message.edit_text("Enter Phone Number (+12345678900):", reply_markup=get_login_cancel_keyboard())
            return
        session["step"] = "otp"
        await query.message.edit_text(f"📱 Phone: `{session['phone']}`\n\n✏️ Enter valid OTP again:", reply_markup=get_login_cancel_keyboard())

    elif data == "back_to_menu":
        user_sessions.pop(user_id, None)
        await query.message.edit_text(MAIN_TEXT, reply_markup=get_main_keyboard(user_id))

    elif data == "cancel_action":
        user_sessions.pop(user_id, None)
        await query.message.edit_text("❌ **Campaign creation cancelled.**")

    elif data == "skip_join_link":
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        action = cached.get("action")
        user_sessions[user_id]["join_link"] = "Skipped"
        if "react" in action:
            user_sessions[user_id]["step"] = "choose_emoji_type"
            step_4_text = (
                f"✅ **Action: 😀+👁 {cached.get('action_display', 'React')}**\n\n"
                "**Step 4️⃣ — 😀 Choose emoji type**"
            )
            await query.message.edit_text(step_4_text, reply_markup=emoji_type_keyboard)
        else:
            session_key = secrets.token_hex(8)
            user_sessions[user_id].update({"key": session_key, "chosen_emoji": "None"})
            summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
            confirm_keyboard = InlineKeyboardMarkup([
                [
                    styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                    styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
                ]
            ])
            await query.message.edit_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif data == "emoji_type_normal":
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        user_sessions[user_id]["emoji_type"] = "Normal"
        user_sessions[user_id]["step"] = "choose_emoji"
        user_sessions[user_id]["selected_emojis"] = []
        txt, kbd = get_normal_emoji_keyboard([])
        await query.message.edit_text(txt, reply_markup=kbd)

    elif data == "emoji_type_premium":
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        user_sessions[user_id]["emoji_type"] = "Premium"
        user_sessions[user_id]["step"] = "premium_instructions"
        await query.message.edit_text(PREMIUM_EMOJI_TEXT, reply_markup=get_premium_emoji_keyboard())

    elif data == "custom_emoji_single":
        user_sessions[user_id]["step"] = "collect_custom_emoji"
        await query.message.reply_text("Please type or paste single custom emoji you want to react with:")

    elif data == "premium_ready_start":
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        session_key = secrets.token_hex(8)
        user_sessions[user_id].update({"key": session_key, "chosen_emoji": "auto"})
        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await query.message.edit_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif data in ["new_campaign", "user_adv_campaign"]:
        acc_count = (
            allowed_adv_users.get(user_id, len(get_all_bot_accounts()))
            if (is_owner(user_id) or user_id in allowed_adv_users)
            else len(accounts)
        )
        adv_text = (
            "🚀 **Adv Campaign**\n"
            "-----------------------------------\n\n"
            f"📱 **{acc_count} active account(s) available.**\n\n"
            "**Step 1 — Choose what your accounts should do:**"
        )
        await query.message.edit_text(adv_text, reply_markup=get_adv_campaign_keyboard())

    elif data == "camp_leave_channel_menu":
        leave_menu_text = "✅ **Action:** 🚪 Leave Channel\n\nStep 2️⃣ — Choose which channels to leave:"
        await query.message.edit_text(leave_menu_text, reply_markup=get_leave_channel_sub_keyboard())

    elif data == "camp_leave_all_channels":
        if not accounts and not is_owner(user_id) and user_id not in allowed_adv_users:
            await query.answer("Please add at least 1 account first!", show_alert=True)
            return
        if is_owner(user_id) or user_id in allowed_adv_users:
            acc_limit = allowed_adv_users.get(user_id, len(get_all_bot_accounts()))
            accounts_to_use = get_all_bot_accounts()[:acc_limit]
        else:
            accounts_to_use = get_user_accounts(user_id)
        session_key = secrets.token_hex(8)
        user_sessions[user_id] = {
            "step": "confirm_run",
            "action": "camp_leave_all_channels",
            "action_display": "Leave All Channels",
            "target_link": "ALL",
            "accounts_to_use": accounts_to_use,
            "key": session_key,
            "chosen_emoji": "None",
            "join_link": "Skipped",
        }
        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await query.message.edit_text(summary_text, reply_markup=confirm_keyboard)

    elif data == "camp_bot_referral":
        if not accounts and not is_owner(user_id) and user_id not in allowed_adv_users:
            await query.answer("Please add at least 1 account first!", show_alert=True)
            return
        user_sessions[user_id] = {"step": "collect_referral_link", "action": "camp_bot_referral", "action_display": "Bot Referral"}
        prompt_msg = (
            "🔗 **BOT REFERRAL**\n\n"
            "**> 📩 Enter Referral Link**\n\n"
            "**> 💡 Example :**\n"
            "> `https://t.me/YourBot?start=ref_12345`\n"
            "> `https://t.me/YourBot?start=ABC123`\n\n"
            "> ⚠️ All accounts will open this link"
        )
        kbd = InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")]])
        await query.message.reply_text(prompt_msg, reply_markup=kbd)

    elif data == "owner_menu":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        user_sessions.pop(user_id, None)
        await query.message.edit_text(get_owner_dashboard_text(), reply_markup=get_owner_keyboard())

    elif data == "admin_broadcast":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "admin_broadcast_input"}
        prompt_text = (
            "📢 **BROADCAST PANEL**\n"
            "-----------------------------------\n\n"
            "Aap jo bhi announcement bhejna chahte hain (Text, Photo, Video, Forward Message) niche send karein:"
        )
        cancel_kb = InlineKeyboardMarkup([[styled_button("❌ Cancel Broadcast", callback_data="cancel_broadcast", style="danger", emoji_key="skull")]])
        await query.message.edit_text(prompt_text, reply_markup=cancel_kb)

    elif data == "cancel_broadcast":
        user_sessions.pop(user_id, None)
        await query.message.edit_text(get_owner_dashboard_text(), reply_markup=get_owner_keyboard())

    elif data == "admin_adv_access":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        user_sessions.pop(user_id, None)
        await query.message.edit_text(get_adv_access_menu_text(), reply_markup=get_adv_access_keyboard())

    elif data == "adv_grant_access":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        user_sessions[user_id] = {"step": "adv_access_step1"}
        await query.message.edit_text(
            "➕ **GRANT ADV ACCESS**\n\nSend Telegram User ID to grant access:",
            reply_markup=InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_adv_process", style="danger", emoji_key="skull")]]),
        )

    elif data == "adv_revoke_access":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        user_sessions[user_id] = {"step": "adv_revoke_input_uid"}
        await query.message.edit_text(
            "➖ **REVOKE ADV ACCESS**\n\nSend Telegram User ID to revoke access:",
            reply_markup=InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_adv_process", style="danger", emoji_key="skull")]]),
        )

    elif data == "adv_authorized_users":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        if not allowed_adv_users:
            await query.message.edit_text("👥 No authorized users.", reply_markup=get_adv_access_keyboard())
            return
        lines = ["👥 **AUTHORIZED ADV USERS LIST**\n====================================\n"]
        for uid_, limit in allowed_adv_users.items():
            lines.append(f"• User ID: `{uid_}` — Limit: `{limit}` accounts")
        lines.append("\n_Use Revoke button to remove access._")
        await query.message.edit_text("\n".join(lines), reply_markup=InlineKeyboardMarkup([[styled_button("🔙 Back", callback_data="admin_adv_access", style="primary", emoji_key="skull")]]))

    elif data.startswith("set_adv_all_"):
        parts = data.split("_")
        target_uid = int(parts[3])
        total_active = int(parts[4])
        allowed_adv_users[target_uid] = total_active
        save_adv_users()
        user_sessions.pop(user_id, None)
        await query.message.edit_text(f"✅ Granted ALL ({total_active}) accounts access to `{target_uid}`!", reply_markup=get_adv_access_keyboard())

    elif data == "cancel_adv_process":
        user_sessions.pop(user_id, None)
        await query.message.edit_text(get_adv_access_menu_text(), reply_markup=get_adv_access_keyboard())

    elif data == "admin_ban_unban":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "admin_ban_unban_step"}
        await query.message.edit_text("Send User ID to Ban or Unban:", reply_markup=get_owner_back_keyboard())


# ═══════════════════════════════════════
    # EXTENDED OWNER PANEL CALLBACKS
    # ═══════════════════════════════════════
    elif data == "admin_all_sessions":
        if not is_owner(user_id):
            return
        all_s = get_all_bot_accounts()
        st = await query.message.reply_text(f"⏳ Checking {len(all_s)} sessions...")
        live, dead = [], []
        for s in all_s[:30]:
            try:
                async with Client("all_sess_tmp", api_id=API_ID, api_hash=API_HASH, session_string=s, in_memory=True) as tc:
                    await tc.get_me()
                    live.append(s)
            except Exception:
                dead.append(s)
        await st.edit_text(
            f"✅ **All Sessions**\n\n> 🟢 Live: `{len(live)}`\n> 🔴 Dead: `{len(dead)}`\n> 📊 Checked: `{min(30, len(all_s))}/{len(all_s)}`",
            reply_markup=get_owner_back_keyboard()
        )

    elif data == "admin_log_gc":
        if not is_owner(user_id):
            return
        if not log_gc_id:
            await query.answer("Log GC not set!", show_alert=True)
            return
        try:
            await bot.send_message(log_gc_id, f"🧪 Test Log — `{datetime.now()}`")
            await query.answer("✅ Test log sent!", show_alert=True)
        except Exception as e:
            await query.answer(f"❌ Failed: {str(e)[:100]}", show_alert=True)

    elif data == "admin_fsub_check":
        if not is_owner(user_id):
            return
        fsub = bot_settings.get("fsub_channel", "Not Set")
        await query.message.edit_text(
            f"📣 **FSub Check**\n\n> 📡 Channel: `{fsub}`\n\n✅ FSub enforcement ACTIVE.",
            reply_markup=get_owner_back_keyboard()
        )

    elif data == "admin_manage_owners":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "admin_manage_owners_step"}
        ol = bot_settings.get("extra_owners", [])
        txt = "❤️ **Manage Owners**\n\n"
        txt += f"> 👑 Extra Owners: `{len(ol)}`\n"
        for o in ol:
            txt += f"> • `{o}`\n"
        txt += "\n**> 📩 Send User ID to ADD/REMOVE**"
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_campaign_info":
        if not is_owner(user_id):
            return
        txt = (
            f"🔍 **Campaign Info**\n\n"
            f"> 🚀 Total Campaigns: `{sum(user_campaign_counter.values())}`\n"
            f"> 🔄 Running Now: `{ACTIVE_RUNNING_CAMPAIGNS}`\n"
            f"> ⚡ Total Actions: `{TOTAL_ACTIONS_DONE}`\n"
            f"> 📝 History Entries: `{len(campaign_history)}`"
        )
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_db_stats":
        if not is_owner(user_id):
            return
        sizes = {}
        for f in [DB_FILE, SETTINGS_FILE, ADV_USERS_FILE, FROZEN_FILE, LOG_FILE]:
            if os.path.exists(f):
                sizes[f] = f"{os.path.getsize(f)/1024:.1f} KB"
            else:
                sizes[f] = "N/A"
        txt = (
            f"💾 **DB Stats**\n\n"
            f"> 👥 Users: `{len(user_db)}`\n"
            f"> 📱 Accounts: `{len(get_all_bot_accounts())}`\n"
            f"> 📌 Adv Users: `{len(allowed_adv_users)}`\n"
            f"> 🧊 Frozen: `{len(frozen_accounts)}`\n\n"
            "**> 📁 Files :**\n"
        )
        for k, v in sizes.items():
            txt += f"> • `{k}` — `{v}`\n"
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_db_diagnostics":
        if not is_owner(user_id):
            return
        issues = []
        empty_users = sum(1 for v in user_db.values() if not v)
        if empty_users:
            issues.append(f"> ⚠️ `{empty_users}` users with 0 accounts")
        all_s = get_all_bot_accounts()
        dupes = len(all_s) - len(set(all_s))
        if dupes:
            issues.append(f"> ⚠️ `{dupes}` duplicate sessions")
        if not issues:
            issues.append("> ✅ No issues detected")
        txt = (
            f"🧟 **DB Diagnostics**\n\n"
            f"> 👥 Total users: `{len(user_db)}`\n"
            f"> 📱 Total accounts: `{len(all_s)}`\n"
            f"> 🔄 Unique sessions: `{len(set(all_s))}`\n\n"
            "**> 🔍 Results :**\n" + "\n".join(issues)
        )
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_frozen_accounts":
        if not is_owner(user_id):
            return
        if not frozen_accounts:
            await query.message.edit_text("❄️ **No frozen accounts.**", reply_markup=get_owner_back_keyboard())
            return
        txt = "❄️ **Frozen Accounts**\n\n"
        for label, info in list(frozen_accounts.items())[:20]:
            txt += f"> • `{label[:20]}` — {info.get('error', 'Unknown')[:30]}\n"
        txt += f"\n**> Total : `{len(frozen_accounts)}`**"
        kbd = InlineKeyboardMarkup([
            [styled_button("🗑️ Clear All", callback_data="clear_frozen", style="danger", emoji_key="skull")],
            [styled_button("◀️ Back", callback_data="owner_menu", style="primary", emoji_key="crown")],
        ])
        await query.message.edit_text(txt, reply_markup=kbd)

    elif data == "clear_frozen":
        if not is_owner(user_id):
            return
        frozen_accounts.clear()
        save_frozen()
        await query.answer("✅ Cleared!", show_alert=True)
        await query.message.edit_text(get_owner_dashboard_text(), reply_markup=get_owner_keyboard())

    elif data == "admin_account_health":
        if not is_owner(user_id):
            return
        all_s = get_all_bot_accounts()
        live = dead = 0
        for s in all_s[:20]:
            try:
                async with Client("ah_tmp", api_id=API_ID, api_hash=API_HASH, session_string=s, in_memory=True) as tc:
                    await tc.get_me()
                    live += 1
            except Exception:
                dead += 1
        health = int((live / max(1, live + dead)) * 100) if (live + dead) else 0
        txt = (
            f"📊 **Account Health**\n\n"
            f"> 🟢 Live: `{live}`\n"
            f"> 🔴 Dead: `{dead}`\n"
            f"> 💯 Health: `{health}%`\n"
            f"> 📊 Sampled: `{min(20, len(all_s))}/{len(all_s)}`"
        )
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_analytics":
        if not is_owner(user_id):
            return
        top_users = sorted(user_campaign_counter.items(), key=lambda x: x[1], reverse=True)[:5]
        txt = (
            f"📈 **Analytics**\n\n"
            f"> 👥 Total Users: `{len(user_db)}`\n"
            f"> 🚀 All Campaigns: `{sum(user_campaign_counter.values())}`\n"
            f"> ⚡ Total Actions: `{TOTAL_ACTIONS_DONE}`\n\n"
            "**> 🏆 Top Users :**\n"
        )
        for u, c in top_users:
            txt += f"> • `{u}` — `{c}` camps\n"
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_rotation":
        if not is_owner(user_id):
            return
        total_accs = len(get_all_bot_accounts())
        txt = (
            f"⚡ **Rotation**\n\n"
            f"> 📱 Total accounts: `{total_accs}`\n"
            f"> ✅ Active: `{total_accs - len(frozen_accounts)}`\n"
            f"> 🧊 Frozen: `{len(frozen_accounts)}`\n\n"
            "**> 💡 Rotation happens automatically**\n"
            "> _between campaigns to avoid ban_"
        )
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_notifications":
        if not is_owner(user_id):
            return
        n_st = "🟢 ON" if bot_settings.get("notifications", True) else "🔴 OFF"
        log_st = "✅ Set" if log_gc_id else "❌ Not Set"
        log_entries = 0
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r") as f:
                    log_entries = sum(1 for _ in f)
            except Exception:
                log_entries = 0
        txt = (
            f"🔔 **Notifications**\n\n"
            f"> 🔔 Notifications: {n_st}\n"
            f"> 📝 Log GC: {log_st}\n"
            f"> 📊 Log Entries: `{log_entries}`\n\n"
            "**> 💡 Toggle via Settings**"
        )
        await query.message.edit_text(txt, reply_markup=get_owner_back_keyboard())

    elif data == "admin_session_health":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        status_msg = await query.message.reply_text("⏳ Checking session health...")
        all_sessions = get_all_bot_accounts()
        live_sessions, expired_sessions = [], []
        for session_str in all_sessions:
            try:
                async with Client("health_tmp", api_id=API_ID, api_hash=API_HASH, session_string=session_str, in_memory=True) as tc:
                    await tc.get_me()
                    live_sessions.append(session_str)
            except Exception:
                expired_sessions.append(session_str)
        active_file, expired_file = "active_sessions.txt", "expired_sessions.txt"
        with open(active_file, "w") as f:
            f.write("\n".join(live_sessions))
        with open(expired_file, "w") as f:
            f.write("\n".join(expired_sessions))
        await client.send_document(chat_id=user_id, document=active_file, caption=f"✅ Active Sessions — {len(live_sessions)}")
        health_kbd_rows = []
        if len(expired_sessions) > 0:
            health_kbd_rows.append([styled_button("💖 🗑️ Remove All Expired", callback_data="remove_all_expired_sessions", style="danger", emoji_key="skull")])
        health_kbd_rows.append([styled_button("📊 ◀️ Owner Panel", callback_data="owner_menu", style="primary", emoji_key="crown")])
        await client.send_document(chat_id=user_id, document=expired_file, caption=f"🔴 Expired Sessions — {len(expired_sessions)}", reply_markup=InlineKeyboardMarkup(health_kbd_rows))
        try:
            await status_msg.delete()
        except Exception:
            pass
        for f in [active_file, expired_file]:
            if os.path.exists(f):
                os.remove(f)

    elif data == "remove_all_expired_sessions":
        if not is_owner(user_id):
            await query.answer("Access Denied!", show_alert=True)
            return
        await query.answer("Cleaning expired sessions...", show_alert=True)
        all_uids = list(user_db.keys())
        removed_count = 0
        for uid_str in all_uids:
            user_accs = user_db.get(uid_str, [])
            valid_accs = []
            for s in user_accs:
                try:
                    async with Client("clean_tmp", api_id=API_ID, api_hash=API_HASH, session_string=s, in_memory=True) as tc:
                        await tc.get_me()
                        valid_accs.append(s)
                except Exception:
                    removed_count += 1
            user_db[uid_str] = valid_accs
        save_db()
        await query.message.reply_text(f"✅ **Expired Sessions Removed!**\nCleaned `{removed_count}` expired.", reply_markup=get_owner_back_keyboard())

    elif data == "admin_export_db":
        if not is_owner(user_id):
            return
        st = await query.message.reply_text("⏳ Extracting DB Backup...")
        if create_sql_backup("manual-export"):
            try:
                await client.send_document(
                    chat_id=user_id, document=SQL_BACKUP_FILE,
                    caption=(
                        f"💾 **DB Backup Extracted**\n\n"
                        f"> 👥 Users: `{len(user_db)}`\n"
                        f"> 📱 Accounts: `{sum(len(v) for v in user_db.values())}`\n"
                        f"> 📌 Adv Users: `{len(allowed_adv_users)}`\n"
                        f"> 🚫 Banned: `{len(banned_users)}`\n"
                        f"> 💾 Saved: `{SQL_BACKUP_FILE}`"
                    )
                )
                try:
                    await st.delete()
                except Exception:
                    pass
            except Exception as e:
                await st.edit_text(f"❌ Send error: `{str(e)}`", reply_markup=get_owner_back_keyboard())
        else:
            await st.edit_text("❌ Backup failed!", reply_markup=get_owner_back_keyboard())

    elif data == "admin_import_db":
        if not is_owner(user_id):
            return
        user_sessions[user_id] = {"step": "admin_import_db_input"}
        kbd = InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="owner_menu", style="danger", emoji_key="skull")]])
        await query.message.edit_text(
            "📥 Send .sql file to import:\n\n> 💡 After import, auto backup will be created",
            reply_markup=kbd
        )

    elif data == "my_profile":
        profile_text = await get_user_profile_text(client, query.from_user)
        await query.message.edit_text(profile_text, reply_markup=get_back_keyboard())

    elif data == "settings":
        await query.message.edit_text(get_settings_text(user_id), reply_markup=get_settings_keyboard())

    elif data.startswith("set_speed_"):
        speed_val = data.replace("set_speed_", "")
        user_settings[user_id] = speed_val
        await query.message.edit_text(get_settings_text(user_id), reply_markup=get_settings_keyboard())

    elif data == "scheduled_campaigns_menu":
        text = (
            "⏰ **SCHEDULED CAMPAIGNS**\n\n"
            "Schedule your campaigns to run automatically!\n\n"
            "📖 **How to use:**\n"
            "1. Click 'Schedule New Campaign'\n"
            "2. Choose campaign type\n"
            "3. Enter target/post link\n"
            "4. Set date/time (DD/MM/YYYY HH:MM)\n"
            "5. Confirm schedule\n\n"
            "⏰ Time format: 25/12/2024 14:30"
        )
        scheduled_menu_keyboard = InlineKeyboardMarkup([
            [styled_button("📅 Schedule New Campaign", callback_data="schedule_new_campaign", style="primary", emoji_key="crown")],
            [styled_button("📋 My Scheduled Campaigns", callback_data="my_scheduled_campaigns", style="primary", emoji_key="gift")],
            [styled_button("❌ Cancel Schedule", callback_data="cancel_schedule", style="danger", emoji_key="skull")],
            [styled_button("🏠 Back to Main", callback_data="back_to_menu", style="primary", emoji_key="crown")]
        ])
        await query.message.edit_text(text=text, reply_markup=scheduled_menu_keyboard)

    elif data == "my_accounts":
        user_accs = get_user_accounts(user_id)
        await query.message.edit_text(f"🎭 **My Accounts**\n\nConnected: `{len(user_accs)}`", reply_markup=owner_accounts_keyboard)

    elif data == "confirm_acc_remove_all":
        uid_str = str(user_id)
        if uid_str in user_db:
            user_db[uid_str] = []
            save_db()
        await query.message.edit_text("✅ All accounts removed!", reply_markup=get_back_keyboard())

    elif data in [
        "camp_auto_diff_react_view", "camp_react_only", "camp_auto_react", "camp_vote_only",
        "camp_react_vote", "camp_view_only", "camp_react_view", "camp_vote_view",
        "camp_react_vote_view", "camp_join_channel", "camp_leave_specific_channel", "camp_bulk_dm",
    ]:
        if not accounts and not is_owner(user_id) and user_id not in allowed_adv_users:
            await query.answer("Please add at least 1 account first!", show_alert=True)
            return
        action_display = data.replace("camp_", "").replace("_", " ").title()
        user_sessions[user_id] = {"step": "collect_link", "action": data, "action_display": action_display}
        if data == "camp_bulk_dm":
            await query.message.reply_text("Send Target Username or Link for Bulk DM:")
        elif data == "camp_join_channel":
            await query.message.reply_text("🎯 **Action: Join Channel**\n\n👉 Paste Telegram Channel Link:", reply_markup=InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")]]))
        elif data == "camp_leave_specific_channel":
            await query.message.reply_text("🐸🚪 **Action: Leave Specific Channel**\n\n👉 Paste Telegram Channel Link/Username:", reply_markup=InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")]]))
        else:
            await query.message.reply_text(f"**Action:** {action_display}\n\nStep 1 — Paste Telegram post URL:", reply_markup=InlineKeyboardMarkup([[styled_button("❌ Cancel", callback_data="cancel_action", style="danger", emoji_key="skull")]]))

    elif data.startswith("select_emoji_"):
        selected_emoji = data.replace("select_emoji_", "")
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        selected_list = user_sessions[user_id].get("selected_emojis", [])
        if selected_emoji in selected_list:
            selected_list.remove(selected_emoji)
            await query.answer(f"Removed {selected_emoji}")
        else:
            selected_list.append(selected_emoji)
            await query.answer(f"Added {selected_emoji}")
        user_sessions[user_id]["selected_emojis"] = selected_list
        txt, kbd = get_normal_emoji_keyboard(selected_list)
        await query.message.edit_text(txt, reply_markup=kbd)

    elif data == "confirm_multi_emoji":
        cached = user_sessions.get(user_id)
        if not cached:
            await query.answer("Session expired!", show_alert=True)
            return
        selected_list = cached.get("selected_emojis", [])
        if not selected_list:
            await query.answer("Kam se kam 1 Emoji select karein!", show_alert=True)
            return
        user_sessions[user_id]["chosen_emoji"] = selected_list
        session_key = secrets.token_hex(8)
        user_sessions[user_id].update({"key": session_key})
        summary_text = generate_campaign_summary_text(user_sessions[user_id], user_id)
        confirm_keyboard = InlineKeyboardMarkup([
            [
                styled_button("🚀 Run Campaign", callback_data=f"run_confirmed_{session_key}", style="success", emoji_key="crown"),
                styled_button("❌ Cancel", callback_data="cancel_campaign_setup", style="danger", emoji_key="skull"),
            ]
        ])
        await query.message.edit_text(summary_text, reply_markup=confirm_keyboard, disable_web_page_preview=True)

    elif data.startswith("run_confirmed_"):
        session_key = data.replace("run_confirmed_", "")
        cached = user_sessions.get(user_id)
        if not cached or cached.get("key") != session_key:
            await query.answer("Session Expired!", show_alert=True)
            return
        target_link = cached["target_link"]
        action = cached["action"]
        accounts_to_use = cached["accounts_to_use"]
        action_display = cached["action_display"]
        emoji = cached.get("chosen_emoji", ["👍"])
        extra_text = cached.get("extra_text", "")
        join_link = cached.get("join_link", "Skipped")
        campaign_hex_id = "#" + secrets.token_hex(11)
        launch_panel = (
            f"🚀 **Campaign {campaign_hex_id}\nLaunched!**\n\n"
            f"⚡ Action: 🔥 {action_display}\n"
            f"📱 Accounts: {len(accounts_to_use)}"
        )
        launch_keyboard = InlineKeyboardMarkup([
            [styled_button("❤️‍🔥 My Campaigns", callback_data="my_campaigns", style="primary", emoji_key="heart_fire")],
            [styled_button("🏠 Main Menu", callback_data="back_to_menu", style="primary", emoji_key="crown")],
        ])
        await query.message.edit_text(launch_panel, reply_markup=launch_keyboard)
        user_campaign_counter[user_id] = user_campaign_counter.get(user_id, 0) + 1
        campaign_history.append({"user_id": user_id, "id": campaign_hex_id, "action": action_display, "time": datetime.now().strftime("%H:%M")})
        launch_msg_id = query.message.id
        user_sessions.pop(user_id, None)
        asyncio.create_task(
            execute_background_campaign(
                client, user_id, target_link, action, accounts_to_use, emoji,
                extra_text=extra_text, launch_msg_id=launch_msg_id,
                campaign_id=campaign_hex_id, join_link=join_link,
            )
        )

    elif data == "cancel_campaign_setup":
        user_sessions.pop(user_id, None)
        await query.message.edit_text("Campaign Cancelled.", reply_markup=get_back_keyboard())

    elif data == "my_campaigns":
        user_camps = [c for c in campaign_history if c["user_id"] == user_id][-10:]
        if not user_camps:
            await query.message.edit_text("📋 My Campaigns:\nNo active tasks.", reply_markup=get_back_keyboard())
            return
        txt = "📋 **My Campaigns**\n\n"
        for c in user_camps:
            txt += f"> 🆔 `{c['id']}` · {c['action']} · {c['time']}\n"
        await query.message.edit_text(txt, reply_markup=get_back_keyboard())

    elif data == "stats":
        user_accs = get_user_accounts(user_id)
        campaigns_count = user_campaign_counter.get(user_id, 0)
        stats_text = f"📈 **YOUR STATS**\n\n🎭 Accounts: `{len(user_accs)}`\n🚀 Campaigns: `{campaigns_count}`"
        await query.message.edit_text(stats_text, reply_markup=get_back_keyboard())

    elif data == "help_guide":
        await query.message.edit_text(HELP_TEXT, reply_markup=get_back_keyboard())

    elif data == "support":
        await query.message.edit_text(SUPPORT_TEXT, reply_markup=get_back_keyboard())


# ----------------- MAIN EXECUTION -----------------
if __name__ == "__main__":
    print("✅ Marco Auto Voting Bot is starting...")
    print(f"📂 SQL file: {SQL_FILE} ({'✅ Found' if os.path.exists(SQL_FILE) else '❌ Not found'})")
    load_db()
    print(f"👥 Loaded Users : {len(user_db)}")
    print(f"📱 Loaded Accounts : {sum(len(v) for v in user_db.values())}")
    bot.run()