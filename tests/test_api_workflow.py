def advisory_payload(**overrides):
    payload = {
        "patient_id": "P001",
        "clinician_name": "Dr Sharma",
        "instruction": "Record blood sugar every morning",
        "schedule_type": "daily",
        "time": "08:00",
    }
    payload.update(overrides)
    return payload


def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ui_home_renders_publish_form(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "Publish Advisory" in response.text
    assert "Patient ID" in response.text


def test_create_advisory_generates_schedules_and_events(client):
    response = client.post(
        "/advisories",
        json=advisory_payload(),
        headers={"Idempotency-Key": "advisory-001"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["advisory"]["patient_id"] == "P001"
    assert body["advisory"]["advisory_id"].startswith("ADV")
    assert len(body["schedules"]) == 7
    assert len(body["event_ids"]) == 2


def test_create_advisory_auto_generates_patient_id(client):
    payload = advisory_payload()
    payload.pop("patient_id")

    response = client.post("/advisories", json=payload)

    assert response.status_code == 201
    patient_id = response.json()["advisory"]["patient_id"]
    assert patient_id.startswith("P")
    assert len(patient_id) == 9


def test_advisory_validation_rejects_bad_time(client):
    response = client.post("/advisories", json=advisory_payload(time="25:00"))

    assert response.status_code == 422


def test_advisory_idempotency_returns_cached_response(client):
    headers = {"Idempotency-Key": "same-advisory"}

    first = client.post("/advisories", json=advisory_payload(), headers=headers)
    second = client.post("/advisories", json=advisory_payload(), headers=headers)
    advisories = client.get("/advisories")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["advisory"]["advisory_id"] == second.json()["advisory"]["advisory_id"]
    assert len(advisories.json()) == 1


def test_advisory_search_filters_results(client):
    first = client.post("/advisories", json=advisory_payload(patient_id="P-FILTER-1")).json()
    client.post("/advisories", json=advisory_payload(patient_id="P-FILTER-2", instruction="Record heart rate"))

    response = client.get("/advisories", params={"q": first["advisory"]["advisory_id"]})

    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["patient_id"] == "P-FILTER-1"


def test_idempotency_key_conflict(client):
    headers = {"Idempotency-Key": "conflict-key"}

    first = client.post("/advisories", json=advisory_payload(), headers=headers)
    second = client.post(
        "/advisories",
        json=advisory_payload(patient_id="P002"),
        headers=headers,
    )

    assert first.status_code == 201
    assert second.status_code == 409


def test_response_ingestion_triggers_alert_and_is_idempotent(client):
    advisory = client.post("/advisories", json=advisory_payload()).json()
    schedule_id = advisory["schedules"][0]["schedule_id"]
    payload = {
        "patient_id": "P001",
        "schedule_id": schedule_id,
        "observation_type": "blood_sugar",
        "value": 320,
    }
    headers = {"Idempotency-Key": "response-001"}

    first = client.post("/responses", json=payload, headers=headers)
    second = client.post("/responses", json=payload, headers=headers)
    alerts = client.get("/alerts")

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["response"]["response_id"] == second.json()["response"]["response_id"]
    assert first.json()["alerts"][0]["severity"] == "HIGH"
    assert len(alerts.json()) == 1
