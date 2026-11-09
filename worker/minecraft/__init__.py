"""
ShortForge AI — Minecraft Story Studio Module.
"""
from .metadata import (
    StoryProject, SceneSpec, CanonicalCharacter, CameraInstruction,
    CharacterAction, AudioCue, MinecraftGenre
)
from .story_generator import generate_story_with_ollama_or_fallback, generate_procedural_story
from .character_models import CANONICAL_CHARACTERS, get_canonical_character
from .character_registry import get_all_canonical_characters, generate_character_reference_image
from .blender_minecraft import render_minecraft_scene
from .audio_director import synthesize_minecraft_voice, mix_minecraft_audio
from .subtitles_minecraft import render_minecraft_overlay
from .pipeline import render_minecraft_video

__all__ = [
    "StoryProject", "SceneSpec", "CanonicalCharacter", "CameraInstruction",
    "CharacterAction", "AudioCue", "MinecraftGenre",
    "generate_story_with_ollama_or_fallback", "generate_procedural_story",
    "CANONICAL_CHARACTERS", "get_canonical_character",
    "get_all_canonical_characters", "generate_character_reference_image",
    "render_minecraft_scene", "synthesize_minecraft_voice",
    "mix_minecraft_audio", "render_minecraft_overlay", "render_minecraft_video"
]
