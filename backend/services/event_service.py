import logging
import os
import re

from sqlalchemy.orm import Session

from backend.core.config import AUTO_REGISTER_AGENTS
from backend.core.websocket import manager
from backend.database.models import (
    ActivityLog,
    Employee,
    FileActivity,
    Project,
    utc_now,
)

logger = logging.getLogger("leakguard.event_service")


# ============================================================
# EXISTING EVENT SYSTEM
# ============================================================

async def record_event(
    db: Session,
    agent_id: str,
    event_type: str,
    description: str,
    severity: str = "INFO"
) -> tuple[ActivityLog | None, Employee | None]:
    """
    Record an activity/security event from an agent.

    Existing behavior is preserved:
    - Auto-register unknown agents when enabled
    - Store ActivityLog
    - Broadcast ACTIVITY_EVENT
    - Broadcast SECURITY_EVENT for important events
    """

    employee = (
        db.query(Employee)
        .filter(Employee.agent_id == agent_id)
        .first()
    )

    if not employee:
        if not AUTO_REGISTER_AGENTS:
            return None, None

        logger.info(
            f"Auto-registering new agent on event: {agent_id}"
        )

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

    # Existing realtime activity notification
    await manager.broadcast({
        "type": "ACTIVITY_EVENT",
        "description": (
            f"[{employee.display_name or employee.username}] "
            f"{description}"
        ),
        "event_id": event.id,
        "event_type": event_type,
        "severity": event.severity,
        "employee_id": employee.id,
        "timestamp": (
            event.timestamp.isoformat()
            if event.timestamp
            else ""
        )
    })

    # Existing security notification
    if (
        event.severity in ("HIGH", "CRITICAL", "WARNING")
        or event_type in ("RESOURCE_LEAK", "SECURITY_ALERT")
    ):
        await manager.broadcast({
            "type": "SECURITY_EVENT",
            "description": (
                f"[{employee.display_name or employee.username}] "
                f"{description}"
            ),
            "severity": event.severity,
            "employee_id": employee.id,
            "agent_id": agent_id,
            "event_type": event_type,
            "timestamp": (
                event.timestamp.isoformat()
                if event.timestamp
                else ""
            )
        })

    return event, employee


# ============================================================
# PROJECT / FILE HELPERS
# ============================================================

def normalize_path(path: str) -> str:
    """
    Normalize a filesystem path so comparisons work consistently
    across Windows/Linux path formatting.
    """

    if not path:
        return ""

    path = path.replace("\\", "/")

    # Remove duplicate separators
    path = re.sub(r"/+", "/", path)

    return path.rstrip("/").lower()


def make_project_key(project_name: str) -> str:
    """
    Create a stable project identifier from a project name.

    Example:
        'My Weather App' -> 'my-weather-app'
    """

    if not project_name:
        return "unknown-project"

    key = project_name.strip().lower()

    key = re.sub(
        r"[^a-z0-9]+",
        "-",
        key
    )

    key = key.strip("-")

    return key or "unknown-project"


def calculate_relative_path(
    file_path: str,
    project_path: str
) -> str:
    """
    Calculate the path of a file relative to its project folder.

    If the file is outside the project folder, the normalized
    absolute path is returned instead.
    """

    normalized_file = normalize_path(file_path)
    normalized_project = normalize_path(project_path)

    if not normalized_file:
        return ""

    if not normalized_project:
        return normalized_file

    prefix = normalized_project + "/"

    if normalized_file.startswith(prefix):
        return normalized_file[len(prefix):]

    if normalized_file == normalized_project:
        return os.path.basename(normalized_file)

    return normalized_file


# ============================================================
# PROJECT CREATION / LOOKUP
# ============================================================

def get_or_create_project(
    db: Session,
    project_name: str,
    project_path: str
) -> Project:
    """
    Find an existing project or create a new one.

    project_key is shared between machines so that:

        C:/Projects/LeakGuard
        D:/Work/LeakGuard

    can still represent the same logical project.
    """

    project_key = make_project_key(project_name)

    project = (
        db.query(Project)
        .filter(Project.project_key == project_key)
        .first()
    )

    if project:
        return project

    project = Project(
        project_key=project_key,
        name=project_name.strip() or "Unknown Project",
    )

    db.add(project)
    db.commit()
    db.refresh(project)

    logger.info(
        f"Created project '{project.name}' "
        f"({project.project_key})"
    )

    return project


# ============================================================
# FILE ACTIVITY
# ============================================================

async def record_file_activity(
    db: Session,
    agent_id: str,
    project_name: str,
    project_path: str,
    file_path: str,
    file_name: str,
    activity_type: str = "OPEN",
    machine_name: str | None = None
) -> dict:
    """
    Record an employee's activity on a project file.

    This function:

    1. Finds the employee.
    2. Creates/finds the project.
    3. Creates/updates FileActivity.
    4. Detects whether another employee is using the same file.
    5. Creates a security/activity log for a conflict.
    6. Sends realtime WebSocket notifications.
    """

    # --------------------------------------------------------
    # Find employee
    # --------------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(Employee.agent_id == agent_id)
        .first()
    )

    if not employee:
        if not AUTO_REGISTER_AGENTS:
            return {
                "success": False,
                "error": "Agent not registered",
                "employee": None,
            }

        logger.info(
            f"Auto-registering new agent on file activity: "
            f"{agent_id}"
        )

        employee = Employee(
            username=f"agent_{agent_id}",
            display_name=f"Agent ({agent_id})",
            role="EMPLOYEE",
            agent_id=agent_id,
            machine_name=machine_name,
            status="ONLINE",
            last_seen=utc_now()
        )

        db.add(employee)
        db.commit()
        db.refresh(employee)

    elif machine_name:
        # Keep machine information updated.
        employee.machine_name = machine_name
        employee.last_seen = utc_now()
        employee.status = "ONLINE"

    # --------------------------------------------------------
    # Project
    # --------------------------------------------------------

    project = get_or_create_project(
        db=db,
        project_name=project_name,
        project_path=project_path
    )

    project_key = project.project_key

    relative_path = calculate_relative_path(
        file_path=file_path,
        project_path=project_path
    )

    normalized_file_path = normalize_path(file_path)

    normalized_activity_type = (
        activity_type.strip().upper()
        if activity_type
        else "OPEN"
    )

    now = utc_now()

    # --------------------------------------------------------
    # Find current activity for THIS employee/file
    # --------------------------------------------------------

    current_activity = (
        db.query(FileActivity)
        .filter(
            FileActivity.employee_id == employee.id,
            FileActivity.project_key == project_key,
            FileActivity.relative_path == relative_path,
            FileActivity.status == "ACTIVE",
        )
        .first()
    )

    if current_activity:

        current_activity.file_path = file_path
        current_activity.file_name = (
            file_name
            or os.path.basename(file_path)
        )
        current_activity.activity_type = (
            normalized_activity_type
        )
        current_activity.machine_name = (
            machine_name or employee.machine_name
        )
        current_activity.last_seen = now

        db.commit()
        db.refresh(current_activity)

        file_activity = current_activity

    else:

        file_activity = FileActivity(
            employee_id=employee.id,
            project_id=project.id,
            project_key=project_key,
            file_name=(
                file_name
                or os.path.basename(file_path)
            ),
            file_path=file_path,
            relative_path=relative_path,
            activity_type=normalized_activity_type,
            status="ACTIVE",
            machine_name=(
                machine_name
                or employee.machine_name
            ),
            started_at=now,
            last_seen=now,
        )

        db.add(file_activity)
        db.commit()
        db.refresh(file_activity)

    # --------------------------------------------------------
    # Detect other employees using SAME logical file
    # --------------------------------------------------------

    other_activities = (
        db.query(FileActivity)
        .filter(
            FileActivity.project_key == project_key,
            FileActivity.relative_path == relative_path,
            FileActivity.status == "ACTIVE",
            FileActivity.employee_id != employee.id,
        )
        .all()
    )

    conflict_detected = len(other_activities) > 0

    # --------------------------------------------------------
    # Realtime file activity notification
    # --------------------------------------------------------

    await manager.broadcast({
        "type": "FILE_ACTIVITY",
        "employee_id": employee.id,
        "employee_name": (
            employee.display_name
            or employee.username
        ),
        "agent_id": agent_id,
        "machine_name": (
            machine_name
            or employee.machine_name
        ),
        "project_id": project.id,
        "project_name": project.name,
        "project_key": project_key,
        "file_name": file_activity.file_name,
        "file_path": file_activity.file_path,
        "relative_path": relative_path,
        "activity_type": normalized_activity_type,
        "status": file_activity.status,
        "timestamp": now.isoformat(),
    })

    # --------------------------------------------------------
    # FILE CONFLICT
    # --------------------------------------------------------

    if conflict_detected:

        other_employee_data = []

        for activity in other_activities:

            other_employee = (
                db.query(Employee)
                .filter(
                    Employee.id == activity.employee_id
                )
                .first()
            )

            if not other_employee:
                continue

            other_employee_data.append({
                "employee_id": other_employee.id,
                "employee_name": (
                    other_employee.display_name
                    or other_employee.username
                ),
                "agent_id": other_employee.agent_id,
                "machine_name": (
                    other_employee.machine_name
                    or activity.machine_name
                ),
            })

        other_names = ", ".join(
            item["employee_name"]
            for item in other_employee_data
        )

        description = (
            f"Multiple employees are accessing the same file. "
            f"Project: {project.name}. "
            f"File: {relative_path}. "
            f"Current employee: "
            f"{employee.display_name or employee.username}. "
            f"Other active users: {other_names}."
        )

        # Store conflict in the existing ActivityLog system.
        conflict_event = ActivityLog(
            employee_id=employee.id,
            event_type="FILE_CONFLICT",
            description=description,
            severity="WARNING",
            timestamp=now,
        )

        db.add(conflict_event)
        db.commit()
        db.refresh(conflict_event)

        # Send security event to admin immediately.
        await manager.broadcast({
            "type": "SECURITY_EVENT",
            "event_id": conflict_event.id,
            "event_type": "FILE_CONFLICT",
            "severity": "WARNING",
            "description": description,
            "employee_id": employee.id,
            "employee_name": (
                employee.display_name
                or employee.username
            ),
            "agent_id": agent_id,
            "machine_name": (
                machine_name
                or employee.machine_name
            ),
            "project_id": project.id,
            "project_name": project.name,
            "project_key": project_key,
            "file_name": file_activity.file_name,
            "file_path": file_activity.file_path,
            "relative_path": relative_path,
            "other_employees": other_employee_data,
            "timestamp": now.isoformat(),
        })

    # --------------------------------------------------------
    # Return result
    # --------------------------------------------------------

    return {
        "success": True,
        "conflict_detected": conflict_detected,
        "employee": {
            "id": employee.id,
            "name": (
                employee.display_name
                or employee.username
            ),
            "agent_id": employee.agent_id,
            "machine_name": employee.machine_name,
        },
        "project": project.to_dict(),
        "file_activity": file_activity.to_dict(),
        "other_active_users": (
            other_employee_data
            if conflict_detected
            else []
        ),
    }


# ============================================================
# END FILE ACTIVITY
# ============================================================

async def close_file_activity(
    db: Session,
    agent_id: str,
    project_key: str,
    relative_path: str
) -> bool:
    """
    Mark an employee's file activity as CLOSED.
    """

    employee = (
        db.query(Employee)
        .filter(Employee.agent_id == agent_id)
        .first()
    )

    if not employee:
        return False

    activity = (
        db.query(FileActivity)
        .filter(
            FileActivity.employee_id == employee.id,
            FileActivity.project_key == project_key,
            FileActivity.relative_path == relative_path,
            FileActivity.status == "ACTIVE",
        )
        .first()
    )

    if not activity:
        return False

    now = utc_now()

    activity.status = "CLOSED"
    activity.ended_at = now
    activity.last_seen = now

    db.commit()
    db.refresh(activity)

    await manager.broadcast({
        "type": "FILE_ACTIVITY_CLOSED",
        "employee_id": employee.id,
        "employee_name": (
            employee.display_name
            or employee.username
        ),
        "project_key": project_key,
        "relative_path": relative_path,
        "timestamp": now.isoformat(),
    })

    return True


# ============================================================
# EXISTING LOG FUNCTIONS
# ============================================================

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
        query = query.filter(
            ActivityLog.employee_id == employee_id
        )

    if severity is not None:
        query = query.filter(
            ActivityLog.severity == severity.upper()
        )

    if event_type is not None:
        query = query.filter(
            ActivityLog.event_type == event_type
        )

    return (
        query
        .order_by(ActivityLog.timestamp.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_total_log_count(
    db: Session,
    employee_id: int | None = None,
    severity: str | None = None,
    event_type: str | None = None
) -> int:

    query = db.query(ActivityLog)

    if employee_id is not None:
        query = query.filter(
            ActivityLog.employee_id == employee_id
        )

    if severity is not None:
        query = query.filter(
            ActivityLog.severity == severity.upper()
        )

    if event_type is not None:
        query = query.filter(
            ActivityLog.event_type == event_type
        )

    return query.count()


def get_dashboard_statistics(db: Session) -> dict:

    total_employees = db.query(Employee).count()

    online_employees = (
        db.query(Employee)
        .filter(Employee.status == "ONLINE")
        .count()
    )

    offline_employees = (
        db.query(Employee)
        .filter(Employee.status == "OFFLINE")
        .count()
    )

    total_logs = db.query(ActivityLog).count()

    security_incidents = (
        db.query(ActivityLog)
        .filter(
            (ActivityLog.severity.in_(["HIGH", "CRITICAL"]))
            | (
                ActivityLog.event_type
                == "RESOURCE_LEAK"
            )
        )
        .count()
    )

    return {
        "total_employees": total_employees,
        "online_employees": online_employees,
        "offline_employees": offline_employees,
        "total_logs": total_logs,
        "security_incidents": security_incidents,
    }