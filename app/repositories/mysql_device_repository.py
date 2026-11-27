"""MySQL implementation of the DeviceRepository contract."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import AlertRow, DeviceRow
from app.models import AlertResponse, DeviceResponse, DeviceStatus
from app.services.device_service import DeviceAlreadyExistsError


class MySqlDeviceRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    @staticmethod
    def _device_response(row: DeviceRow) -> DeviceResponse:
        return DeviceResponse(
            device_id=row.device_id,
            name=row.name,
            device_type=row.device_type,
            ip_address=row.ip_address,
            status=row.status,
        )

    @staticmethod
    def _alert_response(row: AlertRow) -> AlertResponse:
        return AlertResponse(device_id=row.device_id, message=row.message, timestamp=row.timestamp)

    def add_device(self, device: DeviceResponse) -> DeviceResponse:
        row = DeviceRow(
            device_id=device.device_id,
            name=device.name,
            device_type=device.device_type,
            ip_address=str(device.ip_address),
            status=device.status,
        )
        self.session.add(row)
        try:
            self.session.flush()
        except IntegrityError as error:
            self.session.rollback()
            raise DeviceAlreadyExistsError(device.device_id) from error
        return self._device_response(row)

    def list_devices(self) -> list[DeviceResponse]:
        rows = self.session.scalars(select(DeviceRow).order_by(DeviceRow.device_id)).all()
        return [self._device_response(row) for row in rows]

    def get_device(self, device_id: str) -> DeviceResponse | None:
        row = self.session.get(DeviceRow, device_id)
        return self._device_response(row) if row is not None else None

    def update_status(self, device_id: str, status: DeviceStatus) -> DeviceResponse | None:
        row = self.session.get(DeviceRow, device_id)
        if row is None:
            return None
        row.status = status
        self.session.flush()
        return self._device_response(row)

    def save_alert(self, alert: AlertResponse) -> AlertResponse:
        row = AlertRow(device_id=alert.device_id, message=alert.message, timestamp=alert.timestamp)
        self.session.add(row)
        self.session.flush()
        return self._alert_response(row)

    def list_alerts(self) -> list[AlertResponse]:
        rows = self.session.scalars(select(AlertRow).order_by(AlertRow.id)).all()
        return [self._alert_response(row) for row in rows]
