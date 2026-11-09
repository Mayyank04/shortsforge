import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from PIL import Image

from backend.app.main import app
from worker.geo.geo_resolver import resolve_geo_context
from worker.geo_research import generate_research_notes
from worker.geo_script import make_geo_storyboard
from worker.subtitles import render_scene_overlay
from worker.qc import (
    validate_coordinates,
    validate_narration,
    validate_scene_durations,
    validate_output_video,
    QualityControlError
)

client = TestClient(app)

def test_geo_resolver_gibraltar():
    ctx = resolve_geo_context("Why is Gibraltar British?")
    assert ctx.primary_name == "Gibraltar"
    assert abs(ctx.primary_lat - 36.1408) < 0.01
    assert abs(ctx.primary_lon - (-5.3536)) < 0.01
    assert len(ctx.highlights) >= 3
    # Check that United Kingdom and Spain are present
    names = [h.name for h in ctx.highlights]
    assert "United Kingdom" in names
    assert "Spain" in names
    assert len(ctx.landmarks) >= 3
    assert len(ctx.trade_routes) >= 1

def test_geo_resolver_canonical_topics():
    for topic in ["Why does Russia have an isolated territory?", "Why is the Suez Canal important?"]:
        ctx = resolve_geo_context(topic)
        assert ctx.primary_name in ["Kaliningrad", "Suez Canal"]
        assert -90 <= ctx.primary_lat <= 90
        assert -180 <= ctx.primary_lon <= 180

def test_geo_research_notes():
    research = generate_research_notes("Why is Gibraltar British?")
    assert "Gibraltar" in research.title
    assert len(research.verified_claims) >= 3
    assert len(research.historical_timeline) >= 4
    # Check treaty verification
    treaty_claims = [c for c in research.verified_claims if c.category == "treaty"]
    assert len(treaty_claims) >= 1
    assert "1713" in treaty_claims[0].statement

def test_geo_storyboard_generation():
    sb = make_geo_storyboard("Why is Gibraltar British?", duration=75)
    assert len(sb.scenes) >= 10
    assert len(sb.scenes) <= 18
    # Scene durations should sum up to target duration
    total_dur = sum(s.target_duration for s in sb.scenes)
    assert abs(total_dur - 75.0) < 1.0
    for s in sb.scenes:
        assert s.scene_id.startswith("scene_")
        assert len(s.narration) > 10
        assert -90 <= s.lat <= 90
        assert -180 <= s.lon <= 180
        assert s.camera_distance > 1.0

def test_qc_coordinate_validation():
    # Valid
    validate_coordinates(36.14, -5.35, "Gibraltar")
    validate_coordinates(-33.86, 151.20, "Sydney")

    # Invalid latitude > 90
    try:
        validate_coordinates(91.0, 0.0, "Invalid")
        assert False
    except QualityControlError:
        pass

    # Invalid longitude < -180
    try:
        validate_coordinates(0.0, -185.0, "Invalid")
        assert False
    except QualityControlError:
        pass

def test_qc_scene_durations_validation():
    scenes = [{"target_duration": 10.0}, {"target_duration": 15.0}]
    validate_scene_durations(scenes, target_duration=25.0)

    # Sum mismatch
    try:
        validate_scene_durations(scenes, target_duration=50.0)
        assert False
    except QualityControlError:
        pass

def test_subtitles_safe_overlay():
    base = Image.new("RGB", (1080, 1920), (20, 30, 45))
    with tempfile.TemporaryDirectory() as td:
        out_p = Path(td) / "test_sub.png"
        render_scene_overlay(
            base_image=base,
            scene_index=0,
            total_scenes=12,
            narration_text="On the very southern tip of Spain sits a tiny piece of land guarded by British soldiers.",
            badge_text="GEOPOLITICAL MYSTERY",
            headline_text="The Rock of Gibraltar",
            stat_callout="6.7 km² Territory",
            output_path=out_p
        )
        assert out_p.exists()
        img = Image.open(out_p)
        assert img.size == (1080, 1920)

def test_api_batch_jobs_creation():
    payload = {
        "jobs": [
            {"topic": "Why is Gibraltar British?", "style": "geo_realistic", "duration": 75},
            {"topic": "Why does Russia have an isolated territory?", "style": "geo_political", "duration": 60}
        ]
    }
    r = client.post("/api/jobs/batch", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["topic"] == "Why is Gibraltar British?"
    assert data[1]["topic"] == "Why does Russia have an isolated territory?"

def test_api_retry_and_cancel_job():
    created = client.post(
        "/api/jobs",
        json={"topic": "Job to cancel and retry", "style": "geo_realistic", "duration": 75}
    ).json()
    job_id = created["id"]

    # Cancel
    r_cancel = client.post(f"/api/jobs/{job_id}/cancel")
    assert r_cancel.status_code == 200
    assert r_cancel.json()["status"] == "cancelled"

    # Retry
    r_retry = client.post(f"/api/jobs/{job_id}/retry")
    assert r_retry.status_code == 200
    assert r_retry.json()["status"] == "queued"

def test_api_get_job_logs():
    created = client.post(
        "/api/jobs",
        json={"topic": "Job for logs test", "style": "geo_terrain", "duration": 60}
    ).json()
    job_id = created["id"]

    r_logs = client.get(f"/api/jobs/{job_id}/logs")
    assert r_logs.status_code == 200
    data = r_logs.json()
    assert data["id"] == job_id
    assert "status" in data
