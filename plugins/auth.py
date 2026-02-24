import __main__
from telethon import events
from plugins.db_utils import add_authorized_user, remove_authorized_user

client = __main__.client

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.approve(?: |$)(.*)'))
async def approve_user(event):
    target = event.pattern_match.group(1).strip()
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    
    if not target:
        await event.edit("⚠️ **Usage:** `.approve @username` or reply to a user.")
        return
        
    try:
        user = await client.get_entity(target)
        success = add_authorized_user(user.id)
        if success:
            await event.edit(f"✅ **Approved:** {user.first_name} (`{user.id}`) can now use ERENBOT commands!")
        else:
            await event.edit(f"⚠️ **{user.first_name} is already approved.**")
    except Exception as e:
        await event.edit(f"❌ **Error approving user:** `{e}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.disapprove(?: |$)(.*)'))
async def disapprove_user(event):
    target = event.pattern_match.group(1).strip()
    
    if not target and event.is_reply:
        reply_msg = await event.get_reply_message()
        target = reply_msg.sender_id
    
    if not target:
        await event.edit("⚠️ **Usage:** `.disapprove @username` or reply to a user.")
        return
        
    try:
        user = await client.get_entity(target)
        success = remove_authorized_user(user.id)
        if success:
            await event.edit(f"🚫 **Revoked:** {user.first_name} (`{user.id}`) can no longer use ERENBOT commands.")
        else:
            await event.edit(f"⚠️ **{user.first_name} is not currently approved.**")
    except Exception as e:
        await event.edit(f"❌ **Error disapproving user:** `{e}`")
