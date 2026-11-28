"""API MinutesStudy. Các route bám theo user flow trong docs/user-flows.md."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import assistant, auth, chat_insights, files, notifications, student, teacher

if settings.sentry_dsn:
    import sentry_sdk  # pip install sentry-sdk

    sentry_sdk.init(dsn=settings.sentry_dsn, traces_sample_rate=0.1, send_default_pii=False)


@asynccontextmanager
async def lifespan(_: FastAPI):
    if settings.auto_create_tables:
        from app.db import engine
        from app.models import Base

        if engine.dialect.name == "postgresql":
            with engine.begin() as conn:
                conn.exec_driver_sql("CREATE EXTENSION IF NOT EXISTS vector")
        Base.metadata.create_all(engine)
    yield


app = FastAPI(title="MinutesStudy API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"ok": True}


app.include_router(auth.router)
app.include_router(teacher.router)
app.include_router(assistant.router)
app.include_router(student.router)
app.include_router(files.router)
app.include_router(notifications.router)
app.include_router(chat_insights.router)
