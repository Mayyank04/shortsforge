import os, math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import numpy as np

W, H = 1080, 1920

# Safe zone boundaries for vertical short-form video (1080x1920):
# Margins: 90px left/right, top header safe area >= 200px, bottom UI safe area >= 320px
SAFE_X_MIN = 90
SAFE_X_MAX = 990
SAFE_Y_CAPTION_MIN = 1140
SAFE_Y_CAPTION_MAX = 1580

PALETTES = [
    ((12, 20, 42), (28, 80, 195)),    # Scene 0: Midnight to Sapphire
    ((36, 14, 56), (175, 45, 110)),   # Scene 1: Deep Plum to Neon Rose
    ((8, 40, 48), (14, 145, 130)),    # Scene 2: Obsidian Teal to Vivid Emerald
    ((48, 24, 14), (200, 95, 26)),    # Scene 3: Charcoal to Amber Gold
    ((16, 22, 64), (45, 140, 195)),   # Scene 4: Royal Indigo to Cyan
    ((52, 16, 44), (185, 62, 98)),    # Scene 5: Velvet Violet to Coral
]

def font(size: int, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except OSError:
                pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()

def wrap_text_to_width(text: str, f: ImageFont.ImageFont, max_width: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.strip().split()
    if not words:
        return []
    lines = []
    current: list[str] = []
    for word in words:
        test_line = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test_line, font=f)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
                current = [word]
            else:
                # Break long single word character by character if it exceeds max_width
                accum = ""
                for ch in word:
                    test_ch = accum + ch
                    bb = draw.textbbox((0, 0), test_ch, font=f)
                    if bb[2] - bb[0] <= max_width:
                        accum = test_ch
                    else:
                        if accum:
                            lines.append(accum)
                        accum = ch
                if accum:
                    current = [accum]
    if current:
        lines.append(" ".join(current))
    return lines

def draw_star(draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, fill: tuple, points: int = 4):
    pts = []
    for i in range(points * 2):
        angle = i * math.pi / points - math.pi / 2
        curr_r = r if i % 2 == 0 else r * 0.42
        pts.append((cx + curr_r * math.cos(angle), cy + curr_r * math.sin(angle)))
    draw.polygon(pts, fill=fill)

def draw_mascot(draw: ImageDraw.ImageDraw, cx: int, cy: int, index: int, style: str):
    r = 165

    # Decorative background orbital rings
    draw.ellipse((cx - 215, cy - 215, cx + 215, cy + 215), outline=(255, 255, 255, 30), width=3)
    draw.ellipse((cx - 245, cy - 245, cx + 245, cy + 245), outline=(255, 255, 255, 18), width=2)

    # 3D shadow or layered depth underneath
    draw.ellipse((cx - r + 8, cy - r + 14, cx + r + 8, cy + r + 14), fill=(0, 0, 0, 75))

    # Base head fill
    base_color = (255, 210, 118)
    outline_color = (20, 24, 34)
    outline_w = 11 if style == "2d" else 9
    draw.ellipse((cx - r, cy - r, cx + r, cy + r), fill=base_color, outline=outline_color, width=outline_w)

    # Style-specific depth
    if style == "3d":
        # Specular reflection / 3D sphere gradient highlight
        draw.ellipse((cx - 105, cy - 115, cx - 15, cy - 25), fill=(255, 255, 255, 95))
        draw.ellipse((cx - 85, cy - 95, cx - 40, cy - 50), fill=(255, 255, 255, 140))
        # Ambient bottom-rim shadow
        draw.arc((cx - r + 10, cy - r + 10, cx + r - 10, cy + r - 10), 40, 140, fill=(195, 135, 55, 180), width=18)
    elif style == "2d":
        # Cel-shade crescent
        draw.arc((cx - r + 8, cy - r + 8, cx + r - 8, cy + r - 8), 35, 145, fill=(230, 175, 75, 255), width=22)
        # Rosy cute cheeks
        draw.ellipse((cx - 115, cy + 18, cx - 65, cy + 48), fill=(255, 130, 130, 180))
        draw.ellipse((cx + 65, cy + 18, cx + 115, cy + 48), fill=(255, 130, 130, 180))
    else:  # mixed
        draw.ellipse((cx - 95, cy - 105, cx - 30, cy - 40), fill=(255, 255, 255, 90))
        draw.ellipse((cx - 110, cy + 20, cx - 65, cy + 46), fill=(255, 135, 135, 150))
        draw.ellipse((cx + 65, cy + 20, cx + 110, cy + 46), fill=(255, 135, 135, 150))

    # Dynamic expressions and scene accents per index
    step = index % 6
    if step == 0:
        # Scene 0 (Hook): Curious wide eyes + sparkle accent
        draw.ellipse((cx - 75, cy - 50, cx - 25, cy + 5), fill=outline_color)
        draw.ellipse((cx + 25, cy - 50, cx + 75, cy + 5), fill=outline_color)
        draw.ellipse((cx - 62, cy - 42, cx - 45, cy - 25), fill=(255, 255, 255))
        draw.ellipse((cx + 38, cy - 42, cx + 55, cy - 25), fill=(255, 255, 255))
        # Eyebrows raised
        draw.arc((cx - 85, cy - 85, cx - 20, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.arc((cx + 20, cy - 85, cx + 85, cy - 45), 200, 340, fill=outline_color, width=7)
        # Open smile
        draw.chord((cx - 60, cy + 15, cx + 60, cy + 85), 0, 180, fill=(210, 50, 65), outline=outline_color, width=7)
        # Sparkle star
        draw_star(draw, cx + 190, cy - 110, 36, (255, 225, 80, 240))
        draw_star(draw, cx - 185, cy - 130, 24, (255, 255, 255, 200))
    elif step == 1:
        # Scene 1 (Twist / Discovery): Surprised/wonder expression + lightbulb spark
        draw.ellipse((cx - 75, cy - 55, cx - 20, cy + 8), fill=outline_color)
        draw.ellipse((cx + 25, cy - 45, cx + 75, cy + 5), fill=outline_color)
        draw.ellipse((cx - 60, cy - 45, cx - 40, cy - 25), fill=(255, 255, 255))
        draw.ellipse((cx + 40, cy - 38, cx + 55, cy - 23), fill=(255, 255, 255))
        # Arched quizzical eyebrow
        draw.arc((cx - 85, cy - 100, cx - 15, cy - 50), 190, 350, fill=outline_color, width=8)
        draw.arc((cx + 20, cy - 75, cx + 80, cy - 45), 200, 340, fill=outline_color, width=7)
        # Wonder mouth
        draw.ellipse((cx - 24, cy + 25, cx + 24, cy + 70), fill=(210, 50, 65), outline=outline_color, width=7)
        # Spark of inspiration above head
        draw_star(draw, cx, cy - 215, 34, (255, 220, 70, 255))
        draw.line((cx, cy - 245, cx, cy - 265), fill=(255, 220, 70, 200), width=5)
        draw.line((cx - 28, cy - 235, cx - 45, cy - 252), fill=(255, 220, 70, 200), width=5)
        draw.line((cx + 28, cy - 235, cx + 45, cy - 252), fill=(255, 220, 70, 200), width=5)
    elif step == 2:
        # Scene 2 (Challenge / Conflict): Focused determined expression
        draw.ellipse((cx - 70, cy - 45, cx - 25, cy), fill=outline_color)
        draw.ellipse((cx + 25, cy - 45, cx + 70, cy), fill=outline_color)
        draw.ellipse((cx - 55, cy - 40, cx - 40, cy - 25), fill=(255, 255, 255))
        draw.ellipse((cx + 40, cy - 40, cx + 55, cy - 25), fill=(255, 255, 255))
        # Focused slanted eyebrows
        draw.line((cx - 80, cy - 70, cx - 20, cy - 50), fill=outline_color, width=8)
        draw.line((cx + 80, cy - 70, cx + 20, cy - 50), fill=outline_color, width=8)
        # Determined smirk
        draw.arc((cx - 50, cy + 10, cx + 50, cy + 65), 20, 160, fill=outline_color, width=8)
        # Dynamic energy streak lines
        draw.line((cx - 250, cy - 40, cx - 200, cy - 40), fill=(255, 255, 255, 130), width=4)
        draw.line((cx - 260, cy, cx - 205, cy), fill=(255, 255, 255, 170), width=5)
        draw.line((cx + 200, cy - 40, cx + 250, cy - 40), fill=(255, 255, 255, 130), width=4)
        draw.line((cx + 205, cy, cx + 260, cy), fill=(255, 255, 255, 170), width=5)
    elif step == 3:
        # Scene 3 (Turning Point): Starry excited eyes + energy diamonds
        draw_star(draw, cx - 50, cy - 25, 24, (30, 35, 45), points=4)
        draw_star(draw, cx + 50, cy - 25, 24, (30, 35, 45), points=4)
        draw.arc((cx - 80, cy - 80, cx - 20, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.arc((cx + 20, cy - 80, cx + 80, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.chord((cx - 55, cy + 18, cx + 55, cy + 85), 0, 180, fill=(210, 50, 65), outline=outline_color, width=8)
        draw_star(draw, cx - 180, cy - 100, 28, (255, 215, 60, 240))
        draw_star(draw, cx + 180, cy - 100, 28, (255, 215, 60, 240))
        draw_star(draw, cx - 170, cy + 80, 20, (255, 255, 255, 190))
        draw_star(draw, cx + 170, cy + 80, 20, (255, 255, 255, 190))
    elif step == 4:
        # Scene 4 (Surprise / Revelation): Big joyful smile + burst sparkles
        draw.arc((cx - 75, cy - 50, cx - 25, cy - 5), 180, 360, fill=outline_color, width=9)
        draw.arc((cx + 25, cy - 50, cx + 75, cy - 5), 180, 360, fill=outline_color, width=9)
        draw.arc((cx - 80, cy - 80, cx - 20, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.arc((cx + 20, cy - 80, cx + 80, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.chord((cx - 65, cy + 15, cx + 65, cy + 90), 0, 180, fill=(220, 55, 70), outline=outline_color, width=8)
        draw_star(draw, cx + 195, cy - 90, 32, (255, 225, 75, 250))
        draw_star(draw, cx - 195, cy + 30, 26, (255, 255, 255, 210))
    else:
        # Scene 5 (Payoff / Conclusion): Confident wink + champion gold star
        # Left eye winking
        draw.line((cx - 75, cy - 25, cx - 25, cy - 25), fill=outline_color, width=9)
        draw.line((cx - 75, cy - 25, cx - 50, cy - 10), fill=outline_color, width=8)
        # Right eye open with sparkle
        draw.ellipse((cx + 25, cy - 50, cx + 75, cy + 5), fill=outline_color)
        draw.ellipse((cx + 40, cy - 42, cx + 58, cy - 24), fill=(255, 255, 255))
        # Eyebrows
        draw.arc((cx - 80, cy - 75, cx - 20, cy - 45), 200, 340, fill=outline_color, width=7)
        draw.arc((cx + 20, cy - 85, cx + 80, cy - 45), 200, 340, fill=outline_color, width=7)
        # Proud warm smile
        draw.arc((cx - 65, cy + 10, cx + 65, cy + 80), 10, 170, fill=outline_color, width=9)
        # Star medal badge below head
        draw_star(draw, cx, cy + 185, 38, (255, 215, 60, 255))
        draw.ellipse((cx - 14, cy + 171, cx + 14, cy + 199), fill=(230, 150, 20))

def make_scene(text: str, index: int, style: str, output: Path):
    top, bottom = PALETTES[index % len(PALETTES)]

    # Fast smooth vertical gradient using numpy
    top_arr = np.array(top, dtype=float)
    bot_arr = np.array(bottom, dtype=float)
    t = np.linspace(0.0, 1.0, H)[:, None]
    col = (top_arr * (1.0 - t) + bot_arr * t).astype(np.uint8)
    img_arr = np.tile(col[:, None, :], (1, W, 1))
    im = Image.fromarray(img_arr)

    d = ImageDraw.Draw(im, "RGBA")

    # Layered ambient background bokeh / depth circles
    for j in range(6):
        radius = 80 + j * 38
        bx = (index * 179 + j * 211) % W
        by = 380 + ((j * 227 + index * 83) % 860)
        d.ellipse(
            (bx - radius, by - radius, bx + radius, by + radius),
            fill=(255, 255, 255, 10),
            outline=(255, 255, 255, 22),
            width=2,
        )

    # Top progress bar (Instagram / Shorts story segments)
    # Stays within safe width [90, 990] at y = 210..216
    bar_y0, bar_y1 = 210, 216
    total_segments = 6
    seg_gap = 10
    total_available_w = SAFE_X_MAX - SAFE_X_MIN
    seg_w = (total_available_w - (total_segments - 1) * seg_gap) // total_segments
    for s in range(total_segments):
        sx0 = SAFE_X_MIN + s * (seg_w + seg_gap)
        sx1 = sx0 + seg_w
        if s < (index % 6):
            # Completed scene: warm gold
            d.rounded_rectangle((sx0, bar_y0, sx1, bar_y1), radius=3, fill=(255, 215, 70, 240))
        elif s == (index % 6):
            # Active scene: glowing white
            d.rounded_rectangle((sx0, bar_y0 - 1, sx1, bar_y1 + 1), radius=4, fill=(255, 255, 255, 255))
        else:
            # Upcoming scene: muted semi-transparent
            d.rounded_rectangle((sx0, bar_y0, sx1, bar_y1), radius=3, fill=(255, 255, 255, 60))

    # Top category & progress badges (Safe y: 236..288)
    badge_style = "2D CARTOON" if style == "2d" else ("3D DEPTH" if style == "3d" else "SHORTFORGE STORY")
    d.rounded_rectangle((SAFE_X_MIN, 236, SAFE_X_MIN + 340, 288), radius=26, fill=(255, 210, 65, 245))
    d.text((SAFE_X_MIN + 22, 248), badge_style, font=font(24, bold=True), fill=(20, 24, 34))

    # Scene counter badge on top-right
    step_num = (index % 6) + 1
    counter_text = f"0{step_num} / 06"
    counter_box_w = 130
    counter_x0 = SAFE_X_MAX - counter_box_w
    d.rounded_rectangle((counter_x0, 236, SAFE_X_MAX, 288), radius=26, fill=(12, 17, 30, 190), outline=(255, 255, 255, 70), width=2)
    d.text((counter_x0 + 20, 249), counter_text, font=font(22, bold=True), fill=(240, 244, 255))

    # Main character / scene artwork (Center: cx = 540, cy = 760)
    draw_mascot(d, 540, 760, index, style)

    # ---------------------------------------------------------
    # Caption card and dynamic typography with safe margins
    # Guaranteed bounds:
    #   Horizontal: [SAFE_X_MIN, SAFE_X_MAX] -> [90, 990] (width 900)
    #   Vertical: [SAFE_Y_CAPTION_MIN, SAFE_Y_CAPTION_MAX] -> [1140, 1580]
    #   Bottom clearance: >= 340px from bottom edge (1920 - 1580)
    # ---------------------------------------------------------
    card_x0, card_x1 = SAFE_X_MIN, SAFE_X_MAX
    card_w = card_x1 - card_x0  # 900px
    pad_h = 44                  # inner horizontal padding
    pad_v = 34                  # inner vertical padding
    max_text_w = card_w - (pad_h * 2)  # 812px max text width
    max_text_h = (SAFE_Y_CAPTION_MAX - SAFE_Y_CAPTION_MIN) - (pad_v * 2)  # 372px

    # Determine optimal font size and wrapped lines
    candidate_sizes = [52, 46, 42, 38, 34, 30]
    chosen_font = None
    chosen_lines: list[str] = []
    chosen_line_h = 0

    for sz in candidate_sizes:
        f = font(sz, bold=True)
        lines = wrap_text_to_width(text, f, max_text_w, d)
        lh = int(sz * 1.34)
        total_h = len(lines) * lh
        if total_h <= max_text_h and len(lines) <= 5:
            chosen_font = f
            chosen_lines = lines
            chosen_line_h = lh
            break

    if not chosen_font:
        chosen_font = font(30, bold=True)
        chosen_lines = wrap_text_to_width(text, chosen_font, max_text_w, d)
        chosen_line_h = int(30 * 1.30)

    total_text_h = len(chosen_lines) * chosen_line_h
    card_h = max(200, min(total_text_h + (pad_v * 2), SAFE_Y_CAPTION_MAX - SAFE_Y_CAPTION_MIN))

    # Center caption card vertically in safe zone [1140, 1580]
    center_y = (SAFE_Y_CAPTION_MIN + SAFE_Y_CAPTION_MAX) // 2  # 1360
    card_y0 = max(SAFE_Y_CAPTION_MIN, center_y - card_h // 2)
    card_y1 = card_y0 + card_h
    if card_y1 > SAFE_Y_CAPTION_MAX:
        card_y1 = SAFE_Y_CAPTION_MAX
        card_y0 = card_y1 - card_h

    # Card drop shadow
    d.rounded_rectangle((card_x0, card_y0 + 10, card_x1, card_y1 + 10), radius=32, fill=(0, 0, 0, 95))
    # Frosted dark slate card container
    d.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=32, fill=(10, 16, 28, 225), outline=(255, 255, 255, 75), width=3)

    # Render text lines centered horizontally inside card
    text_y = card_y0 + (card_h - total_text_h) // 2
    for line_idx, line in enumerate(chosen_lines):
        line_bbox = d.textbbox((0, 0), line, font=chosen_font)
        line_w = line_bbox[2] - line_bbox[0]
        line_x = (W - line_w) // 2

        # Draw subtle black outline / drop shadow for 100% legibility
        d.text((line_x + 2, text_y + 2), line, font=chosen_font, fill=(0, 0, 0, 220))

        # First line gets modern golden highlight on opening 1-2 words
        if line_idx == 0:
            words = line.split()
            if len(words) >= 2:
                hook_words = " ".join(words[:2]) + " "
                rest_words = " ".join(words[2:])
                hook_bb = d.textbbox((0, 0), hook_words, font=chosen_font)
                hook_w = hook_bb[2] - hook_bb[0]

                # Hook words in vibrant gold
                d.text((line_x, text_y), hook_words, font=chosen_font, fill=(255, 218, 75))
                # Rest in clean white
                d.text((line_x + hook_w, text_y), rest_words, font=chosen_font, fill=(255, 255, 255))
            else:
                d.text((line_x, text_y), line, font=chosen_font, fill=(255, 218, 75))
        else:
            d.text((line_x, text_y), line, font=chosen_font, fill=(255, 255, 255))

        text_y += chosen_line_h

    # Ensure output parent directory exists and save
    output.parent.mkdir(parents=True, exist_ok=True)
    im.save(output, quality=95)
