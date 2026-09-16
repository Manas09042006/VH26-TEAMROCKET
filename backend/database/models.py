from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from backend.database.database import Base


def utc_now():
    """Return timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


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
        default=utc_now,
        nullable=False
    )

    activity_logs = relationship(
        "ActivityLog",
        back_populates="employee",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "display_name": self.display_name,
            "role": self.role,
            "machine_name": self.machine_name,
            "agent_id": self.agent_id,
            "status": self.status,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
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
        default=utc_now,
        nullable=False
    )

    employee = relationship(
        "Employee",
        back_populates="activity_logs"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "event_type": self.event_type,
            "description": self.description,
            "severity": self.severity,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


class AdminUser(Base):
    __tablename__ = "admin_users"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
        index=True
    )

    password_hash = Column(
        String(255),
        nullable=False
    )

    role = Column(
        String(50),
        nullable=False,
        default="ADMIN"
    )

    created_at = Column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    def to_dict(self):
        return {
            "id": self.id,
            "username": self.username,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }