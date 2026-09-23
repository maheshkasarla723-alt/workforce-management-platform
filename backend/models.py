from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    ForeignKey,
    Date,
    Text,
    Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from backend.database import Base


class Employee(Base):

    __tablename__ = "employees"

    __table_args__ = (

        # ------------------------------------------------
        # Performance indexes for Level 5 filtering
        # ------------------------------------------------

        Index(
            "ix_employees_status",
            "status"
        ),

        Index(
            "ix_employees_joining_date",
            "joining_date"
        ),

        Index(
            "ix_employees_department_status",
            "department_id",
            "status"
        ),

        Index(
            "ix_employees_manager_status",
            "manager_id",
            "status"
        ),
    )

    # ====================================================
    # BASIC EMPLOYEE INFORMATION
    # ====================================================

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    name = Column(
        String(100),
        nullable=False
    )

    email = Column(
        String(150),
        unique=True,
        nullable=False,
        index=True
    )

    age = Column(
        Integer,
        nullable=False
    )

    salary = Column(
        Float,
        nullable=False
    )

    # ====================================================
    # LEVEL 5.1 — ADVANCED EMPLOYEE FIELDS
    # ====================================================

    status = Column(
        String(30),
        nullable=False,
        default="Active"
    )

    joining_date = Column(
        Date,
        nullable=True
    )

    skills = Column(
        Text,
        nullable=True
    )

    profile_metadata = Column(
        JSONB,
        nullable=True
    )

    # ====================================================
    # DEPARTMENT
    # ====================================================

    department_id = Column(
        Integer,
        ForeignKey(
            "departments.id"
        ),
        nullable=True
    )

    department = relationship(
        "Department",
        back_populates="employees"
    )

    # ====================================================
    # MANAGER
    # ====================================================

    manager_id = Column(
        Integer,
        ForeignKey(
            "employees.id",
            ondelete="SET NULL"
        ),
        nullable=True,
        index=True
    )

    manager = relationship(
        "Employee",
        remote_side=[id],
        backref="subordinates"
    )