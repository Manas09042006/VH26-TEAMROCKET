from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Employee, ActivityLog


router = APIRouter(
    prefix="/agents",
    tags=["Agent"]
)


class HeartbeatRequest(BaseModel):
    agent_id: str
    machine_name: str | None = None


class EventRequest(BaseModel):
    agent_id: str
    event_type: str
    description: str
    severity: str = "INFO"


@router.post("/heartbeat")
def heartbeat(
    heartbeat_data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(
        Employee.agent_id == heartbeat_data.agent_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Agent not registered"
        )

    employee.status = "ONLINE"
    employee.last_seen = datetime.utcnow()

    if heartbeat_data.machine_name:
        employee.machine_name = heartbeat_data.machine_name

    db.commit()
    db.refresh(employee)

    return {
        "message": "Heartbeat received",
        "employee_id": employee.id,
        "status": employee.status,
        "last_seen": employee.last_seen
    }


@router.post("/event")
def create_event(
    event_data: EventRequest,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(
        Employee.agent_id == event_data.agent_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Agent not registered"
        )

    event = ActivityLog(
        employee_id=employee.id,
        event_type=event_data.event_type,
        description=event_data.description,
        severity=event_data.severity,
        timestamp=datetime.utcnow()
    )

    db.add(event)
    db.commit()
    db.refresh(event)

    return {
        "message": "Event recorded",
        "event": {
            "id": event.id,
            "employee_id": event.employee_id,
            "event_type": event.event_type,
            "description": event.description,
            "severity": event.severity,
            "timestamp": event.timestamp
        }
    }