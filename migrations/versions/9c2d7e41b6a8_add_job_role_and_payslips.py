"""add employee job role and payslips

Revision ID: 9c2d7e41b6a8
Revises: a6ba9763237f
Create Date: 2026-09-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9c2d7e41b6a8"
down_revision: Union[str, Sequence[str], None] = "a6ba9763237f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "employees",
        sa.Column("job_role", sa.String(length=120), nullable=True),
    )
    op.create_index(
        "ix_employees_job_role",
        "employees",
        ["job_role"],
        unique=False,
    )

    op.create_table(
        "payslips",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("employee_id", sa.Integer(), nullable=False),
        sa.Column("pay_period", sa.String(length=7), nullable=False),
        sa.Column("gross_salary", sa.Float(), nullable=False),
        sa.Column("deductions", sa.Float(), nullable=False, server_default="0"),
        sa.Column("net_salary", sa.Float(), nullable=False),
        sa.Column("pay_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="Paid"),
        sa.ForeignKeyConstraint(["employee_id"], ["employees.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("employee_id", "pay_period", name="uq_payslip_employee_period"),
    )
    op.create_index("ix_payslips_id", "payslips", ["id"], unique=False)
    op.create_index("ix_payslips_employee_id", "payslips", ["employee_id"], unique=False)
    op.create_index("ix_payslips_pay_period", "payslips", ["pay_period"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payslips_pay_period", table_name="payslips")
    op.drop_index("ix_payslips_employee_id", table_name="payslips")
    op.drop_index("ix_payslips_id", table_name="payslips")
    op.drop_table("payslips")
    op.drop_index("ix_employees_job_role", table_name="employees")
    op.drop_column("employees", "job_role")
