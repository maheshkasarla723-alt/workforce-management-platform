from sqlalchemy import inspect, text

from backend.database import engine


# ============================================================
# PERFORMANCE INDEX DEFINITIONS
# ============================================================

INDEXES = [

    # ========================================================
    # EMPLOYEES
    # ========================================================

    (
        "ix_employees_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_status
        ON employees (status)
        """
    ),

    (
        "ix_employees_joining_date",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_joining_date
        ON employees (joining_date)
        """
    ),

    (
        "ix_employees_department_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_department_status
        ON employees (department_id, status)
        """
    ),

    (
        "ix_employees_manager_status",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_manager_status
        ON employees (manager_id, status)
        """
    ),

    (
        "ix_employees_manager_id",
        """
        CREATE INDEX IF NOT EXISTS ix_employees_manager_id
        ON employees (manager_id)
        """
    ),

    # ========================================================
    # ATTENDANCE
    # ========================================================

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

    # ========================================================
    # TASKS
    # ========================================================

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

    # ========================================================
    # NOTIFICATIONS
    # ========================================================

    (
        "ix_notifications_user_id",
        """
        CREATE INDEX IF NOT EXISTS ix_notifications_user_id
        ON notifications (user_id)
        """
    ),

    # ========================================================
    # AUDIT LOGS
    # ========================================================

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


# ============================================================
# VERIFY INDEX
# ============================================================

def index_exists(connection, index_name):
    """
    Check whether an index exists in the current database.
    """

    inspector = inspect(connection)

    for table_name in inspector.get_table_names():

        indexes = inspector.get_indexes(table_name)

        for index in indexes:

            if index["name"] == index_name:
                return True

    return False


# ============================================================
# CREATE INDEXES
# ============================================================

def create_indexes():

    print("=" * 70)
    print("WORKFORCE MANAGEMENT PLATFORM")
    print("PERFORMANCE INDEX MIGRATION")
    print("=" * 70)

    # --------------------------------------------------------
    # Make sure we are using PostgreSQL
    # --------------------------------------------------------

    if engine.dialect.name != "postgresql":

        raise RuntimeError(
            "Performance index migration requires PostgreSQL. "
            f"Current database: {engine.dialect.name}"
        )

    print(
        f"Database dialect: {engine.dialect.name}"
    )

    successful = 0
    failed = 0

    # --------------------------------------------------------
    # Create indexes
    # --------------------------------------------------------

    with engine.begin() as connection:

        for index_name, sql in INDEXES:

            try:

                connection.execute(
                    text(sql)
                )

                if index_exists(
                    connection,
                    index_name
                ):

                    print(
                        f"[OK] {index_name}"
                    )

                    successful += 1

                else:

                    print(
                        f"[WARNING] {index_name} "
                        "was not found after creation"
                    )

                    failed += 1

            except Exception as error:

                print(
                    f"[ERROR] {index_name}"
                )

                print(
                    f"        {error}"
                )

                failed += 1

    # --------------------------------------------------------
    # Summary
    # --------------------------------------------------------

    print("=" * 70)
    print("PERFORMANCE INDEX MIGRATION COMPLETE")
    print("=" * 70)

    print(
        f"Total indexes : {len(INDEXES)}"
    )

    print(
        f"Successful    : {successful}"
    )

    print(
        f"Failed        : {failed}"
    )

    print("=" * 70)

    if failed > 0:

        raise RuntimeError(
            f"{failed} performance index(es) failed."
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":

    create_indexes()