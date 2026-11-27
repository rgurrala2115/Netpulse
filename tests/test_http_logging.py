from fastapi.testclient import TestClient

from app.main import app
from app.repositories.device_repository import InMemoryDeviceRepository
from app.routes.devices import get_device_service
from app.services.device_service import DeviceService
from app.logging_config import redact_sensitive_fields


def test_request_ids_and_domain_errors():
    service = DeviceService(InMemoryDeviceRepository())
    app.dependency_overrides[get_device_service] = lambda: service
    try:
        with TestClient(app) as client:
            device = {
                "device_id": "RTR-401",
                "name": "Branch Router",
                "device_type": "router",
                "ip_address": "10.0.0.41",
                "status": "online",
            }
            first = client.post("/devices", json=device, headers={"X-Request-ID": "lab-trace-401"})
            assert first.status_code == 201
            assert first.headers["X-Request-ID"] == "lab-trace-401"

            duplicate = client.post("/devices", json=device)
            assert duplicate.status_code == 409
            assert duplicate.headers["X-Request-ID"]

            missing = client.get("/devices/unknown-404", headers={"X-Request-ID": "lab-trace-404"})
            assert missing.status_code == 404
            assert missing.json() == {"detail": "Device not found"}
    finally:
        app.dependency_overrides.clear()


def test_invalid_request_id_is_replaced():
    service = DeviceService(InMemoryDeviceRepository())
    app.dependency_overrides[get_device_service] = lambda: service
    try:
        with TestClient(app) as client:
            response = client.get("/health", headers={"X-Request-ID": "bad header!"})
            assert response.headers["X-Request-ID"].isalnum()
    finally:
        app.dependency_overrides.clear()


def test_status_alert_probe_and_summary():
    service = DeviceService(InMemoryDeviceRepository())
    app.dependency_overrides[get_device_service] = lambda: service
    try:
        with TestClient(app) as client:
            client.post("/devices", json={
                "device_id": "RTR-402", "name": "Branch Router", "device_type": "router",
                "ip_address": "10.0.0.42", "status": "online",
            })
            client.post("/devices", json={
                "device_id": "SW-402", "name": "Floor Switch", "device_type": "switch",
                "ip_address": "10.0.0.43", "status": "online",
            })

            assert client.patch("/devices/RTR-402/status", json={"status": "unknown"}).status_code == 422

            first = client.patch("/devices/RTR-402/status", json={"status": "offline"}, headers={"X-Request-ID": "lab-trace-402"})
            second = client.patch("/devices/RTR-402/status", json={"status": "offline"})
            assert first.status_code == 200
            assert second.status_code == 200

            alerts = client.get("/alerts").json()
            assert len([alert for alert in alerts if alert["device_id"] == "RTR-402"]) == 1

            probe = client.get("/devices/RTR-402/probe")
            assert probe.status_code == 200
            assert probe.json() == {"device_id": "RTR-402", "reachable": True, "simulated": True}

            assert client.get("/devices/summary").json() == {
                "total_devices": 2,
                "online_count": 1,
                "offline_count": 1,
                "device_types": ["router", "switch"],
            }
    finally:
        app.dependency_overrides.clear()


def test_redaction_masks_fake_sensitive_fields():
    result = redact_sensitive_fields(None, "info", {
        "event": "test_event",
        "device_id": "RTR-TEST",
        "token": "DEMO-DO-NOT-USE",
    })
    assert result["device_id"] == "RTR-TEST"
    assert result["token"] == "***"
