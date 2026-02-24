import time
import random
import asyncio
from telethon import events
import __main__

client = __main__.client

# Cooldown dictionary per user
last_hack_time = {}
COOLDOWN = 10  # seconds

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.hack(?: |$)(.*)'))
async def hack_simulation(event):
    user_id = event.sender_id
    current_time = time.time()
    
    # Anti-Abuse: Check cooldown
    if user_id in last_hack_time and current_time - last_hack_time[user_id] < COOLDOWN:
        remaining = int(COOLDOWN - (current_time - last_hack_time[user_id]))
        await event.edit(f"⏳ **Cooldown active.** Please wait {remaining} seconds before hacking again.")
        return
    
    target = event.pattern_match.group(1)
    
    # Enable replying to target directly instead of tagging
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
        
    if not target:
        await event.edit("⚠️ **ERROR**: Reply to a message or provide a username. Example: `.hack` (in reply)")
        return
        
    # Update cooldown time
    last_hack_time[user_id] = current_time
    
    try:
        # Fetch target details
        user = await client.get_entity(target)
        
        # User/Bot detection
        target_type = "🤖 BOT" if user.bot else "👤 REAL USER"
        
        # Last seen status handling
        last_seen = str(type(user.status).__name__).replace("UserStatus", "") if user.status else "Unknown"
        
        await event.edit(
            f"⚠️ **TARGET ANALYSIS COMPLETE** ⚠️\n\n"
            f"**Name**: {user.first_name}\n"
            f"**Target ID**: `{user.id}`\n\n"
            f"🚨 **ENTITY TYPE:** **{target_type}** 🚨"
        )
        await asyncio.sleep(2.5)
        
        # Fake Hacking Sequence with cooler glitching/terminal animation
        if user.bot:
            hacking_texts = [
                "🟢 Initializing BOT API override...",
                "🔴 Bypassing Telegram Bot API restrictions...",
                "⚙️ Bruteforcing bot token... [██████░░░░]",
                "⚙️ Token acquired: 123456:ABC-DEF1234ghIkl-zyx...",
                "🟢 Accessing bot webhook database...",
                "🔴 Injecting malicious /start payload...",
                "🟢 Hijacking active user sessions...",
                "⚠️ COMPROMISING BOT PERMISSIONS... 64% complete",
                "⚠️ COMPROMISING BOT PERMISSIONS... 100% complete",
                "🟢 Disabling bot admin alerts..."
            ]
            fake_assets = (
                f"• **Extracted Token**: `Hidden for security`\n"
                f"• **Active Chats Hijacked**: `{random.randint(50, 5000)}`\n"
                f"• **Webhook Redirected**: `True`\n\n"
            )
        else:
            hacking_texts = [
                "🟢 Initializing attack sequence on USER...",
                "🔴 Firewall bypassed! Accessing Telegram backend...",
                "⚙️ Decrypting AES-256 session lock... [██████░░░░]",
                "⚙️ Session lock decrypted... [██████████]",
                "🟢 Accessing mainframe databases...",
                "🔴 Injecting payload ::::: $ sudo rm -rf /",
                "🟢 Downloading local device directories...",
                "⚠️ EXFILTRATING DATA... 64% complete",
                "⚠️ EXFILTRATING DATA... 100% complete",
                "🟢 Covering tracks... deleting logs..."
            ]
            fake_passwords = random.randint(15, 87)
            fake_crypto_wallet = f"0x{random.randint(1000000000, 9999999999)}...{random.randint(100, 999)}"
            fake_assets = (
                f"• **Saved Passwords**: `{fake_passwords} Found`\n"
                f"• **Crypto Wallet ID**: `{fake_crypto_wallet}`\n"
                f"• **Private Chats Exported**: `True`\n\n"
            )
        
        for text in hacking_texts:
            await event.edit(f"**[HACK_SIMULATION_SYSTEM]**\n\n`{text}`")
            await asyncio.sleep(0.6)  # Delays between steps
        
        final_msg = (
            "✅ **SYSTEM COMPROMISED SUCCESSFULLY**\n\n"
            f"**Target**: {user.first_name} \n"
            f"**ID**: `{user.id}`\n"
            f"**Entity**: {target_type}\n"
            f"**Last Sync**: {last_seen}\n\n"
            "🕵️ **Dumped Assets (SIMULATED)**:\n"
            f"{fake_assets}"
        )
        
        await event.edit(final_msg)
        
    except Exception as e:
        await event.edit(f"❌ **ERROR**: Failed to locate target or network issue.\n`{e}`")
