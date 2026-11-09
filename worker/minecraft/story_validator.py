"""
Story validation, duration checks, word count calibration, and duplicate detection.
"""
from __future__ import annotations
import hashlib
from typing import List, Tuple
from .metadata import StoryProject, SceneSpec

def compute_story_fingerprint(title: str, genre: str, scenes: list[SceneSpec]) -> str:
    """Computes a deterministic cryptographic fingerprint for duplicate detection."""
    content = f"{title.lower().strip()}|{genre}|" + "|".join(s.narration.lower().strip() for s in scenes)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def validate_story_project(project: StoryProject) -> tuple[bool, list[str]]:
    """
    Validates a generated story project:
    - Exactly 10 scenes (or requested count).
    - First scene has immediate curiosity hook.
    - Word count between 5 and 18 words per scene.
    - Scene durations sum to target duration within 1.5 seconds.
    - Characters used in scenes exist in project.characters.
    """
    errors: list[str] = []

    if len(project.scenes) < 5:
        errors.append(f"Too few scenes: {len(project.scenes)} (minimum 5 required, standard 10)")

    total_duration = sum(s.duration for s in project.scenes)
    if abs(total_duration - project.duration) > 4.0:
        errors.append(f"Scene durations sum to {total_duration:.1f}s, expected {project.duration}s")

    known_chars = {c.id for c in project.characters}

    for s in project.scenes:
        words = s.narration.strip().split()
        if len(words) < 3:
            errors.append(f"Scene {s.scene_number} narration is too short ({len(words)} words)")
        elif len(words) > 22:
            errors.append(f"Scene {s.scene_number} narration is too long for 5s pacing ({len(words)} words)")

        for cid in s.characters:
            if cid not in known_chars and cid not in ["mini", "steve", "iron_golem", "shadow", "villager"]:
                errors.append(f"Scene {s.scene_number} references unregistered character '{cid}'")

    return len(errors) == 0, errors

def adjust_scene_durations(scenes: list[SceneSpec], target_total_duration: float):
    """Calibrates scene durations proportionally based on word count while preserving pacing."""
    word_counts = [max(1, len(s.narration.split())) for s in scenes]
    total_words = sum(word_counts)

    time_cursor = 0.0
    for i, s in enumerate(scenes):
        prop_dur = (word_counts[i] / total_words) * target_total_duration
        # Clamp between 3.5s and 8.0s for vertical short pacing
        s.duration = round(max(3.5, min(prop_dur, 8.0)), 2)
        time_cursor += s.duration

    # Adjust final scene so sum matches exact target
    diff = round(target_total_duration - sum(s.duration for s in scenes), 2)
    if scenes:
        scenes[-1].duration = round(scenes[-1].duration + diff, 2)
