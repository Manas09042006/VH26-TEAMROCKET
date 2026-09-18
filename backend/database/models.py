from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Index
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

    # New relationship for project/file monitoring.
    file_activities = relationship(
        "FileActivity",
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
            "last_seen": (
                self.last_seen.isoformat()
                if self.last_seen
                else None
            ),
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
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
            "timestamp": (
                self.timestamp.isoformat()
                if self.timestamp
                else None
            ),
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
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }


# ============================================================
# PROJECT MONITORING
# ============================================================

class Project(Base):
    """
    Represents a project/workspace being monitored by LeakGuard.

    project_key is used to identify the same logical project across
    different employee machines.

    Example:
        project_key = "leakguard"
        name = "LeakGuard"
    """

    __tablename__ = "projects"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    project_key = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    created_at = Column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    file_activities = relationship(
        "FileActivity",
        back_populates="project",
        cascade="all, delete-orphan"
    )

    def to_dict(self):
        return {
            "id": self.id,
            "project_key": self.project_key,
            "name": self.name,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
        }


class FileActivity(Base):
    """
    Tracks an employee's current/recent activity on a project file.

    The combination of project_key + relative_path identifies a
    logical file across different machines.

    Example:

        Employee A:
            C:\\Users\\Manas\\Projects\\LeakGuard\\backend\\main.py

        Employee B:
            D:\\Work\\LeakGuard\\backend\\main.py

    Both can resolve to:

        project_key = "leakguard"
        relative_path = "backend/main.py"

    This allows LeakGuard to detect that both employees are working
    on the same logical project file even when their absolute paths
    are different.
    """

    __tablename__ = "file_activities"

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

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=False,
        index=True
    )

    project_key = Column(
        String(255),
        nullable=False,
        index=True
    )

    file_name = Column(
        String(255),
        nullable=False
    )

    file_path = Column(
        String(1000),
        nullable=False
    )

    relative_path = Column(
        String(1000),
        nullable=False
    )

    activity_type = Column(
        String(50),
        nullable=False,
        default="OPEN"
    )

    status = Column(
        String(30),
        nullable=False,
        default="ACTIVE",
        index=True
    )

    machine_name = Column(
        String(150),
        nullable=True
    )

    started_at = Column(
        DateTime,
        default=utc_now,
        nullable=False
    )

    last_seen = Column(
        DateTime,
        default=utc_now,
        nullable=False,
        index=True
    )

    ended_at = Column(
        DateTime,
        nullable=True
    )

    employee = relationship(
        "Employee",
        back_populates="file_activities"
    )

    project = relationship(
        "Project",
        back_populates="file_activities"
    )

    # This index will make same-file activity checks faster.
    __table_args__ = (
        Index(
            "ix_file_activity_same_file",
            "project_key",
            "relative_path",
            "status"
        ),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "employee_id": self.employee_id,
            "project_id": self.project_id,
            "project_key": self.project_key,
            "file_name": self.file_name,
            "file_path": self.file_path,
            "relative_path": self.relative_path,
            "activity_type": self.activity_type,
            "status": self.status,
            "machine_name": self.machine_name,
            "started_at": (
                self.started_at.isoformat()
                if self.started_at
                else None
            ),
            "last_seen": (
                self.last_seen.isoformat()
                if self.last_seen
                else None
            ),
            "ended_at": (
                self.ended_at.isoformat()
                if self.ended_at
                else None
            ),
        }