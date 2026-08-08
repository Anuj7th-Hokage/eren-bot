import os
from telethon import events
import __main__
from gtts import gTTS
import asyncio

client = __main__.client

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.voice(?: |$)(.*)"))
async def voice_command(event):
    text = event.pattern_match.group(1).strip()
    
    if not text:
        # Check if it's a reply to a message
        if event.is_reply:
            reply = await event.get_reply_message()
            text = reply.raw_text
            
    if not text:
        await event.edit("⚠️ **Usage:** `.voice <text>` or reply to a message with `.voice`")
        return
        
    status = await event.edit("🎙 **Recording voice...**")
    
    try:
        def generate_tts():
            # lang='hi' naturally provides a female Indian voice that handles both Hindi and English (Hinglish) well.
            tts = gTTS(text=text, lang='hi', tld='co.in')
            tts.save("voice_note.mp3")
            
        await asyncio.to_thread(generate_tts)
        
        await event.client.send_file(
            event.chat_id, 
            "voice_note.mp3", 
            voice_note=True, 
            reply_to=event.id
        )
        await status.delete()
        if os.path.exists("voice_note.mp3"):
            os.remove("voice_note.mp3")
            
    except Exception as e:
        await status.edit(f"❌ **Error generating voice:** `{str(e)}`")

@client.on(events.NewMessage(outgoing=True, pattern=r"(?i)^\.meow$"))
async def meow_command(event):
    status = await event.edit("🎙 **Meowing...**")
    try:
        audio_path = os.path.join(os.path.dirname(__file__), "meow_audio.mp3")
        
        await event.client.send_file(
            event.chat_id, 
            audio_path, 
            voice_note=True, 
            reply_to=event.id
        )
        await status.delete()
            
    except Exception as e:
        await status.edit(f"❌ **Error sending meow:** `{str(e)}`")
