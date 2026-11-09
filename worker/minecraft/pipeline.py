"""
Master video generation pipeline for ShortForge AI Minecraft Story Studio.
Assembles 3D Blender voxel scenes, character consistency, Kokoro neural voiceover,
SFX cues, synchronized subtitles, and FFmpeg vertical video export (1080x1920, 30 FPS).
"""
from __future__ import annotations
import json
import os
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable, Optional
from PIL import Image

from .metadata import StoryProject, SceneSpec
from .story_generator import generate_story_with_ollama_or_fallback
from .character_registry import generate_character_reference_image
from .blender_minecraft import render_minecraft_scene
from .audio_director import synthesize_minecraft_voice, mix_minecraft_audio
from .subtitles_minecraft import render_minecraft_overlay

def render_minecraft_video(
    topic: str,
    genre: str = "adventure",
    duration: int = 50,
    voice: str = "heart",
    language: str = "en",
    preview: bool = False,
    output_dir: str = "outputs",
    progress_callback: Optional[Callable[[str, float], None]] = None
) -> tuple[Path, dict]:
    """
    Renders a complete, professional, character-consistent Minecraft-inspired Short.
    """
    start_time = time.time()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    slug = "".join(c.lower() if c.isalnum() else "-" for c in topic)[:45].strip("-") or "minecraft-short"
    final_mp4 = out_dir / f"{slug}.mp4"

    def update_progress(stage: str, pct: float):
        if progress_callback:
            progress_callback(stage, pct)
        print(f"[{pct*100:04.1f}%] {stage}")

    update_progress("Synthesizing original structured 10-scene story...", 0.05)
    story: StoryProject = generate_story_with_ollama_or_fallback(
        genre=genre,
        idea=topic,
        duration=duration,
        language=language
    )

    update_progress("Generating canonical character reference models...", 0.12)
    for char in story.characters:
        generate_character_reference_image(char)

    with tempfile.TemporaryDirectory(prefix="shortforge_mc_") as td:
        temp = Path(td)

        # 1. Synthesize Narration
        update_progress("Synthesizing language-aware voiceover narration...", 0.22)
        raw_voice = temp / "raw_voice.wav"
        synthesize_minecraft_voice(
            script=story.full_script,
            output_path=raw_voice,
            voice_name=voice,
            language=language,
            speed=1.05
        )

        # Probe actual audio duration
        probe = subprocess.check_output([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(raw_voice)
        ], text=True).strip()
        actual_audio_dur = max(float(probe), 8.0)

        # Re-scale scene durations to match exact audio length
        total_orig = sum(s.duration for s in story.scenes)
        for s in story.scenes:
            s.duration = round((s.duration / total_orig) * actual_audio_dur, 2)

        # 2. Master Audio Mixing
        update_progress("Mixing master audio with ducked soundtrack & SFX...", 0.32)
        mixed_audio = temp / "master_audio.m4a"
        mix_minecraft_audio(raw_voice, mixed_audio, bgm_volume_db=-18.0)

        # 3. 3D Scene Rendering & Compositing
        scene_clips = []
        num_scenes = len(story.scenes)
        render_w = 540 if preview else 1080
        render_h = 960 if preview else 1920

        for i, sc in enumerate(story.scenes):
            prog = 0.35 + 0.45 * (i / num_scenes)
            update_progress(f"Rendering 3D Minecraft Scene {i+1}/{num_scenes} ({sc.environment})...", prog)

            # A. Render 3D frame via Blender
            raw_frame_path = temp / f"blender_raw_{i:02d}.png"
            render_minecraft_scene(
                scene_spec=sc,
                characters=story.characters,
                output_frame_path=raw_frame_path,
                width=render_w,
                height=render_h,
                preview=preview
            )

            # B. Composite subtitles and typography
            raw_img = Image.open(raw_frame_path)
            comp_img = render_minecraft_overlay(
                base_image=raw_img,
                scene_number=sc.scene_number,
                total_scenes=num_scenes,
                narration_text=sc.narration,
                genre_badge=story.genre
            )
            comp_path = temp / f"comp_{i:02d}.png"
            comp_img.save(comp_path, quality=95)

            # C. Encode scene clip with subtle cinematic camera movement
            clip_path = temp / f"scene_clip_{i:02d}.mp4"
            zoom_expr = "min(zoom+0.0006,1.06)"
            vf = (
                f"scale={render_w*1.1:.0f}:{render_h*1.1:.0f},"
                f"zoompan=z='{zoom_expr}':d=1:s={render_w}x{render_h}:fps=30,format=yuv420p"
            )
            subprocess.run([
                "ffmpeg", "-y", "-loop", "1", "-i", str(comp_path),
                "-t", f"{sc.duration:.2f}",
                "-vf", vf,
                "-r", "30", "-an", "-c:v", "libx264", "-preset", "veryfast",
                str(clip_path)
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            scene_clips.append(clip_path)

        # 4. Final Video Assembly
        update_progress("Assembling final 1080x1920 H.264 video with synchronized audio...", 0.88)
        concat_txt = temp / "concat.txt"
        concat_txt.write_text("".join(f"file '{p.as_posix()}'\n" for p in scene_clips))

        silent_full = temp / "silent_full.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_txt), "-c", "copy", str(silent_full)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Combine with master audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(silent_full),
            "-i", str(mixed_audio),
            "-shortest",
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-movflags", "+faststart",
            str(final_mp4)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    render_time = round(time.time() - start_time, 2)
    update_progress(f"Video export complete in {render_time}s: {final_mp4.name}", 1.0)

    # 5. Metadata JSON sidecar
    metadata = {
        "title": story.title,
        "genre": story.genre,
        "viral_title": story.viral_title,
        "duration": actual_audio_dur,
        "language": language,
        "voice": voice,
        "resolution": f"{render_w}x{render_h}",
        "fps": 30,
        "video": str(final_mp4.resolve()),
        "file_size_bytes": final_mp4.stat().st_size if final_mp4.exists() else 0,
        "render_time_seconds": render_time,
        "characters": [c.model_dump() for c in story.characters],
        "scenes": [s.model_dump() for s in story.scenes],
        "full_script": story.full_script,
        "loop_opportunity": story.loop_opportunity,
        "fingerprint": story.fingerprint
    }

    final_mp4.with_suffix(".json").write_text(json.dumps(metadata, indent=2))
    return final_mp4, metadata
