import sys, tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from PIL import Image

from worker.visuals import make_scene, font, wrap_text_to_width, SAFE_X_MIN, SAFE_X_MAX, SAFE_Y_CAPTION_MIN, SAFE_Y_CAPTION_MAX
from worker.script import make_script, split_scenes
from worker.cli import main as cli_main

def test_script_and_scene_splitting():
    # Test deterministic fallback script template
    with patch.dict("os.environ", {"OLLAMA_MODEL": ""}):
        script = make_script("The mystery of the lost ship", 25)
        assert "lost ship" in script.lower()
        assert "what if" in script.lower()
        scenes = split_scenes(script, 6)
        assert len(scenes) == 6
        for s in scenes:
            assert isinstance(s, str) and len(s) > 0

def test_make_script_live_or_fallback():
    script = make_script("Ancient deep sea creatures", 20)
    assert isinstance(script, str) and len(script) > 20
    # Ensure stage directions like (0s-2s) or Narrator: are removed
    assert "(0s" not in script
    assert "Narrator:" not in script

def test_make_scene_dimensions_and_safe_margins():
    with tempfile.TemporaryDirectory() as td:
        img_path = Path(td) / "scene_test.png"
        text = "This is a test narration caption for vertical video scene layout."
        make_scene(text, index=0, style="mixed", output=img_path)

        assert img_path.exists()
        img = Image.open(img_path)
        assert img.size == (1080, 1920)

def test_caption_text_overflow_prevention_long_text():
    with tempfile.TemporaryDirectory() as td:
        img_path = Path(td) / "scene_long.png"
        # 50 words - long narration line
        long_text = (
            "This is an exceptionally long voiceover sentence containing numerous descriptive words "
            "intended to specifically test whether the dynamic typography algorithm correctly adjusts font size, "
            "wraps words into multiple balanced lines without clipping, and strictly respects vertical video safety margins."
        )
        make_scene(long_text, index=2, style="2d", output=img_path)
        assert img_path.exists()
        img = Image.open(img_path)
        assert img.size == (1080, 1920)

def test_all_scene_styles_and_indices():
    with tempfile.TemporaryDirectory() as td:
        for idx in range(6):
            for style in ["mixed", "2d", "3d"]:
                out = Path(td) / f"scene_{style}_{idx}.png"
                make_scene(f"Scene {idx} testing {style} visual style.", index=idx, style=style, output=out)
                assert out.exists()

def test_worker_cli_validation_missing_args():
    # If neither --topic nor --job-id is supplied, should exit with error
    with patch.object(sys, "argv", ["cli"]):
        try:
            cli_main()
            assert False, "Should have raised SystemExit"
        except SystemExit as exc:
            assert exc.code != 0

def test_worker_cli_successful_job_render():
    # Mock requests and render to test CLI flow with --job-id
    mock_job = {
        "id": "test-job-uuid-1",
        "topic": "The mystery of deep ocean caves",
        "style": "2d",
        "duration": 20,
        "status": "queued"
    }

    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post, \
         patch("worker.cli.render") as mock_render, \
         patch.object(sys, "argv", ["cli", "--job-id", "test-job-uuid-1", "--api-url", "http://127.0.0.1:8000"]):

        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_job, raise_for_status=lambda: None)
        mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)
        mock_render.return_value = (Path("outputs/test.mp4"), "Generated script text")

        cli_main()

        # Check that job was fetched
        mock_get.assert_called_once_with("http://127.0.0.1:8000/api/jobs/test-job-uuid-1", timeout=10)

        # Check status was updated to running, then completed
        assert mock_post.call_count == 2
        first_post_call = mock_post.call_args_list[0]
        assert first_post_call[1]["json"] == {"status": "running"}

        second_post_call = mock_post.call_args_list[1]
        assert second_post_call[1]["json"]["status"] == "completed"
        assert second_post_call[1]["json"]["error"] is None

def test_worker_cli_failed_job_render():
    # Test that failed renders update status to failed with error message
    mock_job = {
        "id": "test-job-failed-1",
        "topic": "A topic that triggers render error",
        "style": "3d",
        "duration": 20,
        "status": "queued"
    }

    with patch("requests.get") as mock_get, \
         patch("requests.post") as mock_post, \
         patch("worker.cli.render", side_effect=RuntimeError("FFmpeg encoding failed: exit code 1")), \
         patch.object(sys, "argv", ["cli", "--job-id", "test-job-failed-1", "--api-url", "http://127.0.0.1:8000"]):

        mock_get.return_value = MagicMock(status_code=200, json=lambda: mock_job, raise_for_status=lambda: None)
        mock_post.return_value = MagicMock(status_code=200, raise_for_status=lambda: None)

        try:
            cli_main()
            assert False, "Should have raised SystemExit on error"
        except SystemExit as exc:
            assert exc.code == 1

        # Check that failure was posted to API
        assert mock_post.call_count == 2
        failure_call = mock_post.call_args_list[1]
        assert failure_call[1]["json"]["status"] == "failed"
        assert "RuntimeError: FFmpeg encoding failed" in failure_call[1]["json"]["error"]

