import os
import asyncio
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

API_ID = os.environ.get("API_ID", "34081269")
API_HASH = os.environ.get("API_HASH", "60fe75009bae6b19d0dae5512b511647")

print("Initializing session generation...")
print("Please enter your phone number when prompted (e.g., +1234567890).")

with TelegramClient(StringSession(), int(API_ID), API_HASH) as client:
    session_string = client.session.save()
    
    # Save the string session to a file
    session_file = os.path.expanduser("~/.config/erenbot/session.txt")
    os.makedirs(os.path.dirname(session_file), exist_ok=True)
    
    with open(session_file, "w") as f:
        f.write(session_string)

    print("\n✅ Session successfully generated!")
    print(f"✅ Saved to: {session_file}")
    print("You can now run 'python3 bot.py'")
