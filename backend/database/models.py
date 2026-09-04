from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from backend.database.database import Base


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    display_name = Column(
        String(150),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="EMPLOYEE"
    )

    machine_name = Column(
        String(150),
        nullable=True
    )

    agent_id = Column(
        String(150),
        unique=True,
        nullable=True
    )

    status = Column(
        String(20),
        nullable=False,
        default="OFFLINE"
    )

    last_seen = Column(
        DateTime,
        nullable=True
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_id = Column(
        Integer,
        nullable=False,
        index=True
    )

    event_type = Column(
        String(50),
        nullable=False
    )

    description = Column(
        String(500),
        nullable=False
    )

    severity = Column(
        String(20),
        nullable=False,
        default="INFO"
    )

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )    