# NetPulse verification

## Swagger endpoints

The Swagger UI displayed these six operations:

- `POST /devices`
- `GET /devices`
- `GET /devices/{device_id}`
- `PATCH /devices/{device_id}/status`
- `GET /alerts`
- `GET /health`

## Walkthrough

Registering the README's `RTR-101` device returned HTTP 201 and:

```json
{
  "device_id": "RTR-101",
  "name": "Branch Router",
  "device_type": "router",
  "ip_address": "192.168.10.1",
  "status": "online"
}
```

Two successive PATCH requests with `{"status":"offline"}` each returned HTTP
200 and status `offline`. `GET /alerts` returned HTTP 200 and exactly:

```json
[
  {
    "device_id": "RTR-101",
    "message": "Device RTR-101 went offline",
    "timestamp": "2026-11-26T09:04:57.135022Z"
  }
]
```

Duplicate registration returned 409, a missing device returned 404, and invalid
IPv4, device type, and status values returned 422. Health returned
`{"status":"ok"}`.

## Tests and layers

```text
$ python -m pytest -q
.............                                                            [100%]
13 passed
```

Routes handle HTTP, the service enforces business rules, the repository owns
storage, and the event handler records offline alerts. They form one deployable
modular monolith. A future database repository can implement the same methods
and be injected without changing service rules.