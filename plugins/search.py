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

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.img(?: |$)(.*)'))
async def image_search(event):
    query = event.pattern_match.group(1).strip()
    
    if not query:
        await event.edit("⚠️ **Usage:** `.img <query>`\n*Example:* `.img bra`")
        return
        
    status = await event.edit(f"🔍 **Searching image for:** `{query}`...")
    
    try:
        def fetch_image():
            import urllib.request, re, urllib.parse
            req = urllib.request.Request(
                'https://www.bing.com/images/search?q=' + urllib.parse.quote(query), 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
            matches = re.findall(r'murl&quot;:&quot;(.*?)&quot;', html)
            if matches:
                import random
                # Get one of the top 3 images to add slight variety but keep relevance
                return random.choice(matches[:3])
            return None
            
        import asyncio
        img_url = await asyncio.to_thread(fetch_image)
        
        if img_url:
            await event.client.send_file(
                event.chat_id, 
                img_url, 
                caption=f"📸 **Image Search:** `{query}`",
                reply_to=event.reply_to_msg_id if event.is_reply else None
            )
            await status.delete()
        else:
            await status.edit(f"❌ **No image found for:** `{query}`")
            
    except Exception as e:
        await status.edit(f"❌ **Error searching image:** `{str(e)}`")

@client.on(events.NewMessage(outgoing=True, pattern=r'^\.google(?: |$)(.*)'))
async def google_search(event):
    query = event.pattern_match.group(1).strip()
    
    if not query:
        await event.edit("⚠️ **Usage:** `.google <query>`\n*Example:* `.google latest technology news`")
        return
        
    status = await event.edit(f"🔍 **Searching Google for:** `{query}`...")
    
    try:
        def fetch_results():
            import urllib.request, urllib.parse, re, html as html_lib
            # Using DuckDuckGo Lite as a reliable backend for web searches
            data = urllib.parse.urlencode({'q': query}).encode('utf-8')
            req = urllib.request.Request(
                'https://lite.duckduckgo.com/lite/', 
                data=data, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            html = urllib.request.urlopen(req).read().decode('utf-8', errors='ignore')
            
            # Extract titles and links
            results = re.findall(r'<a rel="nofollow" href="([^"]+)"[^>]*>(.*?)</a>', html)
            
            cleaned_results = []
            for url, title in results:
                if url.startswith('http') and not 'duckduckgo' in url:
                    clean_title = html_lib.unescape(title)
                    clean_title = re.sub(r'<[^>]+>', '', clean_title)
                    if clean_title and url:
                        cleaned_results.append((url, clean_title))
                    if len(cleaned_results) >= 5: # Top 5 results
                        break
            return cleaned_results

        import asyncio
        results = await asyncio.to_thread(fetch_results)
        
        if results:
            output = f"🌐 **Search Results for:** `{query}`\n\n"
            for i, (url, title) in enumerate(results, 1):
                output += f"**{i}.** [{title}]({url})\n"
            await status.edit(output, link_preview=False)
        else:
            await status.edit(f"❌ **No results found for:** `{query}`")
            
    except Exception as e:
        await status.edit(f"❌ **Search error:** `{str(e)}`")
