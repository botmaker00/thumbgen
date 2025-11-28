# thumbnail_bot.py - Final AnimeFlicker Exact Match Generator
import telebot
import requests
import os
import math
from PIL import Image, ImageDraw, ImageFont
import textwrap
from io import BytesIO

# ⚠️ YAHAN APNA NAYA TOKEN DAALNA (purana wala mat daalna)
API_TOKEN = os.getenv("BOT_TOKEN", "7597391690:AAFdUlJBP46IJNvkaM6vIhW6J1fbmUTlkjA")  # ← ABHI KE LIYE RAKH RAHA, PAR NAYA BANA KE CHANGE KAR DENA
bot = telebot.TeleBot(API_TOKEN)

# Fonts (fonts folder bana ke daal do)
FONTS_DIR = "fonts"
try:
    TITLE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "BebasNeue-Regular.ttf"), 110)
    BOLD_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 30)
    MEDIUM_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Medium.ttf"), 25)
    REG_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Regular.ttf"), 22)
    # Using Roboto-Condensed-Bold or similar if possible for genre, else Roboto-Bold
    # Falling back to Roboto-Bold for Genre if coolvetica is missing
    GENRE_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 26)
    LOGO_FONT = ImageFont.truetype(os.path.join(FONTS_DIR, "Roboto-Bold.ttf"), 28)
except:
    TITLE_FONT = BOLD_FONT = MEDIUM_FONT = REG_FONT = GENRE_FONT = LOGO_FONT = ImageFont.load_default()

BG_PATH = "hex_bg.png"
CANVAS_WIDTH, CANVAS_HEIGHT = 1280, 720

# Colors exact from example
BG_COLOR = (20, 25, 40)
HEX_OUTLINE = (35, 40, 60)  # Darker outline
DEC_HEX_FILL = (112, 124, 140)
TEXT_COLOR = (255, 255, 255)
SUBTEXT_COLOR = (200, 200, 200)
GENRE_COLOR = (80, 80, 100) # Dark text for genres like in the image
BUTTON_LEFT = (20, 20, 30) # Dark bg
BUTTON_RIGHT = (20, 20, 30) # Dark bg
LOGO_COLOR = (255, 255, 255)

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

def create_honeycomb_mask(size, hex_radius=70, gap=5):
    """
    Creates a mask with a honeycomb pattern covering the area.
    """
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)

    # Calculate spacing
    # Horizontal distance between centers is sqrt(3) * radius
    # Vertical distance between centers is 1.5 * radius

    import math

    width, height = size

    dx = math.sqrt(3) * hex_radius
    dy = 1.5 * hex_radius

    cols = int(width / dx) + 2
    rows = int(height / dy) + 2

    for row in range(rows):
        for col in range(cols):
            cx = col * dx
            cy = row * dy

            # Offset every odd row
            if row % 2 == 1:
                cx += dx / 2

            # Draw hexagon filled with white (opaque)
            # Adjust radius slightly to create gaps (outline effect)
            draw_regular_polygon(draw, (cx, cy), hex_radius - gap, fill=255)

    return mask

def generate_hex_background():
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Exact hex grid from example
    for x in range(0, 1300, 120):
        for y in range(0, 800, 104):
            center = (x + 60, y + 52)
            draw_regular_polygon(draw, center, 58, outline=HEX_OUTLINE, width=2)

    # Draw left side gradient or overlay to make text readable?
    # The image has a fairly clean dark background on the left.

    return img

def wrap_text(text, font, max_width):
    lines = []
    # Use textwrap
    # Estimate characters per line
    avg_char_width = font.getlength('x')
    chars_per_line = int(max_width / avg_char_width)

    wrapped = textwrap.fill(text, width=chars_per_line)
    return wrapped.split('\n')

def generate_thumbnail(anime):
    title = anime['title']['english'] or anime['title']['romaji']
    poster_url = anime['coverImage']['extraLarge']
    score = anime['averageScore']
    genres = anime['genres'][:3] # Only first 3 usually fit well
    desc = (anime['description'] or "").replace("<br>", " ").replace("<i>", "").replace("</i>", "")
    desc = " ".join(desc.split()[:50]) + "..."

    # Background
    bg = generate_hex_background()
    canvas = bg.copy()
    draw = ImageDraw.Draw(canvas)

    # 1. Logo (Top Left)
    # Drawing a simple icon for logo
    icon_x, icon_y = 50, 40
    # Simple diamond shape icon
    draw.polygon([(icon_x, icon_y+10), (icon_x+10, icon_y), (icon_x+20, icon_y+10), (icon_x+10, icon_y+20)], outline=LOGO_COLOR, width=2)
    draw.polygon([(icon_x+8, icon_y+10), (icon_x+18, icon_y), (icon_x+28, icon_y+10), (icon_x+18, icon_y+20)], outline=LOGO_COLOR, width=2)
    draw.text((icon_x + 40, icon_y - 2), "ANIME FLICKER", font=LOGO_FONT, fill=LOGO_COLOR)

    # 2. Rating (Below Logo)
    if score:
        rating_text = f"{score/10:.1f}+ Rating"
        draw.text((50, 140), rating_text, font=MEDIUM_FONT, fill=TEXT_COLOR)

    # 3. Title (Large, Below Rating)
    # Text wrapping for Title if it's too long
    # We allow 2 lines max
    title_lines = wrap_text(title.upper(), TITLE_FONT, 600)
    title_y = 180
    for line in title_lines[:2]:
        draw.text((50, title_y), line, font=TITLE_FONT, fill=TEXT_COLOR)
        title_y += 100

    # 4. Genres (Below Title)
    # Dark text like "COMEDY, DRAMA, SPORTS"
    genre_text = ", ".join(genres).upper()
    # In the image, this text is dark grey/black? No, "COMEDY, DRAMA, SPORTS" looks like dark grey on dark background?
    # Actually checking the image again (mentally), it's visible. Maybe it's a lighter grey or a specific color.
    # The code snippet said GENRE_COLOR = (170, 170, 255), but I changed it to (80, 80, 100).
    # Let's use a slightly more visible grey.
    GENRE_TEXT_COLOR = (100, 110, 130) # Greyish
    draw.text((50, title_y + 10), genre_text, font=GENRE_FONT, fill=GENRE_TEXT_COLOR)

    # 5. Description (Below Genres)
    desc_y = title_y + 60
    desc_lines = wrap_text(desc, REG_FONT, 500)
    for line in desc_lines[:6]: # Max 6 lines
        draw.text((50, desc_y), line, font=REG_FONT, fill=SUBTEXT_COLOR)
        desc_y += 30

    # 6. Buttons (Bottom Left)
    btn_y = 600
    btn_width = 160
    btn_height = 50

    # Button 1: DOWNLOAD
    draw.rounded_rectangle((50, btn_y, 50 + btn_width, btn_y + btn_height), radius=5, fill=BUTTON_LEFT)
    # Center text
    text_w = BOLD_FONT.getlength("DOWNLOAD")
    text_x = 50 + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 10), "DOWNLOAD", font=BOLD_FONT, fill=TEXT_COLOR)

    # Button 2: JOIN NOW
    btn2_x = 50 + btn_width + 40
    draw.rounded_rectangle((btn2_x, btn_y, btn2_x + btn_width, btn_y + btn_height), radius=5, fill=BUTTON_RIGHT)
    text_w = BOLD_FONT.getlength("JOIN NOW")
    text_x = btn2_x + (btn_width - text_w) / 2
    draw.text((text_x, btn_y + 10), "JOIN NOW", font=BOLD_FONT, fill=TEXT_COLOR)


    # 7. Right Side Honeycomb Poster
    # Fetch poster
    poster_resp = requests.get(poster_url)
    poster = Image.open(BytesIO(poster_resp.content)).convert("RGBA")

    # Define area for the honeycomb collage (Right side)
    # Let's say from x=600 to 1280, y=0 to 720
    collage_width = 1280 - 550
    collage_height = 720

    # Resize poster to fill this area (cover)
    # Aspect ratio
    aspect = poster.width / poster.height
    target_aspect = collage_width / collage_height

    if aspect > target_aspect:
        # Poster is wider, crop width
        new_height = collage_height
        new_width = int(new_height * aspect)
        poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Center crop
        left = (new_width - collage_width) // 2
        poster = poster.crop((left, 0, left + collage_width, new_height))
    else:
        # Poster is taller, crop height
        new_width = collage_width
        new_height = int(new_width / aspect)
        poster = poster.resize((new_width, new_height), Image.Resampling.LANCZOS)
        # Center crop
        top = (new_height - collage_height) // 2
        poster = poster.crop((0, top, collage_width, top + collage_height))

    # Create Honeycomb Mask
    # We want the honeycombs to be visible on the right side.
    # We'll create a mask of the same size as the collage area.
    mask = create_honeycomb_mask((collage_width, collage_height), hex_radius=80, gap=4)

    # Apply mask
    poster.putalpha(mask)

    # Paste on canvas
    canvas.paste(poster, (550, 0), poster)

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
    bot.reply_to(msg, "Thumbnail ban raha hai... 10 sec ruk")
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
        bot.reply_to(msg, f"Error: {e}\nBot restart kar ya font daal")

if __name__ == "__main__":
    print("Bot chal gaya!")
    bot.infinity_polling()
