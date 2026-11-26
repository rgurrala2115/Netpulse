# NetPulse

Create and activate a virtual environment, install dependencies, and start the app:

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```

Open http://127.0.0.1:8000/docs for the six endpoints, or
http://127.0.0.1:8000/openapi.json for the generated contract. FastAPI builds
OpenAPI from the routes, response codes, and Pydantic models. The Swagger UI
assets are served locally, so the interactive documentation works offline.

## Swagger walkthrough

For a clean walkthrough, restart the server first; all in-memory data is cleared
on restart. In `POST /devices`, select **Try it out**, enter the following, and
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

Run the isolated tests from the project root with:

```sh
python -m pytest -q
```

## Architecture

- Routes validate HTTP requests and translate service errors to HTTP responses.
- The service enforces device rules and detects online-to-offline transitions.
- The repository owns the in-memory device and alert collections and returns copies.
- The event handler records a UTC-stamped offline alert through the repository.

NetPulse is one deployable modular monolith: its layers run together in one
application process. A future database repository can implement the same methods
and be injected into the service without changing its business rules. In-memory
data is per process and is not shared across multiple workers or restarts.