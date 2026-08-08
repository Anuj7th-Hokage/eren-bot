import os
import sys
import logging
from telethon import TelegramClient

# Set up hacker-themed logging in the terminal output
logging.basicConfig(
    level=logging.INFO,
    format="\x1b[32m[%(asctime)s] [%(levelname)s] [UserBot]\x1b[0m %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("UserBot")

from telethon.sessions import StringSession

# Fetch API credentials from environment variables or use hardcoded ones
API_ID = os.environ.get("API_ID", "34081269")
API_HASH = os.environ.get("API_HASH", "60fe75009bae6b19d0dae5512b511647")

if not API_ID or not API_HASH:
    logger.error("API_ID and API_HASH environment variables are missing!")
    logger.error("Please export them before running the bot.")
    sys.exit(1)

# Initialize the Telethon Client using StringSession (No SQLite = No lock errors)
SESSION_FILE = os.path.expanduser("~/.config/erenbot/session.txt")

# First try to get it from environment variable (useful for servers like Render/Railway)
session_string = os.environ.get("STRING_SESSION", "")

if not session_string and os.path.exists(SESSION_FILE):
    with open(SESSION_FILE, "r") as f:
        session_string = f.read().strip()

if not session_string:
    logger.error("No StringSession found! Please run 'python3 generate_session.py' first or set STRING_SESSION.")
    sys.exit(1)

client = TelegramClient(StringSession(session_string), int(API_ID), API_HASH)

if __name__ == "__main__":
    logger.info("Initializing UserBot Sequence...")
    logger.info("Connecting to Telegram Mainframe...")
    try:
        # Load all plugins
        from plugins.utils import *
        from plugins.hack_sim import *
        from plugins.spam import *
        from plugins.interactions import *
        from plugins.auth import *
        from plugins.weather import *
        from plugins.search import *
        from plugins.song import *
        from plugins.voice import *
        from plugins.ss import *
        from plugins.ai import *
        
        client.start()
        logger.info("UserBot is online and ready. Awaiting commands.")
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Critical System Error: {e}")
    finally:
        logger.info("Shutting down UserBot...")
        
