"""Device business rules."""

from __future__ import annotations

from app.events import create_offline_alert
from app.models import AlertResponse, DeviceCreate, DeviceResponse, DeviceStatus, DeviceSummary
from app.repositories.contracts import DeviceRepository


class DeviceAlreadyExistsError(Exception):
	pass


class DeviceNotFoundError(Exception):
	pass


class DeviceService:
	def __init__(self, repository: DeviceRepository) -> None:
		self.repository = repository

	def register(self, device: DeviceCreate) -> DeviceResponse:
		if self.repository.get_device(device.device_id) is not None:
			raise DeviceAlreadyExistsError(device.device_id)
		return self.repository.add_device(DeviceResponse(**device.model_dump()))

	def list(self) -> list[DeviceResponse]:
		return self.repository.list_devices()

	def get_device_summary(self) -> DeviceSummary:
		devices = self.repository.list_devices()
		counts = {"online": 0, "offline": 0}
		device_types = set()
		for device in devices:
			counts[device.status] += 1
			device_types.add(device.device_type)
		return DeviceSummary(
			total_devices=len(devices),
			online_count=counts["online"],
			offline_count=counts["offline"],
			device_types=sorted(device_types),
		)

	def get(self, device_id: str) -> DeviceResponse:
		device = self.repository.get_device(device_id)
		if device is None:
			raise DeviceNotFoundError(device_id)
		return device

	def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse:
		previous = self.get(device_id)
		device = self.repository.update_status(device_id, status)
		if device is None:
			raise DeviceNotFoundError(device_id)
		if previous.status == "online" and device.status == "offline":
			create_offline_alert(self.repository, device_id)
		return device

	def list_alerts(self) -> list[AlertResponse]:
		return self.repository.list_alerts()