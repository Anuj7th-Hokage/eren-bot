import os
import asyncio
from telethon import TelegramClient

API_ID = os.environ.get("API_ID", "34081269")
API_HASH = os.environ.get("API_HASH", "60fe75009bae6b19d0dae5512b511647")
SESSION_PATH = os.path.expanduser("~/.config/erenbot/my_userbot")

async def main():
    client = TelegramClient(SESSION_PATH, int(API_ID), API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("NOT AUTHORIZED")
    else:
        me = await client.get_me()
        print(f"AUTHORIZED AS: {me.first_name} (@{me.username})")
    await client.disconnect()

asyncio.run(main())
