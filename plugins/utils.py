import time
import os
import sys
import asyncio
import logging
import shutil
from telethon import events
import platform
import __main__

from plugins.db_utils import (
    init_db, save_user, get_user_history,
    add_tracked_user, remove_tracked_user, get_all_tracked_users,
    save_vv_cache, get_vv_cache,
)
from datetime import datetime, timezone
from telethon.tl.functions.contacts import GetContactsRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import (
    UserStatusOnline, 
    UserStatusOffline, 
    UserStatusRecently, 
    UserStatusLastWeek, 
    UserStatusLastMonth
)

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
@client.on(events.NewMessage())
async def debug_all_messages(event):
    print(f"[DEBUG] Received message: {event.raw_text} (outgoing={event.out})")

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

async def _resolve_user_phone(user):
    """Best-effort phone lookup via full user + saved contacts."""
    phone = getattr(user, "phone", None)
    if phone:
        return phone

    try:
        full = await client(GetFullUserRequest(user))
        if full.users:
            phone = getattr(full.users[0], "phone", None)
            if phone:
                return phone
    except Exception:
        pass

    # Contacts often keep the number you saved even when profile phone is hidden
    try:
        contacts = await client(GetContactsRequest(hash=0))
        for contact_user in getattr(contacts, "users", []) or []:
            if contact_user.id == user.id:
                phone = getattr(contact_user, "phone", None)
                if phone:
                    return phone
                break
    except Exception:
        pass

    return None


@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.phoneNo(?: |$)(.*)'))
async def phone_no(event):
    target = event.pattern_match.group(1).strip()

    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target and event.is_private:
        target = event.chat_id
    elif not target:
        await event.edit("⚠️ **Please provide a username/ID or reply to a user.**")
        return

    try:
        user = await client.get_entity(target)
        phone = await _resolve_user_phone(user)
        name = user.first_name or "User"
        username_str = f" (@{user.username})" if user.username else ""

        if phone:
            display = phone if str(phone).startswith("+") else f"+{phone}"
            await event.edit(
                f"📱 **Phone Number**\n\n"
                f"**User:** {name}{username_str}\n"
                f"**Phone:** `{display}`"
            )
        else:
            await event.edit(
                f"📱 **Phone Number**\n\n"
                f"**User:** {name}{username_str}\n"
                f"**Phone:** `Hidden / not available`\n\n"
                f"_Telegram does not send this number to clients when privacy hides it "
                f"and it is not saved in your contacts._"
            )
    except Exception as e:
        await event.edit(f"❌ **Error fetching phone number:** `{e}`")

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
        "`.alive` - Check system status.\n"
        "`.help` - Display this menu.\n"
        "`.info [username/id]` - Get details of a user.\n"
        "`.phoneNo [username/id]` - Get a user's phone number.\n"
        "`.status [username/id]` - Check online/offline status of a user.\n"
        "`.track [username/id]` - Track when a user goes online or offline.\n"
        "`.untrack [username/id]` - Stop tracking a user.\n"
        "`.tracked` - List all currently tracked users.\n"
        "`.gimme [username/id]` - Get profile photo or download replied media.\n"
        "`.vv` - Open a replied view-once photo/video and save it permanently.\n"
        "`.grpvv <link>` - Open a view-once photo from a group/channel message link.\n"
        "`.ss [count]` - Phone-style screenshot of this Telegram chat.\n"
        "`.ai [prompt]` - Ask Groq AI (or reply to a message).\n"
        "`.weather [city]` - Get current weather details for a location.\n"
        "`.searching [query]` - Perform a web search.\n"
        "`.save [text]` - Save a custom note.\n\n"
        "**Media & Spam (Use carefully!):**\n"
        "`.song [song name]` - Search and download a song.\n"
        "`.voice [text]` - Convert text to a female voice note.\n"
        "`.spam [number] [text]` - Sends text multiple times automatically.\n"
        "`.delspam [number] [text]` - Sends text multiple times and deletes it immediately.\n\n"
        "**Authorization:**\n"
        "`.approve [username/id]` - Allow another user to use your bot.\n"
        "`.disapprove [username/id]` - Remove a user's permission.\n\n"
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
        session_path = os.path.expanduser("~/.config/erenbot/my_userbot.session")
        if os.path.exists(session_path):
            os.remove(session_path)
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


# ==================== ONLINE/OFFLINE TRACKER & CHECKER ====================

ACTIVE_TRACKS = {}

def format_relative_time(dt):
    if not dt:
        return "Unknown"
    now = datetime.now(timezone.utc)
    diff = now - dt
    
    seconds = int(diff.total_seconds())
    if seconds < 0:
        return "just now"
    
    if seconds < 60:
        return f"{seconds}s ago"
    
    minutes = seconds // 60
    if minutes < 60:
        return f"{minutes}m ago"
        
    hours = minutes // 60
    if hours < 24:
        return f"{hours}h {minutes % 60}m ago"
        
    days = hours // 24
    if days == 1:
        return "yesterday"
    if days < 7:
        return f"{days} days ago"
        
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")

def get_status_info(status):
    if isinstance(status, UserStatusOnline):
        return "🟢 **Online**", True
    elif isinstance(status, UserStatusOffline):
        last_seen = format_relative_time(status.was_online)
        return f"🔴 **Offline** (last seen {last_seen})", False
    elif isinstance(status, UserStatusRecently):
        return "🟡 **Recently** (last seen recently)", False
    elif isinstance(status, UserStatusLastWeek):
        return "🕒 **Last Week** (last seen within a week)", False
    elif isinstance(status, UserStatusLastMonth):
        return "📅 **Last Month** (last seen within a month)", False
    else:
        return "❓ **Unknown** (status hidden or unavailable)", False

async def status_tracker_loop(client, user_id, chat_id):
    last_online_state = None
    first_run = True
    
    try:
        while True:
            try:
                user = await client.get_entity(user_id)
                status = user.status
                is_online = isinstance(status, UserStatusOnline)
                
                name = user.first_name or "User"
                username_str = f" (@{user.username})" if user.username else ""
                
                if first_run:
                    last_online_state = is_online
                    first_run = False
                elif is_online != last_online_state:
                    last_online_state = is_online
                    if is_online:
                        status_msg = f"🟢 **Tracker Alert:** {name}{username_str} is now **ONLINE**!"
                    else:
                        status_text, _ = get_status_info(status)
                        status_msg = f"🔴 **Tracker Alert:** {name}{username_str} is now **OFFLINE**!\nStatus: {status_text}"
                    
                    await client.send_message(chat_id, status_msg)
            except Exception as e:
                # Silently ignore fetching errors to prevent loop crash
                pass
            await asyncio.sleep(60)
    except asyncio.CancelledError:
        pass

async def init_tracker(client):
    # Wait a bit for client to connect
    await asyncio.sleep(5)
    tracked = get_all_tracked_users()
    for user_id, chat_id in tracked:
        track_key = (user_id, chat_id)
        if track_key not in ACTIVE_TRACKS:
            task = client.loop.create_task(status_tracker_loop(client, user_id, chat_id))
            ACTIVE_TRACKS[track_key] = task

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.(?:status|online)(?: |$)(.*)'))
async def check_user_status(event):
    target = event.pattern_match.group(1).strip()
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target:
        target = "me"
        
    try:
        user = await client.get_entity(target)
        status_text, _ = get_status_info(user.status)
        
        name = user.first_name or "User"
        username_str = f" (@{user.username})" if user.username else ""
        
        response = (
            f"👤 **User:** {name}{username_str}\n"
            f"🆔 **ID:** `{user.id}`\n"
            f"⚡ **Status:** {status_text}"
        )
        await event.edit(response)
    except Exception as e:
        await event.edit(f"❌ **Error getting status:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.track(?: |$)(.*)'))
async def track_user(event):
    target = event.pattern_match.group(1).strip()
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target:
        await event.edit("⚠️ **Please specify a user to track (reply or username/ID).**")
        return
        
    try:
        user = await client.get_entity(target)
        user_id = user.id
        chat_id = event.chat_id
        track_key = (user_id, chat_id)
        
        if track_key in ACTIVE_TRACKS:
            await event.edit(f"⚠️ **Already tracking this user in this chat.**")
            return
            
        # Save to DB
        add_tracked_user(user_id, chat_id)
        
        # Start background task
        task = client.loop.create_task(status_tracker_loop(client, user_id, chat_id))
        ACTIVE_TRACKS[track_key] = task
        
        name = user.first_name or "User"
        username_str = f" (@{user.username})" if user.username else ""
        
        await event.edit(f"✅ **Started tracking:** {name}{username_str}\nI will notify in this chat when they go online or offline.")
    except Exception as e:
        await event.edit(f"❌ **Error starting tracker:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.untrack(?: |$)(.*)'))
async def untrack_user(event):
    target = event.pattern_match.group(1).strip()
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    elif not target:
        await event.edit("⚠️ **Please specify a user to untrack (reply or username/ID).**")
        return
        
    try:
        user = await client.get_entity(target)
        user_id = user.id
        chat_id = event.chat_id
        track_key = (user_id, chat_id)
        
        if track_key not in ACTIVE_TRACKS:
            await event.edit(f"⚠️ **Not tracking this user in this chat.**")
            return
            
        # Remove from DB
        remove_tracked_user(user_id, chat_id)
        
        # Cancel task
        task = ACTIVE_TRACKS.pop(track_key)
        task.cancel()
        
        name = user.first_name or "User"
        username_str = f" (@{user.username})" if user.username else ""
        
        await event.edit(f"🚫 **Stopped tracking:** {name}{username_str}")
    except Exception as e:
        await event.edit(f"❌ **Error stopping tracker:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.tracked$'))
async def list_tracked(event):
    tracked = get_all_tracked_users()
    if not tracked:
        await event.edit("❓ **No users are currently being tracked.**")
        return
        
    response = "📋 **Currently Tracked Users:**\n\n"
    for user_id, chat_id in tracked:
        try:
            user = await client.get_entity(user_id)
            name = user.first_name or "User"
            username_str = f" (@{user.username})" if user.username else ""
            response += f" • {name}{username_str} (ID: `{user_id}`) [Chat: `{chat_id}`]\n"
        except Exception:
            response += f" • User ID: `{user_id}` [Chat: `{chat_id}`]\n"
            
    await event.edit(response)

# Schedule auto-start tracker task on startup
client.loop.create_task(init_tracker(client))

_vv_log = logging.getLogger("UserBot.vv")
VV_DIR = os.path.expanduser("~/.config/erenbot/vv")
os.makedirs(VV_DIR, exist_ok=True)


def _is_view_once(media):
    # ttl_seconds is set on view-once / disappearing media (including large sentinel values)
    return media is not None and getattr(media, "ttl_seconds", None) is not None


def _vv_local_path(chat_id, msg_id):
    for name in os.listdir(VV_DIR) if os.path.isdir(VV_DIR) else []:
        if name.startswith(f"{chat_id}_{msg_id}."):
            return os.path.join(VV_DIR, name)
    return None


async def _download_view_media(message):
    """Try several ways to pull view-once media before Telegram wipes it."""
    if not message:
        return None

    targets = []
    if message.media:
        targets.append(message)
        targets.append(message.media)
    if getattr(message, "photo", None):
        targets.append(message.photo)
    if getattr(message, "document", None):
        targets.append(message.document)

    for target in targets:
        try:
            path = await client.download_media(target, file=os.path.join(VV_DIR, "tmp_"))
            if path and os.path.exists(path) and os.path.getsize(path) > 0:
                return path
        except Exception as e:
            _vv_log.debug("download attempt failed: %s", e)
    return None


async def _save_vv_permanent(chat_id, msg_id, file_path, from_name="Unknown"):
    """Keep a permanent copy on disk + Saved Messages. Returns local path."""
    if not file_path or not os.path.exists(file_path):
        return None

    local = _vv_local_path(chat_id, msg_id)
    if not local:
        ext = os.path.splitext(file_path)[1] or ".bin"
        local = os.path.join(VV_DIR, f"{chat_id}_{msg_id}{ext}")
        if os.path.abspath(file_path) != os.path.abspath(local):
            shutil.copy2(file_path, local)

    if not get_vv_cache(chat_id, msg_id):
        try:
            saved = await client.send_file(
                "me",
                local,
                caption=(
                    f"💾 **Saved view-once**\n"
                    f"**From:** {from_name}\n"
                    f"**Chat:** `{chat_id}`\n"
                    f"**Msg:** `{msg_id}`"
                ),
                force_document=False,
            )
            save_vv_cache(chat_id, msg_id, saved.id)
        except Exception as e:
            _vv_log.warning("Saved Messages copy failed (disk ok): %s", e)

    return local


async def _cache_view_once(event):
    """Download view-once media as soon as it arrives (so it survives after open)."""
    if not event.media or not _is_view_once(event.media):
        return False

    chat_id, msg_id = event.chat_id, event.id
    if _vv_local_path(chat_id, msg_id) and get_vv_cache(chat_id, msg_id):
        return True

    file_path = None
    try:
        file_path = await _download_view_media(event)
        if not file_path:
            _vv_log.warning("Failed to auto-save view-once %s:%s", chat_id, msg_id)
            return False

        sender = await event.get_sender()
        name = getattr(sender, "first_name", None) or "Unknown"
        await _save_vv_permanent(chat_id, msg_id, file_path, name)
        _vv_log.info("Cached view-once %s:%s", chat_id, msg_id)
        return True
    except Exception as e:
        _vv_log.warning("auto-save error: %s", e)
        return False
    finally:
        # permanent copy is under VV_DIR; remove temp download if different
        if file_path and os.path.exists(file_path) and not os.path.basename(file_path).startswith(f"{chat_id}_{msg_id}"):
            try:
                os.remove(file_path)
            except Exception:
                pass


@client.on(events.NewMessage(incoming=True))
async def auto_save_view_once(event):
    """Save view-once on arrival — before you open it in Telegram."""
    if _is_view_once(event.media):
        await _cache_view_once(event)


@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.vv$'))
async def view_once(event):
    """Open view-once media and always save a permanent copy."""
    if not event.is_reply:
        await event.edit(
            "⚠️ **Reply to a view-once photo/video with** `.vv`\n\n"
            "_This opens it and saves a copy to Saved Messages._"
        )
        return

    reply = await event.get_reply_message()
    if not reply:
        await event.edit("❌ **No replied message found.**")
        return

    await event.edit("🔓 **Opening & saving...**")
    chat_id, msg_id = reply.chat_id, reply.id
    temp_path = None

    try:
        sender = await reply.get_sender()
        from_name = getattr(sender, "first_name", None) or "Unknown"
        send_path = None

        # 1) Already saved on disk
        local = _vv_local_path(chat_id, msg_id)
        if local and os.path.exists(local):
            send_path = await _save_vv_permanent(chat_id, msg_id, local, from_name)

        # 2) Already in Saved Messages
        if not send_path:
            cached_id = get_vv_cache(chat_id, msg_id)
            if cached_id:
                saved_msg = await client.get_messages("me", ids=cached_id)
                if saved_msg and saved_msg.media:
                    # re-download to disk for local cache, then show
                    temp_path = await client.download_media(
                        saved_msg, file=os.path.join(VV_DIR, "tmp_")
                    )
                    if temp_path:
                        send_path = await _save_vv_permanent(
                            chat_id, msg_id, temp_path, from_name
                        )

        # 3) Still on Telegram (not opened in app yet) — open + save now
        if not send_path and reply.media:
            temp_path = await _download_view_media(reply)
            if temp_path:
                send_path = await _save_vv_permanent(
                    chat_id, msg_id, temp_path, from_name
                )

        if send_path and os.path.exists(send_path):
            await client.send_file(
                event.chat_id,
                send_path,
                caption="🔓 **Opened & saved** → check **Saved Messages**",
                reply_to=reply.id,
                force_document=False,
            )
            await event.delete()
            return

        await event.edit(
            "❌ **Can't open/save this one.**\n\n"
            "You already opened it in Telegram, so the server deleted it, "
            "and the bot had no saved copy.\n\n"
            "**Next time:**\n"
            "1. Keep bot running (`python3 bot.py`)\n"
            "2. **Don't tap open** in Telegram\n"
            "3. Reply with `.vv` → it opens **and** saves forever"
        )
    except Exception as e:
        await event.edit(f"❌ **Failed:** `{e}`")
    finally:
        if temp_path and os.path.exists(temp_path):
            # only remove temps, not permanent cache files
            base = os.path.basename(temp_path)
            if base.startswith("tmp_") or not base.startswith(f"{chat_id}_{msg_id}"):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass


@client.on(events.NewMessage(outgoing=True, pattern=r'^\.gimme(?: |$)(.*)'))
async def gimme_media_or_pfp(event):
    target = event.pattern_match.group(1).strip()
    
    # Check if replying to a message
    reply_msg = None
    if event.is_reply:
        reply_msg = await event.get_reply_message()
        
    # Case 1: Replying to a message with media -> Download and send that media
    if reply_msg and reply_msg.media:
        await event.edit("📥 **Downloading media...**")
        try:
            file_path = await client.download_media(reply_msg)
            if file_path:
                await event.client.send_file(
                    event.chat_id,
                    file_path,
                    caption="Here is your media! 📂",
                    reply_to=reply_msg.id
                )
                await event.delete()
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                await event.edit("❌ **Failed to download media.**")
        except Exception as e:
            await event.edit(f"❌ **Error downloading media:** `{e}`")
        return

    # Case 2: No replied media -> get profile photo of target (or replied user, or self)
    if not target and reply_msg:
        target = reply_msg.sender_id
    elif not target:
        target = "me"
        
    await event.edit("📥 **Fetching profile photo...**")
    try:
        user = await client.get_entity(target)
        photo_path = await client.download_profile_photo(user)
        if photo_path:
            name = user.first_name or "User"
            await event.client.send_file(
                event.chat_id,
                photo_path,
                caption=f"👤 Profile photo of **{name}**",
                reply_to=event.id
            )
            await event.delete()
            if os.path.exists(photo_path):
                os.remove(photo_path)
        else:
            await event.edit("❌ **User has no profile photo.**")
    except Exception as e:
        await event.edit(f"❌ **Error fetching profile photo:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.list(?: |$)(.*)'))
async def list_anim(event):
    text = event.pattern_match.group(1).strip()
    if not text:
        await event.edit("⚠️ **Usage:** `.list item1, item2, item3`")
        return
        
    # Split by comma and clean up spaces
    items = [item.strip() for item in text.split(',') if item.strip()]
    
    if not items:
        await event.edit("⚠️ **No valid items found. Use commas to separate.**")
        return
        
    try:
        msg = await event.edit(items[0])
        for item in items[1:]:
            await asyncio.sleep(1.0) # 1 second delay between edits
            await msg.edit(item)
    except Exception as e:
        pass

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.(?:tr|translate|tranlation)(?: |$)(.*)'))
async def translate_cmd(event):
    input_str = event.pattern_match.group(1).strip()
    
    if event.is_reply and not input_str:
        # Default target language to english if no language specified and it's a reply
        target_lang = "en"
        reply_msg = await event.get_reply_message()
        text_to_translate = reply_msg.text
    elif event.is_reply and input_str:
        # Target language specified, text is from reply
        target_lang = input_str.split()[0]
        reply_msg = await event.get_reply_message()
        text_to_translate = reply_msg.text
    else:
        # Target language and text both in command
        if not input_str or len(input_str.split()) < 2:
            await event.edit("⚠️ **Usage:** `.tr <lang_code> <text>` or reply to a message with `.tr <lang_code>`\n*(Example: `.tr hi hello`)*")
            return
        target_lang = input_str.split()[0]
        text_to_translate = input_str[len(target_lang):].strip()
        
    if not text_to_translate:
        await event.edit("⚠️ **No text found to translate.**")
        return
        
    try:
        def fetch_translation():
            import urllib.request, json, urllib.parse
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode('utf-8'))
                # Handle potentially multiple sentences
                translated = "".join([sentence[0] for sentence in data[0] if sentence[0]])
                source_lang = data[2]
                return translated, source_lang

        await event.edit("🔄 **Translating...**")
        translated_text, source_lang = await asyncio.to_thread(fetch_translation)
        
        output = (
            f"🌍 **Translation**\n"
            f"**From:** `{source_lang}` ➔ **To:** `{target_lang}`\n\n"
            f"`{translated_text}`"
        )
        await event.edit(output)
    except Exception as e:
        await event.edit(f"❌ **Error during translation:** `{str(e)}`")


# ─── .grpvv — Open view-once from a group/channel message link ───────────────
import re as _re

_GRPVV_PUBLIC  = _re.compile(r"https?://t\.me/([^/]+)/(\d+)")
_GRPVV_PRIVATE = _re.compile(r"https?://t\.me/c/(\d+)/(\d+)")


@client.on(events.NewMessage(outgoing=True, pattern=_re.compile(r'^[.]grpvv(?: |$)(.*)', _re.IGNORECASE | _re.DOTALL)))
async def grpvv_cmd(event):

    """
    .grpvv <telegram_message_link>

    Fetches the view-once photo/video from any group or channel message link
    and saves it permanently — just like .vv but for remote links.

    Supported formats:
      https://t.me/channelname/123
      https://t.me/c/1234567890/123
    """
    link = (event.pattern_match.group(1) or "").strip()

    if not link:
        await event.edit(
            "⚠️ **Usage:** `.grpvv <telegram_message_link>`\n\n"
            "**Supported formats:**\n"
            "• `https://t.me/channelname/123`\n"
            "• `https://t.me/c/1234567890/123`\n\n"
            "_Bot must be a member of the group/channel._"
        )
        return

    await event.edit("🔍 **Fetching message...**")

    try:
        # Parse public link: t.me/username/msg_id
        m_pub = _GRPVV_PUBLIC.search(link)
        # Parse private link: t.me/c/chat_id/msg_id
        m_prv = _GRPVV_PRIVATE.search(link)

        if m_prv:
            raw_chat_id = int(m_prv.group(1))
            msg_id      = int(m_prv.group(2))
            # Telethon needs the full negative ID for supergroups/channels
            chat_entity = int(f"-100{raw_chat_id}")
        elif m_pub:
            username = m_pub.group(1)
            msg_id   = int(m_pub.group(2))
            chat_entity = username
        else:
            await event.edit(
                "❌ **Invalid link format.**\n\n"
                "Use: `https://t.me/channelname/123` or `https://t.me/c/1234567890/123`"
            )
            return

        # Fetch the message
        target_msg = await client.get_messages(chat_entity, ids=msg_id)

        if not target_msg:
            await event.edit("❌ **Message not found.** Make sure the bot is in that group/channel.")
            return

        # Check if it has any media
        if not target_msg.media:
            await event.edit(
                "⚠️ **This message has no media.**\n\n"
                f"Message text: `{(target_msg.message or '')[:200]}`"
            )
            return

        is_vv = _is_view_once(target_msg.media)

        await event.edit(
            f"{'🔒 **View-once detected!** Opening & saving...' if is_vv else '📥 **Downloading media...**'}"
        )

        chat_id = target_msg.chat_id
        temp_path = None

        try:
            sender = await target_msg.get_sender()
            from_name = (
                getattr(sender, "first_name", None)
                or getattr(sender, "title", None)
                or "Unknown"
            )

            send_path = None

            # 1) Already cached on disk (for view-once)
            if is_vv:
                local = _vv_local_path(chat_id, msg_id)
                if local and os.path.exists(local):
                    send_path = await _save_vv_permanent(chat_id, msg_id, local, from_name)

                # 2) Check Saved Messages cache
                if not send_path:
                    cached_id = get_vv_cache(chat_id, msg_id)
                    if cached_id:
                        saved_msg = await client.get_messages("me", ids=cached_id)
                        if saved_msg and saved_msg.media:
                            temp_path = await client.download_media(
                                saved_msg, file=os.path.join(VV_DIR, "tmp_")
                            )
                            if temp_path:
                                send_path = await _save_vv_permanent(
                                    chat_id, msg_id, temp_path, from_name
                                )

            # 3) Download directly from Telegram
            dl_error = None
            if not send_path:
                try:
                    if is_vv:
                        temp_path = await _download_view_media(target_msg)
                    else:
                        temp_path = await client.download_media(
                            target_msg, file=os.path.join(VV_DIR, "tmp_")
                        )
                except Exception as dl_ex:
                    dl_error = str(dl_ex)
                    temp_path = None

                if temp_path:
                    if is_vv:
                        send_path = await _save_vv_permanent(chat_id, msg_id, temp_path, from_name)
                    else:
                        send_path = temp_path

            if send_path and os.path.exists(send_path):
                caption = (
                    f"🔓 **Opened & saved** (view-once) → check **Saved Messages**\n"
                    f"📌 From: **{from_name}**"
                    if is_vv else
                    f"📥 **Media from group link**\n📌 From: **{from_name}**"
                )
                await client.send_file(
                    event.chat_id,
                    send_path,
                    caption=caption,
                    force_document=False,
                )
                await event.delete()
                return

            # Show real reason for failure
            if dl_error:
                await event.edit(
                    f"❌ **Download failed.**\n\n"
                    f"**Error:** `{dl_error}`\n\n"
                    f"**Is VV:** `{is_vv}` | **Chat:** `{chat_id}` | **Msg:** `{msg_id}`"
                )
            else:
                await event.edit(
                    "❌ **Could not download the media.**\n\n"
                    f"**Is VV:** `{is_vv}` | **Chat:** `{chat_id}` | **Msg:** `{msg_id}`\n\n"
                    "• If view-once: don't open in Telegram first\n"
                    "• Make sure bot is member of that group/channel"
                )

        except Exception as e:
            await event.edit(f"❌ **Failed to process media:** `{e}`")
        finally:
            # Clean up temp files (not permanent cache files)
            if temp_path and os.path.exists(temp_path):
                base = os.path.basename(temp_path)
                if base.startswith("tmp_") or not base.startswith(f"{chat_id}_{msg_id}"):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass

    except Exception as e:
        await event.edit(f"❌ **Error:** `{e}`")

