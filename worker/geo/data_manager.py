"""
Geographical data and asset manager for ShortForge AI.
Handles local caching of Natural Earth datasets, Earth textures, country flags, and audio assets.
"""
from __future__ import annotations
import os
import urllib.request
import json
import numpy as np
import wave
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
ASSETS_DIR = BASE_DIR / "assets"
GEO_DIR = ASSETS_DIR / "geo"
TEXTURES_DIR = GEO_DIR / "textures"
DATA_DIR = GEO_DIR / "data"
FLAGS_DIR = GEO_DIR / "flags"
AUDIO_DIR = ASSETS_DIR / "audio"

REMOTE_ASSETS = {
    TEXTURES_DIR / "earth_color_4k.jpg": "https://raw.githubusercontent.com/turban/webgl-earth/master/images/2_no_clouds_4k.jpg",
    TEXTURES_DIR / "earth_bump_4k.jpg": "https://raw.githubusercontent.com/turban/webgl-earth/master/images/elev_bump_4k.jpg",
    TEXTURES_DIR / "earth_water_4k.png": "https://raw.githubusercontent.com/turban/webgl-earth/master/images/water_4k.png",
    DATA_DIR / "ne_110m_countries.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
    DATA_DIR / "ne_10m_map_units.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_map_units.geojson",
    DATA_DIR / "ne_110m_populated_places.geojson": "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_populated_places_simple.geojson",
}

FLAG_URLS = {
    "gb": "uk.png",
    "es": "spain.png",
    "gi": "gibraltar.png",
    "ru": "russia.png",
    "ie": "ireland.png",
    "in": "india.png",
    "eg": "egypt.png",
    "fr": "france.png",
    "de": "germany.png",
    "pt": "portugal.png",
    "ma": "morocco.png",
    "us": "usa.png",
}

def ensure_directories():
    for d in [TEXTURES_DIR, DATA_DIR, FLAGS_DIR, AUDIO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def download_file(url: str, dest: Path, timeout: int = 30) -> Path:
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "ShortForgeAI/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as response, open(dest, "wb") as f:
        f.write(response.read())
    return dest

def ensure_geo_assets() -> dict[str, Path]:
    """Ensures all essential geographical textures and Natural Earth datasets exist."""
    ensure_directories()
    results = {}
    for dest, url in REMOTE_ASSETS.items():
        try:
            download_file(url, dest)
            results[dest.name] = dest
        except Exception as exc:
            if not dest.exists():
                print(f"Warning: Failed to download {url}: {exc}")
    return results

def get_flag_path(country_code: str) -> Path | None:
    """Gets or downloads the flag for a given ISO 2-letter country code."""
    ensure_directories()
    code = country_code.lower().strip()
    dest = FLAGS_DIR / f"{FLAG_URLS.get(code, f'{code}.png')}"
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    url = f"https://flagcdn.com/w320/{code}.png"
    try:
        download_file(url, dest, timeout=10)
        return dest
    except Exception as exc:
        print(f"Warning: Could not fetch flag for {country_code}: {exc}")
        return None

def generate_default_audio_assets():
    """Synthesizes high quality clean SFX and ambient soundtrack if not already present."""
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    sr = 44100

    def write_wav(filename: str, data: np.ndarray):
        dest = AUDIO_DIR / filename
        if dest.exists() and dest.stat().st_size > 1000:
            return dest
        data = np.clip(data, -1.0, 1.0)
        int_data = (data * 32767).astype(np.int16)
        with wave.open(str(dest), "w") as f:
            f.setnchannels(1)
            f.setsampwidth(2)
            f.setframerate(sr)
            f.writeframes(int_data.tobytes())
        return dest

    # 1. Whoosh SFX (0.6s)
    whoosh_path = AUDIO_DIR / "whoosh.wav"
    if not whoosh_path.exists() or whoosh_path.stat().st_size < 1000:
        t = np.linspace(0, 0.6, int(sr * 0.6))
        noise = np.random.normal(0, 0.25, len(t))
        env = np.sin(np.pi * t / 0.6) ** 2
        f_sweep = np.linspace(150, 800, len(t))
        tone = np.sin(2 * np.pi * f_sweep * t) * 0.3
        write_wav("whoosh.wav", (noise * 0.7 + tone * 0.3) * env)

    # 2. Pin Drop SFX (0.25s)
    pin_path = AUDIO_DIR / "pin_drop.wav"
    if not pin_path.exists() or pin_path.stat().st_size < 1000:
        t_pin = np.linspace(0, 0.25, int(sr * 0.25))
        env_pin = np.exp(-18 * t_pin)
        pin = (np.sin(2 * np.pi * 880 * t_pin) + 0.5 * np.sin(2 * np.pi * 1760 * t_pin)) * env_pin
        write_wav("pin_drop.wav", pin)

    # 3. Soft chime SFX (0.8s)
    chime_path = AUDIO_DIR / "chime.wav"
    if not chime_path.exists() or chime_path.stat().st_size < 1000:
        t_bell = np.linspace(0, 0.8, int(sr * 0.8))
        env_bell = np.exp(-6 * t_bell)
        bell = (np.sin(2 * np.pi * 523.25 * t_bell) + 0.4 * np.sin(2 * np.pi * 1046.5 * t_bell)) * env_bell
        write_wav("chime.wav", bell)

    # 4. Ambient Cinematic Geography Drone Track (120s)
    bgm_path = AUDIO_DIR / "ambient_geo_drone.wav"
    if not bgm_path.exists() or bgm_path.stat().st_size < 10000:
        dur = 120
        t_m = np.linspace(0, dur, int(sr * dur))
        drone = np.zeros(len(t_m))
        freqs = [73.416, 110.0, 146.83, 220.0, 293.66, 440.0]
        for i, f in enumerate(freqs):
            lfo = 0.5 + 0.5 * np.sin(2 * np.pi * (0.05 + 0.02 * i) * t_m)
            drone += (0.15 / (i + 1)) * np.sin(2 * np.pi * f * t_m) * lfo
        sub = 0.2 * np.sin(2 * np.pi * 36.7 * t_m)
        music = (drone + sub)
        music = music / (np.max(np.abs(music)) + 1e-6) * 0.4
        fade_len = int(sr * 2.0)
        music[:fade_len] *= np.linspace(0, 1, fade_len)
        music[-fade_len:] *= np.linspace(1, 0, fade_len)
        write_wav("ambient_geo_drone.wav", music)

def load_countries_geojson() -> dict:
    dest = DATA_DIR / "ne_110m_countries.geojson"
    if not dest.exists():
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)

def load_map_units_geojson() -> dict:
    dest = DATA_DIR / "ne_10m_map_units.geojson"
    if not dest.exists():
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)

def load_populated_places_geojson() -> dict:
    dest = DATA_DIR / "ne_110m_populated_places.geojson"
    if not dest.exists():
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)
