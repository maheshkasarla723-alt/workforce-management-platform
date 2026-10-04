from datetime import date
from copy import deepcopy

from sqlalchemy.orm import Session

from backend.models import Employee


# ============================================================
# FIXED PAYSLIP DEDUCTIONS
# ============================================================

PROVIDENT_FUND = 1800.00
INSURANCE = 500.00
OTHER_DEDUCTION = 2700.00

TOTAL_DEDUCTION = (
    PROVIDENT_FUND
    + INSURANCE
    + OTHER_DEDUCTION
)


# ============================================================
# CURRENT PAY PERIOD
# ============================================================

def get_current_pay_period() -> str:
    """
    Return the current payroll period as YYYY-MM.
    """
    today = date.today()

    return today.strftime("%Y-%m")


# ============================================================
# GENERATE ONE PAYSLIP
# ============================================================

def build_monthly_payslip(
    employee: Employee,
    pay_period: str | None = None,
) -> dict:
    """
    Build one monthly payslip using the employee salary
    and the fixed deduction rules.
    """

    if pay_period is None:
        pay_period = get_current_pay_period()

    gross_salary = float(employee.salary or 0)

    provident_fund = PROVIDENT_FUND
    insurance = INSURANCE
    other_deduction = OTHER_DEDUCTION

    total_deductions = (
        provident_fund
        + insurance
        + other_deduction
    )

    net_salary = (
        gross_salary
        - total_deductions
    )

    return {
        "month": pay_period,
        "gross_salary": round(gross_salary, 2),
        "provident_fund": round(
            provident_fund,
            2,
        ),
        "insurance": round(
            insurance,
            2,
        ),
        "other_deduction": round(
            other_deduction,
            2,
        ),
        "deductions": round(
            total_deductions,
            2,
        ),
        "net_salary": round(
            net_salary,
            2,
        ),
    }


# ============================================================
# ENSURE CURRENT MONTH PAYSLIP
# ============================================================

def ensure_current_month_payslip(
    employee: Employee,
    db: Session,
) -> dict:
    """
    Create the current month's payslip if it does not exist.

    Existing payslips are preserved.
    Duplicate payslips for the same employee/month are not created.
    """

    metadata = (
        deepcopy(employee.profile_metadata)
        if isinstance(
            employee.profile_metadata,
            dict,
        )
        else {}
    )

    payslips = metadata.get("payslips")

    if not isinstance(payslips, list):
        payslips = []

    current_period = get_current_pay_period()

    # --------------------------------------------------------
    # Check whether this month's payslip already exists.
    # --------------------------------------------------------

    for payslip in payslips:

        if not isinstance(payslip, dict):
            continue

        existing_period = (
            payslip.get("month")
            or payslip.get("period")
            or payslip.get("pay_period")
        )

        if existing_period == current_period:

            return payslip

    # --------------------------------------------------------
    # Generate new payslip.
    # --------------------------------------------------------

    new_payslip = build_monthly_payslip(
        employee=employee,
        pay_period=current_period,
    )

    payslips.append(new_payslip)

    metadata["payslips"] = payslips

    employee.profile_metadata = metadata

    db.add(employee)

    return new_payslip


# ============================================================
# ENSURE PAYSLIPS FOR ACTIVE EMPLOYEES
# ============================================================

def ensure_current_month_payslips_for_active_employees(
    employees: list[Employee],
    db: Session,
) -> int:
    """
    Ensure every Active employee has a current-month payslip.

    Returns the number of newly generated payslips.
    """

    generated_count = 0

    for employee in employees:

        if employee.status != "Active":
            continue

        metadata = (
            employee.profile_metadata
            if isinstance(
                employee.profile_metadata,
                dict,
            )
            else {}
        )

        payslips = metadata.get("payslips")

        if not isinstance(payslips, list):
            payslips = []

        current_period = get_current_pay_period()

        exists = any(
            isinstance(payslip, dict)
            and (
                payslip.get("month")
                or payslip.get("period")
                or payslip.get("pay_period")
            ) == current_period
            for payslip in payslips
        )

        if exists:
            continue

        ensure_current_month_payslip(
            employee=employee,
            db=db,
        )

        generated_count += 1

    if generated_count:
        db.commit()

    return generated_count