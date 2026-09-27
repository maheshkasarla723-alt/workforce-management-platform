from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, func
from sqlalchemy.exc import SQLAlchemyError
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
    tags=["Reports"],
)


# ==================================================
# WORKFORCE SUMMARY REPORT
# ADMIN + HR MANAGER ONLY
# ==================================================

@router.get("/summary")
def get_summary(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    """
    Return the workforce summary for Admin and HR users.

    Includes:
    - Total employees
    - Total departments
    - Today's attendance
    - Today's present/absent counts
    - Total tasks
    - Pending/completed/in-progress task counts
    """

    today = date.today()

    try:
        # --------------------------------------------------
        # EMPLOYEE COUNT
        # --------------------------------------------------

        total_employees = (
            db.query(func.count(Employee.id))
            .scalar()
            or 0
        )

        # --------------------------------------------------
        # DEPARTMENT COUNT
        # --------------------------------------------------

        total_departments = (
            db.query(func.count(Department.id))
            .scalar()
            or 0
        )

        # --------------------------------------------------
        # TODAY'S ATTENDANCE
        #
        # One database query instead of three separate
        # attendance COUNT queries.
        # --------------------------------------------------

        attendance_summary = (
            db.query(
                func.count(Attendance.id).label("total"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Attendance.status == "Present",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("present"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Attendance.status == "Absent",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("absent"),
            )
            .filter(
                Attendance.attendance_date == today
            )
            .first()
        )

        today_attendance = int(
            attendance_summary.total or 0
        )

        present_today = int(
            attendance_summary.present or 0
        )

        absent_today = int(
            attendance_summary.absent or 0
        )

        # --------------------------------------------------
        # TASK SUMMARY
        #
        # One database query instead of four separate
        # task COUNT queries.
        # --------------------------------------------------

        task_summary = (
            db.query(
                func.count(Task.id).label("total"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Task.status == "Pending",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("pending"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Task.status == "Completed",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("completed"),
                func.coalesce(
                    func.sum(
                        case(
                            (
                                Task.status == "In Progress",
                                1,
                            ),
                            else_=0,
                        )
                    ),
                    0,
                ).label("in_progress"),
            )
            .first()
        )

        total_tasks = int(
            task_summary.total or 0
        )

        pending_tasks = int(
            task_summary.pending or 0
        )

        completed_tasks = int(
            task_summary.completed or 0
        )

        in_progress_tasks = int(
            task_summary.in_progress or 0
        )

        # --------------------------------------------------
        # RESPONSE
        # --------------------------------------------------

        return {
            "employees": {
                "total": total_employees,
            },
            "departments": {
                "total": total_departments,
            },
            "attendance": {
                "today": today_attendance,
                "present": present_today,
                "absent": absent_today,
            },
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "completed": completed_tasks,
                "in_progress": in_progress_tasks,
            },
        }

    except SQLAlchemyError:
        # --------------------------------------------------
        # DATABASE ERROR
        # --------------------------------------------------

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to generate workforce summary",
        )

    except Exception:
        # --------------------------------------------------
        # UNEXPECTED ERROR
        # --------------------------------------------------

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to generate workforce summary",
        )