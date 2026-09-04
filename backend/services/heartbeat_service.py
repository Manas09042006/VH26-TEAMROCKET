import asyncio
from datetime import datetime, timedelta

from backend.database.database import SessionLocal
from backend.database.models import Employee


HEARTBEAT_TIMEOUT_SECONDS = 15


def check_employee_status():
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        employees = db.query(Employee).all()

        for employee in employees:
            if employee.last_seen is None:
                employee.status = "OFFLINE"
                continue

            time_since_heartbeat = (
                now - employee.last_seen
            ).total_seconds()

            if time_since_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
                employee.status = "OFFLINE"
            else:
                employee.status = "ONLINE"

        db.commit()

    finally:
        db.close()


async def heartbeat_monitor():
    while True:
        check_employee_status()
        await asyncio.sleep(5)