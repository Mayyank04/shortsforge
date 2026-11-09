"""
Unit and integration tests for ShortForge AI — Phase 2A: Production Hardening.
Tests:
1. Geography asset manager (atomic downloads, integrity checks, retries, error handling, signature preservation)
2. Cross-platform Blender detection (macOS, Linux, Windows, BLENDER_BIN, version query, error capture)
3. Kaggle notebook configuration & workflow validation
4. Real Blender execution verification
"""
import os
import sys
import json
import shutil
import tempfile
import urllib.error
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from worker.geo.data_manager import (
    verify_asset_integrity,
    download_file,
    ensure_geo_assets,
    get_flag_path,
    generate_default_audio_assets,
    load_countries_geojson,
    load_map_units_geojson,
    load_populated_places_geojson,
    AssetDownloadError,
    AssetCorruptionError,
    ASSET_MIN_SIZES
)
from worker.blender_render import (
    find_blender_binary,
    get_blender_version,
    verify_blender_available,
    render_blender_scene,
    BlenderRenderError
)

# ---------------------------------------------------------------------------
# 1. Geography Asset Manager Tests
# ---------------------------------------------------------------------------

def test_verify_asset_integrity_valid_geojson():
    with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as tf:
        json.dump({"type": "FeatureCollection", "features": [{"type": "Feature"}]}, tf)
        tmp_name = tf.name

    try:
        p = Path(tmp_name)
        assert verify_asset_integrity(p, min_bytes=10, is_json=True) is True
        # Fails if required size is larger than actual file
        assert verify_asset_integrity(p, min_bytes=10000, is_json=True) is False
    finally:
        os.remove(tmp_name)

def test_verify_asset_integrity_corrupted_json():
    with tempfile.NamedTemporaryFile("w", suffix=".geojson", delete=False) as tf:
        tf.write("{ this is invalid json content")
        tmp_name = tf.name

    try:
        p = Path(tmp_name)
        assert verify_asset_integrity(p, min_bytes=5, is_json=True) is False
    finally:
        os.remove(tmp_name)

def test_verify_asset_integrity_nonexistent_file():
    p = Path("/tmp/nonexistent_asset_xyz.json")
    assert verify_asset_integrity(p) is False

def test_download_file_atomic_replacement():
    """Verifies download goes to temporary file first before atomically replacing dest."""
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "test_data.geojson"
        valid_json_bytes = b'{"type": "FeatureCollection", "features": []}'

        mock_resp = MagicMock()
        mock_resp.read.return_value = valid_json_bytes
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = None

        with patch("urllib.request.urlopen", return_value=mock_resp):
            result = download_file("https://example.com/data.geojson", dest, min_size=10, is_json=True)
            assert result == dest
            assert dest.exists()
            assert dest.read_bytes() == valid_json_bytes
            # Ensure no orphan .tmp files left in the directory
            assert len(list(Path(td).glob("*.tmp.*"))) == 0

def test_download_file_retry_and_backoff():
    """Verifies download retries on transient network failures and eventually succeeds."""
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "test_retry.geojson"
        valid_bytes = b'{"type": "FeatureCollection", "features": []}'

        mock_resp = MagicMock()
        mock_resp.read.return_value = valid_bytes
        mock_resp.__enter__.return_value = mock_resp
        mock_resp.__exit__.return_value = None

        # Fail twice with URLError, then succeed
        calls = [
            urllib.error.URLError("Connection reset"),
            urllib.error.URLError("Timeout"),
            mock_resp
        ]

        def side_effect(*args, **kwargs):
            val = calls.pop(0)
            if isinstance(val, Exception):
                raise val
            return val

        with patch("urllib.request.urlopen", side_effect=side_effect):
            with patch("time.sleep") as mock_sleep:
                res = download_file(
                    "https://example.com/retry.geojson",
                    dest,
                    retries=3,
                    backoff_factor=1.2,
                    min_size=10,
                    is_json=True
                )
                assert res == dest
                assert dest.exists()
                assert mock_sleep.call_count == 2

def test_download_file_exhaust_retries_raises_error():
    """Verifies AssetDownloadError is raised with descriptive context when all retries fail."""
    with tempfile.TemporaryDirectory() as td:
        dest = Path(td) / "test_failed.geojson"

        with patch("urllib.request.urlopen", side_effect=urllib.error.URLError("Gateway Timeout")):
            with patch("time.sleep"):
                with pytest.raises(AssetDownloadError) as exc_info:
                    download_file("https://example.com/fail.geojson", dest, retries=2, min_size=10)
                assert "Failed to download asset test_failed.geojson" in str(exc_info.value)
                assert not dest.exists()

def test_ensure_geo_assets_uses_cache():
    """Verifies existing cached datasets are returned without network downloads."""
    with patch("worker.geo.data_manager.download_file") as mock_dl:
        assets = ensure_geo_assets()
        assert len(assets) >= 3
        # If files exist on disk with valid integrity, download_file should not be invoked
        assert mock_dl.call_count == 0

def test_data_manager_signature_preservation():
    """Verifies all public functions preserve expected signatures and return types."""
    assert callable(ensure_geo_assets)
    assert callable(get_flag_path)
    assert callable(generate_default_audio_assets)
    assert callable(load_countries_geojson)
    assert callable(load_map_units_geojson)
    assert callable(load_populated_places_geojson)

    # Calling cached loaders returns valid dicts
    countries = load_countries_geojson()
    assert isinstance(countries, dict)
    assert "features" in countries

    map_units = load_map_units_geojson()
    assert isinstance(map_units, dict)
    assert "features" in map_units

    pop_places = load_populated_places_geojson()
    assert isinstance(pop_places, dict)
    assert "features" in pop_places


# ---------------------------------------------------------------------------
# 2. Cross-Platform Blender Detection Tests
# ---------------------------------------------------------------------------

def test_blender_env_var_detection():
    with tempfile.NamedTemporaryFile("w", delete=False) as tf:
        tf.write("#!/bin/sh\nexit 0\n")
        fake_blender = Path(tf.name)
    os.chmod(fake_blender, 0o755)

    try:
        with patch.dict(os.environ, {"BLENDER_BIN": str(fake_blender)}):
            resolved = find_blender_binary()
            assert resolved == fake_blender.resolve()
    finally:
        os.remove(fake_blender)

def test_blender_env_var_invalid_raises():
    with patch.dict(os.environ, {"BLENDER_BIN": "/no/such/blender_bin_999"}):
        with pytest.raises(FileNotFoundError) as exc_info:
            find_blender_binary()
        assert "BLENDER_BIN environment variable is set to" in str(exc_info.value)

def test_blender_which_fallback():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("BLENDER_BIN", None)
        with patch("shutil.which", return_value="/custom/bin/blender"):
            with patch.object(Path, "is_file", return_value=True):
                resolved = find_blender_binary()
                assert resolved == Path("/custom/bin/blender")

def test_blender_platform_search_linux():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("BLENDER_BIN", None)
        with patch("shutil.which", return_value=None):
            with patch("sys.platform", "linux"):
                def fake_is_file(self):
                    return str(self) == "/usr/bin/blender"
                def fake_access(path, mode):
                    return True
                with patch.object(Path, "is_file", fake_is_file):
                    with patch("os.access", fake_access):
                        resolved = find_blender_binary()
                        assert resolved == Path("/usr/bin/blender")

def test_blender_platform_search_windows():
    with patch.dict(os.environ, {"PROGRAMFILES": "C:\\Program Files"}, clear=False):
        os.environ.pop("BLENDER_BIN", None)
        with patch("shutil.which", return_value=None):
            with patch("sys.platform", "win32"):
                fake_win_path = Path("C:/Program Files/Blender Foundation/Blender 4.2/blender.exe")
                with patch.object(Path, "glob", return_value=[fake_win_path]):
                    with patch.object(Path, "is_file", return_value=True):
                        resolved = find_blender_binary()
                        assert resolved == fake_win_path

def test_blender_not_found_raises():
    with patch.dict(os.environ, {}, clear=False):
        os.environ.pop("BLENDER_BIN", None)
        with patch("shutil.which", return_value=None):
            with patch.object(Path, "is_file", return_value=False):
                with patch.object(Path, "glob", return_value=[]):
                    with pytest.raises(FileNotFoundError) as exc_info:
                        find_blender_binary()
                    assert "Blender executable not found" in str(exc_info.value)

def test_get_blender_version_real_or_mock():
    mock_sub = MagicMock()
    mock_sub.stdout = "Blender 4.2.1 LTS\nbuild date: 2026-08-15\n"
    mock_sub.returncode = 0
    with patch("subprocess.run", return_value=mock_sub):
        v = get_blender_version("/usr/bin/blender")
        assert v == "Blender 4.2.1 LTS"

def test_blender_render_error_capture():
    mock_sub = MagicMock()
    mock_sub.returncode = 1
    mock_sub.stdout = "Fra:1 Mem:12.4M\nRendering failed!"
    mock_sub.stderr = "Error: Out of memory or invalid texture path\n"

    with patch("worker.blender_render.find_blender_binary", return_value=Path("/mock/blender")):
        with patch("subprocess.run", return_value=mock_sub):
            with pytest.raises(BlenderRenderError) as exc_info:
                render_blender_scene(
                    scene_spec_dict={"lat": 36.14, "lon": -5.35},
                    geo_context_dict={},
                    texture_path=Path("/tmp/tex.jpg"),
                    output_path=Path("/tmp/out.png"),
                    blender_bin="/mock/blender"
                )
            assert exc_info.value.returncode == 1
            assert "Error: Out of memory" in exc_info.value.stderr
            assert "Blender failed with exit code 1" in str(exc_info.value)


# ---------------------------------------------------------------------------
# 3. Kaggle Configuration Validation Tests
# ---------------------------------------------------------------------------

def test_kaggle_notebook_validity_and_contents():
    nb_path = Path(__file__).resolve().parent.parent / "notebooks" / "shortforge_kaggle.ipynb"
    assert nb_path.exists(), "notebooks/shortforge_kaggle.ipynb must exist"

    with open(nb_path, "r", encoding="utf-8") as f:
        nb = json.load(f)

    assert "cells" in nb
    assert nb["nbformat"] >= 4

    all_code = "\n".join("".join(c["source"]) for c in nb["cells"] if c["cell_type"] == "code")

    # 1. Configurable repo and zip alternative
    assert "REPO_URL" in all_code
    assert "ZIP_PATH" in all_code
    assert "zipfile.ZipFile" in all_code

    # 2. Installs ffmpeg, blender, and espeak-ng
    assert "apt-get install" in all_code
    assert "ffmpeg" in all_code
    assert "blender" in all_code
    assert "espeak-ng" in all_code

    # 3. Geo assets pre-fetch
    assert "ensure_geo_assets" in all_code
    assert "generate_default_audio_assets" in all_code

    # 4. Kokoro TTS with explicit espeak-ng fallback
    assert "synthesize_narration" in all_code
    assert 'os.environ["TTS_ENGINE"] = "system"' in all_code

    # 5. Preview render first
    assert "--preview" in all_code
    assert "RUN_PREVIEW_FIRST" in all_code

    # 6. Output to /kaggle/working and zip download
    assert "/kaggle/working/outputs" in all_code
    assert "shortforge_outputs.zip" in all_code
    assert "FileLink" in all_code


# ---------------------------------------------------------------------------
# 4. Real Host Environment Verification
# ---------------------------------------------------------------------------

def test_real_blender_host_execution():
    """Tests that the real host machine Blender is found, executes, and reports its version."""
    bin_path, version = verify_blender_available()
    assert bin_path.exists()
    assert "Blender" in version
    print(f"\n[Real Host Check] Verified Blender executable: {bin_path} -> {version}")
