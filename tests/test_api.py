import io
import zipfile

from app.services import processor
from app.services.generator import generate_certificate

VALID = {
    "event_name": "Python Workshop",
    "issue_date": "2026-10-08",
    "recipients": [
        {"name": "Asha Rao", "email": "asha@example.com"},
        {"name": "Ravi Kumar", "email": "ravi@example.com"},
    ],
}


def submit(client, payload):
    r = client.post("/jobs", json=payload)
    assert r.status_code == 202
    return r.json()["job_id"]


def status(client, job_id):
    return client.get(f"/jobs/{job_id}").json()


# 1. Creating a generation job
def test_create_job(client):
    r = client.post("/jobs", json=VALID)
    assert r.status_code == 202
    body = r.json()
    assert body["job_id"] > 0
    assert body["total"] == 2


# 2. Input validation
def test_empty_recipients_rejected(client):
    assert client.post("/jobs", json={**VALID, "recipients": []}).status_code == 422


def test_missing_event_name_rejected(client):
    payload = {k: v for k, v in VALID.items() if k != "event_name"}
    assert client.post("/jobs", json=payload).status_code == 422


def test_invalid_recipients_marked_failed(client):
    payload = {**VALID, "recipients": [
        {"name": "Good Person"},
        {"name": "", "email": "a@b.com"},
        {"name": "Bad Email", "email": "nope"},
    ]}
    s = status(client, submit(client, payload))
    assert s["succeeded"] == 1
    assert s["failed"] == 2
    assert s["status"] == "completed_with_errors"
    failed = [c for c in s["certificates"] if c["status"] == "failed"]
    assert all(c["error_message"] for c in failed)


# 3. Certificate generation
def test_pdf_generation(tmp_path):
    out = tmp_path / "c.pdf"
    generate_certificate("Asha Rao", "Python Workshop", "2026-10-08", str(out))
    assert out.read_bytes().startswith(b"%PDF")


def test_very_long_name_does_not_crash(tmp_path):
    out = tmp_path / "long.pdf"
    generate_certificate("A" * 95, "Event", "2026-10-08", str(out))
    assert out.exists()


# 4. Job status / progress
def test_job_progress(client):
    s = status(client, submit(client, VALID))
    assert s["status"] == "completed"
    assert s["succeeded"] + s["failed"] == s["total"] == 2
    assert s["progress_percent"] == 100.0
    assert s["pending"] == 0


def test_unknown_job_404(client):
    assert client.get("/jobs/999999").status_code == 404


# 5. Individual failure handling
def test_one_failure_does_not_stop_others(client, monkeypatch):
    real = processor.generate_certificate

    def flaky(name, *args, **kwargs):
        if name == "Boom":
            raise RuntimeError("disk exploded")
        return real(name, *args, **kwargs)

    monkeypatch.setattr(processor, "generate_certificate", flaky)
    payload = {**VALID, "recipients": [{"name": "Alice"}, {"name": "Boom"}, {"name": "Carol"}]}
    s = status(client, submit(client, payload))
    assert s["succeeded"] == 2
    assert s["failed"] == 1
    bad = next(c for c in s["certificates"] if c["name"] == "Boom")
    assert "disk exploded" in bad["error_message"]


# 6. Retrieving generated certificates
def test_download_single_certificate(client):
    s = status(client, submit(client, VALID))
    r = client.get(s["certificates"][0]["download_url"])
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF")


def test_download_failed_certificate_404(client):
    payload = {**VALID, "recipients": [{"name": ""}]}
    s = status(client, submit(client, payload))
    cert_id = s["certificates"][0]["id"]
    assert client.get(f"/certificates/{cert_id}/download").status_code == 404


def test_download_zip(client):
    job_id = submit(client, VALID)
    r = client.get(f"/jobs/{job_id}/download")
    assert r.status_code == 200
    assert len(zipfile.ZipFile(io.BytesIO(r.content)).namelist()) == 2