"""
Complete end-to-end GeoGlobeTales-style geography video engine.
Coordinates research, scripting, Kokoro TTS, Blender 3D rendering,
FFmpeg audio/video assembly, and automated quality control.
"""
from __future__ import annotations
import os
import json
import subprocess
import tempfile
import time
from dataclasses import asdict
from pathlib import Path
from typing import Callable, Any

from .geo.geo_resolver import resolve_geo_context, GeoContext
from .geo.data_manager import ensure_geo_assets, generate_default_audio_assets
from .geo_research import generate_research_notes, GeoResearchResult
from .geo_script import make_geo_storyboard, Storyboard, SceneSpec
from .blender_render import generate_scene_texture, render_blender_scene
from .subtitles import render_scene_overlay
from .audio_engine import synthesize_narration, extract_word_timestamps, mix_master_audio
from .qc import (
    validate_coordinates,
    validate_narration,
    validate_scene_durations,
    validate_output_video,
    QualityControlError
)

def render_geo_video(
    topic: str,
    duration: int = 75,
    voice: str = "heart",
    style: str = "geo_realistic",
    preview: bool = False,
    output_dir: str = "outputs",
    progress_callback: Callable[[str, float], None] | None = None
) -> tuple[Path, dict[str, Any]]:
    """
    Renders a complete, geographically accurate, narrated, animated vertical MP4 video.
    """
    t_start = time.time()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    slug = "".join(c.lower() if c.isalnum() else "-" for c in topic)[:45].strip("-") or "geo-short"
    final_video = out / f"{slug}.mp4"

    def update_progress(msg: str, pct: float):
        if progress_callback:
            progress_callback(msg, pct)
        print(f"[{pct*100:.0f}%] {msg}")

    update_progress("Initializing geographical datasets and textures...", 0.05)
    ensure_geo_assets()
    generate_default_audio_assets()

    # 1. Research & Geographical Resolution
    update_progress("Generating verified research notes and resolving geography...", 0.10)
    geo_ctx = resolve_geo_context(topic)
    research = generate_research_notes(topic)

    # QC validation on coordinates
    validate_coordinates(geo_ctx.primary_lat, geo_ctx.primary_lon, geo_ctx.primary_name)
    for lm in geo_ctx.landmarks:
        validate_coordinates(lm.lat, lm.lon, lm.name)

    # 2. Scripting & Storyboard Generation
    update_progress("Writing narration script and generating 10-18 scene storyboard...", 0.18)
    storyboard = make_geo_storyboard(topic, duration=duration)
    validate_narration(storyboard.full_script, min_words=25)
    validate_scene_durations(storyboard.scenes, target_duration=float(duration))

    with tempfile.TemporaryDirectory(prefix="shortforge-geo-") as td:
        temp = Path(td)

        # 3. Voiceover Synthesis with Kokoro TTS
        update_progress(f"Synthesizing voiceover with Kokoro TTS (voice: {voice})...", 0.28)
        raw_voice = temp / "narration.wav"
        synthesize_narration(storyboard.full_script, raw_voice, voice_name=voice, speed=1.05)

        # Determine actual audio duration and synchronize scene timings
        probe_cmd = [
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", str(raw_voice)
        ]
        actual_audio_dur = float(subprocess.check_output(probe_cmd, text=True).strip())
        actual_audio_dur = max(actual_audio_dur, 8.0)

        # Rescale scene durations to match exact audio length
        total_sb_dur = sum(s.target_duration for s in storyboard.scenes)
        time_cursor = 0.0
        for s in storyboard.scenes:
            proportional_dur = (s.target_duration / total_sb_dur) * actual_audio_dur
            s.target_duration = round(proportional_dur, 2)
            s.start_time = round(time_cursor, 2)
            s.end_time = round(time_cursor + proportional_dur, 2)
            time_cursor += proportional_dur

        # 4. Word-Level Timestamps
        update_progress("Extracting word-level caption alignment...", 0.38)
        word_timestamps = extract_word_timestamps(raw_voice)

        # 5. Master Audio Mixing (Voiceover + ducked BGM + SFX)
        update_progress("Mixing master audio with ducked BGM and SFX...", 0.45)
        mixed_audio = temp / "master_audio.m4a"
        mix_master_audio(raw_voice, mixed_audio, bgm_volume_db=-18.0)

        # 6. 3D Scene Rendering & Overlay Compositing
        scene_clips = []
        num_scenes = len(storyboard.scenes)
        render_w = 540 if preview else 1080
        render_h = 960 if preview else 1920

        for i, sc in enumerate(storyboard.scenes):
            progress_pct = 0.50 + 0.35 * (i / num_scenes)
            update_progress(f"Rendering 3D Scene {i+1}/{num_scenes} ({sc.target_region})...", progress_pct)

            # Generate texture for this scene
            include_routes = sc.asset_type == "trade_route" or "route" in sc.camera_movement
            tex_file = temp / f"tex_{i:02d}.jpg"
            generate_scene_texture(
                geo_context=geo_ctx,
                highlighted_country_names=sc.highlight_countries,
                include_trade_routes=include_routes,
                output_path=tex_file
            )

            # Render 3D scene with Blender
            raw_3d_frame = temp / f"blender_raw_{i:02d}.png"
            render_blender_scene(
                scene_spec_dict=sc.__dict__,
                geo_context_dict={"highlights": [h.__dict__ for h in geo_ctx.highlights]},
                texture_path=tex_file,
                output_path=raw_3d_frame,
                width=render_w,
                height=render_h,
                preview=preview
            )

            # Apply UI overlays, subtitles, and badges with Pillow
            from PIL import Image
            raw_img = Image.open(raw_3d_frame).resize((1080, 1920), Image.Resampling.LANCZOS)
            comp_frame = temp / f"scene_comp_{i:02d}.png"
            render_scene_overlay(
                base_image=raw_img,
                scene_index=i,
                total_scenes=num_scenes,
                narration_text=sc.narration,
                badge_text=sc.badge_text,
                headline_text=sc.headline_text,
                stat_callout=sc.stat_callout,
                target_region=sc.target_region,
                output_path=comp_frame
            )

            # Generate 30fps animated video clip with FFmpeg camera motion
            clip_file = temp / f"clip_{i:02d}.mp4"
            dur_str = f"{sc.target_duration:.3f}"

            # Alternate camera zoompan direction for dynamic visual rhythm
            if i % 3 == 0:
                zoom_expr = "min(zoom+0.0006,1.06)" # gentle push-in
            elif i % 3 == 1:
                zoom_expr = "max(1.06-0.0006*on,1.0)" # gentle pull-out
            else:
                zoom_expr = "min(zoom+0.0004,1.04)"

            ffmpeg_clip_cmd = [
                "ffmpeg", "-y", "-loop", "1",
                "-i", str(comp_frame),
                "-t", dur_str,
                "-vf", f"scale=1188:2112,zoompan=z='{zoom_expr}':d=1:s=1080x1920:fps=30,format=yuv420p",
                "-r", "30", "-an",
                "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
                str(clip_file)
            ]
            subprocess.run(ffmpeg_clip_cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            scene_clips.append(clip_file)

        # 7. Final Assembly & Audio Sync
        update_progress("Assembling scenes and synchronizing final video...", 0.90)
        concat_list = temp / "concat.txt"
        concat_list.write_text("".join(f"file '{p.as_posix()}'\n" for p in scene_clips))

        silent_full = temp / "silent_full.mp4"
        subprocess.run([
            "ffmpeg", "-y", "-f", "concat", "-safe", "0",
            "-i", str(concat_list),
            "-c", "copy",
            str(silent_full)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        # Merge video and audio
        subprocess.run([
            "ffmpeg", "-y",
            "-i", str(silent_full),
            "-i", str(mixed_audio),
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "192k",
            "-shortest",
            "-movflags", "+faststart",
            str(final_video)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # 8. Post-Render Quality Control Verification
    update_progress("Running quality control validation...", 0.96)
    qc_metrics = validate_output_video(final_video, expected_duration=actual_audio_dur)

    total_time = round(time.time() - t_start, 2)
    metadata = {
        "topic": topic,
        "style": style,
        "voice": voice,
        "duration": qc_metrics["duration"],
        "video": str(final_video.resolve()),
        "resolution": f"{qc_metrics['width']}x{qc_metrics['height']}",
        "fps": 30,
        "file_size_bytes": qc_metrics["size_bytes"],
        "render_time_seconds": total_time,
        "research": {
            "title": research.title,
            "summary": research.summary,
            "strategic_importance": research.strategic_importance,
            "claims": [asdict(c) for c in research.verified_claims],
            "timeline": research.historical_timeline
        },
        "storyboard": {
            "num_scenes": len(storyboard.scenes),
            "scenes": [
                {
                    "id": s.scene_id,
                    "narration": s.narration,
                    "duration": s.target_duration,
                    "region": s.target_region,
                    "lat": s.lat,
                    "lon": s.lon,
                    "badge": s.badge_text,
                    "headline": s.headline_text,
                    "stat": s.stat_callout
                }
                for s in storyboard.scenes
            ]
        },
        "word_timestamps": [asdict(w) for w in word_timestamps[:50]]
    }

    meta_file = final_video.with_suffix(".json")
    meta_file.write_text(json.dumps(metadata, indent=2))

    update_progress(f"Render complete in {total_time}s! Output saved: {final_video.name}", 1.0)
    return final_video, metadata
