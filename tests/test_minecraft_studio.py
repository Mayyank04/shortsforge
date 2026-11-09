"""
Comprehensive automated test suite for ShortForge AI Minecraft Story Studio.
Tests:
1. Story generation, genre variations, 10-scene structure, and duplicate prevention.
2. Character consistency, canonical definitions, and reference image rendering.
3. Camera instructions and character action schemas.
4. Vertical subtitle card generation with safe margins.
5. Minecraft REST API routes, project lifecycle, scene editing, and settings diagnostics.
6. Real Blender 3D scene rendering smoke test.
"""
from __future__ import annotations
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from worker.minecraft.metadata import (
    StoryProject, SceneSpec, CanonicalCharacter, CameraInstruction,
    CharacterAction, AudioCue
)
from worker.minecraft.character_models import CANONICAL_CHARACTERS, get_canonical_character
from worker.minecraft.character_registry import generate_character_reference_image, get_all_canonical_characters
from worker.minecraft.story_generator import generate_procedural_story, generate_story_with_ollama_or_fallback
from worker.minecraft.story_validator import validate_story_project, compute_story_fingerprint
from worker.minecraft.subtitles_minecraft import render_minecraft_overlay
from worker.minecraft.blender_minecraft import render_minecraft_scene

client = TestClient(app)

# -------------------------------------------------------------
# 1. Story Generation & Quality Checks
# -------------------------------------------------------------

def test_benchmark_story_structure():
    story = generate_procedural_story(
        genre="emotional",
        idea="The Villager Who Had Only One Heart",
        duration=50
    )
    assert story.title == "The Villager Who Had Only One Heart"
    assert len(story.scenes) == 10
    assert "Mini" in story.opening_hook or "one" in story.opening_hook
    assert len(story.characters) >= 4
    # Check that Mini, Steve, Iron Golem, Shadow are cast
    char_ids = [c.id for c in story.characters]
    assert "mini" in char_ids
    assert "steve" in char_ids
    assert "iron_golem" in char_ids
    assert "shadow" in char_ids

    # Validate schema
    is_valid, errors = validate_story_project(story)
    assert is_valid, f"Validation errors: {errors}"

def test_story_genre_variations():
    genres = ["adventure", "mystery", "horror", "survival", "friendship"]
    fingerprints = set()

    for g in genres:
        st = generate_procedural_story(genre=g, duration=50)
        assert len(st.scenes) == 10
        assert st.genre == g
        assert st.fingerprint not in fingerprints
        fingerprints.add(st.fingerprint)

def test_story_fingerprint_uniqueness():
    s1 = generate_procedural_story(genre="adventure", idea="Finding the Ancient Portal", duration=50)
    s2 = generate_procedural_story(genre="adventure", idea="Escaping the Deep Cavern", duration=50)
    assert s1.fingerprint != s2.fingerprint

# -------------------------------------------------------------
# 2. Canonical Characters & Consistency
# -------------------------------------------------------------

def test_canonical_characters_consistency():
    mini = get_canonical_character("mini")
    assert mini.name == "Mini"
    assert mini.clothing_primary == "#2563eb"
    assert mini.proportions["height"] == 1.45  # Consistent shorter proportion

    steve = get_canonical_character("steve")
    assert steve.name == "Steve"
    assert steve.clothing_primary == "#06b6d4"  # Iconic cyan

    golem = get_canonical_character("iron_golem")
    assert golem.proportions["height"] == 2.70  # Giant scale

    shadow = get_canonical_character("shadow")
    assert shadow.skin_tone == "#0f172a"  # Dark obsidian

def test_character_reference_image_generation():
    with tempfile.TemporaryDirectory() as td:
        mini = get_canonical_character("mini")
        out_img = Path(td) / "mini_test_ref.png"
        ref_path = generate_character_reference_image(mini, output_path=out_img)
        assert ref_path.exists()
        assert ref_path.stat().st_size > 1000
        # Verify it's a valid 512x512 PNG
        img = Image.open(ref_path)
        assert img.size == (512, 512)

# -------------------------------------------------------------
# 3. Subtitles & Typography
# -------------------------------------------------------------

def test_subtitles_vertical_overlay():
    base = Image.new("RGB", (1080, 1920), (20, 25, 40))
    overlay = render_minecraft_overlay(
        base_image=base,
        scene_number=1,
        total_scenes=10,
        narration_text="Mini was born with only one heart.",
        active_word="heart",
        genre_badge="emotional"
    )
    assert overlay.size == (1080, 1920)

# -------------------------------------------------------------
# 4. Minecraft REST API Endpoints
# -------------------------------------------------------------

def test_api_story_generate():
    r = client.post("/api/minecraft/stories/generate", json={
        "genre": "emotional",
        "idea": "The Villager Who Had Only One Heart",
        "duration": 50,
        "language": "en"
    })
    assert r.status_code == 200
    data = r.json()
    assert data["title"] == "The Villager Who Had Only One Heart"
    assert len(data["scenes"]) == 10

def test_api_project_lifecycle():
    # 1. Create project
    create_r = client.post("/api/minecraft/projects", json={
        "title": "Test Quest for the Core",
        "genre": "adventure",
        "duration": 50,
        "language": "en",
        "voice": "heart",
        "visual_quality": "preview",
        "auto_render": False
    })
    assert create_r.status_code == 201
    proj = create_r.json()
    proj_id = proj["id"]
    assert proj["title"] == "Test Quest for the Core"
    assert len(proj["scenes"]) == 10

    # 2. Get project
    get_r = client.get(f"/api/minecraft/projects/{proj_id}")
    assert get_r.status_code == 200
    assert get_r.json()["id"] == proj_id

    # 3. Update project
    up_r = client.put(f"/api/minecraft/projects/{proj_id}", json={
        "title": "Updated Quest Title"
    })
    assert up_r.status_code == 200
    assert up_r.json()["title"] == "Updated Quest Title"

    # 4. Duplicate project
    dup_r = client.post(f"/api/minecraft/projects/{proj_id}/duplicate")
    assert dup_r.status_code == 200
    clone = dup_r.json()
    assert clone["id"] != proj_id
    assert "Copy" in clone["title"]
    assert len(clone["scenes"]) == 10

    # 5. Scene list & edit
    scenes_r = client.get(f"/api/minecraft/projects/{proj_id}/scenes")
    assert scenes_r.status_code == 200
    scenes = scenes_r.json()
    sc_id = scenes[0]["id"]

    sc_up_r = client.put(f"/api/minecraft/scenes/{sc_id}", json={
        "narration": "Updated custom scene text."
    })
    assert sc_up_r.status_code == 200
    assert sc_up_r.json()["narration"] == "Updated custom scene text."

    # 6. Delete project
    del_r = client.delete(f"/api/minecraft/projects/{proj_id}")
    assert del_r.status_code == 200

def test_api_character_endpoints():
    # List characters
    list_r = client.get("/api/minecraft/characters")
    assert list_r.status_code == 200
    chars = list_r.json()
    assert len(chars) >= 4  # Canonical characters seeded

    # Create new character
    new_c_r = client.post("/api/minecraft/characters", json={
        "name": "Finn",
        "role": "scout",
        "species": "human",
        "skin_tone": "#d49b6a",
        "clothing_primary": "#10b981",
        "clothing_secondary": "#064e3b",
        "hair_color": "#18181b",
        "personality": "Fast and nimble runner"
    })
    assert new_c_r.status_code == 201
    char_id = new_c_r.json()["id"]

    # Delete character
    del_r = client.delete(f"/api/minecraft/characters/{char_id}")
    assert del_r.status_code == 200

def test_api_renders_and_settings():
    # Renders stats
    stats_r = client.get("/api/renders/stats")
    assert stats_r.status_code == 200
    data = stats_r.json()
    assert "total_projects" in data
    assert "completed_videos" in data

    # Settings
    set_r = client.get("/api/settings")
    assert set_r.status_code == 200
    s_data = set_r.json()
    assert "blender" in s_data
    assert "ffmpeg" in s_data
    assert "storage" in s_data

# -------------------------------------------------------------
# 5. Real Blender Smoke Test
# -------------------------------------------------------------

def test_real_blender_minecraft_render():
    """Real smoke test rendering a live Minecraft scene with Blender EEVEE."""
    chars = [get_canonical_character("mini"), get_canonical_character("steve")]
    spec = SceneSpec(
        scene_number=1,
        duration=5.0,
        narration="Mini looked up toward the beacon.",
        characters=["mini", "steve"],
        environment="Village",
        time_of_day="day",
        camera=CameraInstruction(shot="medium_shot", movement="slow_dolly_in", focus="mini", distance=4.0),
        character_actions=[
            CharacterAction(character_id="mini", action="walking", position=[0, 0, 0]),
            CharacterAction(character_id="steve", action="waving", position=[1.5, 0, 0])
        ]
    )

    with tempfile.TemporaryDirectory() as td:
        frame_dest = Path(td) / "smoke_frame.png"
        render_minecraft_scene(spec, chars, frame_dest, width=540, height=960, preview=True)
        assert frame_dest.exists()
        assert frame_dest.stat().st_size > 5000
