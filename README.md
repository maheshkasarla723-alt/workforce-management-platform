# Workforce Management Platform

A full-stack Workforce Management Platform built with Python, FastAPI, SQLAlchemy, PostgreSQL, HTML, CSS, and JavaScript.

The platform provides employee management, departments, attendance, tasks, notifications, audit logging, authentication, role-based access control, dashboard reporting, security controls, automated testing, performance indexes, backup/recovery support, CI, and production deployment configuration.

---

## 1. Project Overview

The Workforce Management Platform is designed to help organizations manage workforce information and employee-related activities through a centralized web application.

### Main Features

- User authentication and JWT-based authorization
- Role-Based Access Control (RBAC)
- Employee management
- Department management
- Attendance management
- Task management
- Employee status management
- Notifications
- Audit logs
- Dashboard and reports
- Search, filtering, sorting, and pagination
- Input validation
- Safe API error handling
- Security headers
- CORS configuration
- Authentication rate limiting
- Request ID tracking
- Structured application logging
- PostgreSQL database
- SQLAlchemy ORM
- Database performance indexes
- Automated tests with pytest
- GitHub Actions CI
- PostgreSQL backup and restore workflow
- Docker configuration
- Production configuration
- Render deployment support

---

# 2. Technology Stack

## Backend

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- PostgreSQL
- JWT
- Passlib
- Pytest
- SlowAPI

## Frontend

- HTML5
- CSS3
- JavaScript
- Responsive UI

## Development Tools

- Visual Studio Code
- Git
- GitHub
- PostgreSQL
- pgAdmin
- PowerShell

## Deployment / DevOps

- GitHub Actions
- Docker
- Docker Compose
- Render
- PostgreSQL

---

# 3. Project Structure

```text
workforce management project/
│
├── .github/
│   └── workflows/
│       └── ci.yml
│
├── .vscode/
│
├── backend/
│   ├── routers/
│   │   ├── auth.py
│   │   ├── employees.py
│   │   ├── departments.py
│   │   ├── attendance.py
│   │   ├── tasks.py
│   │   ├── notifications.py
│   │   ├── audit_logs.py
│   │   └── reports.py
│   │
│   ├── services/
│   │
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── user_models.py
│   ├── notification_models.py
│   ├── task_models.py
│   └── add_performance_indexes.py
│
├── frontend/
│   └── index.html
│
├── tests/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_database_audit.py
│   └── test_security.py
│
├── backups/
│
├── logs/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .gitignore
└── README.md