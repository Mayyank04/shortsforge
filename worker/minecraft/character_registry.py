"""
Character registry and reference render generator for ShortForge AI Minecraft Studio.
Provides persistent character profiles, canonical 3D model specifications, and reference images.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .metadata import CanonicalCharacter
from .character_models import CANONICAL_CHARACTERS, get_canonical_character

CHAR_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "minecraft" / "characters"

def ensure_character_assets_dir() -> Path:
    CHAR_ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    return CHAR_ASSETS_DIR

def hex_to_rgb(hex_str: str) -> tuple[int, int, int]:
    clean = hex_str.lstrip("#")
    if len(clean) == 3:
        clean = "".join([c * 2 for c in clean])
    try:
        return (int(clean[0:2], 16), int(clean[2:4], 16), int(clean[4:6], 16))
    except Exception:
        return (100, 100, 100)

def generate_character_reference_image(character: CanonicalCharacter, output_path: Path | None = None) -> Path:
    """
    Renders an isometric-style voxel reference card for the character
    with consistent skin, hair, eyes, and clothing colors.
    """
    ensure_character_assets_dir()
    dest = output_path or (CHAR_ASSETS_DIR / f"{character.id}_reference.png")
    if dest.exists() and dest.stat().st_size > 1000:
        return dest

    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (15, 23, 42, 255))
    draw = ImageDraw.Draw(img)

    skin_rgb = hex_to_rgb(character.skin_tone)
    cloth_primary = hex_to_rgb(character.clothing_primary)
    cloth_sec = hex_to_rgb(character.clothing_secondary)
    hair_rgb = hex_to_rgb(character.hair_color)

    # Subtle background pedestal
    draw.ellipse((106, 380, 406, 460), fill=(30, 41, 59, 255), outline=(51, 65, 85, 255), width=3)

    scale = character.proportions.get("height", 1.8) / 1.8
    cx, base_y = 256, 390

    # Legs (voxel blocks)
    leg_w = int(32 * scale)
    leg_h = int(90 * scale)
    leg_y = base_y - leg_h
    # Left Leg
    draw.rectangle((cx - leg_w - 6, leg_y, cx - 6, base_y), fill=cloth_sec, outline=(0, 0, 0, 200), width=2)
    # Right Leg
    draw.rectangle((cx + 6, leg_y, cx + leg_w + 6, base_y), fill=cloth_sec, outline=(0, 0, 0, 200), width=2)

    # Torso (voxel block)
    torso_w = int(72 * scale)
    torso_h = int(96 * scale)
    torso_y = leg_y - torso_h
    draw.rectangle((cx - torso_w // 2, torso_y, cx + torso_w // 2, leg_y), fill=cloth_primary, outline=(0, 0, 0, 200), width=2)

    # Heart badge if Mini
    if character.id == "mini":
        hx, hy = cx, torso_y + int(torso_h * 0.4)
        draw.polygon([(hx, hy + 12), (hx - 12, hy), (hx - 6, hy - 10), (hx, hy - 4), (hx + 6, hy - 10), (hx + 12, hy)], fill=(239, 68, 68, 255))

    # Arms (voxel blocks)
    arm_w = int(28 * scale)
    arm_h = int(88 * scale)
    # Left arm
    draw.rectangle((cx - torso_w // 2 - arm_w - 2, torso_y, cx - torso_w // 2 - 2, torso_y + arm_h), fill=cloth_primary, outline=(0, 0, 0, 200), width=2)
    draw.rectangle((cx - torso_w // 2 - arm_w - 2, torso_y + arm_h - 20, cx - torso_w // 2 - 2, torso_y + arm_h), fill=skin_rgb, outline=(0, 0, 0, 200), width=2)
    # Right arm
    draw.rectangle((cx + torso_w // 2 + 2, torso_y, cx + torso_w // 2 + arm_w + 2, torso_y + arm_h), fill=cloth_primary, outline=(0, 0, 0, 200), width=2)
    draw.rectangle((cx + torso_w // 2 + 2, torso_y + arm_h - 20, cx + torso_w // 2 + arm_w + 2, torso_y + arm_h), fill=skin_rgb, outline=(0, 0, 0, 200), width=2)

    # Head (voxel block)
    head_size = int(88 * scale)
    head_y = torso_y - head_size
    draw.rectangle((cx - head_size // 2, head_y, cx + head_size // 2, torso_y), fill=skin_rgb, outline=(0, 0, 0, 200), width=2)

    # Hair / Helmet
    if character.hair_style != "none":
        draw.rectangle((cx - head_size // 2, head_y, cx + head_size // 2, head_y + 24), fill=hair_rgb)

    # Eyes
    eye_y = head_y + 42
    eye_col = (59, 130, 246) if character.id in ["mini", "steve"] else ((168, 85, 247) if character.id == "shadow" else (220, 38, 38) if character.id == "iron_golem" else (34, 197, 94))
    draw.rectangle((cx - 24, eye_y, cx - 10, eye_y + 12), fill=(255, 255, 255))
    draw.rectangle((cx - 18, eye_y, cx - 10, eye_y + 12), fill=eye_col)
    draw.rectangle((cx + 10, eye_y, cx + 24, eye_y + 12), fill=(255, 255, 255))
    draw.rectangle((cx + 10, eye_y, cx + 18, eye_y + 12), fill=eye_col)

    # Label & ID watermark
    draw.text((24, 24), character.name.upper(), fill=(255, 255, 255, 240))
    draw.text((24, 46), f"Role: {character.role.title()} · {character.species.title()}", fill=(148, 163, 184, 200))
    draw.text((24, H - 36), f"ShortForge Canonical Asset: #{character.id}", fill=(100, 116, 139, 180))

    dest.parent.mkdir(parents=True, exist_ok=True)
    img.save(dest, format="PNG")
    character.reference_image_path = str(dest.resolve())
    return dest

def get_all_canonical_characters() -> list[CanonicalCharacter]:
    """Retrieves all standard canonical characters and ensures reference renders exist."""
    chars = list(CANONICAL_CHARACTERS.values())
    for c in chars:
        generate_character_reference_image(c)
    return chars
