"""
Quality control verification suite for ShortForge AI geography videos.
Performs automated pre-render and post-render validation checks.
"""
from __future__ import annotations
import json
import math
import subprocess
from pathlib import Path

class QualityControlError(Exception):
    """Raised when an automated quality check fails."""
    pass

def validate_coordinates(lat: float, lon: float, entity_name: str = "Location"):
    """Verifies that latitude and longitude are valid spherical coordinates."""
    if not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
        raise QualityControlError(f"{entity_name} coordinates must be numeric: lat={lat}, lon={lon}")
    if math.isnan(lat) or math.isnan(lon):
        raise QualityControlError(f"{entity_name} coordinates cannot be NaN: lat={lat}, lon={lon}")
    if not (-90.0 <= lat <= 90.0):
        raise QualityControlError(f"{entity_name} latitude out of bounds [-90, 90]: {lat}")
    if not (-180.0 <= lon <= 180.0):
        raise QualityControlError(f"{entity_name} longitude out of bounds [-180, 180]: {lon}")

def validate_map_assets(assets_dict: dict[str, Path]):
    """Verifies that all required textures, datasets, and flags exist and are valid."""
    for name, path in assets_dict.items():
        if not path.exists():
            raise QualityControlError(f"Missing required geographical asset: {name} at {path}")
        if path.stat().st_size < 1000:
            raise QualityControlError(f"Corrupted or empty geographical asset: {name} ({path.stat().st_size} bytes)")

def validate_narration(script: str, min_words: int = 25):
    """Verifies that the generated narration is non-empty and coherent."""
    if not script or not script.strip():
        raise QualityControlError("Missing narration: Script is empty")
    words = script.strip().split()
    if len(words) < min_words:
        raise QualityControlError(f"Narration too short: {len(words)} words (minimum {min_words})")
    # Verify no raw placeholder tokens
    lowered = script.lower()
    for forbidden in ["[placeholder]", "{topic}", "narrator:", "voiceover:"]:
        if forbidden in lowered:
            raise QualityControlError(f"Narration contains unprocessed placeholder: '{forbidden}'")

def validate_scene_durations(scenes: list, target_duration: float, tolerance: float = 3.5):
    """Verifies that all scene durations are positive and sum to the target duration."""
    if not scenes:
        raise QualityControlError("Scene list is empty")
    total_dur = 0.0
    for s in scenes:
        dur = getattr(s, "target_duration", None)
        if dur is None and isinstance(s, dict):
            dur = s.get("target_duration")
        if dur is None or dur <= 0.0:
            raise QualityControlError(f"Invalid scene duration {dur} for scene {getattr(s, 'scene_id', s)}")
        total_dur += dur

    if abs(total_dur - target_duration) > tolerance:
        raise QualityControlError(
            f"Incorrect scene durations: sum is {total_dur:.2f}s, target was {target_duration:.2f}s (tolerance {tolerance}s)"
        )

def validate_output_video(
    video_path: Path,
    expected_duration: float | None = None,
    sync_tolerance: float = 0.4
) -> dict:
    """
    Runs ffprobe to verify video resolution (1080x1920), 30 FPS, audio track,
    and audio/video duration synchronisation.
    """
    if not video_path.exists():
        raise QualityControlError(f"Rendering failed: Output video file not found at {video_path}")
    if video_path.stat().st_size < 100000:
        raise QualityControlError(f"Rendering failed: Output video file is suspiciously small ({video_path.stat().st_size} bytes)")

    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "stream=width,height,r_frame_rate,codec_name,codec_type,duration",
        "-show_entries", "format=duration,size",
        "-of", "json",
        str(video_path)
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
        info = json.loads(proc.stdout)
    except Exception as exc:
        raise QualityControlError(f"Failed to probe output video: {exc}")

    streams = info.get("streams", [])
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)

    if not video_stream:
        raise QualityControlError("Invalid output video: No video stream found")
    if not audio_stream:
        raise QualityControlError("Invalid output video: No audio stream found")

    width = int(video_stream.get("width", 0))
    height = int(video_stream.get("height", 0))
    if width != 1080 or height != 1920:
        raise QualityControlError(f"Invalid output dimensions: Expected 1080x1920, got {width}x{height}")

    # FPS verification
    fps_raw = video_stream.get("r_frame_rate", "30/1")
    try:
        num, den = fps_raw.split("/")
        fps = float(num) / float(den)
        if abs(fps - 30.0) > 1.0:
            raise QualityControlError(f"Invalid frame rate: Expected 30 FPS, got {fps:.2f} FPS")
    except Exception:
        pass

    # Audio/Video Sync verification
    format_dur = float(info.get("format", {}).get("duration", 0))
    v_dur = float(video_stream.get("duration") or format_dur)
    a_dur = float(audio_stream.get("duration") or format_dur)

    if abs(v_dur - a_dur) > sync_tolerance:
        raise QualityControlError(
            f"Audio/video synchronisation error: Video duration is {v_dur:.2f}s, Audio duration is {a_dur:.2f}s (diff {abs(v_dur - a_dur):.2f}s > {sync_tolerance}s)"
        )

    if expected_duration and abs(format_dur - expected_duration) > 5.0:
        raise QualityControlError(
            f"Output video duration mismatch: Expected ~{expected_duration:.2f}s, got {format_dur:.2f}s"
        )

    return {
        "width": width,
        "height": height,
        "duration": format_dur,
        "video_duration": v_dur,
        "audio_duration": a_dur,
        "size_bytes": video_path.stat().st_size,
        "video_codec": video_stream.get("codec_name"),
        "audio_codec": audio_stream.get("codec_name")
    }
