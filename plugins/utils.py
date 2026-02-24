import time
import os
import sys
import asyncio
from telethon import events
import platform
import __main__

from plugins.db_utils import init_db, save_user, get_user_history

client = __main__.client
start_time = time.time()

# Initialize history database
init_db()

def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)
    return ping_time

# Track all incoming messages to catalog user's names for history
@client.on(events.NewMessage(incoming=True))
async def track_names(event):
    if not event.sender_id:
        return
    try:
        user = await event.get_sender()
        if user:
            save_user(
                user.id, 
                getattr(user, 'first_name', None), 
                getattr(user, 'last_name', None), 
                getattr(user, 'username', None)
            )
    except Exception:
        pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.ping$'))
async def ping(event):
    start = time.time()
    msg = await event.reply("`Pinging Server...`")
    end = time.time()
    ms = round((end - start) * 1000, 3)
    uptime = get_readable_time(time.time() - start_time)
    await msg.edit(f"🏓 **Pong!**\n**Latency:** `{ms}ms`\n**Uptime:** `{uptime}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.info(?: |$)(.*)'))
async def user_info(event):
    target = event.pattern_match.group(1)
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target:
        target = event.sender_id

    try:
        user = await client.get_entity(target)
        
        # Save user to DB manually on lookup
        save_user(
            user.id, 
            getattr(user, 'first_name', None), 
            getattr(user, 'last_name', None), 
            getattr(user, 'username', None)
        )
        history = get_user_history(user.id)
        
        # Try fetching previous profile photos to get a sense of history if possible
        photos = await client.get_profile_photos(user)
        photo_count = len(photos) if photos else 0
        
        # Format history string
        history_display = "\n".join([f" • `{name}`" for name in history]) if history else "`No history recorded yet.`"
        
        info = (
            f"👤 **User Information**\n\n"
            f"**First Name:** `{getattr(user, 'first_name', 'None')}`\n"
            f"**Last Name:** `{getattr(user, 'last_name', 'None')}`\n"
            f"**Username:** `{'@' + user.username if getattr(user, 'username', None) else 'None'}`\n"
            f"**ID:** `{user.id}`\n"
            f"**Known History:**\n{history_display}\n\n"
            f"**Profile Photos:** `{photo_count}`\n"
            f"**Is Bot:** `{'Yes' if getattr(user, 'bot', False) else 'No'}`\n"
            f"**Is Scam:** `{'Yes' if getattr(user, 'scam', False) else 'No'}`\n"
            f"**Is Fake:** `{'Yes' if getattr(user, 'fake', False) else 'No'}`\n"
            f"**Is Verified:** `{'Yes' if getattr(user, 'verified', False) else 'No'}`\n"
            f"**Premium User:** `{'Yes' if getattr(user, 'premium', False) else 'No'}`\n"
        )
        await event.reply(info)
    except Exception as e:
        await event.reply(f"❌ **Error fetching info:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.checkbot(?: |$)(.*)'))
async def check_bot(event):
    target = event.pattern_match.group(1)
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target:
        await event.edit("⚠️ **Please provide a username/ID or reply to a user.**")
        return

    try:
        user = await client.get_entity(target)
        if getattr(user, 'bot', False):
            await event.edit(f"🤖 **CONFIRMED:** {user.first_name} (`{user.id}`) is a **BOT**.")
        else:
            await event.edit(f"👤 **CONFIRMED:** {user.first_name} (`{user.id}`) is a **REAL USER**.")
    except Exception as e:
        await event.edit(f"❌ **Error checking entity:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.alive$'))
async def alive(event):
    uptime = get_readable_time(time.time() - start_time)
    python_version = sys.version.split()[0]
    os_name = platform.system()
    app_version = "1.0.0"
    
    alive_msg = (
        f"🟢 **Eren is Online!**\n\n"
        f"**System Status**: All systems operational\n"
        f"**Uptime**: `{uptime}`\n"
        f"**Python**: `{python_version}`\n"
        f"**OS**: `{os_name}`\n"
        f"**Bot Version**: `{app_version}`\n"
    )
    await event.edit(alive_msg)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.help$'))
async def help_menu(event):
    help_text = (
        "🛠️ **Erenxd Command Menu**\n\n"
        "**Core Utilities:**\n"
        "`.ping` - Check latency and bot uptime.\n"
        "`.info [username/id]` - Get details of a user.\n"
        "`.alive` - Check system status.\n"
        "`.help` - Display this menu.\n\n"
        "**Prank / Fun:**\n"
        "`.hack [@username]` - Run a fake hacking simulation.\n\n"
        "**System Settings:**\n"
        "`.deletebot` - Safely destroy session and exit."
    )
    await event.edit(help_text)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.deletebot$'))
async def self_destruct(event):
    await event.edit("⚠️ **WARNING: INITIATING SELF DESTRUCT SEQUENCE** ⚠️")
    await asyncio.sleep(2)
    await event.edit("🚨 **Deleting session data...**")
    
    try:
        if os.path.exists("my_userbot.session"):
            os.remove("my_userbot.session")
    except Exception as e:
        await event.reply(f"Could not delete session manually: `{e}`")
        
    await asyncio.sleep(1)
    await event.edit("💥 **Self Destruct Complete. Bot terminated.**")
    
    # Self Destruct Feature - Exit Process Safely
    await client.disconnect()
    os._exit(0)

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.hi$'))
async def hi_flirt(event):
    if not event.is_reply:
        await event.edit("⚠️ **Please reply to a user's message to flirt with them!**")
        return
        
    reply_msg = await event.get_reply_message()
    if not reply_msg or not reply_msg.sender:
        await event.edit("⚠️ **Could not fetch the user's details.**")
        return
        
    target_name = getattr(reply_msg.sender, 'first_name', '')
    if not target_name:
        target_name = "Beautiful" # Safe fallback if they somehow have no name

    flirts = [
        f"hello {target_name}, Cute 🥺✨",
        f"hello {target_name}, Beautiful 😍🌸",
        f"hello {target_name}, Gorgeous 💖🔥",
        f"hello {target_name}, Pretty 🌷💫",
        f"hello {target_name}, Lovely 💕🌼",
        f"hello {target_name}, Adorable 🧸💗",
        f"hello {target_name}, Charming 😌🌹",
        f"hello {target_name}, Elegant 👑✨",
        f"hello {target_name}, Stunning 😍💎",
        f"hello {target_name}, Sweetheart 🍯❤️",
        f"hello {target_name}, Angelic 😇🤍",
        f"hello {target_name}, Doll 🪆💞",
        f"hello {target_name}, Sunshine ☀️💛",
        f"hello {target_name}, Queen 👑💖",
        f"hello {target_name}, Princess 👸✨",
        f"hello {target_name}, Honey 🍯😘",
        f"hello {target_name}, Darling 💝🥰",
        f"hello {target_name}, Cutiepie 🥺🍰",
        f"hello {target_name}, Mesmerizing 😍🌙"
    ]
    
    # Send the first message, then edit it to create the animation
    msg = await event.edit(flirts[0])
    for flirt in flirts[1:]:
        await asyncio.sleep(0.8) # Adjust speed of animation here
        await msg.edit(flirt)
