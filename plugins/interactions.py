import re
import __main__
from telethon import events
from telethon.tl.types import MessageMediaDocument, DocumentAttributeAnimated
from plugins.db_utils import save_gif, get_random_gif, get_all_authorized_users

client = __main__.client

# List of supported interaction types
SUPPORTED_ACTIONS = ['kick', 'pat', 'kiss', 'slap', 'hug', 'bite', 'punch', 'lick', 'poke', 'cuddle', 'kill']

def get_action_text(action, sender_name, target_name):
    # Just basic present/past tense mapping for the action string
    templates = {
        'kick': f"**{sender_name}** kicked **{target_name}**! 💥",
        'pat': f"**{sender_name}** gave **{target_name}** a headpat! 🥺",
        'kiss': f"**{sender_name}** kissed **{target_name}**! 💋",
        'slap': f"**{sender_name}** slapped **{target_name}**! 💢",
        'hug': f"**{sender_name}** hugged **{target_name}**! 🤗",
        'bite': f"**{sender_name}** bit **{target_name}**! 🧛‍♂️",
        'punch': f"**{sender_name}** punched **{target_name}**! 🥊",
        'lick': f"**{sender_name}** licked **{target_name}**! 👅",
        'poke': f"**{sender_name}** poked **{target_name}**! 👉",
        'cuddle': f"**{sender_name}** cuddled with **{target_name}**! 🥰",
        'kill': f"**{sender_name}** completely destroyed **{target_name}**! 💀"
    }
    return templates.get(action.lower(), f"**{sender_name}** used {action} on **{target_name}**!")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.save (.*)'))
async def save_interaction_gif(event):
    action = event.pattern_match.group(1).strip().lower()
    
    if action not in SUPPORTED_ACTIONS:
        await event.edit(f"⚠️ **Unsupported action.** \nTry one of: `{', '.join(SUPPORTED_ACTIONS)}`")
        return
        
    if not event.is_reply:
        await event.edit("⚠️ **You must reply to a GIF to save it.**")
        return
        
    reply_msg = await event.get_reply_message()
    
    if not reply_msg.media or not isinstance(reply_msg.media, MessageMediaDocument):
        await event.edit("⚠️ **The replied message is not a valid GIF or animation.**")
        return
        
    # Check if it's animated
    is_animated = any(isinstance(attr, DocumentAttributeAnimated) for attr in reply_msg.document.attributes)
    if not is_animated:
        await event.edit("⚠️ **Please reply to an actual GIF or animated sticker.**")
        return
        
    # Forward the GIF to Saved Messages ('me') to cement it in the cache forever
    try:
        saved_media_msg = await client.forward_messages('me', reply_msg)
        media_ref = f"me:{saved_media_msg.id}"
    except Exception as e:
        await event.edit(f"⚠️ **Failed to safely cache the GIF.** Error: `{e}`")
        return
    
    # Save to SQLite
    success = save_gif(action, media_ref)
    
    if success:
        await event.edit(f"✅ **Successfully saved this GIF under:** `.{action}`\n*(You can delete the message now if you want)*")
    else:
        await event.edit(f"⚠️ **This exact GIF is already saved under:** `.{action}`")

# Regex matches .kick, .kiss, .pat, etc + optional username
pattern_str = r'^\.(' + '|'.join(SUPPORTED_ACTIONS) + r')(?: |$)(.*)'

@client.on(events.NewMessage(pattern=pattern_str))
async def perform_interaction(event):
    # Check authorization first
    is_outgoing = getattr(event, 'out', False)
    if not is_outgoing and getattr(event, 'sender_id', None) not in get_all_authorized_users():
        return # Ignore unauthorized external users
        
    action = event.pattern_match.group(1).lower()
    target_input = event.pattern_match.group(2).strip()
    
    sender_name = getattr(event.sender, 'first_name', 'ERENBOT')
    target_name = None
    target_entity = None
    
    # Logic for finding exactly who the target is
    if target_input:
        target_entity = target_input
        try:
            user = await client.get_entity(target_entity)
            target_name = getattr(user, 'first_name', target_input)
        except:
            target_name = target_input # Fallback to raw text if it wasn't a valid @username
    elif event.is_reply:
        reply_msg = await event.get_reply_message()
        if reply_msg and reply_msg.sender:
            target_name = getattr(reply_msg.sender, 'first_name', 'someone')
    
    if not target_name:
        if is_outgoing:
            await event.edit(f"⚠️ **Usage:** `.{action} @username` or reply to someone.")
        else:
            await event.reply(f"⚠️ **Usage:** `.{action} @username` or reply to someone.")
        return

    # Delete the command trigger if we have permission to (owner messages only)
    if is_outgoing:
        await event.delete()
    
    # Fetch random GIF ID from database
    random_gif_file_id = get_random_gif(action)
    action_text = get_action_text(action, sender_name, target_name)
    
    if random_gif_file_id and ":" in random_gif_file_id:
        try:
            # Parse stored chat_id and message_id
            from_chat, from_msg_id = random_gif_file_id.split(":")
            if from_chat != "me":
                from_chat = int(from_chat)
            from_msg_id = int(from_msg_id)
            
            # Fetch the actual message object from the original chat
            saved_msg = await client.get_messages(from_chat, ids=from_msg_id)
            
            if saved_msg and saved_msg.media:
                await client.send_message(
                    event.chat_id,
                    action_text,
                    file=saved_msg.media,
                    reply_to=event.reply_to_msg_id if event.is_reply else None
                )
            else:
                 await client.send_message(
                    event.chat_id, 
                    f"{action_text}\n*(Error: The saved GIF was deleted or is inaccessible)*",
                    reply_to=event.reply_to_msg_id if event.is_reply else None
                )
        except Exception as e:
            await client.send_message(
                event.chat_id, 
                f"{action_text}\n*(Media failed to load from cache: {str(e)})*",
                reply_to=event.reply_to_msg_id if event.is_reply else None
            )
    else:
        # No valid GIF found or legacy format, so just send text
        await client.send_message(
            event.chat_id,
            action_text,
            reply_to=event.reply_to_msg_id if event.is_reply else None
        )
