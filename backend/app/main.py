from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import get_settings

from backend.app.tools.bootstrap import register_tools
from backend.app.agents.bootstrap import register_agents

from backend.app.api.auth import (
    router as auth_router,
)
from backend.app.api.gmail import (
    router as gmail_router,
)
from backend.app.api.email_intelligence import (
    router as email_intelligence_router,
)
from backend.app.api.agents import (
    router as agent_router,
)
from backend.app.api.chat import (
    router as chat_router,
)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan.

    Background processing is handled by Celery workers,
    so FastAPI only manages the API lifecycle.
    """

    print("✓ FastAPI application started")

    yield

    print("✓ FastAPI application shutdown complete")


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)

# ----------------------------------------
# Bootstrap
# ----------------------------------------

register_tools()
register_agents()

# ----------------------------------------
# Middleware
# ----------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)

# ----------------------------------------
# Routes
# ----------------------------------------

app.include_router(auth_router)
app.include_router(gmail_router)
app.include_router(email_intelligence_router)
app.include_router(agent_router)
app.include_router(chat_router)

print("✓ Inquirea started successfully")