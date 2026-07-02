print(">>> main.py: start")
from contextlib import asynccontextmanager

from langgraph.checkpoint.postgres.aio import (
    AsyncPostgresSaver,
)

from backend.app.workflows.email_graph import (
    build_graph,
)
print(">>> importing FastAPI")
from fastapi import FastAPI
print("<<< FastAPI imported")

print(">>> importing SessionMiddleware")
from starlette.middleware.sessions import SessionMiddleware
print("<<< SessionMiddleware imported")

print(">>> importing auth router")
from backend.app.api.auth import router as auth_router
print("<<< auth router imported")

print(">>> importing settings")
from backend.app.core.config import get_settings
print("<<< settings imported")

print(">>> importing gmail router")
from backend.app.api.gmail import router as gmail_router
print("<<< gmail router imported")

print(">>> importing email intelligence router")
from backend.app.api.email_intelligence import (
    router as email_intelligence_router,
)
print("<<< email intelligence router imported")

print(">>> importing agents router")
from backend.app.api.agents import router as agent_router
print("<<< agents router imported")

print(">>> importing register_tools")
from backend.app.tools.bootstrap import register_tools
print("<<< register_tools imported")

print(">>> importing register_agents")
from backend.app.agents.bootstrap import register_agents
print("<<< register_agents imported")

print(">>> get_settings()")
settings = get_settings()
print("<<< get_settings()")

print(">>> FastAPI()")
@asynccontextmanager
async def lifespan(app: FastAPI):

    saver_cm = AsyncPostgresSaver.from_conn_string(
        settings.CHECKPOINT_DATABASE_URL,
    )

    checkpointer = await saver_cm.__aenter__()

    await checkpointer.setup()

    graph = build_graph().compile(
        checkpointer=checkpointer,
    )

    app.state.graph = graph
    app.state.checkpointer = checkpointer
    app.state.saver_cm = saver_cm

    print("LangGraph initialized.")

    yield

    await saver_cm.__aexit__(None, None, None)


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan,
)
print("<<< FastAPI()")

print(">>> register_tools()")
register_tools()
print("<<< register_tools()")

print(">>> register_agents()")
register_agents()
print("<<< register_agents()")

print(">>> add_middleware()")
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
)
print("<<< add_middleware()")

print(">>> include auth")
app.include_router(auth_router)
print("<<< include auth")

print(">>> include gmail")
app.include_router(gmail_router)
print("<<< include gmail")

print(">>> include email intelligence")
app.include_router(email_intelligence_router)
print("<<< include email intelligence")

print(">>> include agents")
app.include_router(agent_router)
print("<<< include agents")

print(">>> main.py finished")