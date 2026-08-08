import os
import json
import aiohttp
from telethon import events
import __main__

client = __main__.client

DEFAULT_GROQ_KEY = "gsk_jQVyU4aZmlB2dE9oiK1LWG" + "dyb3FYXMog2lLDlVH7u8mbiyCZjg62"
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", DEFAULT_GROQ_KEY)
GROQ_BASE_URL = os.environ.get(
    "GROQ_BASE_URL",
    "https://api.groq.com/openai/v1",
).rstrip("/")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
CHAT_URL = f"{GROQ_BASE_URL}/chat/completions"

SYSTEM_PROMPT = "You are an intelligent assistant, please reply concisely."


def _extract_reply(data):
    if data is None:
        return None
    if isinstance(data, str):
        return data.strip() or None
    if not isinstance(data, dict):
        return str(data)

    choices = data.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            msg = first.get("message") or first.get("delta") or first
            if isinstance(msg, dict):
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content.strip()
            if isinstance(first.get("text"), str) and first["text"].strip():
                return first["text"].strip()

    return None


async def _ask_ai(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "stream": False,
    }

    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.post(CHAT_URL, headers=headers, json=payload) as resp:
            raw = await resp.text()
            if resp.status != 200:
                raise RuntimeError(f"API {resp.status}: {raw[:300]}")
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                return raw.strip()
            reply = _extract_reply(data)
            if not reply:
                raise RuntimeError(f"Empty AI response: {raw[:300]}")
            return reply


async def _ask_ai_keyless(prompt: str) -> str:
    # Keyless fallback using Pollinations AI
    url = f"https://text.pollinations.ai/{prompt}"
    timeout = aiohttp.ClientTimeout(total=60)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                text = await resp.text()
                if text.strip():
                    return text.strip()
            raise RuntimeError(f"Pollinations API error status {resp.status}")

@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.ai(?: |$)(.*)'))
async def ai_chat(event):
    prompt = (event.pattern_match.group(1) or "").strip()

    if not prompt and event.is_reply:
        reply_msg = await event.get_reply_message()
        prompt = (reply_msg.message or "").strip() if reply_msg else ""

    if not prompt:
        await event.edit(
            "⚠️ **Usage:** `.ai <prompt>`\n"
            "Or reply to a message with `.ai`"
        )
        return

    await event.edit("🤖 **Thinking...**")

    try:
        if GROQ_API_KEY:
            answer = await _ask_ai(prompt)
        else:
            answer = await _ask_ai_keyless(prompt)

        if len(answer) > 3900:
            answer = answer[:3900] + "…"
        await event.edit(f"🤖 **AI**\n\n{answer}")
    except Exception as e:
        await event.edit(f"❌ **AI Error:** `{e}`")
