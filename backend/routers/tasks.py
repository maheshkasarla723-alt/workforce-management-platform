from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.task_models import Task
from backend.models import Employee
from backend.user_models import User
from backend.notification_models import Notification
from backend.audit_models import AuditLog

from backend.services.permissions import (
    require_admin,
    require_admin_or_hr,
)

from backend.routers.auth import get_current_user


# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/api/tasks",
    tags=["Tasks"],
)


# ============================================================
# REQUEST MODELS
# ============================================================

class TaskCreate(BaseModel):
    employee_id: int
    title: str
    description: str | None = None
    priority: str = "Medium"
    status: str = "Pending"
    due_date: date | None = None


class TaskStatusUpdate(BaseModel):
    status: str


# ============================================================
# VALID VALUES
# ============================================================

VALID_PRIORITIES = {
    "Low",
    "Medium",
    "High",
}

VALID_STATUSES = {
    "Pending",
    "In Progress",
    "Completed",
}


# ============================================================
# COMMON RESPONSE HELPERS
# ============================================================

def serialize_employee(employee: Employee | None):
    if not employee:
        return None

    return {
        "id": employee.id,
        "name": employee.name,
        "email": employee.email,
    }


def serialize_task(
    task: Task,
    employee: Employee | None = None,
):
    return {
        "id": task.id,
        "employee_id": task.employee_id,
        "employee": serialize_employee(employee),
        "title": task.title,
        "description": task.description,
        "priority": task.priority,
        "status": task.status,
        "due_date": task.due_date,
    }


# ============================================================
# AUDIT LOG HELPER
# ============================================================

def create_audit_log(
    db: Session,
    current_user,
    action: str,
    entity_id: int,
    details: str,
):
    audit_log = AuditLog(
        user_id=current_user.id,
        username=current_user.username,
        action=action,
        entity="Task",
        entity_id=entity_id,
        details=details,
    )

    db.add(audit_log)


# ============================================================
# NOTIFICATION HELPER
# ============================================================

def create_task_notification(
    db: Session,
    employee: Employee,
    task: Task,
):
    user = (
        db.query(User)
        .filter(
            User.email == employee.email
        )
        .first()
    )

    if not user:
        return None

    notification = Notification(
        user_id=user.id,
        title="New Task Assigned",
        message=(
            f"You have been assigned the task "
            f"'{task.title}'. "
            f"Priority: {task.priority}. "
            f"Due date: "
            f"{task.due_date if task.due_date else 'Not specified'}."
        ),
        type="Task",
        is_read=False,
    )

    db.add(notification)

    return notification


# ============================================================
# TASK VALIDATION
# ============================================================

def validate_task_data(
    task_data: TaskCreate,
):
    if not task_data.title or not task_data.title.strip():
        raise HTTPException(
            status_code=400,
            detail="Task title cannot be empty.",
        )

    if task_data.priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid priority. "
                "Use Low, Medium, or High."
            ),
        )

    if task_data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use Pending, In Progress, or Completed."
            ),
        )

    if (
        task_data.due_date
        and task_data.due_date < date.today()
    ):
        raise HTTPException(
            status_code=400,
            detail="Due date cannot be in the past.",
        )


# ============================================================
# ADMIN / HR — GET ALL TASKS
# ============================================================

@router.get("/")
def get_tasks(
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    rows = (
        db.query(Task, Employee)
        .outerjoin(
            Employee,
            Task.employee_id == Employee.id,
        )
        .order_by(Task.id.asc())
        .all()
    )

    return [
        serialize_task(task, employee)
        for task, employee in rows
    ]


# ============================================================
# ADMIN / HR — CREATE TASK
# ============================================================

@router.post("/")
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    validate_task_data(task_data)

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == task_data.employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    new_task = Task(
        employee_id=task_data.employee_id,
        title=task_data.title.strip(),
        description=task_data.description,
        priority=task_data.priority,
        status=task_data.status,
        due_date=task_data.due_date,
    )

    try:
        db.add(new_task)

        # Get generated task ID before creating
        # audit/notification records.
        db.flush()

        create_audit_log(
            db,
            current_user,
            "CREATE",
            new_task.id,
            (
                f"Task '{new_task.title}' "
                f"was created for employee "
                f"'{employee.name}'"
            ),
        )

        create_task_notification(
            db,
            employee,
            new_task,
        )

        db.commit()
        db.refresh(new_task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Task could not be created because of a data conflict.",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Task could not be created.",
        )

    return {
        "message": "Task created successfully",
        "task": serialize_task(
            new_task,
            employee,
        ),
    }


# ============================================================
# EMPLOYEE — GET MY TASKS
#
# IMPORTANT:
# This route MUST appear before /{task_id}
# ============================================================

@router.get("/my")
def get_my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail=(
                "Employee profile not found "
                "for this user account."
            ),
        )

    tasks = (
        db.query(Task)
        .filter(
            Task.employee_id == employee.id
        )
        .order_by(Task.id.desc())
        .all()
    )

    return [
        serialize_task(task, employee)
        for task in tasks
    ]


# ============================================================
# EMPLOYEE — GET ONE OF MY TASKS
#
# IMPORTANT:
# This route MUST appear before /{task_id}
# ============================================================

@router.get("/my/{task_id}")
def get_my_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail=(
                "Employee profile not found "
                "for this user account."
            ),
        )

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.employee_id == employee.id,
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    return serialize_task(
        task,
        employee,
    )


# ============================================================
# EMPLOYEE — UPDATE MY TASK STATUS
# ============================================================

@router.put("/{task_id}/status")
def update_my_task_status(
    task_id: int,
    status_data: TaskStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if status_data.status not in VALID_STATUSES:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                "Use Pending, In Progress, "
                "or Completed."
            ),
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.email == current_user.email
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail=(
                "Employee profile not found "
                "for this user account."
            ),
        )

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id,
            Task.employee_id == employee.id,
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    previous_status = task.status
    task.status = status_data.status

    try:
        create_audit_log(
            db,
            current_user,
            "UPDATE_STATUS",
            task.id,
            (
                f"Employee changed task "
                f"'{task.title}' status from "
                f"'{previous_status}' to "
                f"'{task.status}'"
            ),
        )

        db.commit()
        db.refresh(task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Task status could not be updated because of a data conflict.",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Task status could not be updated.",
        )

    return {
        "message": "Task status updated successfully",
        "task": serialize_task(
            task,
            employee,
        ),
    }


# ============================================================
# ADMIN / HR — GET ONE TASK
#
# IMPORTANT:
# This generic route comes AFTER /my routes.
# ============================================================

@router.get("/{task_id}")
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    row = (
        db.query(Task, Employee)
        .outerjoin(
            Employee,
            Task.employee_id == Employee.id,
        )
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task, employee = row

    return serialize_task(
        task,
        employee,
    )


# ============================================================
# ADMIN / HR — UPDATE TASK
# ============================================================

@router.put("/{task_id}")
def update_task(
    task_id: int,
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin_or_hr),
):
    validate_task_data(task_data)

    task = (
        db.query(Task)
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if not task:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    employee = (
        db.query(Employee)
        .filter(
            Employee.id == task_data.employee_id
        )
        .first()
    )

    if not employee:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    previous_employee_id = task.employee_id
    previous_title = task.title
    previous_status = task.status

    task.employee_id = task_data.employee_id
    task.title = task_data.title.strip()
    task.description = task_data.description
    task.priority = task_data.priority
    task.status = task_data.status
    task.due_date = task_data.due_date

    try:
        create_audit_log(
            db,
            current_user,
            "UPDATE",
            task.id,
            (
                f"Task '{previous_title}' "
                f"was updated. "
                f"Employee ID changed from "
                f"'{previous_employee_id}' to "
                f"'{task.employee_id}'. "
                f"Status changed from "
                f"'{previous_status}' to "
                f"'{task.status}'."
            ),
        )

        # If the task is reassigned to a different employee,
        # create a notification for the new employee.
        if previous_employee_id != task.employee_id:
            create_task_notification(
                db,
                employee,
                task,
            )

        db.commit()
        db.refresh(task)

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail="Task could not be updated because of a data conflict.",
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Task could not be updated.",
        )

    return {
        "message": "Task updated successfully",
        "task": serialize_task(
            task,
            employee,
        ),
    }


# ============================================================
# ADMIN ONLY — DELETE TASK
# ============================================================

@router.delete("/{task_id}")
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_admin),
):
    row = (
        db.query(Task, Employee)
        .outerjoin(
            Employee,
            Task.employee_id == Employee.id,
        )
        .filter(
            Task.id == task_id
        )
        .first()
    )

    if not row:
        raise HTTPException(
            status_code=404,
            detail="Task not found",
        )

    task, employee = row

    task_title = task.title

    employee_name = (
        employee.name
        if employee
        else "Unknown employee"
    )

    try:
        create_audit_log(
            db,
            current_user,
            "DELETE",
            task.id,
            (
                f"Task '{task_title}' "
                f"was deleted from employee "
                f"'{employee_name}'"
            ),
        )

        db.delete(task)

        db.commit()

    except IntegrityError:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=(
                "Task could not be deleted because "
                "it is referenced by another record."
            ),
        )

    except Exception:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Task could not be deleted.",
        )

    return {
        "message": "Task deleted successfully",
        "task_id": task_id,
    }