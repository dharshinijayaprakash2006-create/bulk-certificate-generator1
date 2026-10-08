\# Bulk Certificate Generator API



FastAPI + SQLAlchemy (SQLite) + reportlab.



\## Setup

```

python -m venv venv

venv\\Scripts\\activate        # Mac/Linux: source venv/bin/activate

pip install -r requirements.txt

```



\## Run

```

uvicorn app.main:app --reload

```

Interactive docs: http://127.0.0.1:8000/docs



\## Test

```

python -m pytest -v

```



\## Submit a request

```

curl -X POST http://127.0.0.1:8000/jobs -H "Content-Type: application/json" -d '{

&#x20; "event\_name": "Python Workshop 2026",

&#x20; "issue\_date": "2026-10-08",

&#x20; "recipients": \[

&#x20;   {"name": "Asha Rao", "email": "asha@example.com"},

&#x20;   {"name": "", "email": "bad"}

&#x20; ]

}'

```

Returns `202` with a `job\_id`.



\## Check progress

`GET /jobs/{job\_id}` returns status, succeeded/failed/pending counts, progress %, and per-recipient results with error messages.



\## Retrieve certificates

\- One PDF: `GET /certificates/{id}/download`

\- All successful PDFs as ZIP: `GET /jobs/{job\_id}/download`



\## Design decisions

\- \*\*Background processing\*\* (FastAPI BackgroundTasks): large jobs would block or time out a synchronous request. The client gets a job ID immediately and polls. Trade-off: jobs in flight are lost if the server restarts. For production I would use Celery/RQ with Redis and a retry for stuck jobs.

\- \*\*Two-layer validation\*\*: request-level problems (no recipients, no event name, over 1000 recipients) return 422. Recipient-level problems (empty name, bad email) do not reject the request; that recipient is saved as `failed` with a reason.

\- \*\*Isolated failures\*\*: each certificate is generated in its own try/except, so one failure does not stop the others.

\- \*\*One row per recipient\*\* in the `certificates` table gives per-recipient status and errors.

\- \*\*SQLite\*\* for zero setup; swap via the `DATABASE\_URL` env var (e.g. PostgreSQL).

\- \*\*Single template\*\* in `app/services/generator.py` (landscape A4 PDF); long names shrink to fit.



\## Known limitations

\- Built-in PDF fonts only cover Latin characters; other scripts would need a bundled TTF font.

\- No authentication or rate limiting.

\- Max 1000 recipients per request.

