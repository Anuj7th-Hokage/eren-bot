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

# Fetch API credentials from environment variables or use hardcoded ones
API_ID = os.environ.get("API_ID", "31739032")
API_HASH = os.environ.get("API_HASH", "271eb45b268af130c6a1ef7e1724b9cc")

if not API_ID or not API_HASH:
    logger.error("API_ID and API_HASH environment variables are missing!")
    logger.error("Please export them before running the bot.")
    sys.exit(1)

# Initialize the Telethon Client
# session name will be "my_userbot", which creates my_userbot.session locally
client = TelegramClient('my_userbot', int(API_ID), API_HASH)

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
        
        client.start()
        logger.info("UserBot is online and ready. Awaiting commands.")
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Critical System Error: {e}")
    finally:
        logger.info("Shutting down UserBot...")
        
