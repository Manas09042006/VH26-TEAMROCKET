import asyncio
from datetime import datetime

from backend.database.database import SessionLocal
from backend.database.models import Employee
from backend.core.websocket import manager


HEARTBEAT_TIMEOUT_SECONDS = 240 


def check_employee_status():
    db = SessionLocal()

    try:
        now = datetime.utcnow()

        employees = db.query(Employee).all()

        for employee in employees:
            old_status = employee.status

            if employee.last_seen is None:
                new_status = "OFFLINE"

            else:
                time_since_heartbeat = (
                    now - employee.last_seen
                ).total_seconds()

                if time_since_heartbeat > HEARTBEAT_TIMEOUT_SECONDS:
                    new_status = "OFFLINE"
                else:
                    new_status = "ONLINE"

            employee.status = new_status

            # Broadcast only when the status actually changes.
            if old_status != new_status:
                asyncio.create_task(
                    manager.broadcast(
                        {
                            "type": "EMPLOYEE_STATUS",
                            "employee_id": employee.id,
                            "agent_id": employee.agent_id,
                            "machine_name": employee.machine_name,
                            "status": new_status,
                        }
                    )
                )

        db.commit()

    finally:
        db.close()


async def heartbeat_monitor():
    while True:
        check_employee_status()
        await asyncio.sleep(5)