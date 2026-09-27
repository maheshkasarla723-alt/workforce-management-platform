from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import IntegrityError
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
    tags=["Departments"],
)


# ==================================================
# REQUEST MODEL
# ==================================================

class DepartmentCreate(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        description="Department name",
    )

    description: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError(
                "Department name cannot be empty"
            )

        return value

    @field_validator("description")
    @classmethod
    def validate_description(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None

        value = value.strip()

        return value if value else None


# ==================================================
# GET ALL DEPARTMENTS
# ADMIN + HR MANAGER
# ==================================================

@router.get("/")
def get_departments(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    departments = (
        db.query(Department)
        .order_by(
            Department.name.asc(),
            Department.id.asc(),
        )
        .all()
    )

    return [
        {
            "id": department.id,
            "name": department.name,
            "description": department.description,
        }
        for department in departments
    ]


# ==================================================
# CREATE DEPARTMENT
# ADMIN + HR MANAGER
# ==================================================

@router.post("/")
def create_department(
    department: DepartmentCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    # ------------------------------------------------
    # Prevent duplicate department names
    # ------------------------------------------------

    existing_department = (
        db.query(Department)
        .filter(
            Department.name == department.name,
        )
        .first()
    )

    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Department already exists",
        )

    # ------------------------------------------------
    # Create department
    # ------------------------------------------------

    new_department = Department(
        name=department.name,
        description=department.description,
    )

    db.add(new_department)

    # ------------------------------------------------
    # Transaction-safe commit
    # ------------------------------------------------

    try:
        db.commit()
        db.refresh(new_department)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Department could not be created because "
                "the department name already exists"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department could not be created",
        )

    return {
        "message": "Department created successfully",
        "department": {
            "id": new_department.id,
            "name": new_department.name,
            "description": new_department.description,
        },
    }


# ==================================================
# GET SINGLE DEPARTMENT
# ADMIN + HR MANAGER
# ==================================================

@router.get("/{department_id}")
def get_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    return {
        "id": department.id,
        "name": department.name,
        "description": department.description,
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
    current_user=Depends(require_admin_or_hr),
):
    # ------------------------------------------------
    # Find department
    # ------------------------------------------------

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    # ------------------------------------------------
    # Prevent duplicate names
    # ------------------------------------------------

    existing_department = (
        db.query(Department)
        .filter(
            Department.name == department_data.name,
            Department.id != department_id,
        )
        .first()
    )

    if existing_department:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Another department already uses this name"
            ),
        )

    # ------------------------------------------------
    # Apply changes
    # ------------------------------------------------

    department.name = department_data.name
    department.description = department_data.description

    # ------------------------------------------------
    # Transaction-safe commit
    # ------------------------------------------------

    try:
        db.commit()
        db.refresh(department)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Department could not be updated because "
                "the department name already exists"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department could not be updated",
        )

    return {
        "message": "Department updated successfully",
        "department": {
            "id": department.id,
            "name": department.name,
            "description": department.description,
        },
    }


# ==================================================
# DELETE DEPARTMENT
# ADMIN ONLY
# ==================================================

@router.delete("/{department_id}")
def delete_department(
    department_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    # ------------------------------------------------
    # Find department
    # ------------------------------------------------

    department = (
        db.query(Department)
        .filter(
            Department.id == department_id,
        )
        .first()
    )

    if not department:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Department not found",
        )

    # ------------------------------------------------
    # Delete transaction
    # ------------------------------------------------

    try:
        db.delete(department)
        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Department could not be deleted because "
                "it is referenced by another record"
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Department could not be deleted",
        )

    return {
        "message": "Department deleted successfully",
        "department_id": department_id,
    }