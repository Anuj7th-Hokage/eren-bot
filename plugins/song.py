import os
import glob
import asyncio
import yt_dlp
from telethon import events
import __main__

client = __main__.client

# Pattern regex accepts '.song <name>'
@client.on(events.NewMessage(pattern=r"(?i)^\.song(?: |$)(.*)"))
async def easy_song_for_all(event):
    # Only allow outgoing (owner) or if the bot is mentioned by an authorized user
    if not (event.out or getattr(event, 'mentioned', False)):
        return

    song_name = event.pattern_match.group(1).strip()
    
    if not song_name:
        usage_msg = "⚠️ **Usage:** `.song <song name>`\n*Example:* `.song blinding lights`"
        if event.out:
            await event.edit(usage_msg)
        else:
            await event.reply(usage_msg)
        return

    # Create or update status message
    status_text = f"🔎 **Searching for:** `{song_name}`..."
    try:
        if event.out:
            status = await event.edit(status_text)
        else:
            status = await event.reply(status_text)
    except Exception:
        status = event

    # Clean up old temporary files
    for old_file in glob.glob("song_temp_*"):
        try:
            os.remove(old_file)
        except Exception:
            pass

    ydl_opts = {
        'format': 'bestaudio/best', 
        'outtmpl': 'song_temp_%(id)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'web']
            }
        }
    }

    file_path = None
    # Try search providers in order: YouTube search -> SoundCloud search fallback
    search_queries = [f"ytsearch1:{song_name}", f"scsearch1:{song_name}"]

    for search_query in search_queries:
        try:
            loop = asyncio.get_running_loop()
        except AttributeError:
            loop = asyncio.get_event_loop()

        def download_func(query=search_query):
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([query])

        try:
            await loop.run_in_executor(None, download_func)
            downloaded_files = glob.glob("song_temp_*")
            if downloaded_files:
                file_path = downloaded_files[0]
                break
        except Exception:
            continue

    try:
        if file_path and os.path.exists(file_path):
            try:
                await status.edit(f"⬆️ **Uploading:** `{song_name}`...")
            except Exception:
                pass
            await event.client.send_file(
                event.chat_id, 
                file_path, 
                caption=f"🎵 **Found:** `{song_name}`",
                reply_to=event.id,
                supports_streaming=True
            )
            try:
                await status.delete()
            except Exception:
                pass
        else:
            try:
                await status.edit(f"❌ **Could not find song:** `{song_name}`. Please try another name.")
            except Exception:
                pass
    except Exception as e:
        try:
            await status.edit(f"❌ **Error uploading song:** `{str(e)}`")
        except Exception:
            pass
    finally:
        # Always clean up temporary audio files
        for temp_file in glob.glob("song_temp_*"):
            try:
                os.remove(temp_file)
            except Exception:
                pass
