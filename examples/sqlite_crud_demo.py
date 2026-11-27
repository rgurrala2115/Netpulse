"""Demonstrate the four CRUD actions against an isolated SQLite database."""

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.db.models import Base, DeviceRow


def main() -> None:
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine, expire_on_commit=False)

    with Session(engine) as session:
        row = DeviceRow(
            device_id="RTR-DEMO",
            name="CRUD Demo Router",
            device_type="router",
            ip_address="10.0.0.10",
            status="online",
        )
        session.add(row)
        session.commit()
        print("Create: added RTR-DEMO")

    with Session(engine) as session:
        row = session.get(DeviceRow, "RTR-DEMO")
        print(f"Read: {row.name if row is not None else 'missing'}")

    with Session(engine) as session:
        row = session.get(DeviceRow, "RTR-DEMO")
        if row is not None:
            row.status = "offline"
            session.commit()
        print("Update: changed RTR-DEMO to offline")

    with Session(engine) as session:
        row = session.get(DeviceRow, "RTR-DEMO")
        if row is not None:
            session.delete(row)
            session.commit()
        print("Delete: removed RTR-DEMO")

    with Session(engine) as session:
        remaining = list(session.scalars(select(DeviceRow)).all())
        print(f"Remaining devices: {remaining}")

    engine.dispose()


if __name__ == "__main__":
    main()
