"""Application entry point."""

from fastapi_offline import FastAPIOffline

from app.routes.devices import router


app = FastAPIOffline(title="NetPulse")
app.include_router(router)