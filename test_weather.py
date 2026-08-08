import asyncio
import aiohttp
async def get_w():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://wttr.in/Mumbai?format=3") as response:
            print(await response.text())
asyncio.run(get_w())
