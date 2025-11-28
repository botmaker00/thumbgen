# thumbnail_bot.py - Final AnimeFlicker Exact Match Generator
import telebot
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import textwrap
from io import BytesIO

# ⚠️ YAHAN APNA NAYA TOKEN DAALNA (purana wala mat daalna)
API_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")  # ← Replace with your actual token
bot = telebot.TeleBot(API_TOKEN)

# Fonts
FONTS_DIR = "fonts"
try:
    TITLE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf"), 110)
    BOLD_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 30)
    MEDIUM_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Medium.ttf"), 25)
    REG_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Regular.ttf"), 22)
    GENRE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Condensed-Bold.ttf"), 26) # Fallback to Roboto-Bold if not found
except:
    # Try finding condensed
    try:
        GENRE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto_Condensed-Bold.ttf"), 26)
    except:
        try:
             GENRE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 26)
        except:
             GENRE_FONT = ImageFont.load_default()

    try:
        TITLE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf"), 110)
    except:
        TITLE_FONT = ImageFont.load_default()

    try:
        BOLD_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 30)
        MEDIUM_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Medium.ttf"), 25)
        REG_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Regular.ttf"), 22)
    except:
        BOLD_FONT = MEDIUM_FONT = REG_FONT = ImageFont.load_default()

LOGO_FONT = BOLD_FONT

BG_PATH = "hex_bg.png"
CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720

# Colors
BG_COLOR = (15, 20, 35) # Dark Blue/Black
HEX_OUTLINE = (40, 50, 70)  # Faint outline for background
TEXT_COLOR = (255, 255, 255)
SUBTEXT_COLOR = (200, 200, 200)
GENRE_COLOR = (100, 110, 130)
BUTTON_BG = (25, 30, 45) # Dark button bg
LOGO_COLOR = (255, 255, 255)
HONEYCOMB_OUTLINE_COLOR = (200, 220, 255) # Light outline for poster honeycombs

# Helper Functions
def draw_regular_polygon(draw, center, radius, n_sides=6, rotation=30, fill=None, outline=None, width=1):
    points = []
    for i in range(n_sides):
        angle = math.radians(rotation + 360 / n_sides * i)
        x = center[0] + radius * math.cos(angle)
        y = center[1] + radius * math.sin(angle)
        points.append((x, y))
    if fill:
        draw.polygon(points, fill=fill)
    if outline:
        draw.polygon(points, outline=outline, width=width)

def generate_hex_background():
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Background Grid (Left side mainly)
    # Use larger hexagons
    hex_radius = 60
    import math
    dx = math.sqrt(3) * hex_radius
    dy = 1.5 * hex_radius

    cols = int(CANVAS_WIDTH / dx) + 2
    rows = int(CANVAS_HEIGHT / dy) + 2

    for row in range(rows):
        for col in range(cols):
            cx = col * dx
            cy = row * dy
            if row % 2 == 1:
                cx += dx / 2

            # Draw faint outline
            draw_regular_polygon(draw, (cx, cy), hex_radius, outline=HEX_OUTLINE, width=2)

    return img

def wrap_text(text, font, max_width):
    # Estimate characters per line
    avg_char_width = font.getlength('x')
    chars_per_line = int(max_width / avg_char_width)
    wrapped = textwrap.fill(text, width=chars_per_line)
    return wrapped.split('\n')

def generate_thumbnail(anime):
    title = anime['title']['english'] or anime['title']['romaji']
    poster_url = anime['coverImage']['extraLarge']
    score = anime['averageScore']
    genres = anime['genres'][:3]
    desc = (anime['description'] or "").replace("<br>", " ").replace("<i>", "").replace("</i>", "")
    desc = " ".join(desc.split()[:50]) + "..."

    # Background
    bg = generate_hex_background()
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 1. Logo (Top Left)
    icon_x, icon_y = 50, 40
    # Simple diamond shape icon for logo
    # Draw two overlapping diamonds/squares
    sz = 12
    draw.polygon([(icon_x, icon_y+sz), (icon_x+sz, icon_y), (icon_x+2*sz, icon_y+sz), (icon_x+sz, icon_y+2*sz)], outline=LOGO_COLOR, width=3)
    draw.polygon([(icon_x+8, icon_y+sz), (icon_x+sz+8, icon_y), (icon_x+2*sz+8, icon_y+sz), (icon_x+sz+8, icon_y+2*sz)], outline=LOGO_COLOR, width=3)

    draw.text((icon_x + 50, icon_y), "ANIME FLICKER", font=MEDIUM_FONT, fill=LOGO_COLOR)

    # 2. Rating (Below Logo)
    if score:
        rating_text = f"{score/10:.1f}+ Rating"
        draw.text((50, 130), rating_text, font=REG_FONT, fill=TEXT_COLOR)

    # 3. Title (Large, Below Rating)
    title_lines = wrap_text(title.upper(), TITLE_FONT, 600)
    title_y = 170
    for line in title_lines[:2]:
        draw.text((50, title_y), line, font=TITLE_FONT, fill=TEXT_COLOR)
        title_y += 110 # Line height

    # 4. Genres (Below Title)
    genre_text = ", ".join(genres).upper()
    draw.text((50, title_y + 10), genre_text, font=GENRE_FONT, fill=GENRE_COLOR)

    # 5. Description (Below Genres)
    desc_y = title_y + 60
    desc_lines = wrap_text(desc, REG_FONT, 500)
    for line in desc_lines[:6]:
        draw.text((50, desc_y), line, font=REG_FONT, fill=SUBTEXT_COLOR)
        desc_y += 30

    # 6. Buttons (Bottom Left)
    btn_y = 620
    btn_width = 160
    btn_height = 50

    # Button 1: DOWNLOAD
    draw.rounded_rectangle((50, btn_y, 50 + btn_width, btn_y + btn_height), radius=5, fill=BUTTON_BG)
    text_w = BOLD_FONT.getlength("DOWNLOAD")
    text_x = 50 + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 10), "DOWNLOAD", font=BOLD_FONT, fill=TEXT_COLOR)

    # Button 2: JOIN NOW
    btn2_x = 50 + btn_width + 40
    draw.rounded_rectangle((btn2_x, btn_y, btn2_x + btn_width, btn_y + btn_height), radius=5, fill=BUTTON_BG)
    text_w = BOLD_FONT.getlength("JOIN NOW")
    text_x = btn2_x + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 10), "JOIN NOW", font=BOLD_FONT, fill=TEXT_COLOR)


    # 7. Right Side Honeycomb Poster
    # Fetch poster
    poster_resp = requests.get(poster_url)
    poster = Image.open(BytesIO(poster_resp.content)).convert("RGBA")

    # Define area
    collage_x = 550
    collage_width = CANVAS_WIDTH - collage_x
    collage_height = CANVAS_HEIGHT

    # Resize/Crop poster
    aspect = poster.width / poster.height
    target_aspect = collage_width / collage_height

    if aspect > target_aspect:
        new_height = collage_height
        new_width = int(new_height * aspect)
        poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
        left = (new_width - collage_width) // 2
        poster = poster.crop((left, 0, left + collage_width, new_height))
    else:
        new_width = collage_width
        new_height = int(new_width / aspect)
        poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
        top = (new_height - collage_height) // 2
        poster = poster.crop((0, top, collage_width, top + collage_height))

    # Create Honeycomb Pattern
    # We will draw the honeycombs on a mask, but also draw the outlines on an overlay.

    mask = Image.new("L", (collage_width, collage_height), 0)
    mask_draw = ImageDraw.Draw(mask)

    overlay = Image.new("RGBA", (collage_width, collage_height), (0,0,0,0))
    overlay_draw = ImageDraw.Draw(overlay)

    hex_radius = 85 # Larger hexagons
    gap = 4

    dx = math.sqrt(3) * hex_radius
    dy = 1.5 * hex_radius

    cols = int(collage_width / dx) + 2
    rows = int(collage_height / dy) + 2

    # Start drawing from slightly outside to cover edges
    for row in range(-1, rows):
        for col in range(-1, cols):
            cx = col * dx
            cy = row * dy
            if row % 2 == 1:
                cx += dx / 2

            # Center in the collage area
            # Adjust offset to align nicely?

            # Draw hexagon on mask (filled white)
            # Make the mask slightly smaller than full size to leave room for outline?
            # Or make the mask full size and draw outline on top?
            # User image shows outlines BETWEEN images.
            # So the gaps between mask hexagons should be transparent?
            # If gap > 0, then there is space between images.

            draw_regular_polygon(mask_draw, (cx, cy), hex_radius - gap, fill=255)

            # Draw outline on overlay
            # The outline should be around the hexagon.
            # Thick outline.
            draw_regular_polygon(overlay_draw, (cx, cy), hex_radius - gap, outline=HONEYCOMB_OUTLINE_COLOR, width=4)

    # Apply mask to poster
    poster.putalpha(mask)

    # Paste poster
    canvas.paste(poster, (collage_x, 0), poster)

    # Paste overlay (outlines)
    canvas.paste(overlay, (collage_x, 0), overlay)

    # Final
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
