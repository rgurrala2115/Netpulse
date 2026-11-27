"""Application entry point."""

import re
import time
import uuid

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_offline import FastAPIOffline

import app.db.models  # noqa: F401
from app.logging_config import configure_logging
from app.routes.devices import router
from app.services.device_service import DeviceAlreadyExistsError, DeviceNotFoundError


configure_logging()
logger = structlog.get_logger("netpulse.app")

app = FastAPIOffline(title="NetPulse")
app.include_router(router)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
	structlog.contextvars.clear_contextvars()
	header_request_id = request.headers.get("X-Request-ID")
	if header_request_id and re.fullmatch(r"[A-Za-z0-9_-]{1,64}", header_request_id):
		request_id = header_request_id
	else:
		request_id = uuid.uuid4().hex
	structlog.contextvars.bind_contextvars(request_id=request_id)

	started = time.perf_counter()
	status_code = 500
	try:
		response = await call_next(request)
		status_code = response.status_code
		response.headers["X-Request-ID"] = request_id
		return response
	except Exception as error:
		logger.exception(
			"unexpected_error",
			exception_type=type(error).__name__,
		)
		raise
	finally:
		duration_ms = round((time.perf_counter() - started) * 1000, 3)
		route = request.scope.get("route")
		path_template = getattr(route, "path", None) or request.url.path
		logger.info(
			"request_completed",
			method=request.method,
			path=path_template,
			status_code=status_code,
			duration_ms=duration_ms,
		)
		structlog.contextvars.clear_contextvars()


@app.exception_handler(DeviceAlreadyExistsError)
async def device_already_exists_handler(
	request: Request, error: DeviceAlreadyExistsError
) -> JSONResponse:
	device_id = str(error.args[0]) if error.args else None
	logger.warning("domain_error", error_type="DeviceAlreadyExistsError", status_code=409, device_id=device_id)
	return JSONResponse(status_code=409, content={"detail": "Device already exists"})


@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(
	request: Request, error: DeviceNotFoundError
) -> JSONResponse:
	device_id = str(error.args[0]) if error.args else None
	logger.warning("domain_error", error_type="DeviceNotFoundError", status_code=404, device_id=device_id)
	return JSONResponse(status_code=404, content={"detail": "Device not found"})