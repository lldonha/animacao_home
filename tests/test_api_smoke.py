import json
import time
from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def _wait_for_completion(job_id: str, timeout: float = 30.0) -> dict:
    start = time.time()
    while time.time() - start < timeout:
        response = client.get(f"/status/{job_id}")
        data = response.json()
        if data["status"] in {"completed", "failed"}:
            return data
        time.sleep(0.2)
    raise RuntimeError("Job did not complete in time")


def test_generate_and_render_pipeline(tmp_path: Path, monkeypatch):
    payload = {
        "scene_id": "test_scene",
        "prompt_base": "test prompt",
        "camera": "static",
        "duration": 1,
        "motion_type": "loop",
        "effects": ["bloom"],
    }

    response = client.post("/generate", json=payload)
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    status_data = _wait_for_completion(job_id)
    assert status_data["status"] == "completed"
    assert status_data["frames"], "Frames should be generated"

    render_response = client.post(f"/render/{job_id}")
    assert render_response.status_code == 200
    video_path = Path(render_response.json()["output_video"])
    assert video_path.exists()
    assert video_path.stat().st_size > 0
