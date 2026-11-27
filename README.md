# NetPulse

Create and activate a virtual environment, install dependencies, and start the app:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the eight endpoints, or
http://127.0.0.1:8000/openapi.json for the generated contract. FastAPI builds
OpenAPI from the routes, response codes, and Pydantic models. The Swagger UI
assets are served locally, so the interactive documentation works offline.

## Swagger walkthrough

For a clean walkthrough, stop Uvicorn and delete only disposable `netpulse.db`
if you want an empty database, then restart; persistent records survive normal
server restarts. In `POST /devices`, select **Try it out**, enter the following, and
execute (201):

```json
{
	"device_id": "RTR-101",
	"name": "Branch Router",
	"device_type": "router",
	"ip_address": "192.168.10.1",
	"status": "online"
}
```

In `PATCH /devices/{device_id}/status`, enter `RTR-101` and execute twice with
`{"status": "offline"}` (200 each time). `GET /alerts` contains exactly one
alert. Registering `RTR-101` again returns 409. If it already exists, restart
the server or use a different ID such as `RTR-102`.

Register a second device with `device_id` `SW-102`, device type `switch`, and
IP address `192.168.10.2`. `GET /devices/summary` reports device counts and
sorted unique device types. `GET /devices/RTR-101/probe` simulates an async
check without contacting a device, changing its status, or creating an alert.

Compare sequential and concurrent simulated probes with:

```sh
python -m examples.async_probe_demo
```

Run the isolated tests from the project root with:

```sh
python -m pytest -q
```

## Architecture

- Routes validate HTTP requests and translate service errors to HTTP responses.
- The service enforces device rules and detects online-to-offline transitions.
- The repository owns the in-memory device and alert collections and returns copies;
	its protocol defines the contract used by the service and event handler.
- The event handler records a UTC-stamped offline alert through the repository.

NetPulse is one deployable modular monolith: its layers run together in one
application process. The SQLite repository implements the same protocol methods
and is injected into the service; changing repositories does not change business
rules.

## SQLite and runtime

The app stores devices and alerts in `netpulse.db`. The SQLAlchemy session is
request-scoped: it commits once after successful request completion, rolls back
on exceptions, and closes in `finally`. `netpulse.db` is ignored by Git.
Restarting Uvicorn preserves persisted records.

Uvicorn is the ASGI server and FastAPI is the ASGI application. ASGI supports
async endpoints such as the simulated probe. Database operations use synchronous
SQLAlchemy, so HTTP data routes use `def` to avoid blocking async code. WSGI is
the older synchronous Python web interface and does not use the ASGI protocol.

## Structured logs and request tracing

NetPulse emits JSON application events through `structlog`. Every response has an
`X-Request-ID`: a supplied safe ID is returned; otherwise the app generates a
UUID hex value. Route, service, alert and completion events share `request_id`,
while `device_id` identifies the device. INFO records normal activity, WARNING
records handled domain errors, and ERROR records unexpected failures.

Do not log request bodies, passwords, tokens or connection URLs. The redaction
processor masks exact `password`, `token`, `api_key`, `authorization` and `secret`
keys as a last-resort safety net.