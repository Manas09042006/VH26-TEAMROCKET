from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services import employee_service, event_service


router = APIRouter(
    prefix="/agents",
    tags=["Agent"]
)


# ============================================================
# EXISTING REQUEST MODELS
# ============================================================

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


# ============================================================
# NEW FILE ACTIVITY REQUEST MODEL
# ============================================================

class FileActivityRequest(BaseModel):
    """
    Request sent by a LeakGuard agent when an employee
    interacts with a project file.
    """

    agent_id: str

    project_name: str
    project_path: str

    file_path: str
    file_name: str

    activity_type: str = "OPEN"

    machine_name: str | None = None


# ============================================================
# AGENT REGISTRATION
# ============================================================

@router.post("/register")
async def register_agent(
    register_data: AgentRegisterRequest,
    db: Session = Depends(get_db)
):
    """
    Explicitly register an agent or update its machine details.
    """

    employee = employee_service.get_employee_by_agent_id(
        db,
        register_data.agent_id
    )

    if employee:
        if register_data.machine_name:
            employee.machine_name = (
                register_data.machine_name
            )

        if register_data.display_name:
            employee.display_name = (
                register_data.display_name
            )

        db.commit()
        db.refresh(employee)

        return {
            "message": "Agent already registered, details updated",
            "employee": employee.to_dict()
        }

    username = (
        register_data.username
        or f"agent_{register_data.agent_id}"
    )

    display_name = (
        register_data.display_name
        or (
            f"{register_data.machine_name or 'Agent'} "
            f"({register_data.agent_id})"
        )
    )

    existing_user = employee_service.get_employee_by_username(
        db,
        username
    )

    if existing_user:
        username = (
            f"{username}_"
            f"{register_data.agent_id[:6]}"
        )

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


# ============================================================
# HEARTBEAT
# ============================================================

@router.post("/heartbeat")
async def heartbeat(
    heartbeat_data: HeartbeatRequest,
    db: Session = Depends(get_db)
):
    """
    Record heartbeat from an employee monitoring agent
    and broadcast status.
    """

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
        "last_seen": (
            employee.last_seen.isoformat()
            if employee.last_seen
            else None
        )
    }


# ============================================================
# EXISTING SECURITY / ACTIVITY EVENT
# ============================================================

@router.post("/event")
async def create_event(
    event_data: EventRequest,
    db: Session = Depends(get_db)
):
    """
    Receive security or activity events from agent
    and broadcast them in real time.

    Existing endpoint preserved.
    """

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


# ============================================================
# NEW FILE ACTIVITY ENDPOINT
# ============================================================

@router.post("/file-activity")
async def create_file_activity(
    activity_data: FileActivityRequest,
    db: Session = Depends(get_db)
):
    """
    Receive project/file activity from a LeakGuard agent.

    This endpoint:
        1. Identifies the employee.
        2. Identifies/creates the project.
        3. Records the current file activity.
        4. Detects if another employee is using
           the same logical file.
        5. Creates a FILE_CONFLICT event when required.
        6. Sends realtime WebSocket notifications.
    """

    result = await event_service.record_file_activity(
        db=db,
        agent_id=activity_data.agent_id,
        project_name=activity_data.project_name,
        project_path=activity_data.project_path,
        file_path=activity_data.file_path,
        file_name=activity_data.file_name,
        activity_type=activity_data.activity_type,
        machine_name=activity_data.machine_name
    )

    if not result.get("success"):
        error = result.get(
            "error",
            "Unable to record file activity"
        )

        if error == "Agent not registered":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return {
        "message": "File activity recorded",
        "activity": result
    }


# ============================================================
# CLOSE FILE ACTIVITY
# ============================================================

@router.post("/file-activity/close")
async def close_file_activity(
    activity_data: FileActivityRequest,
    db: Session = Depends(get_db)
):
    """
    Mark a currently active file activity as closed.

    The same FileActivityRequest model is intentionally used
    here so no additional dependency/model is required.
    """

    project_key = event_service.make_project_key(
        activity_data.project_name
    )

    relative_path = event_service.calculate_relative_path(
        file_path=activity_data.file_path,
        project_path=activity_data.project_path
    )

    closed = await event_service.close_file_activity(
        db=db,
        agent_id=activity_data.agent_id,
        project_key=project_key,
        relative_path=relative_path
    )

    if not closed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active file activity not found"
        )

    return {
        "message": "File activity closed",
        "project_key": project_key,
        "relative_path": relative_path
    }