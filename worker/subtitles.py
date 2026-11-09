"""
Dynamic typography, subtitle cards, and graphical overlays for geography shorts.
Guarantees strict safe margins and high readability for vertical format (1080x1920).
"""
from __future__ import annotations
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

W, H = 1080, 1920
SAFE_X_MIN = 90
SAFE_X_MAX = 990
SAFE_Y_TOP = 200
SAFE_Y_CAPTION_MIN = 1140
SAFE_Y_CAPTION_MAX = 1580

def get_font(size: int, bold: bool = True) -> ImageFont.ImageFont:
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

def wrap_text_to_width(text: str, font_obj: ImageFont.ImageFont, max_w: int, draw: ImageDraw.ImageDraw) -> list[str]:
    words = text.strip().split()
    if not words:
        return []
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        test = " ".join(current + [word])
        bbox = draw.textbbox((0, 0), test, font=font_obj)
        if bbox[2] - bbox[0] <= max_w:
            current.append(word)
        else:
            if current:
                lines.append(" ".join(current))
                current = [word]
            else:
                lines.append(word)
    if current:
        lines.append(" ".join(current))
    return lines

def render_scene_overlay(
    base_image: Image.Image,
    scene_index: int,
    total_scenes: int,
    narration_text: str,
    badge_text: str = "",
    headline_text: str = "",
    stat_callout: str = "",
    target_region: str = "",
    output_path: Path | None = None
) -> Image.Image:
    """
    Renders top story progress segments, category badges, location coordinates,
    stat callouts, and the centered safe subtitle card over the 3D scene image.
    """
    im = base_image.copy().convert("RGBA")
    draw = ImageDraw.Draw(im, "RGBA")

    # 1. Top Story Progress Bar (Instagram / TikTok story segments)
    bar_y0, bar_y1 = 210, 216
    total_available_w = SAFE_X_MAX - SAFE_X_MIN
    seg_gap = 8
    total_segments = max(total_scenes, 1)
    seg_w = (total_available_w - (total_segments - 1) * seg_gap) // total_segments

    for s in range(total_segments):
        sx0 = SAFE_X_MIN + s * (seg_w + seg_gap)
        sx1 = sx0 + seg_w
        if s < scene_index:
            draw.rounded_rectangle((sx0, bar_y0, sx1, bar_y1), radius=3, fill=(255, 215, 60, 240))
        elif s == scene_index:
            draw.rounded_rectangle((sx0, bar_y0 - 1, sx1, bar_y1 + 1), radius=4, fill=(255, 255, 255, 255))
        else:
            draw.rounded_rectangle((sx0, bar_y0, sx1, bar_y1), radius=3, fill=(255, 255, 255, 60))

    # 2. Category Eyebrow Badge (Top-left: y = 236..286)
    badge = badge_text or "GEOGRAPHY EXPLAINER"
    b_font = get_font(22, bold=True)
    b_bbox = draw.textbbox((0, 0), badge, font=b_font)
    badge_w = (b_bbox[2] - b_bbox[0]) + 36
    draw.rounded_rectangle((SAFE_X_MIN, 236, SAFE_X_MIN + badge_w, 286), radius=25, fill=(255, 205, 50, 245))
    draw.text((SAFE_X_MIN + 18, 249), badge, font=b_font, fill=(15, 20, 30))

    # Scene Counter Badge (Top-right: y = 236..286)
    counter_txt = f"{scene_index + 1:02d} / {total_scenes:02d}"
    c_bbox = draw.textbbox((0, 0), counter_txt, font=b_font)
    c_w = (c_bbox[2] - c_bbox[0]) + 32
    draw.rounded_rectangle((SAFE_X_MAX - c_w, 236, SAFE_X_MAX, 286), radius=25, fill=(12, 18, 30, 200), outline=(255, 255, 255, 80), width=2)
    draw.text((SAFE_X_MAX - c_w + 16, 249), counter_txt, font=b_font, fill=(240, 245, 255))

    # 3. Location / Headline Banner (y = 300..348)
    if headline_text or target_region:
        sub_title = headline_text or target_region
        st_font = get_font(24, bold=True)
        st_bbox = draw.textbbox((0, 0), sub_title, font=st_font)
        st_w = (st_bbox[2] - st_bbox[0]) + 32
        draw.rounded_rectangle((SAFE_X_MIN, 300, min(SAFE_X_MAX, SAFE_X_MIN + st_w), 348), radius=24, fill=(10, 16, 28, 180), outline=(255, 255, 255, 50), width=2)
        draw.text((SAFE_X_MIN + 16, 312), sub_title, font=st_font, fill=(255, 255, 255))

    # 4. Stat Callout Pill (Floating mid-screen accent if present)
    if stat_callout:
        pill_font = get_font(22, bold=True)
        p_bbox = draw.textbbox((0, 0), stat_callout, font=pill_font)
        p_w = (p_bbox[2] - p_bbox[0]) + 36
        draw.rounded_rectangle((SAFE_X_MIN, 1060, SAFE_X_MIN + p_w, 1110), radius=25, fill=(0, 210, 240, 225))
        draw.text((SAFE_X_MIN + 18, 1073), stat_callout, font=pill_font, fill=(10, 20, 35))

    # 5. Caption Card (Guaranteed bounds: [90, 990], [1140, 1580])
    card_x0, card_x1 = SAFE_X_MIN, SAFE_X_MAX
    card_w = card_x1 - card_x0  # 900px
    pad_h = 44
    pad_v = 34
    max_text_w = card_w - (pad_h * 2)  # 812px
    max_text_h = (SAFE_Y_CAPTION_MAX - SAFE_Y_CAPTION_MIN) - (pad_v * 2)  # 372px

    candidate_sizes = [50, 44, 40, 36, 32, 28]
    chosen_font = None
    chosen_lines: list[str] = []
    chosen_line_h = 0

    for sz in candidate_sizes:
        f = get_font(sz, bold=True)
        lines = wrap_text_to_width(narration_text, f, max_text_w, draw)
        lh = int(sz * 1.34)
        if len(lines) * lh <= max_text_h and len(lines) <= 5:
            chosen_font = f
            chosen_lines = lines
            chosen_line_h = lh
            break

    if not chosen_font:
        chosen_font = get_font(28, bold=True)
        chosen_lines = wrap_text_to_width(narration_text, chosen_font, max_text_w, draw)
        chosen_line_h = int(28 * 1.30)

    total_text_h = len(chosen_lines) * chosen_line_h
    card_h = max(180, min(total_text_h + (pad_v * 2), SAFE_Y_CAPTION_MAX - SAFE_Y_CAPTION_MIN))

    center_y = (SAFE_Y_CAPTION_MIN + SAFE_Y_CAPTION_MAX) // 2
    card_y0 = max(SAFE_Y_CAPTION_MIN, center_y - card_h // 2)
    card_y1 = card_y0 + card_h

    # Card Drop Shadow
    draw.rounded_rectangle((card_x0, card_y0 + 10, card_x1, card_y1 + 10), radius=32, fill=(0, 0, 0, 110))
    # Frosted Slate Card Surface
    draw.rounded_rectangle((card_x0, card_y0, card_x1, card_y1), radius=32, fill=(8, 14, 25, 230), outline=(255, 255, 255, 75), width=3)

    # Centered Caption Text with Drop Shadow & Golden Highlight on First Words
    text_y = card_y0 + (card_h - total_text_h) // 2
    for line_idx, line in enumerate(chosen_lines):
        line_bb = draw.textbbox((0, 0), line, font=chosen_font)
        line_w = line_bb[2] - line_bb[0]
        line_x = (W - line_w) // 2

        # Shadow
        draw.text((line_x + 2, text_y + 2), line, font=chosen_font, fill=(0, 0, 0, 240))

        if line_idx == 0:
            words = line.split()
            if len(words) >= 2:
                hook_w = " ".join(words[:2]) + " "
                rest_w = " ".join(words[2:])
                h_bb = draw.textbbox((0, 0), hook_w, font=chosen_font)
                hw = h_bb[2] - h_bb[0]
                draw.text((line_x, text_y), hook_w, font=chosen_font, fill=(255, 218, 75))
                draw.text((line_x + hw, text_y), rest_w, font=chosen_font, fill=(255, 255, 255))
            else:
                draw.text((line_x, text_y), line, font=chosen_font, fill=(255, 218, 75))
        else:
            draw.text((line_x, text_y), line, font=chosen_font, fill=(255, 255, 255))

        text_y += chosen_line_h

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        im.convert("RGB").save(output_path, quality=95)

    return im
