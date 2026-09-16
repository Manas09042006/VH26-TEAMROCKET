import logging
from sqlalchemy.orm import Session

from backend.core.config import AUTO_REGISTER_AGENTS
from backend.core.websocket import manager
from backend.database.models import ActivityLog, Employee, utc_now

logger = logging.getLogger("leakguard.event_service")


async def record_event(
    db: Session,
    agent_id: str,
    event_type: str,
    description: str,
    severity: str = "INFO"
) -> tuple[ActivityLog | None, Employee | None]:
    """Record an activity or security event from an agent and broadcast via WebSocket."""
    employee = db.query(Employee).filter(Employee.agent_id == agent_id).first()

    if not employee:
        if not AUTO_REGISTER_AGENTS:
            return None, None

        logger.info(f"Auto-registering new agent on event: {agent_id}")
        employee = Employee(
            username=f"agent_{agent_id}",
            display_name=f"Agent ({agent_id})",
            role="EMPLOYEE",
            agent_id=agent_id,
            status="ONLINE",
            last_seen=utc_now()
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

    # Record event in database
    event = ActivityLog(
        employee_id=employee.id,
        event_type=event_type,
        description=description,
        severity=severity.upper(),
        timestamp=utc_now()
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    # 1. Broadcast ACTIVITY_EVENT
    await manager.broadcast({
        "type": "ACTIVITY_EVENT",
        "description": f"[{employee.display_name or employee.username}] {description}",
        "event_id": event.id,
        "event_type": event_type,
        "severity": event.severity,
        "employee_id": employee.id,
        "timestamp": event.timestamp.isoformat() if event.timestamp else ""
    })

    # 2. If high/critical/warning or leak, also broadcast SECURITY_EVENT
    if event.severity in ("HIGH", "CRITICAL", "WARNING") or event_type in ("RESOURCE_LEAK", "SECURITY_ALERT"):
        await manager.broadcast({
            "type": "SECURITY_EVENT",
            "description": f"[{employee.display_name or employee.username}] {description}",
            "severity": event.severity,
            "employee_id": employee.id,
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": event.timestamp.isoformat() if event.timestamp else ""
        })

    return event, employee


def get_activity_logs(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    employee_id: int | None = None,
    severity: str | None = None,
    event_type: str | None = None
) -> list[ActivityLog]:
    query = db.query(ActivityLog)

    if employee_id is not None:
        query = query.filter(ActivityLog.employee_id == employee_id)
    if severity is not None:
        query = query.filter(ActivityLog.severity == severity.upper())
    if event_type is not None:
        query = query.filter(ActivityLog.event_type == event_type)

    return query.order_by(ActivityLog.timestamp.desc()).offset(skip).limit(limit).all()


def get_total_log_count(
    db: Session,
    employee_id: int | None = None,
    severity: str | None = None,
    event_type: str | None = None
) -> int:
    query = db.query(ActivityLog)

    if employee_id is not None:
        query = query.filter(ActivityLog.employee_id == employee_id)
    if severity is not None:
        query = query.filter(ActivityLog.severity == severity.upper())
    if event_type is not None:
        query = query.filter(ActivityLog.event_type == event_type)

    return query.count()


def get_dashboard_statistics(db: Session) -> dict:
    total_employees = db.query(Employee).count()
    online_employees = db.query(Employee).filter(Employee.status == "ONLINE").count()
    offline_employees = db.query(Employee).filter(Employee.status == "OFFLINE").count()
    total_logs = db.query(ActivityLog).count()
    security_incidents = db.query(ActivityLog).filter(
        (ActivityLog.severity.in_(["HIGH", "CRITICAL"])) | (ActivityLog.event_type == "RESOURCE_LEAK")
    ).count()

    return {
        "total_employees": total_employees,
        "online_employees": online_employees,
        "offline_employees": offline_employees,
        "total_logs": total_logs,
        "security_incidents": security_incidents,
    }
