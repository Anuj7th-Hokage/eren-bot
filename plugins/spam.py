import asyncio
from telethon import events
import __main__

client = __main__.client

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.spam (\d+) (.*)'))
async def spam(event):
    """
    .spam <count> <message>
    Sends a message multiple times.
    """
    try:
        count = int(event.pattern_match.group(1))
        message = event.pattern_match.group(2)
    except Exception:
        await event.edit("⚠️ **Usage:** `.spam <count> <message>`")
        return

    # Delete the command message
    await event.delete()
    
    # Cap spam at 100 to prevent self-ban and abuse
    if count > 100:
        count = 100
        
    for _ in range(count):
        await event.respond(message)
        await asyncio.sleep(0.5) # Protection delay to avoid flood waits

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.delspam (\d+) (.*)'))
async def delspam(event):
    """
    .delspam <count> <message>
    Sends a message multiple times and deletes them immediately (ghost spam).
    """
    try:
        count = int(event.pattern_match.group(1))
        message = event.pattern_match.group(2)
    except Exception:
        await event.edit("⚠️ **Usage:** `.delspam <count> <message>`")
        return

    await event.delete()
    
    if count > 100:
        count = 100
        
    for _ in range(count):
        msg = await event.respond(message)
        await asyncio.sleep(0.3)
        await msg.delete()
        await asyncio.sleep(0.3)
