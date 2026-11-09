"""
Canonical voxel character specifications for ShortForge AI Minecraft Story Studio.
Enforces strict character consistency across all scenes.
Provides exact color palettes, proportions, accessory specifications, and 3D mesh definitions.
"""
from __future__ import annotations
from typing import Dict, Any
from .metadata import CanonicalCharacter

# Benchmark Canonical Characters with strictly defined visual attributes
CANONICAL_CHARACTERS: dict[str, CanonicalCharacter] = {
    "mini": CanonicalCharacter(
        id="mini",
        name="Mini",
        role="protagonist",
        species="villager",
        skin_tone="#e29b68",
        clothing_primary="#2563eb",      # Bright royal blue tunic
        clothing_secondary="#1e3a8a",    # Deep navy trim
        hair_style="tuft",
        hair_color="#78350f",
        proportions={
            "head": 1.15,
            "torso": 0.85,
            "arms": 0.85,
            "legs": 0.85,
            "height": 1.45,  # noticeably shorter, cute & vulnerable
            "eye_scale": 1.25
        },
        personality="Vulnerable yet immensely brave; possesses only one heart but never retreats when others are in danger.",
        voice_preference="heart",
        model_spec={
            "voxel_resolution": 16,
            "head_dims": [0.55, 0.55, 0.55],
            "torso_dims": [0.42, 0.22, 0.50],
            "arm_dims": [0.15, 0.15, 0.45],
            "leg_dims": [0.16, 0.16, 0.45],
            "eye_color": [0.20, 0.55, 0.90, 1.0],  # Bright blue expressive eyes
            "nose_dims": [0.10, 0.12, 0.16],
            "badge": "golden_heart"
        }
    ),
    "steve": CanonicalCharacter(
        id="steve",
        name="Steve",
        role="companion",
        species="human",
        skin_tone="#c68653",
        clothing_primary="#06b6d4",      # Classic cyan shirt
        clothing_secondary="#1e3a8a",    # Dark blue jeans
        hair_style="blocky_crop",
        hair_color="#3e2723",
        proportions={
            "head": 1.0,
            "torso": 1.0,
            "arms": 1.0,
            "legs": 1.0,
            "height": 1.85,
            "eye_scale": 1.0
        },
        personality="Resourceful veteran miner and builder; protective of younger companions and practical in combat.",
        voice_preference="adam",
        model_spec={
            "voxel_resolution": 16,
            "head_dims": [0.50, 0.50, 0.50],
            "torso_dims": [0.50, 0.25, 0.70],
            "arm_dims": [0.22, 0.22, 0.65],
            "leg_dims": [0.22, 0.22, 0.68],
            "eye_color": [0.15, 0.35, 0.80, 1.0]
        }
    ),
    "iron_golem": CanonicalCharacter(
        id="iron_golem",
        name="Iron Golem",
        role="guardian",
        species="golem",
        skin_tone="#d1d5db",             # Pale metallic iron
        clothing_primary="#9ca3af",      # Weathered stone plate
        clothing_secondary="#16a34a",    # Creeping green ivy accents
        hair_style="none",
        hair_color="#000000",
        proportions={
            "head": 0.85,
            "torso": 1.65,
            "arms": 1.80,
            "legs": 1.10,
            "height": 2.70,  # Giant guardian proportions
            "eye_scale": 0.9
        },
        personality="Silent, loyal protector of the settlement; moves with deliberate weight and devastating strength.",
        voice_preference="george",
        model_spec={
            "voxel_resolution": 16,
            "head_dims": [0.45, 0.45, 0.45],
            "torso_dims": [0.95, 0.55, 0.90],
            "arm_dims": [0.35, 0.35, 1.15],
            "leg_dims": [0.35, 0.35, 0.80],
            "eye_color": [0.85, 0.15, 0.15, 1.0],  # Glowing crimson optical core
            "nose_dims": [0.12, 0.15, 0.25]
        }
    ),
    "shadow": CanonicalCharacter(
        id="shadow",
        name="Shadow",
        role="antagonist",
        species="shadow",
        skin_tone="#0f172a",             # Pitch obsidian dark
        clothing_primary="#090d16",      # Matte void cloak
        clothing_secondary="#7c3aed",    # Shimmering purple soul glow
        hair_style="smoky_wisp",
        hair_color="#581c87",
        proportions={
            "head": 1.0,
            "torso": 0.95,
            "arms": 1.25,                    # Slightly elongated, eerie arms
            "legs": 1.15,
            "height": 2.05,
            "eye_scale": 1.2
        },
        personality="Mysterious shadowy entity drawn to light and courage; seeks to extinguish the village beacon.",
        voice_preference="michael",
        model_spec={
            "voxel_resolution": 16,
            "head_dims": [0.48, 0.48, 0.48],
            "torso_dims": [0.46, 0.22, 0.72],
            "arm_dims": [0.18, 0.18, 0.80],
            "leg_dims": [0.18, 0.18, 0.82],
            "eye_color": [0.75, 0.20, 0.95, 1.0]  # Ominous purple luminescence
        }
    ),
    "villager": CanonicalCharacter(
        id="villager",
        name="Elder Barnaby",
        role="mentor",
        species="villager",
        skin_tone="#c27d48",
        clothing_primary="#854d0e",      # Earthy brown robes
        clothing_secondary="#15803d",    # Emerald pouch
        hair_style="bald",
        hair_color="#713f12",
        proportions={
            "head": 1.05,
            "torso": 1.0,
            "arms": 1.0,
            "legs": 0.95,
            "height": 1.75
        },
        personality="Wise but cautious village keeper who fears the outside world.",
        voice_preference="george",
        model_spec={
            "voxel_resolution": 16,
            "head_dims": [0.50, 0.50, 0.50],
            "torso_dims": [0.48, 0.28, 0.75],
            "arm_dims": [0.20, 0.20, 0.65],
            "leg_dims": [0.20, 0.20, 0.65],
            "eye_color": [0.10, 0.65, 0.30, 1.0],  # Emerald green eyes
            "nose_dims": [0.12, 0.14, 0.22]
        }
    )
}

def get_canonical_character(char_id: str) -> CanonicalCharacter:
    """Returns canonical character definition with fallback defaults."""
    key = char_id.lower().strip().replace(" ", "_")
    if key in CANONICAL_CHARACTERS:
        return CANONICAL_CHARACTERS[key]
    # Procedural fallback character
    return CanonicalCharacter(
        id=key,
        name=char_id.title(),
        role="companion",
        species="human",
        skin_tone="#c68653",
        clothing_primary="#3b82f6",
        clothing_secondary="#1e293b",
        hair_style="short",
        hair_color="#1f2937",
        personality=f"Courageous adventurer known as {char_id}."
    )
