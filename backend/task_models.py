from sqlalchemy import (
    Column,
    Integer,
    String,
    Date,
    ForeignKey,
    Index,
    Text,
)

from backend.database import Base


class Task(Base):

    __tablename__ = "tasks"

    __table_args__ = (
        # Faster employee task searches.
        Index(
            "ix_tasks_employee_id",
            "employee_id"
        ),

        # Faster task status filtering.
        Index(
            "ix_tasks_status",
            "status"
        ),

        # Faster priority filtering.
        Index(
            "ix_tasks_priority",
            "priority"
        ),

        # Faster due-date queries.
        Index(
            "ix_tasks_due_date",
            "due_date"
        ),

        # Useful for employee task dashboards.
        Index(
            "ix_tasks_employee_status",
            "employee_id",
            "status"
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False
    )

    title = Column(
        String(200),
        nullable=False
    )

    description = Column(
        Text,
        nullable=True
    )

    priority = Column(
        String(50),
        nullable=False,
        default="Medium"
    )

    status = Column(
        String(50),
        nullable=False,
        default="Pending"
    )

    due_date = Column(
        Date,
        nullable=False
    )