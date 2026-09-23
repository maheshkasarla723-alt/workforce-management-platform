from sqlalchemy import (
    Column,
    Integer,
    Date,
    Time,
    String,
    ForeignKey,
    Index,
    UniqueConstraint,
)

from backend.database import Base


class Attendance(Base):

    __tablename__ = "attendance"

    __table_args__ = (
        # Prevent duplicate attendance for
        # the same employee on the same date.
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="uq_attendance_employee_date"
        ),

        # Faster employee attendance searches.
        Index(
            "ix_attendance_employee_id",
            "employee_id"
        ),

        # Faster date-based attendance reports.
        Index(
            "ix_attendance_date",
            "attendance_date"
        ),

        # Faster employee + date searches.
        Index(
            "ix_attendance_employee_date",
            "employee_id",
            "attendance_date"
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

    attendance_date = Column(
        Date,
        nullable=False
    )

    status = Column(
        String(50),
        nullable=False
    )

    check_in = Column(
        Time,
        nullable=True
    )

    check_out = Column(
        Time,
        nullable=True
    )