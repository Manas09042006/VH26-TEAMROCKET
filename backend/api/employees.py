from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.database.models import Employee


router = APIRouter(
    prefix="/employees",
    tags=["Employees"]
)


class EmployeeCreate(BaseModel):
    username: str
    display_name: str
    role: str = "EMPLOYEE"
    machine_name: str | None = None
    agent_id: str | None = None


@router.post("/")
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    existing = db.query(Employee).filter(
        Employee.username == employee_data.username
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="Employee username already exists"
        )

    employee = Employee(
        username=employee_data.username,
        display_name=employee_data.display_name,
        role=employee_data.role,
        machine_name=employee_data.machine_name,
        agent_id=employee_data.agent_id,
        status="OFFLINE"
    )

    db.add(employee)
    db.commit()
    db.refresh(employee)

    return {
        "message": "Employee created successfully",
        "employee": {
            "id": employee.id,
            "username": employee.username,
            "display_name": employee.display_name,
            "role": employee.role,
            "machine_name": employee.machine_name,
            "agent_id": employee.agent_id,
            "status": employee.status
        }
    }


@router.get("/")
def get_employees(
    db: Session = Depends(get_db)
):
    employees = db.query(Employee).all()

    return {
        "count": len(employees),
        "employees": [
            {
                "id": employee.id,
                "username": employee.username,
                "display_name": employee.display_name,
                "role": employee.role,
                "machine_name": employee.machine_name,
                "agent_id": employee.agent_id,
                "status": employee.status,
                "last_seen": employee.last_seen
            }
            for employee in employees
        ]
    }


@router.get("/{employee_id}")
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    employee = db.query(Employee).filter(
        Employee.id == employee_id
    ).first()

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return {
        "id": employee.id,
        "username": employee.username,
        "display_name": employee.display_name,
        "role": employee.role,
        "machine_name": employee.machine_name,
        "agent_id": employee.agent_id,
        "status": employee.status,
        "last_seen": employee.last_seen
    }