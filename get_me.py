import asyncio
from telethon import TelegramClient
import os

API_ID = os.environ.get("API_ID", "34081269")
API_HASH = os.environ.get("API_HASH", "60fe75009bae6b19d0dae5512b511647")
SESSION_PATH = os.path.expanduser("~/.config/erenbot/my_userbot")

async def main():
    client = TelegramClient(SESSION_PATH, int(API_ID), API_HASH)
    await client.connect()
    me = await client.get_me()
    print(f"Logged in as: {me.first_name} (ID: {me.id}, Username: {me.username})")
    await client.disconnect()

asyncio.run(main())
