from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database.database import get_db
from backend.services import employee_service

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


class EmployeeUpdate(BaseModel):
    username: str | None = None
    display_name: str | None = None
    role: str | None = None
    machine_name: str | None = None
    agent_id: str | None = None
    status: str | None = None


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_employee(
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db)
):
    existing = employee_service.get_employee_by_username(db, employee_data.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Employee username already exists"
        )

    if employee_data.agent_id:
        existing_agent = employee_service.get_employee_by_agent_id(db, employee_data.agent_id)
        if existing_agent:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Agent ID is already assigned to another employee"
            )

    employee = employee_service.create_employee(
        db=db,
        username=employee_data.username,
        display_name=employee_data.display_name,
        role=employee_data.role,
        machine_name=employee_data.machine_name,
        agent_id=employee_data.agent_id
    )

    return {
        "message": "Employee created successfully",
        "employee": employee.to_dict()
    }


@router.get("/")
def get_employees(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    employees = employee_service.get_employees(db, skip=skip, limit=limit)

    return {
        "count": len(employees),
        "employees": [emp.to_dict() for emp in employees]
    }


@router.get("/{employee_id}")
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    employee = employee_service.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return employee.to_dict()


@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    employee_data: EmployeeUpdate,
    db: Session = Depends(get_db)
):
    employee = employee_service.get_employee_by_id(db, employee_id)
    if not employee:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    if employee_data.username and employee_data.username != employee.username:
        existing = employee_service.get_employee_by_username(db, employee_data.username)
        if existing and existing.id != employee_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Employee username already exists"
            )

    updated_employee = employee_service.update_employee(
        db=db,
        employee_id=employee_id,
        username=employee_data.username,
        display_name=employee_data.display_name,
        role=employee_data.role,
        machine_name=employee_data.machine_name,
        agent_id=employee_data.agent_id,
        status=employee_data.status
    )

    return {
        "message": "Employee updated successfully",
        "employee": updated_employee.to_dict()
    }


@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db)
):
    deleted = employee_service.delete_employee(db, employee_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    return {
        "message": "Employee deleted successfully"
    }