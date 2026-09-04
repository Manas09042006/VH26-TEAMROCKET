import asyncio

from contextlib import asynccontextmanager

from fastapi import FastAPI

from backend.database.database import Base, engine
from backend.database import models

from backend.api.employees import router as employee_router
from backend.api.events import router as events_router
from backend.api.admin import router as admin_router

from backend.services.heartbeat_service import heartbeat_monitor


Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    monitor_task = asyncio.create_task(
        heartbeat_monitor()
    )

    yield

    monitor_task.cancel()

    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title="LeakGuard Backend",
    description="Backend API for LeakGuard administration and monitoring",
    version="1.0.0",
    lifespan=lifespan
)


app.include_router(employee_router)
app.include_router(events_router)
app.include_router(admin_router)


@app.get("/")
def root():
    return {
        "system": "LeakGuard",
        "status": "online",
        "message": "LeakGuard backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }