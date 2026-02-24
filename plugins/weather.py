import aiohttp
from telethon import events
import __main__

client = __main__.client

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.weather(?: |$)(.*)'))
async def get_weather(event):
    city = event.pattern_match.group(1).strip()
    if not city:
        await event.edit("⚠️ **Usage:** `.weather <city name>`\n*Example:* `.weather Mumbai`")
        return
        
    await event.edit(f"🔍 **Fetching weather for** `{city}`...")
    
    try:
        # wttr.in is a free, no-auth API that returns plaintext formatted weather
        # Format 3 is a short one-liner, format 4 is slightly more detailed
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=3"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    weather_data = await response.text()
                    await event.edit(f"🌤 **Weather Report**\n\n`{weather_data.strip()}`")
                else:
                    await event.edit(f"❌ **Could not fetch weather for:** `{city}`\n*(API returned status {response.status})*")
    except Exception as e:
        await event.edit(f"❌ **Error fetching weather:** `{str(e)}`")
