from fastapi import FastAPI

from backend.app.api.health import router as health_router
from backend.app.core.config import get_settings
from backend.app.core.logger import setup_logging

setup_logging()

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
)
@app.get("/")
def root():
    return {
        "app": "Inquirea",
        "status": "running"
    }
app.include_router(health_router)