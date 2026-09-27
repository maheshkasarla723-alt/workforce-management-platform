from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool

from backend.database import Base, engine

# Import every model so Alembic can detect all tables and relationships.
from backend.models import Employee
from backend.department_models import Department
from backend.attendance_models import Attendance
from backend.task_models import Task
from backend.user_models import User
from backend.audit_models import AuditLog
from backend.notification_models import Notification


# Alembic Config object
config = context.config


# Configure Python logging from alembic.ini when available.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# SQLAlchemy metadata used by Alembic autogenerate.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations without creating a database connection.
    """

    url = str(engine.url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named"
        },
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations using the application's SQLAlchemy engine.
    """

    connectable = engine

    with connectable.connect() as connection:

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()