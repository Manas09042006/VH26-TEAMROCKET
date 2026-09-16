import logging
from sqlalchemy.orm import Session

from backend.core.config import AUTO_REGISTER_AGENTS
from backend.core.websocket import manager
from backend.database.models import Employee, utc_now

logger = logging.getLogger("leakguard.employee_service")


def get_employees(db: Session, skip: int = 0, limit: int = 100) -> list[Employee]:
    return db.query(Employee).offset(skip).limit(limit).all()


def get_employee_by_id(db: Session, employee_id: int) -> Employee | None:
    return db.query(Employee).filter(Employee.id == employee_id).first()


def get_employee_by_username(db: Session, username: str) -> Employee | None:
    return db.query(Employee).filter(Employee.username == username).first()


def get_employee_by_agent_id(db: Session, agent_id: str) -> Employee | None:
    return db.query(Employee).filter(Employee.agent_id == agent_id).first()


def create_employee(
    db: Session,
    username: str,
    display_name: str,
    role: str = "EMPLOYEE",
    machine_name: str | None = None,
    agent_id: str | None = None
) -> Employee:
    employee = Employee(
        username=username,
        display_name=display_name,
        role=role,
        machine_name=machine_name,
        agent_id=agent_id,
        status="OFFLINE"
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(
    db: Session,
    employee_id: int,
    username: str | None = None,
    display_name: str | None = None,
    role: str | None = None,
    machine_name: str | None = None,
    agent_id: str | None = None,
    status: str | None = None
) -> Employee | None:
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        return None

    if username is not None:
        employee.username = username
    if display_name is not None:
        employee.display_name = display_name
    if role is not None:
        employee.role = role
    if machine_name is not None:
        employee.machine_name = machine_name
    if agent_id is not None:
        employee.agent_id = agent_id
    if status is not None:
        employee.status = status

    db.commit()
    db.refresh(employee)
    return employee


def delete_employee(db: Session, employee_id: int) -> bool:
    employee = get_employee_by_id(db, employee_id)
    if not employee:
        return False
    db.delete(employee)
    db.commit()
    return True


async def handle_heartbeat(
    db: Session,
    agent_id: str,
    machine_name: str | None = None
) -> Employee:
    """Process agent heartbeat, update status, and broadcast changes."""
    employee = get_employee_by_agent_id(db, agent_id)

    if not employee:
        if not AUTO_REGISTER_AGENTS:
            return None

        # Auto-register newly discovered agent
        logger.info(f"Auto-registering new agent: {agent_id}")
        employee = Employee(
            username=f"agent_{agent_id}",
            display_name=f"{machine_name or 'Agent'} ({agent_id})",
            role="EMPLOYEE",
            machine_name=machine_name,
            agent_id=agent_id,
            status="ONLINE",
            last_seen=utc_now()
        )
        db.add(employee)
        db.commit()
        db.refresh(employee)

        await manager.broadcast({
            "type": "EMPLOYEE_STATUS",
            "employee_id": employee.id,
            "username": employee.username,
            "display_name": employee.display_name,
            "role": employee.role,
            "agent_id": employee.agent_id,
            "machine_name": employee.machine_name,
            "status": employee.status,
        })
        return employee

    status_changed = employee.status != "ONLINE"
    employee.status = "ONLINE"
    employee.last_seen = utc_now()
    if machine_name:
        employee.machine_name = machine_name

    db.commit()
    db.refresh(employee)

    if status_changed:
        await manager.broadcast({
            "type": "EMPLOYEE_STATUS",
            "employee_id": employee.id,
            "username": employee.username,
            "display_name": employee.display_name,
            "role": employee.role,
            "agent_id": employee.agent_id,
            "machine_name": employee.machine_name,
            "status": employee.status,
        })

    return employee
