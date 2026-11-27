from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base
from app.models import DeviceCreate
from app.repositories.sqlalchemy_device_repository import SQLAlchemyDeviceRepository
from app.services.device_service import (
    DeviceAlreadyExistsError,
    DeviceNotFoundError,
    DeviceService,
)


def make_service(database_path):
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    session = Session(engine)
    service = DeviceService(SQLAlchemyDeviceRepository(session))
    return engine, session, service


def test_sqlite_create_read_update_persistence(tmp_path):
    engine, session, service = make_service(tmp_path / "devices.db")
    service.register(DeviceCreate(
        device_id="RTR-201",
        name="Persisted Router",
        device_type="router",
        ip_address="10.0.0.201",
    ))
    session.commit()

    second = Session(engine)
    persisted = DeviceService(SQLAlchemyDeviceRepository(second)).get("RTR-201")
    assert persisted.status == "online"
    second.close()

    service.update_status("RTR-201", "offline")
    session.commit()
    third = Session(engine)
    assert DeviceService(SQLAlchemyDeviceRepository(third)).get("RTR-201").status == "offline"
    assert len(DeviceService(SQLAlchemyDeviceRepository(third)).list_alerts()) == 1
    third.close()

    session.close()
    engine.dispose()


def test_sqlite_duplicate_and_missing(tmp_path):
    engine, session, service = make_service(tmp_path / "errors.db")
    device = DeviceCreate(
        device_id="RTR-202",
        name="Router",
        device_type="router",
        ip_address="10.0.0.202",
    )
    service.register(device)
    session.commit()

    try:
        service.register(device)
    except DeviceAlreadyExistsError:
        pass
    else:
        raise AssertionError("duplicate device was accepted")

    try:
        service.get("missing")
    except DeviceNotFoundError:
        pass
    else:
        raise AssertionError("missing device was accepted")

    session.close()
    engine.dispose()


def test_sqlite_summary(tmp_path):
    engine, session, service = make_service(tmp_path / "summary.db")
    service.register(DeviceCreate(device_id="RTR-203", name="Router", device_type="router", ip_address="10.0.0.203"))
    service.register(DeviceCreate(device_id="SW-203", name="Switch", device_type="switch", ip_address="10.0.0.204"))
    session.commit()

    summary = service.get_device_summary().model_dump()
    assert summary == {
        "total_devices": 2,
        "online_count": 2,
        "offline_count": 0,
        "device_types": ["router", "switch"],
    }

    session.close()
    engine.dispose()


def test_sqlite_rolls_back_status_and_alert(tmp_path):
    engine, session, service = make_service(tmp_path / "rollback.db")
    service.register(DeviceCreate(device_id="RTR-204", name="Router", device_type="router", ip_address="10.0.0.204"))
    session.commit()

    service.update_status("RTR-204", "offline")
    session.rollback()

    check = Session(engine)
    persisted = DeviceService(SQLAlchemyDeviceRepository(check))
    assert persisted.get("RTR-204").status == "online"
    assert persisted.list_alerts() == []

    check.close()
    session.close()
    engine.dispose()
