from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services import employee_service, event_service

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


class AgentRegisterRequest(BaseModel):
    agent_id: str
    machine_name: str | None = None
    username: str | None = None
    display_name: str | None = None


@router.post("/register")
async def register_agent(
    register_data: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """Explicitly register an agent or update its machine details."""
    employee = employee_service.get_employee_by_agent_id(db, register_data.agent_id)

    if employee:
        if register_data.machine_name:
            employee.machine_name = register_data.machine_name
        if register_data.display_name:
            employee.display_name = register_data.display_name
        db.commit()
        db.refresh(employee)
        return {
            "message": "Agent already registered, details updated",
            "employee": employee.to_dict()
        }

    username = register_data.username or f"agent_{register_data.agent_id}"
    display_name = register_data.display_name or f"{register_data.machine_name or 'Agent'} ({register_data.agent_id})"

    existing_user = employee_service.get_employee_by_username(db, username)
    if existing_user:
        username = f"{username}_{register_data.agent_id[:6]}"

    employee = employee_service.create_employee(
        db=db,
        username=username,
        display_name=display_name,
        role="EMPLOYEE",
        machine_name=register_data.machine_name,
        agent_id=register_data.agent_id
    )

    return {
        "message": "Agent registered successfully",
        "employee": employee.to_dict()
    }


@router.post("/heartbeat")
async def heartbeat(
    heartbeat_data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """Record heartbeat from an employee monitoring agent and broadcast status."""
    employee = await employee_service.handle_heartbeat(
        db=db,
        agent_id=heartbeat_data.agent_id,
        machine_name=heartbeat_data.machine_name
    )

    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not registered"
        )

    return {
        "message": "Heartbeat received",
        "employee_id": employee.id,
        "status": employee.status,
        "last_seen": employee.last_seen.isoformat() if employee.last_seen else None
    }


@router.post("/event")
async def create_event(
    event_data: EventRequest,
    db: Session = Depends(get_db)
):
    """Receive security or activity events from agent and broadcast in real time."""
    event, employee = await event_service.record_event(
        db=db,
        agent_id=event_data.agent_id,
        event_type=event_data.event_type,
        description=event_data.description,
        severity=event_data.severity
    )

    if not event or not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not registered"
        )

    return {
        "message": "Event recorded",
        "event": event.to_dict()
    }