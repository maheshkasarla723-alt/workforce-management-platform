from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.department_models import Department
from backend.services.permissions import (
    require_admin,
    require_admin_or_hr,
)


# ==================================================
# ROUTER
# ==================================================

router = APIRouter(
    prefix="/api/departments",
    tags=["Departments"]
)


# ==================================================
# REQUEST MODEL
# ==================================================

class DepartmentCreate(BaseModel):
    name: str
    description: str | None = None


# ==================================================
# GET ALL DEPARTMENTS
# ADMIN + HR MANAGER
# ==================================================

@router.get("/")
def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    departments = db.query(Department).all()

    result = []

    for department in departments:

        result.append({
            "id": department.id,
            "name": department.name,
            "description": department.description
        })

    return result


# ==================================================
# CREATE DEPARTMENT
# ADMIN + HR MANAGER
# ==================================================

@router.post("/")
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    existing_department = (
        db.query(Department)
        .filter(
            Department.name == department.name
        )
        .first()
    )

    if existing_department:

        raise HTTPException(
            status_code=409,
            detail="Department already exists"
        )

    new_department = Department(
        name=department.name,
        description=department.description
    )

    db.add(new_department)
    db.commit()
    db.refresh(new_department)

    return {
        "message": "Department created successfully",
        "department": {
            "id": new_department.id,
            "name": new_department.name,
            "description": new_department.description
        }
    }


# ==================================================
# GET SINGLE DEPARTMENT
# ADMIN + HR MANAGER
# ==================================================

@router.get("/{department_id}")
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    return {
        "id": department.id,
        "name": department.name,
        "description": department.description
    }


# ==================================================
# UPDATE DEPARTMENT
# ADMIN + HR MANAGER
# ==================================================

@router.put("/{department_id}")
def update_department(
    department_id: int,
    department_data: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    existing_department = (
        db.query(Department)
        .filter(
            Department.name == department_data.name,
            Department.id != department_id
        )
        .first()
    )

    if existing_department:

        raise HTTPException(
            status_code=409,
            detail="Another department already uses this name"
        )

    department.name = department_data.name
    department.description = department_data.description

    db.commit()
    db.refresh(department)

    return {
        "message": "Department updated successfully",
        "department": {
            "id": department.id,
            "name": department.name,
            "description": department.description
        }
    }


# ==================================================
# DELETE DEPARTMENT
# ADMIN ONLY
# ==================================================

@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin)
):

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id
        )
        .first()
    )

    if not department:

        raise HTTPException(
            status_code=404,
            detail="Department not found"
        )

    db.delete(department)
    db.commit()

    return {
        "message": "Department deleted successfully",
        "department_id": department_id
    }