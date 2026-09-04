from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import ActivityLog


router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/logs")
def get_activity_logs(
    db: Session = Depends(get_db)
):
    logs = (
        db.query(ActivityLog)
        .order_by(ActivityLog.timestamp.desc())
        .all()
    )

    return {
        "count": len(logs),
        "logs": [
            {
                "id": log.id,
                "employee_id": log.employee_id,
                "event_type": log.event_type,
                "description": log.description,
                "severity": log.severity,
                "timestamp": log.timestamp
            }
            for log in logs
        ]
    }