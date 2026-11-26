"""Device and alert endpoints."""

from fastapi import APIRouter, status

from app.models import (
	AlertResponse,
	DeviceCreate,
	DeviceProbeResponse,
	DeviceResponse,
	DeviceSummary,
	StatusUpdate,
)
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import DeviceService
from app.services.probe import simulate_device_probe


router = APIRouter()
service = DeviceService(InMemoryDeviceRepository())


@router.post(
	"/devices",
	response_model=DeviceResponse,
	status_code=status.HTTP_201_CREATED,
	responses={409: {"description": "Device already exists"}},
)
async def register_device(device: DeviceCreate) -> DeviceResponse:
	return service.register(device)


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices() -> list[DeviceResponse]:
	return service.list()


@router.get("/devices/summary", response_model=DeviceSummary)
async def get_device_summary() -> DeviceSummary:
	return service.get_device_summary()


@router.get(
	"/devices/{device_id}",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
async def get_device(device_id: str) -> DeviceResponse:
	return service.get(device_id)


@router.get(
	"/devices/{device_id}/probe",
	response_model=DeviceProbeResponse,
	responses={404: {"description": "Device not found"}},
)
async def probe_device(device_id: str) -> dict[str, str | bool]:
	service.get(device_id)
	return await simulate_device_probe(device_id)


@router.patch(
	"/devices/{device_id}/status",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
async def update_device_status(device_id: str, update: StatusUpdate) -> DeviceResponse:
	return service.update_status(device_id, update.status)


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts() -> list[AlertResponse]:
	return service.list_alerts()


@router.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}