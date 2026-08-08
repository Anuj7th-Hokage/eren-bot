import os
import io
from datetime import datetime
from telethon import events
import __main__

try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    Image = None

client = __main__.client

# Phone canvas
W, H = 390, 844
BG = (15, 15, 15)
HEADER_BG = (22, 22, 22)
IN_BUBBLE = (33, 33, 33)
OUT_BUBBLE = (50, 120, 210)
TEXT = (255, 255, 255)
MUTED = (160, 160, 160)
GREEN = (82, 196, 26)
BAR = (0, 0, 0)


def _font(size, bold=False):
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "arial.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _wrap(draw, text, font, max_width):
    text = (text or "").replace("\n", " ").strip() or " "
    words = text.split(" ")
    lines, cur = [], ""
    for word in words:
        test = word if not cur else f"{cur} {word}"
        if draw.textlength(test, font=font) <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines[:8]


def _circle_avatar(img, size):
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, (0, 0), mask)
    return out


def _default_avatar(name, size=56):
    img = Image.new("RGBA", (size, size), (90, 90, 200, 255))
    d = ImageDraw.Draw(img)
    letter = (name or "?")[0].upper()
    f = _font(int(size * 0.45), bold=True)
    bbox = d.textbbox((0, 0), letter, font=f)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    d.text(((size - tw) / 2, (size - th) / 2 - 2), letter, font=f, fill=TEXT)
    return _circle_avatar(img, size)


async def _load_avatar(entity, size=56):
    try:
        bio = io.BytesIO()
        path = await client.download_profile_photo(entity, file=bio)
        if path or bio.getbuffer().nbytes:
            bio.seek(0)
            return _circle_avatar(Image.open(bio), size)
    except Exception:
        pass
    name = getattr(entity, "first_name", None) or getattr(entity, "title", None) or "?"
    return _default_avatar(name, size)


def _draw_phone_chrome(base, title, subtitle, avatar, now_str):
    draw = ImageDraw.Draw(base)

    # Status bar
    draw.rectangle((0, 0, W, 44), fill=BAR)
    f_status = _font(15, bold=True)
    draw.text((24, 12), now_str, font=f_status, fill=TEXT)
    # signal / wifi / battery hints
    draw.ellipse((W - 52, 16, W - 46, 22), fill=TEXT)
    draw.ellipse((W - 42, 16, W - 36, 22), fill=TEXT)
    draw.ellipse((W - 32, 16, W - 26, 22), fill=TEXT)
    draw.rounded_rectangle((W - 22, 14, W - 8, 24), radius=3, outline=TEXT, width=1)
    draw.rectangle((W - 20, 16, W - 12, 22), fill=GREEN)

    # Notch
    draw.rounded_rectangle((W // 2 - 60, 0, W // 2 + 60, 28), radius=14, fill=(20, 20, 20))

    # Header
    draw.rectangle((0, 44, W, 108), fill=HEADER_BG)
    base.paste(avatar, (14, 52), avatar)

    f_title = _font(17, bold=True)
    f_sub = _font(12)
    draw.text((78, 58), title[:22], font=f_title, fill=TEXT)
    draw.text((78, 80), subtitle[:28], font=f_sub, fill=MUTED)

    # back chevron
    draw.polygon([(18, 76), (28, 66), (28, 86)], fill=OUT_BUBBLE)


def _bubble(draw, x, y, lines, font, fill, align_right=False):
    pad_x, pad_y = 12, 8
    line_h = 20
    text_w = max(draw.textlength(line, font=font) for line in lines)
    bw = int(text_w + pad_x * 2)
    bh = int(pad_y * 2 + line_h * len(lines))
    if align_right:
        x = x - bw
    draw.rounded_rectangle((x, y, x + bw, y + bh), radius=14, fill=fill)
    ty = y + pad_y
    for line in lines:
        draw.text((x + pad_x, ty), line, font=font, fill=TEXT)
        ty += line_h
    return bh


async def render_chat_screenshot(chat, messages, me):
    chat_title = (
        getattr(chat, "title", None)
        or " ".join(filter(None, [getattr(chat, "first_name", None), getattr(chat, "last_name", None)]))
        or "Chat"
    )
    if getattr(chat, "username", None):
        subtitle = f"@{chat.username}"
    elif getattr(chat, "online", False) or str(getattr(chat, "status", "")).endswith("Online"):
        subtitle = "online"
    else:
        subtitle = "Telegram"

    avatar = await _load_avatar(chat, 48)
    now_str = datetime.now().strftime("%I:%M %p").lstrip("0")

    # Measure needed height roughly, then draw bottom-up on tall canvas and crop
    canvas_h = max(H, 160 + len(messages) * 70)
    base = Image.new("RGB", (W, canvas_h), BG)
    draw = ImageDraw.Draw(base)
    _draw_phone_chrome(base, chat_title, subtitle, avatar, now_str)

    f_msg = _font(15)
    f_time = _font(10)
    y = 120
    max_bubble = W - 90

    # messages oldest → newest
    ordered = list(reversed(messages))
    for msg in ordered:
        if not msg:
            continue
        text = msg.message or ""
        if msg.media and not text:
            if msg.photo:
                text = "📷 Photo"
            elif msg.video:
                text = "🎥 Video"
            elif msg.voice or msg.audio:
                text = "🎤 Voice message"
            elif msg.sticker:
                text = "🎨 Sticker"
            else:
                text = "📎 Media"
        if not text.strip():
            text = " "

        out = bool(msg.out)
        lines = _wrap(draw, text, f_msg, max_bubble)
        if out:
            bh = _bubble(draw, W - 16, y, lines, f_msg, OUT_BUBBLE, align_right=True)
        else:
            bh = _bubble(draw, 16, y, lines, f_msg, IN_BUBBLE, align_right=False)

        t = msg.date.astimezone().strftime("%H:%M") if msg.date else ""
        tw = draw.textlength(t, font=f_time)
        if out:
            draw.text((W - 20 - tw, y + bh + 2), t, font=f_time, fill=MUTED)
        else:
            draw.text((20, y + bh + 2), t, font=f_time, fill=MUTED)
        y += bh + 22

    # Home indicator
    final_h = max(H, y + 40)
    if final_h != canvas_h:
        extended = Image.new("RGB", (W, final_h), BG)
        extended.paste(base, (0, 0))
        base = extended
        draw = ImageDraw.Draw(base)

    draw.rounded_rectangle((W // 2 - 50, final_h - 18, W // 2 + 50, final_h - 10), radius=4, fill=(80, 80, 80))

    # Rounded phone corners overlay
    mask = Image.new("L", (W, final_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, W, final_h), radius=36, fill=255)
    phone = ImageOps.fit(base, (W, final_h), centering=(0.5, 0.5))
    phone.putalpha(mask)

    # Dark backdrop
    out = Image.new("RGBA", (W + 40, final_h + 40), (30, 30, 35, 255))
    out.paste(phone, (20, 20), phone)

    buf = io.BytesIO()
    out.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    buf.name = "ss.png"
    return buf


@client.on(events.NewMessage(outgoing=True, pattern=r'(?i)^\.ss(?: |$)(.*)'))
async def chat_screenshot(event):
    if Image is None:
        await event.edit("❌ **Pillow not installed.** Run: `pip install pillow`")
        return

    arg = (event.pattern_match.group(1) or "").strip()
    count = 10
    if arg.isdigit():
        count = max(1, min(30, int(arg)))

    await event.edit(f"📸 **Capturing last {count} messages...**")

    try:
        chat = await event.get_chat()
        me = await client.get_me()

        # Skip the .ss command itself
        messages = []
        async for msg in client.iter_messages(event.chat_id, limit=count + 5):
            if msg.id == event.id:
                continue
            if msg.message and msg.message.strip().lower().startswith(".ss"):
                continue
            messages.append(msg)
            if len(messages) >= count:
                break

        if not messages:
            await event.edit("❌ **No messages to screenshot.**")
            return

        img = await render_chat_screenshot(chat, messages, me)
        await client.send_file(
            event.chat_id,
            img,
            caption=f"📱 **Chat screenshot** · last {len(messages)} messages",
            reply_to=event.id,
        )
        await event.delete()
    except Exception as e:
        await event.edit(f"❌ **Screenshot failed:** `{e}`")
