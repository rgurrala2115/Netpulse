import asyncio
from datetime import timedelta

import pytest
from pydantic import ValidationError

from app.models import DeviceCreate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)
from app.services.probe import simulate_device_probe


@pytest.fixture
def service() -> DeviceService:
    return DeviceService(InMemoryDeviceRepository())


@pytest.fixture
def device() -> DeviceCreate:
    return DeviceCreate(
        device_id="RTR-101",
        name="Branch Router",
        device_type="router",
        ip_address="192.168.10.1",
    )


def test_registration_and_lookup(service: DeviceService, device: DeviceCreate) -> None:
    registered = service.register(device)
    assert registered.device_id == "RTR-101"
    assert registered.status == "online"
    assert service.get("RTR-101") == registered
    assert service.list() == [registered]


def test_empty_summary(service: DeviceService) -> None:
    assert service.get_device_summary().model_dump() == {
        "total_devices": 0,
        "online_count": 0,
        "offline_count": 0,
        "device_types": [],
    }


def test_populated_summary_has_sorted_unique_types(
    service: DeviceService, device: DeviceCreate
) -> None:
    service.register(device)
    service.register(device.model_copy(update={"device_id": "SW-102", "device_type": "switch"}))
    service.register(device.model_copy(update={"device_id": "RTR-103"}))
    service.update_status("RTR-101", "offline")
    assert service.get_device_summary().model_dump() == {
        "total_devices": 3,
        "online_count": 2,
        "offline_count": 1,
        "device_types": ["router", "switch"],
    }


def test_duplicate_registration(service: DeviceService, device: DeviceCreate) -> None:
    service.register(device)
    with pytest.raises(DeviceAlreadyExistsError):
        service.register(device)


@pytest.mark.parametrize("operation", ["get", "update_status"])
def test_missing_device(service: DeviceService, operation: str) -> None:
    with pytest.raises(DeviceNotFoundError):
        if operation == "get":
            service.get("missing")
        else:
            service.update_status("missing", "offline")


def test_initial_offline_registration_has_no_alert(
    service: DeviceService, device: DeviceCreate
) -> None:
    service.register(device.model_copy(update={"status": "offline"}))
    assert service.list_alerts() == []


def test_offline_transition_creates_one_alert(
    service: DeviceService, device: DeviceCreate
) -> None:
    service.register(device)
    assert service.update_status(device.device_id, "offline").status == "offline"
    alerts = service.list_alerts()
    assert len(alerts) == 1
    assert alerts[0].device_id == device.device_id
    assert "offline" in alerts[0].message
    assert alerts[0].timestamp.utcoffset() == timedelta(0)


def test_repeated_offline_update_does_not_create_another_alert(
    service: DeviceService, device: DeviceCreate
) -> None:
    service.register(device)
    service.update_status(device.device_id, "offline")
    service.update_status(device.device_id, "offline")
    assert len(service.list_alerts()) == 1


def test_new_online_to_offline_transition_creates_another_alert(
    service: DeviceService, device: DeviceCreate
) -> None:
    service.register(device)
    service.update_status(device.device_id, "offline")
    service.update_status(device.device_id, "online")
    service.update_status(device.device_id, "offline")
    assert len(service.list_alerts()) == 2


def test_repository_results_cannot_mutate_stored_data(
    service: DeviceService, device: DeviceCreate
) -> None:
    registered = service.register(device)
    registered.name = "Changed"
    service.update_status(device.device_id, "offline")
    alerts = service.list_alerts()
    alerts[0].message = "Changed"
    alerts.clear()
    assert service.get(device.device_id).name == "Branch Router"
    assert "offline" in service.list_alerts()[0].message


@pytest.mark.parametrize(
    ("field", "value"),
    [("ip_address", "::1"), ("ip_address", "999.0.0.1"),
     ("device_type", "printer"), ("status", "unknown")],
)
def test_invalid_device_fields(device: DeviceCreate, field: str, value: str) -> None:
    with pytest.raises(ValidationError):
        DeviceCreate.model_validate({**device.model_dump(), field: value})


def test_simulated_device_probe() -> None:
    assert asyncio.run(simulate_device_probe("RTR-101")) == {
        "device_id": "RTR-101",
        "reachable": True,
        "simulated": True,
    }