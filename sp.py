import asyncio
import json
import os
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardMarkup, InlineKeyboardButton
)
from pyrogram.enums import ChatMemberStatus

# ============================================================
# CONFIGURATION
# ============================================================
API_ID = 31455231
API_HASH = "abc5f80a6b52c9e2bc1ce3693a0b77c7"
BOT_TOKEN = "8862967081:AAGYRxTnqsDqGeXj5yNQ1P0OKfoUN3oPGPw"  # ⚠️ Revoke kar ke naya token le!
BOT_USERNAME = "ohkflex"
ADMIN_USER_ID = 8639227150
MRFLXX_USERNAME = "@mrflxx"
# ============================================================

USERS_DB = "users.json"
CONFIG_DB = "config.json"
DEFAULT_CONFIG = {"force_join_channels": [], "force_join_enabled": False}

def load_db(file):
    if os.path.exists(file):
        with open(file, "r") as f:
            return json.load(f)
    return {}

def save_db(data, file):
    with open(file, "w") as f:
        json.dump(data, f, indent=2)

def get_config():
    if os.path.exists(CONFIG_DB):
        return load_db(CONFIG_DB)
    return DEFAULT_CONFIG.copy()

def save_config(data):
    save_db(data, CONFIG_DB)

def get_user(user_id):
    users = load_db(USERS_DB)
    uid = str(user_id)
    if uid not in users:
        users[uid] = {
            "username": "",
            "first_name": "",
            "referral_count": 0,
            "referred_by": None,
            "tier1_claimed": False,
            "tier2_claimed": False,
            "tier1_complete_notified": False,
            "tier2_complete_notified": False,
            "join_date": str(datetime.now()),
            "banned": False
        }
        save_db(users, USERS_DB)
    return users[uid]

def update_user(user_id, data):
    users = load_db(USERS_DB)
    users[str(user_id)] = data
    save_db(users, USERS_DB)

def get_all_users():
    return load_db(USERS_DB)

app = Client(
    "FreeAltHubBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# ============================================================
# FORCE JOIN FUNCTIONS
# ============================================================
async def check_channel_membership(user_id, channel):
    try:
        member = await app.get_chat_member(channel, user_id)
        return member.status not in [ChatMemberStatus.LEFT, ChatMemberStatus.BANNED]
    except:
        return False

async def get_unjoined_channels(user_id):
    config = get_config()
    channels = config.get("force_join_channels", [])
    unjoined = []
    for channel in channels:
        if not await check_channel_membership(user_id, channel):
            unjoined.append(channel)
    return unjoined

async def send_force_join_prompt(message):
    config = get_config()
    channels = config.get("force_join_channels", [])
    if not channels:
        return True
    unjoined = await get_unjoined_channels(message.from_user.id)
    if not unjoined:
        return True
    buttons = []
    for ch in unjoined:
        ch_clean = ch.replace("@", "")
        buttons.append([InlineKeyboardButton(f"📢 Join {ch}", url=f"https://t.me/{ch_clean}")])
    buttons.append([InlineKeyboardButton("🔄 Try Again", callback_data="check_join")])
    channels_list = "\n".join([f"• {ch}" for ch in unjoined])
    await message.reply_text(
        f"⚠️ **ACCESS RESTRICTED**\n\nJoin these channels first:\n\n{channels_list}\n\nThen click 'Try Again'",
        reply_markup=InlineKeyboardMarkup(buttons)
    )
    return False

# ============================================================
# ADMIN NOTIFICATIONS
# ============================================================
async def notify_admin_new_user(user_id, user_data, referred_by=None):
    try:
        ref_info = ""
        if referred_by:
            ref_user = get_user(referred_by)
            ref_info = f"\n👤 Referred By: @{ref_user.get('username', 'N/A')}"
        text = (
            f"🆕 **NEW USER**\n\n"
            f"👤 {user_data.get('first_name', 'N/A')}\n"
            f"📛 @{user_data.get('username', 'N/A')}\n"
            f"🆔 `{user_id}`\n"
            f"📅 {user_data.get('join_date', 'N/A')[:10]}"
            f"{ref_info}\n"
            f"📊 Total: {len(get_all_users())}"
        )
        await app.send_message(ADMIN_USER_ID, text)
    except:
        pass

async def notify_admin_referral_complete(user_id, user_data, tier):
    if tier == "tier1":
        reward = "+57/+880/+91 ALT"
        refs = "20"
        cmd = f"/completetier1 {user_id}"
    else:
        reward = "+1/+7/+91 (2019 Old)"
        refs = "30"
        cmd = f"/completetier2 {user_id}"
    try:
        text = (
            f"🔔 **TARGET ACHIEVED**\n\n"
            f"🏆 {tier.upper()} - {refs} Refs\n"
            f"👤 @{user_data.get('username', 'N/A')}\n"
            f"🆔 `{user_id}`\n"
            f"👥 Refs: {user_data['referral_count']}\n"
            f"🎁 {reward}\n\n"
            f"Use: `{cmd}`"
        )
        await app.send_message(ADMIN_USER_ID, text)
    except:
        pass

# ============================================================
# MENU FUNCTIONS
# ============================================================
def get_main_menu_text(user_data, first_name):
    count = user_data["referral_count"]
    
    if user_data.get("tier1_claimed"):
        t1 = "✅ Received"
    elif user_data.get("tier1_complete_notified"):
        t1 = "🟡 Processing"
    elif count >= 20:
        t1 = "🟢 Available"
    else:
        t1 = f"🔒 {count}/20"
    
    if user_data.get("tier2_claimed"):
        t2 = "✅ Received"
    elif user_data.get("tier2_complete_notified"):
        t2 = "🟡 Processing"
    elif count >= 30:
        t2 = "🟢 Available"
    else:
        t2 = f"🔒 {count}/30"
    
    text = (
        "╔═══════════════════════╗\n"
        "   🎁 FREE ALT HUB 🎁\n"
        "╚═══════════════════════╝\n\n"
        f"👋 Welcome, {first_name}!\n\n"
        "🔥 **REWARD TIERS:**\n\n"
        "🥉 **20 Referrals:**\n"
        "└ +57/+880/+91 ALT\n\n"
        "🥇 **30 Referrals:**\n"
        "└ +1/+7/+91 (2019 Old)\n\n"
        "📊 **YOUR PROGRESS:**\n"
        f"👥 Referrals: {count}\n"
        f"🥉 Tier 1: {t1}\n"
        f"🥇 Tier 2: {t2}\n\n"
        f"⚠️ After ALT, DM {MRFLXX_USERNAME}\n\n"
        "👇 **SELECT AN OPTION:**"
    )
    return text

def get_main_menu_buttons():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🔗 Referral Link", callback_data="menu_ref"),
            InlineKeyboardButton("📊 Statistics", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton("ℹ️ Help", callback_data="menu_help"),
            InlineKeyboardButton(f"📩 DM {MRFLXX_USERNAME}", url=f"https://t.me/{MRFLXX_USERNAME.replace('@', '')}")
        ]
    ])

# ============================================================
# START COMMAND
# ============================================================
@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    user = get_user(user_id)
    user["username"] = message.from_user.username or "N/A"
    user["first_name"] = message.from_user.first_name or "N/A"
    
    is_new = (user.get("referral_count", 0) == 0 and user.get("referred_by") is None)
    
    # Handle referral
    if len(message.command) > 1 and message.command[1].startswith("ref"):
        try:
            ref_id = int(message.command[1].replace("ref", ""))
            if ref_id != user_id and user.get("referred_by") is None:
                all_users = get_all_users()
                exists = False
                for uid, data in all_users.items():
                    if data.get("referred_by") == ref_id and uid == str(user_id):
                        exists = True
                        break
                
                if not exists:
                    ref_user = get_user(ref_id)
                    user["referred_by"] = ref_id
                    ref_user["referral_count"] += 1
                    update_user(user_id, user)
                    update_user(ref_id, ref_user)
                    
                    # Notify referrer
                    try:
                        await client.send_message(
                            ref_id,
                            f"🎉 **New Referral!**\n\n"
                            f"👤 @{message.from_user.username or 'N/A'}\n"
                            f"📊 Your Refs: {ref_user['referral_count']}/20 | {ref_user['referral_count']}/30"
                        )
                    except:
                        pass
                    
                    # Check Tier 1
                    if ref_user["referral_count"] >= 20 and not ref_user["tier1_complete_notified"]:
                        ref_user["tier1_complete_notified"] = True
                        update_user(ref_id, ref_user)
                        await notify_admin_referral_complete(ref_id, ref_user, "tier1")
                        try:
                            await client.send_message(
                                ref_id,
                                f"🏆 **20 REFERRALS COMPLETE!**\n\n"
                                f"Admin notified. You'll get ALT soon.\n"
                                f"⚠️ After ALT, DM {MRFLXX_USERNAME}"
                            )
                        except:
                            pass
                    
                    # Check Tier 2
                    if ref_user["referral_count"] >= 30 and not ref_user["tier2_complete_notified"]:
                        ref_user["tier2_complete_notified"] = True
                        update_user(ref_id, ref_user)
                        await notify_admin_referral_complete(ref_id, ref_user, "tier2")
                        try:
                            await client.send_message(
                                ref_id,
                                f"💎 **30 REFERRALS COMPLETE!**\n\n"
                                f"Admin notified. You'll get 2019 Old ALT soon.\n"
                                f"⚠️ After ALT, DM {MRFLXX_USERNAME}"
                            )
                        except:
                            pass
        except:
            pass
    
    update_user(user_id, user)
    
    # Force Join Check
    config = get_config()
    if config.get("force_join_enabled") and config.get("force_join_channels"):
        joined = await send_force_join_prompt(message)
        if not joined:
            return
    
    # Notify admin
    if is_new:
        await notify_admin_new_user(user_id, user, user.get("referred_by"))
    
    # Send menu
    text = get_main_menu_text(user, message.from_user.first_name)
    buttons = get_main_menu_buttons()
    await message.reply_text(text, reply_markup=buttons)

# ============================================================
# REFER COMMAND
# ============================================================
@app.on_message(filters.command("refer"))
async def refer_command(client, message):
    user_id = message.from_user.id
    config = get_config()
    if config.get("force_join_enabled") and config.get("force_join_channels"):
        joined = await send_force_join_prompt(message)
        if not joined:
            return
    
    user = get_user(user_id)
    ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
    
    text = (
        "🔗 **YOUR REFERRAL LINK**\n\n"
        f"`{ref_link}`\n\n"
        f"📊 Total Referrals: {user['referral_count']}\n\n"
        "📤 Share with friends!\n\n"
        "🎯 **Rewards:**\n"
        "• 20 Refs = ALT (+57/+880/+91)\n"
        "• 30 Refs = 2019 Old (+1/+7/+91)\n\n"
        f"⚠️ After ALT, DM {MRFLXX_USERNAME}"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Join%20Free%20Alt%20Hub!")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ])
    
    await message.reply_text(text, reply_markup=buttons)

# ============================================================
# STATS COMMAND
# ============================================================
@app.on_message(filters.command(["stats", "info"]))
async def stats_command(client, message):
    user_id = message.from_user.id
    config = get_config()
    if config.get("force_join_enabled") and config.get("force_join_channels"):
        joined = await send_force_join_prompt(message)
        if not joined:
            return
    
    user = get_user(user_id)
    count = user["referral_count"]
    
    bar20 = "▓" * (min(count, 20) // 2) + "░" * (10 - min(count, 20) // 2)
    bar30 = "▓" * (min(count, 30) // 3) + "░" * (10 - min(count, 30) // 3)
    
    if user.get("tier1_claimed"):
        t1 = "✅ Received"
    elif user.get("tier1_complete_notified"):
        t1 = "🟡 Pending"
    elif count >= 20:
        t1 = "🟢 Ready"
    else:
        t1 = "🔒 Progress"
    
    if user.get("tier2_claimed"):
        t2 = "✅ Received"
    elif user.get("tier2_complete_notified"):
        t2 = "🟡 Pending"
    elif count >= 30:
        t2 = "🟢 Ready"
    else:
        t2 = "🔒 Progress"
    
    text = (
        "📊 **YOUR STATISTICS**\n\n"
        f"👤 {message.from_user.first_name}\n"
        f"📛 @{message.from_user.username or 'N/A'}\n"
        f"🆔 `{user_id}`\n"
        f"👥 Referrals: {count}\n\n"
        f"🥉 **TIER 1:** {bar20} {count}/20\n"
        f"Status: {t1}\n\n"
        f"🥇 **TIER 2:** {bar30} {count}/30\n"
        f"Status: {t2}\n\n"
        f"📌 DM {MRFLXX_USERNAME} after ALT"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Get Referral Link", callback_data="menu_ref")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ])
    
    await message.reply_text(text, reply_markup=buttons)

# ============================================================
# HELP COMMAND
# ============================================================
@app.on_message(filters.command("help"))
async def help_command(client, message):
    text = (
        "ℹ️ **HELP & GUIDE**\n\n"
        "📌 **How to Earn:**\n"
        "1. Join required channels\n"
        "2. /refer - Get your link\n"
        "3. Share with friends\n"
        "4. Earn ALT accounts!\n\n"
        "🎁 **Rewards:**\n"
        "🥉 20 Refs = ALT (+57/+880/+91)\n"
        "🥇 30 Refs = 2019 Old (+1/+7/+91)\n\n"
        "📋 **Commands:**\n"
        "/start, /refer, /stats, /help\n\n"
        f"📩 After ALT, DM {MRFLXX_USERNAME}"
    )
    
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"📩 DM {MRFLXX_USERNAME}", url=f"https://t.me/{MRFLXX_USERNAME.replace('@', '')}")],
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
    ])
    
    await message.reply_text(text, reply_markup=buttons)

# ============================================================
# CALLBACK HANDLER
# ============================================================
@app.on_callback_query()
async def callback_handler(client, callback):
    user_id = callback.from_user.id
    data = callback.data
    
    await callback.answer()
    
    if data == "check_join":
        config = get_config()
        if config.get("force_join_enabled"):
            unjoined = await get_unjoined_channels(user_id)
            if not unjoined:
                await callback.message.edit_text("✅ **Verified! Welcome!**")
                await asyncio.sleep(1)
                user = get_user(user_id)
                text = get_main_menu_text(user, callback.from_user.first_name)
                buttons = get_main_menu_buttons()
                await callback.message.edit_text(text, reply_markup=buttons)
            else:
                remaining = ", ".join(unjoined)
                await callback.answer(f"❌ Still need: {remaining}", show_alert=True)
        else:
            user = get_user(user_id)
            text = get_main_menu_text(user, callback.from_user.first_name)
            buttons = get_main_menu_buttons()
            await callback.message.edit_text(text, reply_markup=buttons)
        return
    
    elif data == "back_menu":
        user = get_user(user_id)
        text = get_main_menu_text(user, callback.from_user.first_name)
        buttons = get_main_menu_buttons()
        await callback.message.edit_text(text, reply_markup=buttons)
        return
    
    elif data == "menu_ref":
        user = get_user(user_id)
        ref_link = f"https://t.me/{BOT_USERNAME}?start=ref{user_id}"
        
        text = (
            "🔗 **YOUR REFERRAL LINK**\n\n"
            f"`{ref_link}`\n\n"
            f"📊 Referrals: {user['referral_count']}\n\n"
            f"⚠️ After ALT, DM {MRFLXX_USERNAME}"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("📤 Share Link", url=f"https://t.me/share/url?url={ref_link}&text=Earn%20free%20ALT!")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=buttons)
        return
    
    elif data == "menu_stats":
        user = get_user(user_id)
        count = user["referral_count"]
        
        bar20 = "▓" * (min(count, 20) // 2) + "░" * (10 - min(count, 20) // 2)
        bar30 = "▓" * (min(count, 30) // 3) + "░" * (10 - min(count, 30) // 3)
        
        if user.get("tier1_claimed"):
            t1 = "✅ Received"
        elif user.get("tier1_complete_notified"):
            t1 = "🟡 Pending"
        elif count >= 20:
            t1 = "🟢 Ready"
        else:
            t1 = "🔒 Progress"
        
        if user.get("tier2_claimed"):
            t2 = "✅ Received"
        elif user.get("tier2_complete_notified"):
            t2 = "🟡 Pending"
        elif count >= 30:
            t2 = "🟢 Ready"
        else:
            t2 = "🔒 Progress"
        
        text = (
            "📊 **YOUR STATISTICS**\n\n"
            f"👤 {callback.from_user.first_name}\n"
            f"👥 Referrals: {count}\n\n"
            f"🥉 **Tier 1:** {bar20} {count}/20\n"
            f"Status: {t1}\n\n"
            f"🥇 **Tier 2:** {bar30} {count}/30\n"
            f"Status: {t2}\n\n"
            f"📌 DM {MRFLXX_USERNAME} after ALT"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Referral Link", callback_data="menu_ref")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=buttons)
        return
    
    elif data == "menu_help":
        text = (
            "ℹ️ **HELP & GUIDE**\n\n"
            "📌 **How to Earn:**\n"
            "1. Join required channels\n"
            "2. /refer - Get your link\n"
            "3. Share with friends\n"
            "4. Earn ALT accounts!\n\n"
            "🎁 **Rewards:**\n"
            "🥉 20 Refs = ALT (+57/+880/+91)\n"
            "🥇 30 Refs = 2019 Old (+1/+7/+91)\n\n"
            "📋 **Commands:**\n"
            "/start, /refer, /stats, /help\n\n"
            f"📩 After ALT, DM {MRFLXX_USERNAME}"
        )
        
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"📩 DM {MRFLXX_USERNAME}", url=f"https://t.me/{MRFLXX_USERNAME.replace('@', '')}")],
            [InlineKeyboardButton("🔙 Back to Menu", callback_data="back_menu")]
        ])
        
        await callback.message.edit_text(text, reply_markup=buttons)
        return

# ============================================================
# ADMIN COMMANDS
# ============================================================

@app.on_message(filters.command("addchannel") & filters.user(ADMIN_USER_ID))
async def add_channel(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/addchannel @channel`")
        return
    channel = message.command[1]
    if not channel.startswith("@"):
        channel = "@" + channel
    config = get_config()
    if channel in config.get("force_join_channels", []):
        await message.reply(f"⚠️ Already added.")
        return
    config["force_join_channels"].append(channel)
    save_config(config)
    await message.reply(f"✅ {channel} added!")

@app.on_message(filters.command("removechannel") & filters.user(ADMIN_USER_ID))
async def remove_channel(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/removechannel @channel`")
        return
    channel = message.command[1]
    if not channel.startswith("@"):
        channel = "@" + channel
    config = get_config()
    if channel not in config.get("force_join_channels", []):
        await message.reply(f"⚠️ Not found.")
        return
    config["force_join_channels"].remove(channel)
    save_config(config)
    await message.reply(f"✅ {channel} removed!")

@app.on_message(filters.command("channels") & filters.user(ADMIN_USER_ID))
async def list_channels(client, message):
    config = get_config()
    channels = config.get("force_join_channels", [])
    status = "🟢 ON" if config.get("force_join_enabled") else "🔴 OFF"
    if not channels:
        await message.reply(f"📋 No channels.\nStatus: {status}")
        return
    ch_list = "\n".join([f"• {ch}" for ch in channels])
    await message.reply(f"📋 **CHANNELS**\nStatus: {status}\n\n{ch_list}")

@app.on_message(filters.command("forcejoin") & filters.user(ADMIN_USER_ID))
async def toggle_force_join(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/forcejoin on` or `/forcejoin off`")
        return
    option = message.command[1].lower()
    config = get_config()
    if option == "on":
        if not config.get("force_join_channels"):
            await message.reply("⚠️ Add channel first!")
            return
        config["force_join_enabled"] = True
        save_config(config)
        await message.reply("✅ Force Join ON!")
    elif option == "off":
        config["force_join_enabled"] = False
        save_config(config)
        await message.reply("🔴 Force Join OFF!")
    else:
        await message.reply("❌ Use `on` or `off`")

@app.on_message(filters.command("completetier1") & filters.user(ADMIN_USER_ID))
async def complete_tier1(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/completetier1 user_id`")
        return
    uid = str(message.command[1])
    users = get_all_users()
    if uid not in users:
        await message.reply("❌ User not found.")
        return
    users[uid]["tier1_claimed"] = True
    save_db(users, USERS_DB)
    try:
        await client.send_message(int(uid), f"🎉 **TIER 1 ALT SENT!**\n\nDM {MRFLXX_USERNAME} to confirm.")
    except:
        pass
    await message.reply(f"✅ Tier 1 done for {uid}")

@app.on_message(filters.command("completetier2") & filters.user(ADMIN_USER_ID))
async def complete_tier2(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/completetier2 user_id`")
        return
    uid = str(message.command[1])
    users = get_all_users()
    if uid not in users:
        await message.reply("❌ User not found.")
        return
    users[uid]["tier2_claimed"] = True
    save_db(users, USERS_DB)
    try:
        await client.send_message(int(uid), f"💎 **TIER 2 ALT SENT!**\n\nDM {MRFLXX_USERNAME} to confirm.")
    except:
        pass
    await message.reply(f"✅ Tier 2 done for {uid}")

@app.on_message(filters.command("pending") & filters.user(ADMIN_USER_ID))
async def pending_rewards(client, message):
    users = get_all_users()
    t1, t2 = [], []
    for uid, data in users.items():
        if data.get("tier1_complete_notified") and not data.get("tier1_claimed"):
            t1.append(f"• `{uid}` @{data.get('username', 'N/A')}")
        if data.get("tier2_complete_notified") and not data.get("tier2_claimed"):
            t2.append(f"• `{uid}` @{data.get('username', 'N/A')}")
    text = "📋 **PENDING**\n\n"
    text += f"🥉 Tier 1: {len(t1)}\n" + ("\n".join(t1) if t1 else "None")
    text += f"\n\n🥇 Tier 2: {len(t2)}\n" + ("\n".join(t2) if t2 else "None")
    await message.reply_text(text)

@app.on_message(filters.command("lookup") & filters.user(ADMIN_USER_ID))
async def lookup_user(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/lookup user_id`")
        return
    uid = str(message.command[1])
    user = get_user(int(uid))
    text = (
        f"🔍 **USER**\n\n"
        f"🆔 `{uid}`\n"
        f"👤 @{user.get('username', 'N/A')}\n"
        f"📛 {user.get('first_name', 'N/A')}\n"
        f"👥 Refs: {user.get('referral_count', 0)}\n"
        f"🥉 T1: {'✅' if user.get('tier1_claimed') else '🟡' if user.get('tier1_complete_notified') else '❌'}\n"
        f"🥇 T2: {'✅' if user.get('tier2_claimed') else '🟡' if user.get('tier2_complete_notified') else '❌'}"
    )
    await message.reply_text(text)

@app.on_message(filters.command("broadcast") & filters.user(ADMIN_USER_ID))
async def broadcast_message(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/broadcast message`")
        return
    msg = " ".join(message.command[1:])
    users = get_all_users()
    s, f = 0, 0
    status = await message.reply("📤 Sending...")
    for uid in users:
        try:
            await client.send_message(int(uid), f"📢 **ANNOUNCEMENT**\n\n{msg}")
            s += 1
            await asyncio.sleep(0.3)
        except:
            f += 1
    await status.edit(f"✅ Done! Sent: {s}, Failed: {f}")

@app.on_message(filters.command("statsbot") & filters.user(ADMIN_USER_ID))
async def bot_stats(client, message):
    users = get_all_users()
    config = get_config()
    text = (
        f"📊 **BOT STATS**\n\n"
        f"👥 Users: {len(users)}\n"
        f"🔗 Refs: {sum(u.get('referral_count', 0) for u in users.values())}\n"
        f"🚫 Banned: {sum(1 for u in users.values() if u.get('banned'))}\n"
        f"🥉 T1: {sum(1 for u in users.values() if u.get('tier1_complete_notified'))} notified / {sum(1 for u in users.values() if u.get('tier1_claimed'))} claimed\n"
        f"🥇 T2: {sum(1 for u in users.values() if u.get('tier2_complete_notified'))} notified / {sum(1 for u in users.values() if u.get('tier2_claimed'))} claimed\n"
        f"📢 Force Join: {'ON' if config.get('force_join_enabled') else 'OFF'}"
    )
    await message.reply_text(text)

@app.on_message(filters.command("ban") & filters.user(ADMIN_USER_ID))
async def ban_user(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/ban user_id`")
        return
    uid = str(message.command[1])
    user = get_user(int(uid))
    user["banned"] = True
    update_user(int(uid), user)
    await message.reply(f"🚫 Banned `{uid}`")

@app.on_message(filters.command("unban") & filters.user(ADMIN_USER_ID))
async def unban_user(client, message):
    if len(message.command) < 2:
        await message.reply("❌ `/unban user_id`")
        return
    uid = str(message.command[1])
    user = get_user(int(uid))
    user["banned"] = False
    update_user(int(uid), user)
    await message.reply(f"✅ Unbanned `{uid}`")

# ============================================================
# RUN
# ============================================================
if __name__ == "__main__":
    print("=" * 40)
    print("🤖 Free Alt Hub Bot")
    print(f"👤 Admin: {ADMIN_USER_ID}")
    print(f"🤖 Bot: @{BOT_USERNAME}")
    print("🚀 Starting...")
    print("=" * 40)
    app.run()
