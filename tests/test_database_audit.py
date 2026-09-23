import uuid
from datetime import date, timedelta

from fastapi.testclient import TestClient

from backend.audit_models import AuditLog
from backend.department_models import Department
from backend.models import Employee
from backend.attendance_models import Attendance
from backend.task_models import Task


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def create_admin_headers(client, db_session):
    from passlib.context import CryptContext
    from backend.user_models import User

    unique_id = uuid.uuid4().hex[:8]

    username = f"audit_admin_{unique_id}"
    email = f"audit_admin_{unique_id}@example.com"
    password = "Test@12345"

    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        deprecated="auto"
    )

    user = User(
        username=username,
        email=email,
        hashed_password=pwd_context.hash(password),
        role="Admin"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}"
    }


def create_employee(db_session):
    unique_id = uuid.uuid4().hex[:8]

    employee = Employee(
        name=f"Database Test Employee {unique_id}",
        email=f"database_employee_{unique_id}@example.com",
        age=30,
        salary=40000
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


# ============================================================
# EMPLOYEE DATABASE CONSTRAINT
# ============================================================

def test_duplicate_employee_email_is_rejected(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    unique_id = uuid.uuid4().hex[:8]

    email = f"duplicate_employee_{unique_id}@example.com"

    first_response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "First Employee",
            "email": email,
            "age": 30,
            "salary": 40000
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "Second Employee",
            "email": email,
            "age": 31,
            "salary": 45000
        }
    )

    assert second_response.status_code == 409


# ============================================================
# DEPARTMENT UNIQUE CONSTRAINT
# ============================================================

def test_duplicate_department_name_is_rejected(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    unique_id = uuid.uuid4().hex[:8]

    department_name = f"Unique Department {unique_id}"

    first_response = client.post(
        "/api/departments/",
        headers=headers,
        json={
            "name": department_name,
            "description": "First department"
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/departments/",
        headers=headers,
        json={
            "name": department_name,
            "description": "Duplicate department"
        }
    )

    assert second_response.status_code == 409


# ============================================================
# EMPLOYEE AUDIT TRAIL
# ============================================================

def test_employee_crud_creates_audit_logs(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    unique_id = uuid.uuid4().hex[:8]

    email = f"audit_employee_{unique_id}@example.com"

    create_response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "Audit Employee",
            "email": email,
            "age": 28,
            "salary": 35000
        }
    )

    assert create_response.status_code == 200

    employee_id = (
        create_response
        .json()["employee"]["id"]
    )

    create_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Employee",
            AuditLog.entity_id == employee_id,
            AuditLog.action == "CREATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert create_log is not None
    assert create_log.entity == "Employee"
    assert create_log.entity_id == employee_id
    assert create_log.action == "CREATE"

    update_response = client.put(
        f"/api/employees/{employee_id}",
        headers=headers,
        json={
            "name": "Updated Audit Employee",
            "email": email,
            "age": 29,
            "salary": 40000
        }
    )

    assert update_response.status_code == 200

    update_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Employee",
            AuditLog.entity_id == employee_id,
            AuditLog.action == "UPDATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert update_log is not None
    assert update_log.entity == "Employee"
    assert update_log.entity_id == employee_id
    assert update_log.action == "UPDATE"

    delete_response = client.delete(
        f"/api/employees/{employee_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    delete_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Employee",
            AuditLog.entity_id == employee_id,
            AuditLog.action == "DELETE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert delete_log is not None
    assert delete_log.entity == "Employee"
    assert delete_log.entity_id == employee_id
    assert delete_log.action == "DELETE"


# ============================================================
# ATTENDANCE AUDIT TRAIL
# ============================================================

def test_attendance_crud_creates_audit_logs(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    employee = create_employee(db_session)

    attendance_date = (
        date.today() + timedelta(days=30)
    )

    create_response = client.post(
        "/api/attendance/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "attendance_date": str(attendance_date),
            "status": "Present",
            "check_in": "09:00:00",
            "check_out": "18:00:00"
        }
    )

    assert create_response.status_code == 200

    attendance_id = (
        create_response
        .json()["attendance"]["id"]
    )

    create_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Attendance",
            AuditLog.entity_id == attendance_id,
            AuditLog.action == "CREATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert create_log is not None
    assert create_log.entity == "Attendance"
    assert create_log.entity_id == attendance_id
    assert create_log.action == "CREATE"

    update_response = client.put(
        f"/api/attendance/{attendance_id}",
        headers=headers,
        json={
            "employee_id": employee.id,
            "attendance_date": str(attendance_date),
            "status": "Half Day",
            "check_in": "09:00:00",
            "check_out": "13:00:00"
        }
    )

    assert update_response.status_code == 200

    update_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Attendance",
            AuditLog.entity_id == attendance_id,
            AuditLog.action == "UPDATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert update_log is not None
    assert update_log.entity == "Attendance"
    assert update_log.entity_id == attendance_id
    assert update_log.action == "UPDATE"

    delete_response = client.delete(
        f"/api/attendance/{attendance_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    delete_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Attendance",
            AuditLog.entity_id == attendance_id,
            AuditLog.action == "DELETE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert delete_log is not None
    assert delete_log.entity == "Attendance"
    assert delete_log.entity_id == attendance_id
    assert delete_log.action == "DELETE"


# ============================================================
# TASK AUDIT TRAIL
# ============================================================

def test_task_crud_creates_audit_logs(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    employee = create_employee(db_session)

    unique_id = uuid.uuid4().hex[:8]

    task_title = f"Audit Task {unique_id}"

    due_date = (
        date.today() + timedelta(days=30)
    )

    create_response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": task_title,
            "description": "Audit task test",
            "priority": "High",
            "status": "Pending",
            "due_date": str(due_date)
        }
    )

    assert create_response.status_code == 200

    task_id = (
        create_response
        .json()["task"]["id"]
    )

    create_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Task",
            AuditLog.entity_id == task_id,
            AuditLog.action == "CREATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert create_log is not None
    assert create_log.entity == "Task"
    assert create_log.entity_id == task_id
    assert create_log.action == "CREATE"

    update_response = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": f"Updated Audit Task {unique_id}",
            "description": "Updated audit task",
            "priority": "Medium",
            "status": "In Progress",
            "due_date": str(due_date)
        }
    )

    assert update_response.status_code == 200

    update_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Task",
            AuditLog.entity_id == task_id,
            AuditLog.action == "UPDATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert update_log is not None
    assert update_log.entity == "Task"
    assert update_log.entity_id == task_id
    assert update_log.action == "UPDATE"

    delete_response = client.delete(
        f"/api/tasks/{task_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    delete_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Task",
            AuditLog.entity_id == task_id,
            AuditLog.action == "DELETE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert delete_log is not None
    assert delete_log.entity == "Task"
    assert delete_log.entity_id == task_id
    assert delete_log.action == "DELETE"


# ============================================================
# AUDIT LOG CONTENT
# ============================================================

def test_audit_log_contains_user_information(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    employee = create_employee(db_session)

    response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "Audit User Test Employee",
            "email": (
                f"audit_user_{uuid.uuid4().hex[:8]}"
                "@example.com"
            ),
            "age": 30,
            "salary": 40000
        }
    )

    assert response.status_code == 200

    employee_id = (
        response.json()["employee"]["id"]
    )

    audit_log = (
        db_session.query(AuditLog)
        .filter(
            AuditLog.entity == "Employee",
            AuditLog.entity_id == employee_id,
            AuditLog.action == "CREATE"
        )
        .order_by(AuditLog.id.desc())
        .first()
    )

    assert audit_log is not None
    assert audit_log.user_id is not None
    assert audit_log.username is not None
    assert audit_log.details is not None
    assert audit_log.created_at is not None


# ============================================================
# AUDIT LOG ADMIN ACCESS
# ============================================================

def test_admin_can_read_audit_logs(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    response = client.get(
        "/api/audit-logs/",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================
# AUDIT LOG DATA ORDER
# ============================================================

def test_audit_logs_are_returned_newest_first(
    client,
    db_session
):
    headers = create_admin_headers(
        client,
        db_session
    )

    employee = create_employee(db_session)

    response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "Audit Order Employee",
            "email": (
                f"audit_order_{uuid.uuid4().hex[:8]}"
                "@example.com"
            ),
            "age": 30,
            "salary": 40000
        }
    )

    assert response.status_code == 200

    audit_response = client.get(
        "/api/audit-logs/",
        headers=headers
    )

    assert audit_response.status_code == 200

    logs = audit_response.json()

    assert isinstance(logs, list)

    if len(logs) > 1:
        ids = [log["id"] for log in logs]

        assert ids == sorted(
            ids,
            reverse=True
        )