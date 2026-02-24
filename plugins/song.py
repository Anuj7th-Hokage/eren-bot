import os
import glob
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
            await event.edit("⚠️ **Usage:** `.song <song name>`\n*Example:* `.song blinding lights`")
            return
            
        status = await event.reply(f"🔎 **Searching for:** `{song_name}`...")

        ydl_opts = {
            'format': 'bestaudio/best', 
            'outtmpl': 'song.%(ext)s',
            'quiet': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # ytsearch automatically picks the first youtube search result
                ydl.download([f"ytsearch:{song_name}"])
            
            # Find whatever file was downloaded
            downloaded_files = glob.glob("song.*")
            if downloaded_files:
                file_path = downloaded_files[0]
                await event.client.send_file(
                    event.chat_id, 
                    file_path, 
                    caption=f"🎵 **Found:** `{song_name}`",
                    reply_to=event.id
                )
                await status.delete()
                os.remove(file_path)
            else:
                 await status.edit("❌ **Error: File not found after downloading.**")

        except Exception as e:
            await status.edit(f"❌ **Error downloading song:** `{str(e)}`")
