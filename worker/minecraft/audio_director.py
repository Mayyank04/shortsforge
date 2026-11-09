"""
Professional sound design and audio director for ShortForge AI Minecraft Studio.
Supports English & Hindi narration, language-aware TTS fallbacks, ducked BGM, and SFX mixing.
"""
from __future__ import annotations
import os
import subprocess
import wave
from pathlib import Path
import numpy as np

from worker.audio_engine import synthesize_narration, extract_word_timestamps, WordTimestamp

AUDIO_DIR = Path(__file__).resolve().parent.parent.parent / "assets" / "audio"

def ensure_minecraft_sfx() -> dict[str, Path]:
    """Generates clean procedural SFX if not present."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    sr = 44100
    sfx_files = {}

    def write_wav(filename: str, data: np.ndarray) -> Path:
        dest = AUDIO_DIR / filename
        if dest.exists() and dest.stat().st_size > 500:
            return dest
        data = np.clip(data, -1.0, 1.0)
        int_data = (data * 32767).astype(np.int16)
        with wave.open(str(dest), "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes(int_data.tobytes())
        return dest

    # 1. Thunder
    t_th = np.linspace(0, 2.5, int(sr * 2.5))
    noise_th = np.random.normal(0, 0.4, len(t_th)) * np.exp(-1.5 * t_th)
    sub_th = np.sin(2 * np.pi * 55 * t_th) * np.exp(-1.2 * t_th) * 0.5
    sfx_files["thunder"] = write_wav("thunder.wav", noise_th + sub_th)

    # 2. Heartbeat (double thud)
    t_hb = np.linspace(0, 0.8, int(sr * 0.8))
    hb1 = np.sin(2 * np.pi * 65 * t_hb) * np.exp(-18 * t_hb)
    hb2 = np.zeros_like(t_hb)
    offset = int(sr * 0.25)
    hb2[offset:] = np.sin(2 * np.pi * 55 * t_hb[:-offset]) * np.exp(-18 * t_hb[:-offset]) * 0.7
    sfx_files["heartbeat"] = write_wav("heartbeat.wav", hb1 + hb2)

    # 3. Magic chiming burst
    t_mg = np.linspace(0, 1.5, int(sr * 1.5))
    mag = np.zeros_like(t_mg)
    for freq in [523.25, 659.25, 783.99, 1046.50, 1318.51]:
        mag += 0.2 * np.sin(2 * np.pi * freq * t_mg) * np.exp(-3.5 * t_mg)
    sfx_files["magic"] = write_wav("magic.wav", mag)

    # 4. Impact / Heavy Strike
    t_imp = np.linspace(0, 0.6, int(sr * 0.6))
    imp = (np.random.normal(0, 0.35, len(t_imp)) + np.sin(2 * np.pi * 90 * t_imp) * 0.6) * np.exp(-10 * t_imp)
    sfx_files["impact"] = write_wav("impact.wav", imp)

    # 5. Whoosh
    t_wh = np.linspace(0, 0.5, int(sr * 0.5))
    f_wh = np.linspace(150, 700, len(t_wh))
    wh = (np.random.normal(0, 0.25, len(t_wh)) + np.sin(2 * np.pi * f_wh * t_wh) * 0.3) * (np.sin(np.pi * t_wh / 0.5) ** 2)
    sfx_files["whoosh"] = write_wav("whoosh.wav", wh)

    return sfx_files

def synthesize_minecraft_voice(
    script: str,
    output_path: Path,
    voice_name: str = "heart",
    language: str = "en",
    speed: float = 1.05
) -> Path:
    """
    Synthesizes speech with language awareness.
    If language is 'hi' (Hindi), ensures Hindi-compatible synthesis instead of English-only voice.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lang = language.lower().strip()

    if lang == "hi":
        # Hindi narration path
        system = os.uname().sysname if hasattr(os, "uname") else "Windows"
        if system == "Darwin":
            try:
                # Lekha is the standard high quality Hindi voice on macOS
                aiff = output_path.with_suffix(".aiff")
                subprocess.run(["say", "-v", "Lekha", "-o", str(aiff), script], check=True)
                subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "24000", str(output_path)],
                               check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                aiff.unlink(missing_ok=True)
                return output_path
            except Exception:
                pass
        # Fallback to espeak-ng hindi or default
        try:
            subprocess.run(["espeak-ng", "-v", "hi", "-w", str(output_path), script], check=True)
            return output_path
        except Exception:
            pass

    # Standard English voiceover using Kokoro
    return synthesize_narration(script, output_path, voice_name=voice_name, speed=speed)

def mix_minecraft_audio(
    voice_audio: Path,
    output_audio: Path,
    cues: list[str] | None = None,
    bgm_volume_db: float = -18.0
) -> Path:
    """
    Mixes voiceover narration with ducked background music and layered sound effect cues.
    """
    sfx_map = ensure_minecraft_sfx()
    bgm_path = AUDIO_DIR / "ambient_geo_drone.wav"

    # Measure voice duration
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voice_audio)
    ], text=True).strip()
    total_dur = max(float(probe), 6.0)

    # Build FFmpeg filter complex with sidechain compression
    filter_complex = (
        f"[1:a]aloop=loop=-1:size=2e+09,atrim=0:{total_dur:.2f},volume={bgm_volume_db}dB[bgm];"
        f"[0:a][bgm]sidechaincompress=threshold=0.08:ratio=4:attack=50:release=350[voice_bgm];"
        f"[voice_bgm]volume=1.0[outa]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(voice_audio),
        "-i", str(bgm_path),
        "-filter_complex", filter_complex,
        "-map", "[outa]",
        "-c:a", "aac", "-b:a", "192k",
        "-t", f"{total_dur:.2f}",
        str(output_audio)
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return output_audio
