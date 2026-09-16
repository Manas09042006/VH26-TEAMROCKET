import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from backend.api.admin import router as admin_router
from backend.api.auth import router as auth_router
from backend.api.employees import router as employee_router
from backend.api.events import router as events_router
from backend.core.config import (
    CORS_ORIGINS,
    DEFAULT_ADMIN_PASSWORD,
    DEFAULT_ADMIN_USERNAME,
    HOST,
    PORT,
    PROJECT_NAME,
    VERSION,
)
from backend.core.security import get_password_hash
from backend.core.websocket import manager
from backend.database.database import Base, SessionLocal, engine
from backend.database.models import AdminUser, Employee
from backend.services.heartbeat_service import heartbeat_monitor

logger = logging.getLogger("leakguard.backend")


def seed_initial_data():
    """Seed initial administrator and default employee records if they do not exist."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # 1. Ensure default admin user exists
        admin = db.query(AdminUser).filter(AdminUser.username == DEFAULT_ADMIN_USERNAME).first()
        if not admin:
            admin = AdminUser(
                username=DEFAULT_ADMIN_USERNAME,
                password_hash=get_password_hash(DEFAULT_ADMIN_PASSWORD),
                role="ADMIN"
            )
            db.add(admin)
            logger.info(f"Initialized default admin user: '{DEFAULT_ADMIN_USERNAME}'")

        # 2. Ensure default demo employee exists if table is empty
        employee_count = db.query(Employee).count()
        if employee_count == 0:
            demo_employee = Employee(
                username="test.employee",
                display_name="Demo Developer",
                role="DEVELOPER",
                machine_name="DEV-STATION-01",
                agent_id="agent-test-001",
                status="OFFLINE"
            )
            db.add(demo_employee)
            logger.info("Initialized demo employee: 'test.employee' (agent-test-001)")

        db.commit()
    except Exception as error:
        logger.error(f"Error seeding database: {error}")
        db.rollback()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables and initial records
    seed_initial_data()

    # Start background heartbeat monitor
    monitor_task = asyncio.create_task(heartbeat_monitor())

    yield

    # Cancel background monitor task on shutdown
    monitor_task.cancel()
    try:
        await monitor_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=PROJECT_NAME,
    description="Backend API for LeakGuard administration and security monitoring",
    version=VERSION,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(employee_router)
app.include_router(events_router)
app.include_router(admin_router)
app.include_router(auth_router)


@app.get("/")
def root():
    return {
        "system": "LeakGuard",
        "status": "online",
        "version": VERSION,
        "message": "LeakGuard backend is running"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }


@app.websocket("/ws/admin")
async def admin_websocket(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            # Keep receiving to detect client ping or disconnect
            await websocket.receive_text()

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception:
        manager.disconnect(websocket)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host=HOST,
        port=PORT,
        reload=False
    )
