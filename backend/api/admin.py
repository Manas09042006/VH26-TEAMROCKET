from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import ActivityLog
from backend.services import event_service

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/logs")
def get_activity_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    employee_id: int | None = Query(None),
    severity: str | None = Query(None),
    event_type: str | None = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieve activity logs with filtering and pagination."""
    logs = event_service.get_activity_logs(
        db=db,
        skip=skip,
        limit=limit,
        employee_id=employee_id,
        severity=severity,
        event_type=event_type
    )
    total = event_service.get_total_log_count(
        db=db,
        employee_id=employee_id,
        severity=severity,
        event_type=event_type
    )

    return {
        "count": len(logs),
        "total": total,
        "logs": [log.to_dict() for log in logs]
    }


@router.get("/stats")
def get_dashboard_stats(
    db: Session = Depends(get_db)
):
    """Get system-wide summary statistics for the admin dashboard."""
    return event_service.get_dashboard_statistics(db)


@router.delete("/logs")
def clear_activity_logs(
    employee_id: int | None = Query(None),
    db: Session = Depends(get_db)
):
    """Clear activity logs (optionally for a specific employee)."""
    query = db.query(ActivityLog)
    if employee_id is not None:
        query = query.filter(ActivityLog.employee_id == employee_id)

    deleted_count = query.delete(synchronize_session=False)
    db.commit()

    return {
        "message": f"Successfully deleted {deleted_count} logs."
    }