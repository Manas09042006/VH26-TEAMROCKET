import asyncio
import logging
from datetime import datetime, timezone

from backend.core.config import HEARTBEAT_CHECK_INTERVAL, HEARTBEAT_TIMEOUT_SECONDS
from backend.core.websocket import manager
from backend.database.database import SessionLocal
from backend.database.models import Employee, utc_now

logger = logging.getLogger("leakguard.heartbeat_service")


def _calculate_elapsed_seconds(last_seen: datetime | None, now: datetime) -> float:
    if last_seen is None:
        return float("inf")

    # Handle naive vs timezone-aware comparisons cleanly
    if last_seen.tzinfo is None and now.tzinfo is not None:
        now = now.replace(tzinfo=None)
    elif last_seen.tzinfo is not None and now.tzinfo is None:
        last_seen = last_seen.replace(tzinfo=None)

    return (now - last_seen).total_seconds()


async def check_employee_status():
    """Evaluate heartbeat timeouts for all registered employees and broadcast changes."""
    db = SessionLocal()
    notifications = []

    try:
        now = utc_now()
        employees = db.query(Employee).all()

        for employee in employees:
            old_status = employee.status
            elapsed = _calculate_elapsed_seconds(employee.last_seen, now)

            if elapsed > HEARTBEAT_TIMEOUT_SECONDS:
                new_status = "OFFLINE"
            else:
                new_status = "ONLINE"

            employee.status = new_status

            if old_status != new_status:
                logger.info(
                    f"Employee status changed: id={employee.id}, "
                    f"username={employee.username}, status={old_status}->{new_status}"
                )
                notifications.append({
                    "type": "EMPLOYEE_STATUS",
                    "employee_id": employee.id,
                    "username": employee.username,
                    "display_name": employee.display_name,
                    "role": employee.role,
                    "agent_id": employee.agent_id,
                    "machine_name": employee.machine_name,
                    "status": new_status,
                })

        db.commit()

    except Exception as error:
        logger.error(f"Error checking employee status: {error}")
        db.rollback()
    finally:
        db.close()

    # Broadcast status change messages
    for message in notifications:
        await manager.broadcast(message)


async def heartbeat_monitor():
    """Background loop checking heartbeat timeouts periodically."""
    logger.info("Heartbeat monitor background service started.")
    while True:
        try:
            await check_employee_status()
        except Exception as error:
            logger.error(f"Unexpected error in heartbeat monitor: {error}")

        await asyncio.sleep(HEARTBEAT_CHECK_INTERVAL)