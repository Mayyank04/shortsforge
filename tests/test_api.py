from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"ok": True, "service": "shortforge-api"}

def test_create_job():
    payload = {"topic": "A strange history story", "style": "mixed", "duration": 35}
    r = client.post("/api/jobs", json=payload)
    assert r.status_code == 201
    data = r.json()
    assert data["topic"] == "A strange history story"
    assert data["style"] == "mixed"
    assert data["duration"] == 35
    assert data["status"] == "queued"
    assert "id" in data
    assert data["error"] is None
    assert data["output_path"] is None

def test_create_job_validation():
    # Topic too short (< 4 chars)
    r = client.post("/api/jobs", json={"topic": "abc", "style": "mixed", "duration": 35})
    assert r.status_code == 422

    # Invalid style
    r = client.post("/api/jobs", json={"topic": "Valid topic", "style": "unknown_style", "duration": 35})
    assert r.status_code == 422

    # Invalid duration (< 15 or > 60)
    r = client.post("/api/jobs", json={"topic": "Valid topic", "style": "2d", "duration": 5})
    assert r.status_code == 422

def test_list_jobs():
    # Create a job first to ensure list is not empty
    client.post("/api/jobs", json={"topic": "List test topic", "style": "2d", "duration": 20})
    r = client.get("/api/jobs")
    assert r.status_code == 200
    jobs = r.json()
    assert isinstance(jobs, list)
    assert len(jobs) > 0
    assert any(j["topic"] == "List test topic" for j in jobs)

def test_get_job_success():
    created = client.post("/api/jobs", json={"topic": "Get test job", "style": "3d", "duration": 35}).json()
    job_id = created["id"]

    r = client.get(f"/api/jobs/{job_id}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == job_id
    assert data["topic"] == "Get test job"
    assert data["style"] == "3d"

def test_get_job_not_found():
    r = client.get("/api/jobs/non-existent-uuid-12345")
    assert r.status_code == 404
    assert r.json()["detail"] == "Job not found"

def test_update_job_status_running():
    created = client.post("/api/jobs", json={"topic": "Status running test", "style": "2d", "duration": 20}).json()
    job_id = created["id"]

    r = client.post(f"/api/jobs/{job_id}/status", json={"status": "running"})
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "running"
    assert data["error"] is None

def test_update_job_status_completed():
    created = client.post("/api/jobs", json={"topic": "Status completed test", "style": "3d", "duration": 45}).json()
    job_id = created["id"]

    r = client.post(
        f"/api/jobs/{job_id}/status",
        json={"status": "completed", "output_path": "/path/to/video.mp4", "error": None}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "completed"
    assert data["output_path"] == "/path/to/video.mp4"
    assert data["error"] is None

def test_update_job_status_failed_with_error():
    created = client.post("/api/jobs", json={"topic": "Status failed test", "style": "mixed", "duration": 35}).json()
    job_id = created["id"]

    err_msg = "FFmpegError: codec libx264 failed or disk full"
    r = client.post(
        f"/api/jobs/{job_id}/status",
        json={"status": "failed", "error": err_msg}
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "failed"
    assert data["error"] == err_msg

def test_update_job_status_invalid_status():
    created = client.post("/api/jobs", json={"topic": "Invalid status test", "style": "2d", "duration": 20}).json()
    job_id = created["id"]

    r = client.post(f"/api/jobs/{job_id}/status", json={"status": "unknown_status"})
    assert r.status_code == 422

def test_update_job_status_not_found():
    r = client.post("/api/jobs/missing-id/status", json={"status": "running"})
    assert r.status_code == 404
