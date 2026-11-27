"""Device and alert endpoints."""

import structlog
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.models import (
	AlertResponse,
	DeviceCreate,
	DeviceProbeResponse,
	DeviceResponse,
	DeviceSummary,
	StatusUpdate,
)
from app.db.database import get_session
from app.repositories.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
from app.services.device_service import DeviceService
from app.services.probe import simulate_device_probe


router = APIRouter()
route_logger = structlog.get_logger("netpulse.routes")


def get_device_service(session: Session = Depends(get_session, scope="function")) -> DeviceService:
	return DeviceService(SQLAlchemyDeviceRepository(session))


@router.post(
	"/devices",
	response_model=DeviceResponse,
	status_code=status.HTTP_201_CREATED,
	responses={409: {"description": "Device already exists"}},
)
def register_device(device: DeviceCreate, service: DeviceService = Depends(get_device_service)) -> DeviceResponse:
	route_logger.info("device_registration_requested", device_id=device.device_id)
	return service.register(device)


@router.get("/devices", response_model=list[DeviceResponse])
def list_devices(service: DeviceService = Depends(get_device_service)) -> list[DeviceResponse]:
	return service.list()


@router.get("/devices/summary", response_model=DeviceSummary)
def get_device_summary(service: DeviceService = Depends(get_device_service)) -> DeviceSummary:
	return service.get_device_summary()


@router.get(
	"/devices/{device_id}",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
def get_device(device_id: str, service: DeviceService = Depends(get_device_service)) -> DeviceResponse:
	return service.get(device_id)


@router.get(
	"/devices/{device_id}/probe",
	response_model=DeviceProbeResponse,
	responses={404: {"description": "Device not found"}},
)
async def probe_device(device_id: str, service: DeviceService = Depends(get_device_service)) -> dict[str, str | bool]:
	service.get(device_id)
	return await simulate_device_probe(device_id)


@router.patch(
	"/devices/{device_id}/status",
	response_model=DeviceResponse,
	responses={404: {"description": "Device not found"}},
)
def update_device_status(device_id: str, update: StatusUpdate, service: DeviceService = Depends(get_device_service)) -> DeviceResponse:
	return service.update_status(device_id, update.status)


@router.get("/alerts", response_model=list[AlertResponse])
def list_alerts(service: DeviceService = Depends(get_device_service)) -> list[AlertResponse]:
	return service.list_alerts()


@router.get("/health")
async def health() -> dict[str, str]:
	return {"status": "ok"}