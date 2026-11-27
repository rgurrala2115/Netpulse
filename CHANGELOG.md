# Changelog

## v0.2.0 - MySQL and Alembic integration

- Completed the NetPulse in-memory baseline with validated Pydantic models, offline alerts, summary collections, and service tests.
- Added the `DeviceRepository` protocol and kept the in-memory implementation for isolated tests.
- Added centralized HTTP 409/404 handlers and preserved 422 validation.
- Added the simulated asynchronous device probe and sequential-versus-concurrent demo.
- Added structured JSON logging, request tracing, safe request IDs, and sensitive-field redaction.
- Added SQLAlchemy MySQL configuration, ORM models, a request-scoped session, and `MySqlDeviceRepository`.
- Added Alembic migrations for the `devices` and `alerts` tables and an evolving `devices.location` column.
- Verified downgrade and upgrade migration behavior and MySQL persistence across application restarts.
