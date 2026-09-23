from datetime import date, time

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.attendance_models import Attendance
from backend.models import Employee
from backend.user_models import User
from backend.audit_models import AuditLog

from backend.services.permissions import (
    require_admin,
    require_admin_or_hr,
)

from backend.routers.auth import get_current_user


# ==================================================
# ROUTER
# ==================================================

router = APIRouter(
    prefix="/api/attendance",
    tags=["Attendance"]
)


# ==================================================
# VALID ATTENDANCE STATUSES
# ==================================================

VALID_ATTENDANCE_STATUSES = [
    "Present",
    "Absent",
    "Leave",
    "Half Day",
]


# ==================================================
# REQUEST MODEL
# ==================================================

class AttendanceCreate(BaseModel):

    employee_id: int = Field(
        ...,
        gt=0,
        description="Employee ID must be greater than 0"
    )

    attendance_date: date

    status: str

    check_in: time | None = None

    check_out: time | None = None


# ==================================================
# AUDIT LOG HELPER
# ==================================================

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
        entity="Attendance",
        entity_id=entity_id,
        details=details
    )

    db.add(audit_log)


# ==================================================
# VALIDATE ATTENDANCE DATA
# ==================================================

def validate_attendance_data(
    attendance_data: AttendanceCreate
):

    # ------------------------------------------------
    # Validate status
    # ------------------------------------------------

    if (
        attendance_data.status
        not in VALID_ATTENDANCE_STATUSES
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Invalid attendance status. "
                "Allowed values: "
                + ", ".join(
                    VALID_ATTENDANCE_STATUSES
                )
            )
        )

    # ------------------------------------------------
    # Check-out requires check-in
    # ------------------------------------------------

    if (
        attendance_data.check_out is not None
        and
        attendance_data.check_in is None
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Check-in is required when "
                "check-out is provided"
            )
        )

    # ------------------------------------------------
    # Check-out must be later
    # than check-in
    # ------------------------------------------------

    if (
        attendance_data.check_in is not None
        and
        attendance_data.check_out is not None
        and
        attendance_data.check_out
        <= attendance_data.check_in
    ):

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Check-out time must be later "
                "than check-in time"
            )
        )


# ==================================================
# GET ALL ATTENDANCE
# ADMIN / HR MANAGER
# ==================================================

@router.get("/")
def get_attendance(

    db: Session = Depends(get_db),

    current_user=Depends(
        require_admin_or_hr
    )
):

    # JOIN Attendance + Employee
    # Avoids N+1 employee queries.

    records = (
        db.query(
            Attendance,
            Employee
        )
        .join(
            Employee,
            Employee.id ==
            Attendance.employee_id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc()
        )
        .all()
    )

    result = []

    for record, employee in records:

        result.append({

            "id":
                record.id,

            "employee_id":
                record.employee_id,

            "employee_name":
                employee.name,

            "attendance_date":
                record.attendance_date,

            "status":
                record.status,

            "check_in":
                record.check_in,

            "check_out":
                record.check_out
        })

    return result


# ==================================================
# CREATE ATTENDANCE
# ADMIN / HR MANAGER
# ==================================================

@router.post("/")
def create_attendance(

    attendance: AttendanceCreate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_admin_or_hr
    )
):

    validate_attendance_data(
        attendance
    )

    # ------------------------------------------------
    # Check employee
    # ------------------------------------------------

    employee = (
        db.query(Employee)
        .filter(
            Employee.id ==
            attendance.employee_id
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    # ------------------------------------------------
    # Prevent duplicate attendance
    # ------------------------------------------------

    existing_record = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id ==
            attendance.employee_id,

            Attendance.attendance_date ==
            attendance.attendance_date
        )
        .first()
    )

    if existing_record:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Attendance already exists for "
                "this employee on this date"
            )
        )

    # ------------------------------------------------
    # Create attendance
    # ------------------------------------------------

    new_record = Attendance(

        employee_id=
            attendance.employee_id,

        attendance_date=
            attendance.attendance_date,

        status=
            attendance.status,

        check_in=
            attendance.check_in,

        check_out=
            attendance.check_out
    )

    db.add(new_record)

    # Generate ID before audit log

    db.flush()

    # ------------------------------------------------
    # Audit
    # ------------------------------------------------

    create_audit_log(

        db=db,

        current_user=current_user,

        action="CREATE",

        entity_id=new_record.id,

        details=(
            f"Attendance created for employee "
            f"'{employee.name}' on "
            f"{attendance.attendance_date}"
        )
    )

    db.commit()

    db.refresh(new_record)

    return {

        "message":
            "Attendance created successfully",

        "attendance": {

            "id":
                new_record.id,

            "employee_id":
                new_record.employee_id,

            "employee_name":
                employee.name,

            "attendance_date":
                new_record.attendance_date,

            "status":
                new_record.status,

            "check_in":
                new_record.check_in,

            "check_out":
                new_record.check_out
        }
    }


# ==================================================
# EMPLOYEE HELPER
# ==================================================

def get_employee_for_user(
    db: Session,
    current_user: User
):

    employee = (
        db.query(Employee)
        .filter(
            Employee.email ==
            current_user.email
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                "Employee profile not found "
                "for this user account."
            )
        )

    return employee


# ==================================================
# EMPLOYEE — MY ATTENDANCE
#
# IMPORTANT:
# This route must come BEFORE
# /{attendance_id}
# ==================================================

@router.get("/my")
def get_my_attendance(

    db: Session = Depends(get_db),

    current_user: User =
        Depends(get_current_user)
):

    employee = get_employee_for_user(
        db,
        current_user
    )

    records = (
        db.query(Attendance)
        .filter(
            Attendance.employee_id ==
            employee.id
        )
        .order_by(
            Attendance.attendance_date.desc(),
            Attendance.id.desc()
        )
        .all()
    )

    result = []

    for record in records:

        result.append({

            "id":
                record.id,

            "employee_id":
                record.employee_id,

            "employee_name":
                employee.name,

            "attendance_date":
                record.attendance_date,

            "status":
                record.status,

            "check_in":
                record.check_in,

            "check_out":
                record.check_out
        })

    return result


# ==================================================
# EMPLOYEE — MY ATTENDANCE MONTHLY SUMMARY
# ==================================================

@router.get("/my/summary")
def get_my_attendance_summary(

    year: int = Query(
        ...,
        ge=2000,
        le=2100
    ),

    month: int = Query(
        ...,
        ge=1,
        le=12
    ),

    db: Session = Depends(get_db),

    current_user: User =
        Depends(get_current_user)
):

    employee = get_employee_for_user(
        db,
        current_user
    )

    # ------------------------------------------------
    # Calculate month boundaries
    # ------------------------------------------------

    if month == 12:

        next_month = date(
            year + 1,
            1,
            1
        )

    else:

        next_month = date(
            year,
            month + 1,
            1
        )

    current_month = date(
        year,
        month,
        1
    )

    # ------------------------------------------------
    # Get monthly records
    # ------------------------------------------------

    records = (
        db.query(Attendance)
        .filter(

            Attendance.employee_id ==
            employee.id,

            Attendance.attendance_date >=
            current_month,

            Attendance.attendance_date <
            next_month
        )
        .order_by(
            Attendance.attendance_date.asc()
        )
        .all()
    )

    # ------------------------------------------------
    # Calculate summary
    # ------------------------------------------------

    present_count = 0
    absent_count = 0
    leave_count = 0
    half_day_count = 0

    for record in records:

        if record.status == "Present":

            present_count += 1

        elif record.status == "Absent":

            absent_count += 1

        elif record.status == "Leave":

            leave_count += 1

        elif record.status == "Half Day":

            half_day_count += 1

    return {

        "employee_id":
            employee.id,

        "employee_name":
            employee.name,

        "year":
            year,

        "month":
            month,

        "total_records":
            len(records),

        "present":
            present_count,

        "absent":
            absent_count,

        "leave":
            leave_count,

        "half_day":
            half_day_count
    }


# ==================================================
# EMPLOYEE — GET ONE OF MY ATTENDANCE RECORDS
#
# IMPORTANT:
# This route must come BEFORE
# /{attendance_id}
# ==================================================

@router.get("/my/{attendance_id}")
def get_my_one_attendance(

    attendance_id: int,

    db: Session = Depends(get_db),

    current_user: User =
        Depends(get_current_user)
):

    employee = get_employee_for_user(
        db,
        current_user
    )

    record = (
        db.query(Attendance)
        .filter(

            Attendance.id ==
            attendance_id,

            Attendance.employee_id ==
            employee.id
        )
        .first()
    )

    if not record:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    return {

        "id":
            record.id,

        "employee_id":
            record.employee_id,

        "employee_name":
            employee.name,

        "attendance_date":
            record.attendance_date,

        "status":
            record.status,

        "check_in":
            record.check_in,

        "check_out":
            record.check_out
    }


# ==================================================
# ADMIN / HR — GET ONE ATTENDANCE
#
# This comes AFTER /my routes.
# ==================================================

@router.get("/{attendance_id}")
def get_one_attendance(

    attendance_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_admin_or_hr
    )
):

    result = (
        db.query(
            Attendance,
            Employee
        )
        .join(
            Employee,
            Employee.id ==
            Attendance.employee_id
        )
        .filter(
            Attendance.id ==
            attendance_id
        )
        .first()
    )

    if not result:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    record, employee = result

    return {

        "id":
            record.id,

        "employee_id":
            record.employee_id,

        "employee_name":
            employee.name,

        "attendance_date":
            record.attendance_date,

        "status":
            record.status,

        "check_in":
            record.check_in,

        "check_out":
            record.check_out
    }


# ==================================================
# UPDATE ATTENDANCE
# ADMIN / HR MANAGER
# ==================================================

@router.put("/{attendance_id}")
def update_attendance(

    attendance_id: int,

    attendance_data: AttendanceCreate,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_admin_or_hr
    )
):

    validate_attendance_data(
        attendance_data
    )

    record = (
        db.query(Attendance)
        .filter(
            Attendance.id ==
            attendance_id
        )
        .first()
    )

    if not record:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.id ==
            attendance_data.employee_id
        )
        .first()
    )

    if not employee:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found"
        )

    duplicate_record = (
        db.query(Attendance)
        .filter(

            Attendance.employee_id ==
            attendance_data.employee_id,

            Attendance.attendance_date ==
            attendance_data.attendance_date,

            Attendance.id !=
            attendance_id
        )
        .first()
    )

    if duplicate_record:

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                "Another attendance record already "
                "exists for this employee on this date"
            )
        )

    record.employee_id = (
        attendance_data.employee_id
    )

    record.attendance_date = (
        attendance_data.attendance_date
    )

    record.status = (
        attendance_data.status
    )

    record.check_in = (
        attendance_data.check_in
    )

    record.check_out = (
        attendance_data.check_out
    )

    create_audit_log(

        db=db,

        current_user=current_user,

        action="UPDATE",

        entity_id=record.id,

        details=(
            f"Attendance for employee "
            f"'{employee.name}' was updated"
        )
    )

    db.commit()

    db.refresh(record)

    return {

        "message":
            "Attendance updated successfully",

        "attendance": {

            "id":
                record.id,

            "employee_id":
                record.employee_id,

            "employee_name":
                employee.name,

            "attendance_date":
                record.attendance_date,

            "status":
                record.status,

            "check_in":
                record.check_in,

            "check_out":
                record.check_out
        }
    }


# ==================================================
# DELETE ATTENDANCE
# ADMIN ONLY
# ==================================================

@router.delete("/{attendance_id}")
def delete_attendance(

    attendance_id: int,

    db: Session = Depends(get_db),

    current_user=Depends(
        require_admin
    )
):

    record = (
        db.query(Attendance)
        .filter(
            Attendance.id ==
            attendance_id
        )
        .first()
    )

    if not record:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance record not found"
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.id ==
            record.employee_id
        )
        .first()
    )

    employee_name = (

        employee.name

        if employee

        else "Unknown Employee"
    )

    create_audit_log(

        db=db,

        current_user=current_user,

        action="DELETE",

        entity_id=record.id,

        details=(
            f"Attendance record for employee "
            f"'{employee_name}' on "
            f"{record.attendance_date} "
            f"was deleted"
        )
    )

    db.delete(record)

    db.commit()

    return {

        "message":
            "Attendance deleted successfully",

        "attendance_id":
            attendance_id
    }