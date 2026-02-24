import os
import yt_dlp
from telethon import events
import __main__

client = __main__.client

# Pattern regex accepts '.song <name>'
@client.on(events.NewMessage(pattern=r"(?i)^\.song(?: |$)(.*)"))
async def easy_song_for_all(event):
    # Only allow outgoing (owner) or if the bot is mentioned by an authorized user
    if event.out or getattr(event, 'mentioned', False):
        song_name = event.pattern_match.group(1).strip()
        
        if not song_name:
            await event.edit("⚠️ **Usage:** `.song <song name>`\n*Example:* `.song blinging lights`")
            return
            
        status = await event.reply(f"🔎 **Searching for:** `{song_name}`...")

        ydl_opts = {
            'format': 'bestaudio[ext=m4a]', 
            'outtmpl': 'song.m4a',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # ytsearch automatically picks the first youtube search result
                ydl.download([f"ytsearch:{song_name}"])
            
            await event.client.send_file(
                event.chat_id, 
                "song.m4a", 
                caption=f"🎵 **Found:** `{song_name}`",
                reply_to=event.id
            )
            await status.delete()
            if os.path.exists("song.m4a"):
                os.remove("song.m4a")

        except Exception as e:
            await status.edit(f"❌ **Error downloading song:** `{e}`")
