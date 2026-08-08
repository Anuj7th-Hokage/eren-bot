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
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=3"
        import urllib.request
        import asyncio
        
        def fetch_weather():
            req = urllib.request.Request(url, headers={'User-Agent': 'curl/7.64.1'})
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read().decode('utf-8')
                
        weather_data = await asyncio.to_thread(fetch_weather)
        await event.edit(f"🌤 **Weather Report**\n\n`{weather_data.strip()}`")
    except Exception as e:
        await event.edit(f"❌ **Error fetching weather:** `{str(e)}`")
