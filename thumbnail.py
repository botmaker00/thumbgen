# thumbnail_bot.py - Final AnimeFlicker Exact Match Generator
import telebot
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from io import BytesIO

# ⚠️ YAHAN APNA NAYA TOKEN DAALNA (purana wala mat daalna)
API_TOKEN = os.getenv("BOT_TOKEN", "7597391690:AAFdUlJBP46IJNvkaM6vIhW6J1fbmUTlkjA")
bot = telebot.TeleBot(API_TOKEN)

# Fonts
FONTS_DIR = "fonts"
try:
    # Use root BebasNeue-Regular.ttf for title
    if os.path.exists("BebasNeue-Regular.ttf"):
        TITLE_FONT_PATH = "BebasNeue-Regular.ttf"
    else:
        TITLE_FONT_PATH = os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf")

    TITLE_FONT = ImageFont.truetype(TITLE_FONT_PATH, 160)

    # Use available Roboto variants from fonts/
    BOLD_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 42)
    MEDIUM_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Medium.ttf"), 36)
    REG_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Light.ttf"), 30)
    GENRE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Medium.ttf"), 38)
except Exception as e:
    print(f"Font loading error: {e}")
    TITLE_FONT = ImageFont.load_default()
    BOLD_FONT = ImageFont.load_default()
    MEDIUM_FONT = ImageFont.load_default()
    REG_FONT = ImageFont.load_default()
    GENRE_FONT = ImageFont.load_default()

LOGO_FONT = MEDIUM_FONT

CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720

# Colors
TEXT_COLOR = (255, 255, 255)
SUBTEXT_COLOR = (210, 210, 210)
GENRE_COLOR = (140, 150, 190) # Bluish grey
BUTTON_BG = (40, 60, 100) # Blue button bg
LOGO_COLOR = (255, 255, 255)

def wrap_text(text, font, max_width):
    avg_char_width = font.getlength('x')
    chars_per_line = int(max_width / avg_char_width)
    wrapped = textwrap.fill(text, width=chars_per_line)
    return wrapped.split('\n')

def add_gradient(image):
    # Add a horizontal gradient from black (left) to transparent (right)
    # to make text readable on the left side
    width, height = image.size
    gradient = Image.new('L', (width, height), color=0)
    draw = ImageDraw.Draw(gradient)

    # Create gradient: 0 to 255 (left to right)
    # But we want opaque black on left (255 alpha) fading to transparent (0 alpha)
    # So we draw opacity mask

    for x in range(width):
        # Opacity decreases as x increases
        # Start fully opaque (255) until x=600, then fade to 0 by x=1000
        if x < 400:
            alpha = 240 # Very dark on left
        elif x < 900:
            # Linear fade
            alpha = int(240 * (1 - (x - 400) / 500))
        else:
            alpha = 0

        draw.line([(x, 0), (x, height)], fill=alpha)

    # Create black layer
    black_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    # Apply gradient as alpha
    black_layer.putalpha(gradient)

    # Paste/Composite
    image.paste(black_layer, (0, 0), black_layer)
    return image

def generate_thumbnail(anime):
    title = anime['title']['english'] or anime['title']['romaji']
    poster_url = anime['coverImage']['extraLarge']
    score = anime['averageScore']
    genres = anime['genres'][:3]
    desc = (anime['description'] or "").replace("<br>", " ").replace("<i>", "").replace("</i>", "")
    desc = " ".join(desc.split()[:40]) + "..."

    # 1. Prepare Background
    if os.path.exists("background.jpg"):
        bg = Image.open("background.jpg").convert("RGBA")
        bg = bg.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)
    else:
        # Fallback to dark blue if missing
        bg = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), (20, 35, 60))

    # Apply gradient to background for text visibility
    bg = add_gradient(bg)
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 2. Prepare Poster & Mask
    try:
        poster_resp = requests.get(poster_url)
        poster = Image.open(BytesIO(poster_resp.content)).convert("RGBA")

        # Resize poster to fill canvas (keeping aspect ratio, crop center/top)
        # We want the poster to fill the mask area which is mostly on the right/center
        aspect = poster.width / poster.height
        target_aspect = CANVAS_WIDTH / CANVAS_HEIGHT

        if aspect > target_aspect:
            new_height = CANVAS_HEIGHT
            new_width = int(new_height * aspect)
            poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Center crop
            left = (new_width - CANVAS_WIDTH) // 2
            poster = poster.crop((left, 0, left + CANVAS_WIDTH, new_height))
        else:
            new_width = CANVAS_WIDTH
            new_height = int(new_width / aspect)
            poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Top crop (faces are usually at top)
            poster = poster.crop((0, 0, CANVAS_WIDTH, CANVAS_HEIGHT))

        # Load PLP mask
        if os.path.exists("plp.jpg"):
            mask = Image.open("plp.jpg").convert("L")
            mask = mask.resize((CANVAS_WIDTH, CANVAS_HEIGHT), Image.Resampling.LANCZOS)

            # Apply mask
            # Paste poster onto canvas using mask
            canvas.paste(poster, (0, 0), mask)
        else:
            print("Warning: plp.jpg not found, skipping masking")
            # Just paste poster on right side as fallback? No, let's keep background.
            pass

    except Exception as e:
        print(f"Error loading poster: {e}")

    # 3. Draw Text & UI (Left Side)

    # Logo (Top Left)
    icon_x, icon_y = 50, 40
    sz = 18
    # Simple logo icon
    draw.polygon([(icon_x, icon_y+sz), (icon_x+sz, icon_y), (icon_x+2*sz, icon_y+sz), (icon_x+sz, icon_y+2*sz)], outline=LOGO_COLOR, width=3)
    draw.polygon([(icon_x+10, icon_y+sz), (icon_x+sz+10, icon_y), (icon_x+2*sz+10, icon_y+sz), (icon_x+sz+10, icon_y+2*sz)], outline=LOGO_COLOR, width=3)
    draw.text((icon_x + 65, icon_y + 2), "ANIME FLICKER", font=LOGO_FONT, fill=LOGO_COLOR)

    # Rating
    if score:
        rating_text = f"{score/10:.1f}+ Rating"
        draw.text((50, 140), rating_text, font=REG_FONT, fill=TEXT_COLOR)

    # Title
    # Use max width for title
    title_lines = wrap_text(title.upper(), TITLE_FONT, 700)
    title_y = 180
    for line in title_lines[:2]: # Max 2 lines
        draw.text((50, title_y), line, font=TITLE_FONT, fill=TEXT_COLOR)
        title_y += 140

    # Genres
    genre_text = ", ".join(genres).upper()
    draw.text((50, title_y + 10), genre_text, font=GENRE_FONT, fill=GENRE_COLOR)

    # Description
    desc_y = title_y + 60
    desc_lines = wrap_text(desc, REG_FONT, 580)
    for line in desc_lines[:4]: # Max 4 lines
        draw.text((50, desc_y), line, font=REG_FONT, fill=SUBTEXT_COLOR)
        desc_y += 42

    # Buttons
    btn_y = 620
    btn_width = 210
    btn_height = 65

    # Button 1: DOWNLOAD
    draw.rounded_rectangle((50, btn_y, 50 + btn_width, btn_y + btn_height), radius=12, fill=BUTTON_BG)
    text_w = BOLD_FONT.getlength("DOWNLOAD")
    text_x = 50 + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 12), "DOWNLOAD", font=BOLD_FONT, fill=TEXT_COLOR)

    # Button 2: JOIN NOW
    btn2_x = 50 + btn_width + 40
    draw.rounded_rectangle((btn2_x, btn_y, btn2_x + btn_width, btn_y + btn_height), radius=12, fill=BUTTON_BG)
    text_w = BOLD_FONT.getlength("JOIN NOW")
    text_x = btn2_x + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 12), "JOIN NOW", font=BOLD_FONT, fill=TEXT_COLOR)

    final = BytesIO()
    canvas.convert("RGB").save(final, "PNG")
    final.seek(0)
    return final

@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(msg, "Anime ka naam bhej ya /thumb Haikyuu likh\nMain ekdam AnimeFlicker jaisa thumbnail bana dunga")

@bot.message_handler(commands=['thumb'])
def thumb(msg):
    query = msg.text.replace("/thumb", "").strip()
    if not query:
        bot.reply_to(msg, "Bhai anime naam toh likh na!\nExample: /thumb One Piece")
        return
    bot.send_chat_action(msg.chat.id, 'upload_photo')
    try:
        resp = requests.post("https://graphql.anilist.co",
            json={"query": """
            query ($search: String) {
              Media(search: $search, type: ANIME) {
                title { romaji english }
                coverImage { extraLarge }
                averageScore
                genres
                description
              }
            }
            """, "variables": {"search": query}}
        ).json()['data']['Media']
        if not resp:
            bot.reply_to(msg, "Anime nahi mila bhai, sahi spelling likh")
            return
        img = generate_thumbnail(resp)
        title_text = resp['title']['english'] or resp['title']['romaji']
        bot.send_photo(msg.chat.id, img,
                      caption=f"{title_text}\n@YourChannelHere")
    except Exception as e:
        import traceback
        traceback.print_exc()
        bot.reply_to(msg, f"Error: {e}")

if __name__ == "__main__":
    print("Bot chal gaya!")
    bot.infinity_polling()
