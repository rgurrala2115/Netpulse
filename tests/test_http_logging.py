from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.database import get_session
from app.db.models import Base
from app.logging_config import configure_logging, redact_sensitive_fields
from app.main import app


@pytest.fixture
def temporary_app(tmp_path):
    configure_logging()
    engine = create_engine(
        f"sqlite:///{tmp_path / 'http.db'}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)

    def override_get_session() -> Iterator[Session]:
        session = Session(engine)
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    app.dependency_overrides[get_session] = override_get_session
    try:
        with TestClient(app) as client:
            yield client
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_request_ids_and_duplicate(temporary_app):
    device = {
        "device_id": "RTR-401",
        "name": "Branch Router",
        "device_type": "router",
        "ip_address": "10.0.0.41",
        "status": "online",
    }
    first = temporary_app.post("/devices", json=device, headers={"X-Request-ID": "lab-trace-401"})
    assert first.status_code == 201
    assert first.headers["X-Request-ID"] == "lab-trace-401"

    duplicate = temporary_app.post("/devices", json=device)
    assert duplicate.status_code == 409
    assert duplicate.headers["X-Request-ID"]

    missing = temporary_app.get("/devices/unknown-404", headers={"X-Request-ID": "lab-trace-404"})
    assert missing.status_code == 404
    assert missing.json() == {"detail": "Device not found"}


def test_invalid_request_id_is_replaced(temporary_app):
    response = temporary_app.get("/health", headers={"X-Request-ID": "bad header!"})
    request_id = response.headers["X-Request-ID"]
    assert request_id.isalnum()
    assert len(request_id) == 32


def test_status_alert_probe_and_summary(temporary_app):
    temporary_app.post("/devices", json={
        "device_id": "RTR-402",
        "name": "Branch Router",
        "device_type": "router",
        "ip_address": "10.0.0.42",
        "status": "online",
    })
    temporary_app.post("/devices", json={
        "device_id": "SW-402",
        "name": "Floor Switch",
        "device_type": "switch",
        "ip_address": "10.0.0.43",
        "status": "online",
    })

    invalid = temporary_app.patch("/devices/RTR-402/status", json={"status": "unknown"})
    assert invalid.status_code == 422

    first = temporary_app.patch(
        "/devices/RTR-402/status",
        json={"status": "offline"},
        headers={"X-Request-ID": "lab-trace-402"},
    )
    second = temporary_app.patch("/devices/RTR-402/status", json={"status": "offline"})
    assert first.status_code == 200
    assert second.status_code == 200

    alerts = temporary_app.get("/alerts").json()
    assert len([alert for alert in alerts if alert["device_id"] == "RTR-402"]) == 1

    probe = temporary_app.get("/devices/RTR-402/probe")
    assert probe.status_code == 200
    assert probe.json() == {"device_id": "RTR-402", "reachable": True, "simulated": True}
    assert temporary_app.get("/devices/RTR-402").json()["status"] == "offline"

    summary = temporary_app.get("/devices/summary").json()
    assert summary == {
        "total_devices": 2,
        "online_count": 1,
        "offline_count": 1,
        "device_types": ["router", "switch"],
    }


def test_redaction_masks_fake_sensitive_fields():
    result = redact_sensitive_fields(None, "info", {
        "event": "test_event",
        "device_id": "RTR-TEST",
        "token": "DEMO-DO-NOT-USE",
    })
    assert result["device_id"] == "RTR-TEST"
    assert result["token"] == "***"
