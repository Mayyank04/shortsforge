"""
Geographical data and asset manager for ShortForge AI.
Handles local caching of Natural Earth datasets, Earth textures, country flags, and audio assets.
Includes robust atomic downloads, integrity verification, mirror fallbacks, and retry mechanisms.
"""
from __future__ import annotations
import os
import sys
import time
import urllib.request
import urllib.error
import json
import uuid
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

class AssetDownloadError(RuntimeError):
    """Raised when an asset cannot be downloaded or fails integrity verification."""
    pass

class AssetCorruptionError(ValueError):
    """Raised when a cached or downloaded asset is invalid or corrupt."""
    pass

# Primary and mirror URLs for robust geographical asset retrieval
REMOTE_ASSETS = {
    TEXTURES_DIR / "earth_color_4k.jpg": [
        "https://raw.githubusercontent.com/turban/webgl-earth/master/images/2_no_clouds_4k.jpg",
        "https://eoimages.gsfc.nasa.gov/images/imagerecords/57752/land_shallow_topo_2048.jpg"
    ],
    TEXTURES_DIR / "earth_bump_4k.jpg": [
        "https://raw.githubusercontent.com/turban/webgl-earth/master/images/elev_bump_4k.jpg"
    ],
    TEXTURES_DIR / "earth_water_4k.png": [
        "https://raw.githubusercontent.com/turban/webgl-earth/master/images/water_4k.png"
    ],
    DATA_DIR / "ne_110m_countries.geojson": [
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_admin_0_countries.geojson",
        "https://raw.githubusercontent.com/martyn512/natural-earth-geojson/master/110m/cultural/ne_110m_admin_0_countries.json"
    ],
    DATA_DIR / "ne_10m_map_units.geojson": [
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_0_map_units.geojson"
    ],
    DATA_DIR / "ne_110m_populated_places.geojson": [
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_110m_populated_places_simple.geojson"
    ],
}

# Minimum byte thresholds for verification
ASSET_MIN_SIZES: dict[str, int] = {
    "earth_color_4k.jpg": 100_000,
    "earth_bump_4k.jpg": 50_000,
    "earth_water_4k.png": 50_000,
    "ne_110m_countries.geojson": 50_000,
    "ne_10m_map_units.geojson": 500_000,
    "ne_110m_populated_places.geojson": 10_000,
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
    "cn": "china.png",
    "np": "nepal.png",
    "pl": "poland.png",
    "lt": "lithuania.png",
}

def ensure_directories():
    """Creates local asset directory structure if missing."""
    for d in [TEXTURES_DIR, DATA_DIR, FLAGS_DIR, AUDIO_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def verify_asset_integrity(path: Path, min_bytes: int = 1024, is_json: bool = False) -> bool:
    """
    Verifies that a file exists, meets minimum size requirements,
    and is structurally valid JSON/GeoJSON if expected.
    """
    if not path.exists():
        return False
    size = path.stat().st_size
    if size < min_bytes:
        return False
    if is_json or path.suffix.lower() in [".json", ".geojson"]:
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False
            # Check GeoJSON has features or type
            if path.suffix.lower() == ".geojson" and "features" not in data and "type" not in data:
                return False
        except Exception:
            return False
    return True

def download_file(
    url: str,
    dest: Path,
    timeout: int = 30,
    retries: int = 3,
    backoff_factor: float = 1.5,
    min_size: int = 100,
    is_json: bool | None = None
) -> Path:
    """
    Downloads a remote file with retry, backoff, atomic temporary file replacement,
    and integrity verification.
    """
    if is_json is None:
        is_json = dest.suffix.lower() in [".json", ".geojson"]

    min_bytes = ASSET_MIN_SIZES.get(dest.name, min_size)

    # Return cached file if already valid
    if dest.exists() and verify_asset_integrity(dest, min_bytes=min_bytes, is_json=is_json):
        return dest

    dest.parent.mkdir(parents=True, exist_ok=True)
    temp_path = dest.with_name(f"{dest.name}.tmp.{uuid.uuid4().hex[:8]}")

    last_error: Exception | None = None
    user_agent = os.getenv("SHORTFORGE_HTTP_USER_AGENT", "ShortForgeAI/2.0")

    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": user_agent})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                content = response.read()

            with open(temp_path, "wb") as f:
                f.write(content)

            # Integrity check on temporary file
            if not verify_asset_integrity(temp_path, min_bytes=min_bytes, is_json=is_json):
                temp_size = temp_path.stat().st_size if temp_path.exists() else 0
                raise AssetCorruptionError(
                    f"Asset from {url} failed verification (size={temp_size} bytes, min required={min_bytes}, is_json={is_json})"
                )

            # Atomic replacement
            os.replace(temp_path, dest)
            return dest

        except Exception as exc:
            last_error = exc
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass
            if attempt < retries:
                sleep_sec = backoff_factor ** attempt
                time.sleep(sleep_sec)

    raise AssetDownloadError(
        f"Failed to download asset {dest.name} from {url} after {retries} attempts: {last_error}"
    )

def ensure_geo_assets(timeout: int = 30, retries: int = 3) -> dict[str, Path]:
    """
    Ensures all essential geographical textures and Natural Earth datasets exist.
    Tries primary and fallback mirrors for each asset. Never creates mock or fake data.
    """
    ensure_directories()
    results: dict[str, Path] = {}

    for dest, urls in REMOTE_ASSETS.items():
        min_bytes = ASSET_MIN_SIZES.get(dest.name, 1024)
        is_json = dest.suffix.lower() in [".json", ".geojson"]

        # Already cached and valid
        if dest.exists() and verify_asset_integrity(dest, min_bytes=min_bytes, is_json=is_json):
            results[dest.name] = dest
            continue

        url_list = urls if isinstance(urls, list) else [urls]
        downloaded = False
        last_exc = None

        for u in url_list:
            try:
                download_file(
                    u, dest,
                    timeout=timeout,
                    retries=retries,
                    min_size=min_bytes,
                    is_json=is_json
                )
                results[dest.name] = dest
                downloaded = True
                break
            except Exception as exc:
                last_exc = exc

        if not downloaded:
            raise AssetDownloadError(
                f"Critical geographical asset '{dest.name}' could not be obtained from any mirror: {last_exc}. "
                "Accurate geography rendering cannot proceed without valid Natural Earth datasets."
            )

    return results

def get_flag_path(country_code: str, timeout: int = 15, retries: int = 2) -> Path | None:
    """Gets or downloads the flag for a given ISO 2-letter country code."""
    ensure_directories()
    code = country_code.lower().strip()
    dest = FLAGS_DIR / f"{FLAG_URLS.get(code, f'{code}.png')}"

    if dest.exists() and dest.stat().st_size > 100:
        return dest

    mirrors = [
        f"https://flagcdn.com/w320/{code}.png",
        f"https://raw.githubusercontent.com/hampusborgos/country-flags/main/png250px/{code}.png"
    ]

    for url in mirrors:
        try:
            download_file(url, dest, timeout=timeout, retries=retries, min_size=80, is_json=False)
            return dest
        except Exception:
            pass

    print(f"Warning: Could not fetch flag for '{country_code}' from any mirror.")
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
    if not dest.exists() or not verify_asset_integrity(dest, min_bytes=ASSET_MIN_SIZES["ne_110m_countries.geojson"], is_json=True):
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)

def load_map_units_geojson() -> dict:
    dest = DATA_DIR / "ne_10m_map_units.geojson"
    if not dest.exists() or not verify_asset_integrity(dest, min_bytes=ASSET_MIN_SIZES["ne_10m_map_units.geojson"], is_json=True):
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)

def load_populated_places_geojson() -> dict:
    dest = DATA_DIR / "ne_110m_populated_places.geojson"
    if not dest.exists() or not verify_asset_integrity(dest, min_bytes=ASSET_MIN_SIZES["ne_110m_populated_places.geojson"], is_json=True):
        ensure_geo_assets()
    with open(dest, "r", encoding="utf-8") as f:
        return json.load(f)
