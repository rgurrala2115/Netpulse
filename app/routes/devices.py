"""Device and alert endpoints."""

from fastapi import APIRouter, HTTPException, status

from app.models import AlertResponse, DeviceCreate, DeviceResponse, StatusUpdate
from app.repositories.device_repository import InMemoryDeviceRepository
from app.services.device_service import (
	DeviceAlreadyExistsError,
	DeviceNotFoundError,
	DeviceService,
)


router = APIRouter()
service = DeviceService(InMemoryDeviceRepository())


@router.post(
	"/devices",
	response_model=DeviceResponse,
	status_code=status.HTTP_201_CREATED,
	responses={409: {"description": "Device already exists"}},
)
async def register_device(device: DeviceCreate) -> DeviceResponse:
	try:
		return service.register(device)
	except DeviceAlreadyExistsError as error:
		raise HTTPException(status_code=409, detail="Device already exists") from error


@router.get("/devices", response_model=list[DeviceResponse])
async def list_devices() -> list[DeviceResponse]:
	return service.list()


@router.get(
	"/devices/{device_id}",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
async def get_device(device_id: str) -> DeviceResponse:
	try:
		return service.get(device_id)
	except DeviceNotFoundError as error:
		raise HTTPException(status_code=404, detail="Device not found") from error


@router.patch(
	"/devices/{device_id}/status",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
async def update_device_status(device_id: str, update: StatusUpdate) -> DeviceResponse:
	try:
		return service.update_status(device_id, update.status)
	except DeviceNotFoundError as error:
		raise HTTPException(status_code=404, detail="Device not found") from error


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts() -> list[AlertResponse]:
	return service.list_alerts()


@router.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}