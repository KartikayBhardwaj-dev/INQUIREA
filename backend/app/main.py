from fastapi import FastAPI

from starlette.middleware.sessions import (
    SessionMiddleware
)

from backend.app.api.auth import router as auth_router

from backend.app.core.config import get_settings
from backend.app.api.gmail import (
    router as gmail_router
)
from backend.app.api.email_intelligence import (

    router as email_intelligence_router

)
settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY
)


@app.get("/")
def root():
    return {
        "message": "Inquirea API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


app.include_router(
    auth_router
)

app.include_router(gmail_router)
app.include_router(

    email_intelligence_router

)