"""Application entry point."""

from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi_offline import FastAPIOffline

from app.routes.devices import router
from app.services.device_service import DeviceAlreadyExistsError, DeviceNotFoundError


app = FastAPIOffline(title="NetPulse")
app.include_router(router)


@app.exception_handler(DeviceAlreadyExistsError)
async def device_already_exists_handler(
	request: Request, error: DeviceAlreadyExistsError
) -> JSONResponse:
	return JSONResponse(status_code=409, content={"detail": "Device already exists"})


@app.exception_handler(DeviceNotFoundError)
async def device_not_found_handler(
	request: Request, error: DeviceNotFoundError
) -> JSONResponse:
	return JSONResponse(status_code=404, content={"detail": "Device not found"})