"""Device event handlers."""

from datetime import datetime, timezone

from app.models import AlertResponse
from app.repositories.contracts import DeviceRepository


def create_offline_alert(repository: DeviceRepository, device_id: str) -> None:
	repository.save_alert(
		AlertResponse(
			device_id=device_id,
			message=f"Device {device_id} went offline",
			timestamp=datetime.now(timezone.utc),
		)
	)