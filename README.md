# CareFlow Clinical Workflow System

CareFlow is a production-ready FastAPI and SQLite backend that simulates an internal clinical workflow system. It focuses on deterministic patient-care operations: clinicians publish advisories, schedules are generated, patient responses are recorded, rules are evaluated, and alerts are written with an auditable event trail.

This project intentionally avoids authentication, AI features, chatbot behavior, analytics dashboards, and decorative UI patterns.

## Core Workflow

1. Clinician publishes an advisory.
2. CareFlow stores an immutable `advisory_created` event.
3. CareFlow generates schedule entries and stores a `schedule_generated` event.
4. Patient response is recorded through `/responses`.
5. A plain Python rule engine evaluates the response and missed schedules.
6. Alerts are created when deterministic rules match and `alert_triggered` events are appended.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLite
- SQLAlchemy
- Pydantic
- Jinja2 templates
- Uvicorn
- Pytest

## Project Structure

```text
app/
  database/    SQLAlchemy setup and startup initialization
  logs/        Reserved for local operational logs
  models/      Database models
  routes/      API and server-rendered UI routes
  rules/       Deterministic rule engine
  schemas/     Pydantic request and response schemas
  services/    Workflow business logic
  static/      Minimal CSS
  templates/   Server-rendered HTML
  utils/       Logging, validation, errors, IDs
main.py
requirements.txt
Procfile
railway.json
Dockerfile
.env.example
```

## Local Development

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open:

- UI: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health

The SQLite database is created automatically on startup if it does not exist.

## Environment Variables

| Variable | Default | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./careflow.db` | SQLite database location |
| `PORT` | `8000` | Runtime port |
| `LOG_LEVEL` | `INFO` | Structured logging level |

## API Examples

Create an advisory:

```bash
curl -X POST http://localhost:8000/advisories \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: advisory-P001-001" \
  -d '{
    "patient_id": "P001",
    "clinician_name": "Dr Sharma",
    "instruction": "Record blood sugar every morning",
    "schedule_type": "daily",
    "time": "08:00"
  }'
```

`patient_id` may be omitted. CareFlow will generate a stable internal patient ID for the advisory.

List advisories:

```bash
curl http://localhost:8000/advisories
```

Filter advisories:

```bash
curl "http://localhost:8000/advisories?q=P001"
```

Get a patient schedule:

```bash
curl http://localhost:8000/patients/P001/schedule
```

Record a patient response:

```bash
curl -X POST http://localhost:8000/responses \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: response-P001-001" \
  -d '{
    "patient_id": "P001",
    "schedule_id": "SCH_REPLACE_WITH_REAL_ID",
    "observation_type": "blood_sugar",
    "value": 320
  }'
```

List alerts:

```bash
curl http://localhost:8000/alerts
```

Filter alerts:

```bash
curl "http://localhost:8000/alerts?patient_id=P001&q=HIGH"
```

## Idempotency

`POST /advisories` and `POST /responses` support the `Idempotency-Key` header. If the same key and request body are retried, CareFlow returns the original response without creating duplicate advisories, responses, schedules, alerts, or events. If the same key is reused with a different request body, CareFlow returns `409 Conflict`.

## Rule Engine

Rules are implemented in `app/rules/engine.py` as readable deterministic Python functions:

- `blood_sugar > 300` creates a `HIGH` alert.
- `heart_rate > 120` creates a `HIGH` alert.
- `missed schedules >= 3` creates a `MEDIUM` alert.

No machine learning or predictive logic is used.

## Event Ledger

The `event_ledger` table is append-only at the application layer. Supported event types:

- `advisory_created`
- `schedule_generated`
- `response_recorded`
- `alert_triggered`

Operational tables such as `advisories`, `schedules`, `patient_responses`, and `alerts` are read snapshots used for efficient workflow screens and API responses.

## Testing

```bash
pytest
```

Included tests cover:

- Health checks
- Advisory validation
- Schedule generation
- Idempotent advisory creation
- Idempotency conflicts
- Response ingestion
- Alert triggering
- Rule engine thresholds

## Railway Deployment

Railway can run this project without additional manual setup.

1. Create a new Railway project from the GitHub repository.
2. Railway will use the included `railway.json` start command.
3. Optionally set `DATABASE_URL` to a persistent SQLite file path.
4. Railway should use `/health` as the health check endpoint.

Start command:

```bash
uvicorn main:app --host 0.0.0.0 --port $PORT
```

The included `Procfile` contains the same command:

```text
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

## Docker

Build and run locally:

```bash
docker build -t careflow .
docker run -p 8000:8000 -e PORT=8000 careflow
```

## Production Notes

- The app logs API requests, validation failures, database failures, advisory creation, response ingestion, and alert creation as structured JSON.
- SQLite transactions are used around workflow writes.
- Startup automatically initializes the schema.
- The UI is intentionally minimal and server-rendered for operational reliability.
- Schema migration tooling can be added later if the database contract evolves beyond this MVP.
