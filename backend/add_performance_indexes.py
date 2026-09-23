from sqlalchemy import text

from backend.database import engine


INDEXES = [
    # =========================================================
    # EMPLOYEES
    # Used by status filtering
    # =========================================================
    (
        "ix_employees_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_status
        ON employees (status)
        """
    ),

    # Used by joining-date range filtering
    (
        "ix_employees_joining_date",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_joining_date
        ON employees (joining_date)
        """
    ),

    # Used by department + status filtering
    (
        "ix_employees_department_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_department_status
        ON employees (department_id, status)
        """
    ),

    # Used by manager + status filtering
    (
        "ix_employees_manager_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_manager_status
        ON employees (manager_id, status)
        """
    ),

    # Used by manager relationship lookups
    (
        "ix_employees_manager_id",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_manager_id
        ON employees (manager_id)
        """
    ),

    # =========================================================
    # ATTENDANCE
    # =========================================================
    (
        "ix_attendance_employee_id",
        """
        CREATE INDEX IF NOT EXISTS ix_attendance_employee_id
        ON attendance (employee_id)
        """
    ),

    (
        "ix_attendance_date",
        """
        CREATE INDEX IF NOT EXISTS ix_attendance_date
        ON attendance (attendance_date)
        """
    ),

    (
        "ix_attendance_employee_date",
        """
        CREATE INDEX IF NOT EXISTS ix_attendance_employee_date
        ON attendance (employee_id, attendance_date)
        """
    ),

    # =========================================================
    # TASKS
    # =========================================================
    (
        "ix_tasks_employee_id",
        """
        CREATE INDEX IF NOT EXISTS ix_tasks_employee_id
        ON tasks (employee_id)
        """
    ),

    (
        "ix_tasks_status",
        """
        CREATE INDEX IF NOT EXISTS ix_tasks_status
        ON tasks (status)
        """
    ),

    (
        "ix_tasks_priority",
        """
        CREATE INDEX IF NOT EXISTS ix_tasks_priority
        ON tasks (priority)
        """
    ),

    (
        "ix_tasks_due_date",
        """
        CREATE INDEX IF NOT EXISTS ix_tasks_due_date
        ON tasks (due_date)
        """
    ),

    (
        "ix_tasks_employee_status",
        """
        CREATE INDEX IF NOT EXISTS ix_tasks_employee_status
        ON tasks (employee_id, status)
        """
    ),

    # =========================================================
    # NOTIFICATIONS
    # Used to load notifications for the logged-in user
    # =========================================================
    (
        "ix_notifications_user_id",
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_user_id
        ON notifications (user_id)
        """
    ),

    # =========================================================
    # AUDIT LOGS
    # Used by audit-history filtering and ordering
    # =========================================================
    (
        "ix_audit_logs_user_id",
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_user_id
        ON audit_logs (user_id)
        """
    ),

    (
        "ix_audit_logs_entity",
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_entity
        ON audit_logs (entity)
        """
    ),

    (
        "ix_audit_logs_entity_id",
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_id
        ON audit_logs (entity_id)
        """
    ),

    (
        "ix_audit_logs_created_at",
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_created_at
        ON audit_logs (created_at)
        """
    ),

    (
        "ix_audit_logs_entity_entity_id",
        """
        CREATE INDEX IF NOT EXISTS ix_audit_logs_entity_entity_id
        ON audit_logs (entity, entity_id)
        """
    ),
]


def main():
    print("=" * 60)
    print("Starting performance index migration...")
    print("=" * 60)

    created = 0
    skipped = 0

    with engine.begin() as connection:

        for index_name, sql in INDEXES:

            try:
                connection.execute(text(sql))

                print(
                    f"[OK] Index ready: {index_name}"
                )

                created += 1

            except Exception as error:

                print(
                    f"[WARNING] Could not create "
                    f"{index_name}: {error}"
                )

                skipped += 1

    print("=" * 60)
    print("Performance index migration completed.")
    print(f"Indexes processed: {len(INDEXES)}")
    print(f"Successful: {created}")
    print(f"Warnings: {skipped}")
    print("=" * 60)


if __name__ == "__main__":
    main()