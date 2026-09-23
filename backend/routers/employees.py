from datetime import date
from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from backend.database import get_db
from backend.models import Employee
from backend.department_models import Department
from backend.audit_models import AuditLog
from backend.services.permissions import (
    require_admin,
    require_admin_or_hr,
)


router = APIRouter(
    prefix="/api/employees",
    tags=["Employees"]
)


# ============================================================
# VALID VALUES
# ============================================================

VALID_STATUSES = {
    "Active",
    "Inactive",
    "On Leave",
    "Terminated",
}


# ============================================================
# REQUEST MODEL
# ============================================================

class EmployeeCreate(BaseModel):
    name: str
    email: EmailStr
    age: int
    salary: float

    department_id: int | None = None
    manager_id: int | None = None

    status: str = "Active"
    joining_date: date | None = None
    skills: str | None = None
    profile_metadata: dict[str, Any] | None = None


# ============================================================
# AUDIT LOG
# ============================================================

def create_audit_log(
    db: Session,
    current_user,
    action: str,
    entity_id: int,
    details: str
):
    audit_log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        entity="Employee",
        entity_id=entity_id,
        details=details
    )

    db.add(audit_log)


# ============================================================
# VALIDATION
# ============================================================

def validate_employee_data(
    employee_data: EmployeeCreate,
    db: Session,
    employee_id: int | None = None
):
    # -----------------------------
    # Name
    # -----------------------------

    if not employee_data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Employee name cannot be empty"
        )

    if len(employee_data.name.strip()) > 100:
        raise HTTPException(
            status_code=400,
            detail="Employee name cannot exceed 100 characters"
        )

    # -----------------------------
    # Age
    # -----------------------------

    if employee_data.age < 18 or employee_data.age > 100:
        raise HTTPException(
            status_code=400,
            detail="Employee age must be between 18 and 100"
        )

    # -----------------------------
    # Salary
    # -----------------------------

    if employee_data.salary < 0:
        raise HTTPException(
            status_code=400,
            detail="Salary cannot be negative"
        )

    # -----------------------------
    # Status
    # -----------------------------

    if employee_data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid employee status. "
                "Allowed values: Active, Inactive, "
                "On Leave, Terminated"
            )
        )

    # -----------------------------
    # Joining Date
    # -----------------------------

    if employee_data.joining_date is not None:
        if employee_data.joining_date > date.today():
            raise HTTPException(
                status_code=400,
                detail="Joining date cannot be in the future"
            )

    # -----------------------------
    # Skills
    # -----------------------------

    if employee_data.skills is not None:
        employee_data.skills = employee_data.skills.strip()

        if len(employee_data.skills) > 2000:
            raise HTTPException(
                status_code=400,
                detail="Skills cannot exceed 2000 characters"
            )

    # -----------------------------
    # Profile Metadata
    # -----------------------------

    if employee_data.profile_metadata is not None:
        if not isinstance(employee_data.profile_metadata, dict):
            raise HTTPException(
                status_code=400,
                detail="Profile metadata must be a JSON object"
            )

    # -----------------------------
    # Department validation
    # -----------------------------

    if employee_data.department_id is not None:

        department = (
            db.query(Department)
            .filter(
                Department.id == employee_data.department_id
            )
            .first()
        )

        if not department:
            raise HTTPException(
                status_code=404,
                detail="Department not found"
            )

    # -----------------------------
    # Manager validation
    # -----------------------------

    if employee_data.manager_id is not None:

        if (
            employee_id is not None
            and employee_data.manager_id == employee_id
        ):
            raise HTTPException(
                status_code=400,
                detail="An employee cannot be their own manager"
            )

        manager = (
            db.query(Employee)
            .filter(
                Employee.id == employee_data.manager_id
            )
            .first()
        )

        if not manager:
            raise HTTPException(
                status_code=404,
                detail="Manager employee not found"
            )


# ============================================================
# RESPONSE FORMAT
# ============================================================

def employee_response(employee: Employee):
    return {
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
        "age": employee.age,
        "salary": employee.salary,

        "status": employee.status,
        "joining_date": (
            employee.joining_date.isoformat()
            if employee.joining_date
            else None
        ),
        "skills": employee.skills,
        "profile_metadata": employee.profile_metadata,

        "department_id": employee.department_id,

        "manager_id": employee.manager_id,

        "manager_name": (
            employee.manager.name
            if employee.manager
            else None
        ),

        "department": (
            {
                "id": employee.department.id,
                "name": employee.department.name,
                "description": employee.department.description
            }
            if employee.department
            else None
        )
    }


# ============================================================
# GET EMPLOYEES
# ADVANCED SEARCH / FILTER / SORT / PAGINATION
# ============================================================

@router.get("/")
def get_employees(
    search: str | None = Query(
        default=None,
        description="Search employee name, email or skills"
    ),

    department_id: int | None = Query(
        default=None
    ),

    manager_id: int | None = Query(
        default=None
    ),

    status: str | None = Query(
        default=None
    ),

    joining_date_from: date | None = Query(
        default=None
    ),

    joining_date_to: date | None = Query(
        default=None
    ),

    skills: str | None = Query(
        default=None
    ),

    sort_by: Literal[
        "id",
        "name",
        "email",
        "age",
        "salary",
        "status",
        "joining_date"
    ] = Query(
        default="id"
    ),

    sort_order: Literal[
        "asc",
        "desc"
    ] = Query(
        default="asc"
    ),

    page: int = Query(
        default=1,
        ge=1
    ),

    limit: int = Query(
        default=50,
        ge=1,
        le=100
    ),

    db: Session = Depends(get_db),

    current_user=Depends(require_admin_or_hr)
):

    # ========================================================
    # BASE QUERY
    # ========================================================

    query = (
        db.query(Employee)
        .options(
            joinedload(Employee.department),
            joinedload(Employee.manager)
        )
    )

    # ========================================================
    # SEARCH
    # ========================================================

    if search:

        search_value = search.strip()

        if search_value:

            search_pattern = f"%{search_value}%"

            query = query.filter(
                (
                    Employee.name.ilike(search_pattern)
                    |
                    Employee.email.ilike(search_pattern)
                    |
                    Employee.skills.ilike(search_pattern)
                )
            )

    # ========================================================
    # DEPARTMENT FILTER
    # ========================================================

    if department_id is not None:

        query = query.filter(
            Employee.department_id == department_id
        )

    # ========================================================
    # MANAGER FILTER
    # ========================================================

    if manager_id is not None:

        query = query.filter(
            Employee.manager_id == manager_id
        )

    # ========================================================
    # STATUS FILTER
    # ========================================================

    if status:

        if status not in VALID_STATUSES:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid status. Allowed values: "
                    "Active, Inactive, On Leave, Terminated"
                )
            )

        query = query.filter(
            Employee.status == status
        )

    # ========================================================
    # JOINING DATE FILTER
    # ========================================================

    if joining_date_from is not None:

        query = query.filter(
            Employee.joining_date >= joining_date_from
        )

    if joining_date_to is not None:

        query = query.filter(
            Employee.joining_date <= joining_date_to
        )

    if (
        joining_date_from is not None
        and joining_date_to is not None
        and joining_date_from > joining_date_to
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "joining_date_from cannot be later "
                "than joining_date_to"
            )
        )

    # ========================================================
    # SKILLS FILTER
    # ========================================================

    if skills:

        skills_value = skills.strip()

        if skills_value:

            query = query.filter(
                Employee.skills.ilike(
                    f"%{skills_value}%"
                )
            )

    # ========================================================
    # SORTING
    # ========================================================

    sort_column = getattr(
        Employee,
        sort_by
    )

    if sort_order == "desc":

        query = query.order_by(
            sort_column.desc()
        )

    else:

        query = query.order_by(
            sort_column.asc()
        )

    # ========================================================
    # PAGINATION
    # ========================================================

    offset = (page - 1) * limit

    employees = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    # ========================================================
    # RESPONSE
    # ========================================================

    return [
        employee_response(employee)
        for employee in employees
    ]


# ============================================================
# CREATE EMPLOYEE
# ============================================================

@router.post("/")
def create_employee(
    employee: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    # Validate fields and relationships

    validate_employee_data(
        employee,
        db
    )

    # Check duplicate email

    existing_employee = (
        db.query(Employee)
        .filter(
            Employee.email == employee.email
        )
        .first()
    )

    if existing_employee:

        raise HTTPException(
            status_code=409,
            detail="Employee email already exists"
        )

    # Create employee

    new_employee = Employee(
        name=employee.name.strip(),
        email=employee.email,
        age=employee.age,
        salary=employee.salary,

        status=employee.status,
        joining_date=employee.joining_date,
        skills=employee.skills,
        profile_metadata=employee.profile_metadata,

        department_id=employee.department_id,
        manager_id=employee.manager_id
    )

    db.add(new_employee)

    try:

        db.flush()

        create_audit_log(
            db=db,
            current_user=current_user,
            action="CREATE",
            entity_id=new_employee.id,
            details=(
                f"Employee '{new_employee.name}' "
                f"was created"
            )
        )

        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Employee could not be created because of a database constraint"
        )

    db.refresh(new_employee)

    return {
        "message": "Employee created successfully",
        "employee": employee_response(new_employee)
    }


# ============================================================
# GET SINGLE EMPLOYEE
# ============================================================

@router.get("/{employee_id}")
def get_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    employee = (
        db.query(Employee)
        .options(
            joinedload(Employee.department),
            joinedload(Employee.manager)
        )
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    return employee_response(employee)


# ============================================================
# UPDATE EMPLOYEE
# ============================================================

@router.put("/{employee_id}")
def update_employee(
    employee_id: int,
    employee_data: EmployeeCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Validate all fields and relationships

    validate_employee_data(
        employee_data,
        db,
        employee_id=employee_id
    )

    # Check duplicate email

    existing_email = (
        db.query(Employee)
        .filter(
            Employee.email == employee_data.email,
            Employee.id != employee_id
        )
        .first()
    )

    if existing_email:

        raise HTTPException(
            status_code=409,
            detail=(
                "Another employee already uses this email"
            )
        )

    # Update basic fields

    employee.name = employee_data.name.strip()
    employee.email = employee_data.email
    employee.age = employee_data.age
    employee.salary = employee_data.salary

    # Update Level 5.1 fields

    employee.status = employee_data.status
    employee.joining_date = employee_data.joining_date
    employee.skills = employee_data.skills
    employee.profile_metadata = employee_data.profile_metadata

    # Update relationships

    employee.department_id = employee_data.department_id
    employee.manager_id = employee_data.manager_id

    create_audit_log(
        db=db,
        current_user=current_user,
        action="UPDATE",
        entity_id=employee.id,
        details=(
            f"Employee '{employee.name}' "
            f"was updated"
        )
    )

    try:

        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Employee could not be updated because of a database constraint"
        )

    db.refresh(employee)

    return {
        "message": "Employee updated successfully",
        "employee": employee_response(employee)
    }


# ============================================================
# DELETE EMPLOYEE
# ADMIN ONLY
# ============================================================

@router.delete("/{employee_id}")
def delete_employee(
    employee_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == employee_id
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=404,
            detail="Employee not found"
        )

    # Prevent deleting a manager who still
    # has subordinate employees.

    has_subordinates = (
        db.query(Employee)
        .filter(
            Employee.manager_id == employee_id
        )
        .first()
    )

    if has_subordinates:

        raise HTTPException(
            status_code=400,
            detail=(
                "Cannot delete this employee because "
                "they are assigned as a manager. "
                "Reassign their employees first."
            )
        )

    employee_name = employee.name

    create_audit_log(
        db=db,
        current_user=current_user,
        action="DELETE",
        entity_id=employee.id,
        details=(
            f"Employee '{employee_name}' "
            f"was deleted"
        )
    )

    db.delete(employee)

    try:

        db.commit()

    except IntegrityError:

        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Employee could not be deleted because "
                "the employee is referenced by another record"
            )
        )

    return {
        "message": "Employee deleted successfully",
        "employee_id": employee_id
    }