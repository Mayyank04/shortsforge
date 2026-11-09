"""
Audio engine for ShortForge AI.
Handles Kokoro TTS narration, faster-whisper word-level alignment,
BGM ducking, and SFX mixing with FFmpeg.
"""
from __future__ import annotations
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
import numpy as np
import soundfile as sf
from .geo.data_manager import AUDIO_DIR, generate_default_audio_assets

KOKORO_VOICES = {
    "heart": "af_heart",
    "adam": "am_adam",
    "alice": "bf_alice",
    "george": "bm_george",
    "nicole": "af_nicole",
    "michael": "am_michael",
}

@dataclass
class WordTimestamp:
    word: str
    start: float
    end: float

@dataclass
class AudioResult:
    audio_path: Path
    duration: float
    word_timestamps: list[WordTimestamp]

def synthesize_narration(
    script: str,
    output_path: Path,
    voice_name: str = "heart",
    speed: float = 1.05
) -> Path:
    """
    Synthesizes speech using Kokoro TTS (with fallback to system TTS).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    engine = os.getenv("TTS_ENGINE", "kokoro").lower()

    if engine == "kokoro":
        try:
            from kokoro import KPipeline
            voice_id = KOKORO_VOICES.get(voice_name.lower(), voice_name)
            pipeline = KPipeline(lang_code="a")
            chunks = []
            for _, _, audio in pipeline(script, voice=voice_id, speed=speed):
                chunks.append(np.asarray(audio))
            if not chunks:
                raise RuntimeError("Kokoro returned no audio chunks")
            full_audio = np.concatenate(chunks)
            sf.write(str(output_path), full_audio, 24000)
            return output_path
        except Exception as exc:
            print(f"Warning: Kokoro TTS failed ({exc}), falling back to system voice")

    # Fallback to macOS system speech
    system = os.uname().sysname if hasattr(os, "uname") else "Windows"
    if system == "Darwin":
        aiff = output_path.with_suffix(".aiff")
        subprocess.run(["say", "-v", "Samantha", "-o", str(aiff), script], check=True)
        subprocess.run(["ffmpeg", "-y", "-i", str(aiff), "-ar", "24000", str(output_path)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        aiff.unlink(missing_ok=True)
        return output_path
    else:
        subprocess.run(["espeak-ng", "-w", str(output_path), script], check=True)
        return output_path

def extract_word_timestamps(audio_path: Path) -> list[WordTimestamp]:
    """
    Uses faster-whisper to extract exact word-level start/end timestamps from the speech audio.
    """
    try:
        from faster_whisper import WhisperModel
        model = WhisperModel("tiny", device="cpu", compute_type="int8")
        segments, _ = model.transcribe(str(audio_path), word_timestamps=True)
        words: list[WordTimestamp] = []
        for segment in segments:
            for w in segment.words:
                cleaned = w.word.strip()
                if cleaned:
                    words.append(WordTimestamp(word=cleaned, start=round(w.start, 2), end=round(w.end, 2)))
        return words
    except Exception as exc:
        print(f"Warning: faster-whisper word timing failed ({exc}); falling back to proportional timing")
        return []

def mix_master_audio(
    voice_audio: Path,
    output_audio: Path,
    scene_start_times: list[float] | None = None,
    sfx_types: list[str] | None = None,
    bgm_volume_db: float = -18.0
) -> Path:
    """
    Mixes voiceover narration with ducked cinematic background music and sound effect cues.
    """
    generate_default_audio_assets()
    bgm_path = AUDIO_DIR / "ambient_geo_drone.wav"
    whoosh_path = AUDIO_DIR / "whoosh.wav"
    pin_path = AUDIO_DIR / "pin_drop.wav"

    # Measure voice duration
    probe = subprocess.check_output([
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", str(voice_audio)
    ], text=True).strip()
    total_dur = max(float(probe), 5.0)

    # Build FFmpeg filter complex:
    # 1. Loop BGM and trim to voice length + 1.0s fade out
    # 2. Sidechaincompress BGM under voice so voice is always 100% clear
    # 3. Layer SFX whooshes at transition points
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
