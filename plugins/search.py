import wikipedia
from telethon import events
import __main__

client = __main__.client

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.searching(?: |$)(.*)'))
async def wikipedia_search(event):
    query = event.pattern_match.group(1).strip()
    
    if not query:
        await event.edit("⚠️ **Usage:** `.searching <topic>`\n*Example:* `.searching Python Programming`")
        return
        
    await event.edit(f"🔍 **Searching Wikipedia for:** `{query}`...")
    
    try:
        # Fetching a short summary (limit to a few sentences)
        # wikipedia.summary automatically handles a bit of disambiguation but we catch exceptions just in case
        summary = wikipedia.summary(query, sentences=3)
        page_url = wikipedia.page(query).url
        
        caption = (
            f"📚 **Wikipedia Search:** `{query}`\n\n"
            f"📖 {summary}\n\n"
            f"🔗 **Read More:** [Link to Article]({page_url})"
        )
        
        await event.edit(caption)
        
    except wikipedia.exceptions.DisambiguationError as e:
        # If the search term is too broad
        options = ", ".join(e.options[:5]) # Show first 5 options
        await event.edit(f"⚠️ **Too many results!** Did you mean:\n`{options}`...?")
    except wikipedia.exceptions.PageError:
        await event.edit(f"❌ **No Wikipedia page found for:** `{query}`")
    except Exception as e:
        await event.edit(f"❌ **Search error:** `{str(e)}`")
