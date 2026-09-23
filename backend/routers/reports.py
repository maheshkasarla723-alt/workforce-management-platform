from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Employee
from backend.department_models import Department
from backend.attendance_models import Attendance
from backend.task_models import Task

from backend.services.permissions import require_admin_or_hr


# ==================================================
# ROUTER
# ==================================================

router = APIRouter(
    prefix="/api/reports",
    tags=["Reports"]
)


# ==================================================
# WORKFORCE SUMMARY REPORT
# ADMIN + HR MANAGER ONLY
# ==================================================

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr)
):

    # --------------------------------------------------
    # EMPLOYEE COUNT
    # --------------------------------------------------

    total_employees = (
        db.query(Employee).count()
    )


    # --------------------------------------------------
    # DEPARTMENT COUNT
    # --------------------------------------------------

    total_departments = (
        db.query(Department).count()
    )


    # --------------------------------------------------
    # TODAY'S DATE
    # --------------------------------------------------

    today = date.today()


    # --------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------

    today_attendance = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today
        )
        .count()
    )


    present_today = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today,
            Attendance.status == "Present"
        )
        .count()
    )


    absent_today = (
        db.query(Attendance)
        .filter(
            Attendance.attendance_date == today,
            Attendance.status == "Absent"
        )
        .count()
    )


    # --------------------------------------------------
    # TASKS
    # --------------------------------------------------

    total_tasks = (
        db.query(Task).count()
    )


    pending_tasks = (
        db.query(Task)
        .filter(
            Task.status == "Pending"
        )
        .count()
    )


    completed_tasks = (
        db.query(Task)
        .filter(
            Task.status == "Completed"
        )
        .count()
    )


    in_progress_tasks = (
        db.query(Task)
        .filter(
            Task.status == "In Progress"
        )
        .count()
    )


    # --------------------------------------------------
    # RESPONSE
    # --------------------------------------------------

    return {

        "employees": {
            "total": total_employees
        },

        "departments": {
            "total": total_departments
        },

        "attendance": {

            "today": today_attendance,

            "present": present_today,

            "absent": absent_today
        },

        "tasks": {

            "total": total_tasks,

            "pending": pending_tasks,

            "completed": completed_tasks,

            "in_progress": in_progress_tasks
        }
    }