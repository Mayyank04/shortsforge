"""
Dynamic vertical typography and animated subtitles for ShortForge AI Minecraft Studio.
Adheres to strict safe margins (1080x1920) with active word highlights and cinematic pill cards.
"""
from __future__ import annotations
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

from worker.subtitles import get_font, wrap_text_to_width

W, H = 1080, 1920
SAFE_X_MIN = 80
SAFE_X_MAX = 1000
SAFE_Y_MIN = 1240
SAFE_Y_MAX = 1620

def render_minecraft_overlay(
    base_image: Image.Image,
    scene_number: int,
    total_scenes: int,
    narration_text: str,
    active_word: str | None = None,
    genre_badge: str | None = None
) -> Image.Image:
    """
    Renders high-visibility subtitle overlay and scene indicator pill.
    """
    canvas = base_image.convert("RGBA").resize((W, H))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_narr = get_font(52, bold=True)
    font_badge = get_font(28, bold=True)

    # 1. Top Scene Pill
    badge_text = f"SCENE {scene_number}/{total_scenes} · {genre_badge.upper()}" if genre_badge else f"SCENE {scene_number}/{total_scenes}"
    bbox_b = draw.textbbox((0, 0), badge_text, font=font_badge)
    bw = (bbox_b[2] - bbox_b[0]) + 40
    bh = 48
    bx = (W - bw) // 2
    by = 180

    # Frosted pill
    draw.rounded_rectangle((bx, by, bx + bw, by + bh), radius=24, fill=(15, 23, 42, 190), outline=(56, 189, 248, 200), width=2)
    draw.text((bx + 20, by + 10), badge_text, font=font_badge, fill=(240, 249, 255, 240))

    # 2. Subtitles Box
    max_w = SAFE_X_MAX - SAFE_X_MIN - 60
    lines = wrap_text_to_width(narration_text, font_narr, max_w, draw)

    if lines:
        line_h = 68
        total_text_h = len(lines) * line_h
        card_w = max_w + 50
        card_h = total_text_h + 40
        cx = (W - card_w) // 2
        cy = SAFE_Y_MIN + (SAFE_Y_MAX - SAFE_Y_MIN - card_h) // 2

        # Dark backdrop card with cyan/gold accent
        draw.rounded_rectangle(
            (cx, cy, cx + card_w, cy + card_h),
            radius=20,
            fill=(10, 15, 28, 215),
            outline=(245, 200, 76, 180),
            width=2
        )

        for i, line in enumerate(lines):
            line_y = cy + 20 + i * line_h
            bbox_line = draw.textbbox((0, 0), line, font=font_narr)
            lw = bbox_line[2] - bbox_line[0]
            line_x = (W - lw) // 2

            # Render words with optional highlight
            if active_word and active_word.lower() in line.lower():
                # Word-level rendering
                words = line.split()
                cur_x = line_x
                for w in words:
                    is_active = (active_word.lower() in w.lower())
                    color = (245, 200, 76, 255) if is_active else (255, 255, 255, 255)
                    # Text shadow
                    draw.text((cur_x + 2, line_y + 2), w, font=font_narr, fill=(0, 0, 0, 220))
                    draw.text((cur_x, line_y), w, font=font_narr, fill=color)
                    w_box = draw.textbbox((0, 0), w + " ", font=font_narr)
                    cur_x += (w_box[2] - w_box[0])
            else:
                # Text shadow
                draw.text((line_x + 2, line_y + 2), line, font=font_narr, fill=(0, 0, 0, 220))
                draw.text((line_x, line_y), line, font=font_narr, fill=(255, 255, 255, 255))

    return Image.alpha_composite(canvas, overlay).convert("RGB")
