import uuid


# ============================================================
# BASIC API TESTS
# ============================================================

def test_health_check(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_root_serves_frontend(client):
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Workforce Management" in response.text


# ============================================================
# AUTHENTICATION / AUTHORIZATION TESTS
# ============================================================

def test_invalid_login(client):
    response = client.post(
        "/api/auth/login",
        json={
            "username": "invalid_test_user",
            "password": "wrong_password"
        }
    )

    assert response.status_code == 401


def test_employee_api_requires_authentication(client):
    response = client.get("/api/employees/")

    assert response.status_code == 401


def test_reports_requires_authentication(client):
    response = client.get("/api/reports/summary")

    assert response.status_code == 401


def test_tasks_requires_authentication(client):
    response = client.get("/api/tasks/")

    assert response.status_code == 401


def test_audit_logs_requires_authentication(client):
    response = client.get("/api/audit-logs/")

    assert response.status_code == 401


def test_notifications_requires_authentication(client):
    response = client.get("/api/notifications/")

    assert response.status_code == 401


# ============================================================
# NOTIFICATION AUTHENTICATED USER TEST
# ============================================================

def test_authenticated_user_can_get_notifications(client):
    unique_id = uuid.uuid4().hex[:8]

    username = f"test_notification_user_{unique_id}"
    email = f"test_notification_{unique_id}@example.com"
    password = "Test@12345"

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "role": "Employee"
        }
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    assert token

    response = client.get(
        "/api/notifications/",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================
# USER REGISTRATION TESTS
# ============================================================

def test_user_registration_success(client):
    unique_id = uuid.uuid4().hex[:8]

    username = f"test_user_{unique_id}"
    email = f"test_user_{unique_id}@example.com"
    password = "Test@12345"

    response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "role": "Employee"
        }
    )

    assert response.status_code == 200


def test_duplicate_email_registration(client):
    unique_id = uuid.uuid4().hex[:8]

    username1 = f"first_user_{unique_id}"
    username2 = f"second_user_{unique_id}"
    email = f"duplicate_{unique_id}@example.com"
    password = "Test@12345"

    first_response = client.post(
        "/api/auth/register",
        json={
            "username": username1,
            "email": email,
            "password": password,
            "role": "Employee"
        }
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/auth/register",
        json={
            "username": username2,
            "email": email,
            "password": password,
            "role": "Employee"
        }
    )

    assert second_response.status_code == 409


def test_employee_role_cannot_create_employee(client):
    unique_id = uuid.uuid4().hex[:8]

    username = f"employee_role_{unique_id}"
    email = f"employee_role_{unique_id}@example.com"
    password = "Test@12345"

    register_response = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": password,
            "role": "Employee"
        }
    )

    assert register_response.status_code == 200

    login_response = client.post(
        "/api/auth/login",
        json={
            "username": username,
            "password": password
        }
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    response = client.post(
        "/api/employees/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "name": "Unauthorized Employee",
            "email": f"unauthorized_{unique_id}@example.com",
            "age": 25,
            "salary": 30000
        }
    )

    assert response.status_code == 403


# ============================================================
# HELPER: CREATE USER
# ============================================================

def create_test_user(
    db_session,
    username_prefix,
    role
):
    from passlib.context import CryptContext
    from backend.user_models import User

    unique_id = uuid.uuid4().hex[:8]

    username = f"{username_prefix}_{unique_id}"
    email = f"{username_prefix}_{unique_id}@example.com"
    password = "Test@12345"

    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        deprecated="auto"
    )

    user = User(
        username=username,
        email=email,
        hashed_password=pwd_context.hash(password),
        role=role
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    return user, password


# ============================================================
# HELPER: LOGIN USER
# ============================================================

def login_test_user(client, user, password):
    response = client.post(
        "/api/auth/login",
        json={
            "username": user.username,
            "password": password
        }
    )

    assert response.status_code == 200

    token = response.json()["access_token"]

    assert token

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# HELPER: CREATE ADMIN
# ============================================================

def create_test_admin(client, db_session):
    user, password = create_test_user(
        db_session,
        "test_admin",
        "Admin"
    )

    return login_test_user(
        client,
        user,
        password
    )["Authorization"].replace("Bearer ", "")


# ============================================================
# HELPER: CREATE HR MANAGER
# ============================================================

def create_test_hr_manager(client, db_session):
    user, password = create_test_user(
        db_session,
        "test_hr_manager",
        "HR Manager"
    )

    return login_test_user(
        client,
        user,
        password
    )


# ============================================================
# HELPER: CREATE EMPLOYEE USER
# ============================================================

def create_test_employee_user(client, db_session):
    user, password = create_test_user(
        db_session,
        "test_employee_user",
        "Employee"
    )

    return login_test_user(
        client,
        user,
        password
    )


# ============================================================
# HELPER: CREATE EMPLOYEE RECORD
# ============================================================

def create_test_employee(db_session):
    from backend.models import Employee

    unique_id = uuid.uuid4().hex[:8]

    employee = Employee(
        name=f"Test Employee {unique_id}",
        email=f"test_employee_{unique_id}@example.com",
        age=30,
        salary=40000
    )

    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)

    return employee


# ============================================================
# EMPLOYEE CRUD TEST
# ============================================================

def test_admin_employee_crud(client, db_session):
    from backend.models import Employee

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    unique_id = uuid.uuid4().hex[:8]

    employee_email = (
        f"crud_employee_{unique_id}@example.com"
    )

    create_response = client.post(
        "/api/employees/",
        headers=headers,
        json={
            "name": "CRUD Test Employee",
            "email": employee_email,
            "age": 28,
            "salary": 35000
        }
    )

    assert create_response.status_code == 200

    created_employee = (
        db_session.query(Employee)
        .filter(Employee.email == employee_email)
        .first()
    )

    assert created_employee is not None

    employee_id = created_employee.id

    assert employee_id is not None

    get_response = client.get(
        f"/api/employees/{employee_id}",
        headers=headers
    )

    assert get_response.status_code == 200

    employee = get_response.json()

    assert employee["name"] == "CRUD Test Employee"
    assert employee["email"] == employee_email

    update_response = client.put(
        f"/api/employees/{employee_id}",
        headers=headers,
        json={
            "name": "Updated CRUD Employee",
            "email": employee_email,
            "age": 29,
            "salary": 40000
        }
    )

    assert update_response.status_code == 200

    db_session.expire_all()

    updated_employee = (
        db_session.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    assert updated_employee is not None
    assert updated_employee.name == "Updated CRUD Employee"
    assert updated_employee.age == 29
    assert updated_employee.salary == 40000

    delete_response = client.delete(
        f"/api/employees/{employee_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    db_session.expire_all()

    deleted_employee = (
        db_session.query(Employee)
        .filter(Employee.id == employee_id)
        .first()
    )

    assert deleted_employee is None

    final_response = client.get(
        f"/api/employees/{employee_id}",
        headers=headers
    )

    assert final_response.status_code == 404


# ============================================================
# DEPARTMENT CRUD TEST
# ============================================================

def test_admin_department_crud(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    unique_id = uuid.uuid4().hex[:8]

    department_name = f"Test Department {unique_id}"

    create_response = client.post(
        "/api/departments/",
        headers=headers,
        json={
            "name": department_name,
            "description": "Department created by automated test"
        }
    )

    assert create_response.status_code == 200

    create_data = create_response.json()

    created_department = create_data["department"]

    department_id = created_department["id"]

    assert department_id is not None
    assert created_department["name"] == department_name

    get_response = client.get(
        f"/api/departments/{department_id}",
        headers=headers
    )

    assert get_response.status_code == 200

    department = get_response.json()

    assert department["id"] == department_id
    assert department["name"] == department_name

    updated_name = f"Updated Department {unique_id}"

    update_response = client.put(
        f"/api/departments/{department_id}",
        headers=headers,
        json={
            "name": updated_name,
            "description": "Updated department description"
        }
    )

    assert update_response.status_code == 200

    update_data = update_response.json()

    updated_department = update_data["department"]

    assert updated_department["id"] == department_id
    assert updated_department["name"] == updated_name

    delete_response = client.delete(
        f"/api/departments/{department_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    delete_data = delete_response.json()

    assert delete_data["department_id"] == department_id

    final_response = client.get(
        f"/api/departments/{department_id}",
        headers=headers
    )

    assert final_response.status_code == 404


# ============================================================
# ATTENDANCE CREATE + GET
# ============================================================

def test_admin_attendance_create_and_get(client, db_session):
    from backend.attendance_models import Attendance

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    attendance_response = client.post(
        "/api/attendance/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "attendance_date": "2026-09-22",
            "status": "Present",
            "check_in": "09:00:00",
            "check_out": "18:00:00"
        }
    )

    assert attendance_response.status_code == 200

    data = attendance_response.json()

    assert data["message"] == (
        "Attendance created successfully"
    )

    attendance = data["attendance"]

    attendance_id = attendance["id"]

    assert attendance_id is not None
    assert attendance["employee_id"] == employee.id
    assert attendance["employee_name"] == employee.name
    assert attendance["status"] == "Present"

    get_response = client.get(
        f"/api/attendance/{attendance_id}",
        headers=headers
    )

    assert get_response.status_code == 200

    get_data = get_response.json()

    assert get_data["id"] == attendance_id
    assert get_data["employee_id"] == employee.id
    assert get_data["status"] == "Present"


# ============================================================
# ATTENDANCE UPDATE + DELETE
# ============================================================

def test_attendance_update_and_delete(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    create_response = client.post(
        "/api/attendance/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "attendance_date": "2026-09-23",
            "status": "Absent"
        }
    )

    assert create_response.status_code == 200

    attendance_id = create_response.json()["attendance"]["id"]

    update_response = client.put(
        f"/api/attendance/{attendance_id}",
        headers=headers,
        json={
            "employee_id": employee.id,
            "attendance_date": "2026-09-23",
            "status": "Present",
            "check_in": "09:15:00",
            "check_out": "18:15:00"
        }
    )

    assert update_response.status_code == 200

    update_data = update_response.json()

    assert update_data["message"] == (
        "Attendance updated successfully"
    )

    updated_attendance = update_data["attendance"]

    assert updated_attendance["id"] == attendance_id
    assert updated_attendance["status"] == "Present"

    delete_response = client.delete(
        f"/api/attendance/{attendance_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    delete_data = delete_response.json()

    assert delete_data["message"] == (
        "Attendance deleted successfully"
    )

    assert delete_data["attendance_id"] == attendance_id

    final_response = client.get(
        f"/api/attendance/{attendance_id}",
        headers=headers
    )

    assert final_response.status_code == 404


# ============================================================
# DUPLICATE ATTENDANCE
# ============================================================

def test_duplicate_attendance_is_rejected(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    attendance_data = {
        "employee_id": employee.id,
        "attendance_date": "2026-09-24",
        "status": "Present",
        "check_in": "09:00:00",
        "check_out": "18:00:00"
    }

    first_response = client.post(
        "/api/attendance/",
        headers=headers,
        json=attendance_data
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/api/attendance/",
        headers=headers,
        json=attendance_data
    )

    assert second_response.status_code == 409


# ============================================================
# TASK CREATE + GET
# ============================================================

def test_admin_task_create_and_get(client, db_session):
    from backend.task_models import Task

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    unique_id = uuid.uuid4().hex[:8]

    task_title = f"Test Task {unique_id}"

    create_response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": task_title,
            "description": "Task created by automated test",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-12-01"
        }
    )

    assert create_response.status_code == 200

    created_task = (
        db_session.query(Task)
        .filter(Task.title == task_title)
        .first()
    )

    assert created_task is not None

    task_id = created_task.id

    assert task_id is not None
    assert created_task.employee_id == employee.id
    assert created_task.priority == "High"
    assert created_task.status == "Pending"

    get_response = client.get(
        f"/api/tasks/{task_id}",
        headers=headers
    )

    assert get_response.status_code == 200

    task_data = get_response.json()

    assert task_data["id"] == task_id
    assert task_data["employee_id"] == employee.id
    assert task_data["title"] == task_title
    assert task_data["priority"] == "High"
    assert task_data["status"] == "Pending"


# ============================================================
# TASK UPDATE
# ============================================================

def test_admin_task_update(client, db_session):
    from backend.task_models import Task

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    unique_id = uuid.uuid4().hex[:8]

    task_title = f"Update Task {unique_id}"

    create_response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": task_title,
            "description": "Original task",
            "priority": "Medium",
            "status": "Pending",
            "due_date": "2026-12-02"
        }
    )

    assert create_response.status_code == 200

    task = (
        db_session.query(Task)
        .filter(Task.title == task_title)
        .first()
    )

    assert task is not None

    task_id = task.id

    update_response = client.put(
        f"/api/tasks/{task_id}",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": f"Updated Task {unique_id}",
            "description": "Updated task description",
            "priority": "High",
            "status": "In Progress",
            "due_date": "2026-12-05"
        }
    )

    assert update_response.status_code == 200

    db_session.expire_all()

    updated_task = (
        db_session.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    assert updated_task is not None
    assert updated_task.title == f"Updated Task {unique_id}"
    assert updated_task.description == "Updated task description"
    assert updated_task.priority == "High"
    assert updated_task.status == "In Progress"


# ============================================================
# TASK DELETE
# ============================================================

def test_admin_task_delete(client, db_session):
    from backend.task_models import Task

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    unique_id = uuid.uuid4().hex[:8]

    task_title = f"Delete Task {unique_id}"

    create_response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": task_title,
            "description": "Task to be deleted",
            "priority": "Low",
            "status": "Pending",
            "due_date": "2026-12-10"
        }
    )

    assert create_response.status_code == 200

    task = (
        db_session.query(Task)
        .filter(Task.title == task_title)
        .first()
    )

    assert task is not None

    task_id = task.id

    delete_response = client.delete(
        f"/api/tasks/{task_id}",
        headers=headers
    )

    assert delete_response.status_code == 200

    db_session.expire_all()

    deleted_task = (
        db_session.query(Task)
        .filter(Task.id == task_id)
        .first()
    )

    assert deleted_task is None

    get_response = client.get(
        f"/api/tasks/{task_id}",
        headers=headers
    )

    assert get_response.status_code == 404


# ============================================================
# TASK INVALID PRIORITY
# ============================================================

def test_invalid_task_priority_is_rejected(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": "Invalid Priority Task",
            "description": "Testing invalid priority",
            "priority": "Critical",
            "status": "Pending",
            "due_date": "2026-12-15"
        }
    )

    assert response.status_code == 400


# ============================================================
# TASK INVALID STATUS
# ============================================================

def test_invalid_task_status_is_rejected(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": "Invalid Status Task",
            "description": "Testing invalid status",
            "priority": "Medium",
            "status": "Cancelled",
            "due_date": "2026-12-16"
        }
    )

    assert response.status_code == 400


# ============================================================
# TASK PAST DUE DATE
# ============================================================

def test_past_due_date_is_rejected(client, db_session):
    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    employee = create_test_employee(db_session)

    response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": "Past Due Task",
            "description": "Testing past due date",
            "priority": "Medium",
            "status": "Pending",
            "due_date": "2020-01-01"
        }
    )

    assert response.status_code == 400


# ============================================================
# TASK AUTOMATIC NOTIFICATION
# ============================================================

def test_task_creation_creates_notification(
    client,
    db_session
):
    from backend.user_models import User
    from backend.task_models import Task
    from backend.notification_models import Notification
    from passlib.context import CryptContext

    unique_id = uuid.uuid4().hex[:8]

    employee_email = (
        f"task_notification_employee_{unique_id}@example.com"
    )

    username = f"task_employee_{unique_id}"

    password = "Employee@12345"

    pwd_context = CryptContext(
        schemes=["pbkdf2_sha256"],
        deprecated="auto"
    )

    employee = create_test_employee(db_session)

    employee.email = employee_email

    employee_user = User(
        username=username,
        email=employee_email,
        hashed_password=pwd_context.hash(password),
        role="Employee"
    )

    db_session.add(employee_user)
    db_session.commit()

    db_session.refresh(employee)
    db_session.refresh(employee_user)

    headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    task_title = f"Notification Task {unique_id}"

    response = client.post(
        "/api/tasks/",
        headers=headers,
        json={
            "employee_id": employee.id,
            "title": task_title,
            "description": "Task notification test",
            "priority": "High",
            "status": "Pending",
            "due_date": "2026-12-20"
        }
    )

    assert response.status_code == 200

    task = (
        db_session.query(Task)
        .filter(Task.title == task_title)
        .first()
    )

    assert task is not None

    notification = (
        db_session.query(Notification)
        .filter(
            Notification.user_id == employee_user.id
        )
        .order_by(Notification.id.desc())
        .first()
    )

    assert notification is not None
    assert notification.title == "New Task Assigned"
    assert task_title in notification.message


# ============================================================
# ============================================================
# RBAC / SECURITY TESTS
# ============================================================
# ============================================================


# ============================================================
# RBAC TEST 1
# EMPLOYEE CANNOT ACCESS REPORTS
# ============================================================

def test_employee_cannot_access_reports(client, db_session):
    headers = create_test_employee_user(
        client,
        db_session
    )

    response = client.get(
        "/api/reports/summary",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 2
# EMPLOYEE CANNOT ACCESS DEPARTMENTS
# ============================================================

def test_employee_cannot_access_departments(client, db_session):
    headers = create_test_employee_user(
        client,
        db_session
    )

    response = client.get(
        "/api/departments/",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 3
# EMPLOYEE CANNOT ACCESS ATTENDANCE
# ============================================================

def test_employee_cannot_access_attendance(client, db_session):
    headers = create_test_employee_user(
        client,
        db_session
    )

    response = client.get(
        "/api/attendance/",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 4
# HR MANAGER CAN ACCESS REPORTS
# ============================================================

def test_hr_manager_can_access_reports(client, db_session):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    response = client.get(
        "/api/reports/summary",
        headers=headers
    )

    assert response.status_code == 200

    data = response.json()

    assert "employees" in data
    assert "departments" in data
    assert "attendance" in data
    assert "tasks" in data


# ============================================================
# RBAC TEST 5
# HR MANAGER CAN ACCESS DEPARTMENTS
# ============================================================

def test_hr_manager_can_access_departments(client, db_session):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    response = client.get(
        "/api/departments/",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================
# RBAC TEST 6
# HR MANAGER CAN ACCESS ATTENDANCE
# ============================================================

def test_hr_manager_can_access_attendance(client, db_session):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    response = client.get(
        "/api/attendance/",
        headers=headers
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ============================================================
# RBAC TEST 7
# HR MANAGER CANNOT ACCESS AUDIT LOGS
# ============================================================

def test_hr_manager_cannot_access_audit_logs(
    client,
    db_session
):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    response = client.get(
        "/api/audit-logs/",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 8
# HR MANAGER CANNOT DELETE EMPLOYEE
# ============================================================

def test_hr_manager_cannot_delete_employee(
    client,
    db_session
):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    employee = create_test_employee(db_session)

    response = client.delete(
        f"/api/employees/{employee.id}",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 9
# HR MANAGER CANNOT DELETE DEPARTMENT
# ============================================================

def test_hr_manager_cannot_delete_department(
    client,
    db_session
):
    from backend.department_models import Department

    headers = create_test_hr_manager(
        client,
        db_session
    )

    unique_id = uuid.uuid4().hex[:8]

    department = Department(
        name=f"HR Delete Test {unique_id}",
        description="RBAC test department"
    )

    db_session.add(department)
    db_session.commit()
    db_session.refresh(department)

    response = client.delete(
        f"/api/departments/{department.id}",
        headers=headers
    )

    assert response.status_code == 403

    db_session.expire_all()

    existing_department = (
        db_session.query(Department)
        .filter(Department.id == department.id)
        .first()
    )

    assert existing_department is not None


# ============================================================
# RBAC TEST 10
# HR MANAGER CANNOT DELETE ATTENDANCE
# ============================================================

def test_hr_manager_cannot_delete_attendance(
    client,
    db_session
):
    headers = create_test_hr_manager(
        client,
        db_session
    )

    employee = create_test_employee(db_session)

    admin_headers = {
        "Authorization": f"Bearer {create_test_admin(client, db_session)}"
    }

    create_response = client.post(
        "/api/attendance/",
        headers=admin_headers,
        json={
            "employee_id": employee.id,
            "attendance_date": "2026-10-01",
            "status": "Present",
            "check_in": "09:00:00",
            "check_out": "18:00:00"
        }
    )

    assert create_response.status_code == 200

    attendance_id = (
        create_response.json()["attendance"]["id"]
    )

    delete_response = client.delete(
        f"/api/attendance/{attendance_id}",
        headers=headers
    )

    assert delete_response.status_code == 403


# ============================================================
# RBAC TEST 11
# EMPLOYEE CANNOT DELETE EMPLOYEE
# ============================================================

def test_employee_cannot_delete_employee(
    client,
    db_session
):
    headers = create_test_employee_user(
        client,
        db_session
    )

    employee = create_test_employee(db_session)

    response = client.delete(
        f"/api/employees/{employee.id}",
        headers=headers
    )

    assert response.status_code == 403


# ============================================================
# RBAC TEST 12
# EMPLOYEE CANNOT ACCESS AUDIT LOGS
# ============================================================

def test_employee_cannot_access_audit_logs(
    client,
    db_session
):
    headers = create_test_employee_user(
        client,
        db_session
    )

    response = client.get(
        "/api/audit-logs/",
        headers=headers
    )

    assert response.status_code == 403