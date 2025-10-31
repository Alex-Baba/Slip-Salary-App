"""Reusable email body builders for payroll notifications.

Goal: Improve deliverability by providing well-structured, benign wording,
plain text + HTML, and consistent footer with contact and unsubscribe hint.
"""
from datetime import datetime
from typing import Dict, List

FOOTER_TEXT = (
    "\n--\nPayroll Automation System\nThis email contains confidential compensation information. "
    "If you received it in error, please delete it and notify payroll@company.example."
)

FOOTER_HTML = (
    "<hr style='border:none;border-top:1px solid #ccc;margin:24px 0;'>"
    "<p style='font-size:12px;color:#666;line-height:1.4'>"
    "Payroll Automation System<br>"
    "This email contains confidential compensation information. If you received it in error, please delete it and notify <a href='mailto:payroll@company.example'>payroll@company.example</a>."
    "</p>"
)

def build_payslip_subject(period: datetime) -> str:
    return f"Payslip for {period.strftime('%B %Y')}"

def build_payslip_bodies(employee_first: str) -> Dict[str, str]:
    text = (
        f"Hello {employee_first},\n\n"
        "Your payslip for this month is attached as a PDF. It includes gross salary, adjustments, and bonus details where applicable.\n\n"
        "Please review and contact Payroll if you notice any discrepancies." + FOOTER_TEXT
    )
    html = (
        f"<p>Hello {employee_first},</p>"
        "<p>Your payslip for this month is attached as a PDF. It includes gross salary, adjustments, and bonus details where applicable.</p>"
        "<p>Please review and contact <a href='mailto:payroll@company.example'>Payroll</a> if you notice any discrepancies.</p>"
        f"{FOOTER_HTML}"
    )
    return {"text": text, "html": html}

def build_aggregate_subject(period: datetime) -> str:
    return f"Monthly Compensation Summary - {period.strftime('%B %Y')}"

def build_aggregate_bodies(employee_first: str, bonuses: List[Dict]) -> Dict[str, str]:
    bonus_line = (
        f"Includes {len(bonuses)} bonus item(s)." if bonuses else "No bonuses recorded this period."
    )
    text = (
        f"Hello {employee_first},\n\nYour monthly compensation summary CSV is attached. {bonus_line}\n"
        "It lists working days, leave days, salary calculation components, and total.\n\n"
        "Reach out to Payroll for clarification." + FOOTER_TEXT
    )
    html = (
        f"<p>Hi {employee_first},</p>"
        f"<p>Your monthly compensation summary (CSV) is attached. {bonus_line}</p>"
        "<p>It lists working days, leave days, salary components, and total amount.</p>"
        "<p>Contact <a href='mailto:payroll@company.example'>Payroll</a> for clarification.</p>"
        f"{FOOTER_HTML}"
    )
    return {"text": text, "html": html}

__all__ = [
    "build_payslip_subject",
    "build_payslip_bodies",
    "build_aggregate_subject",
    "build_aggregate_bodies",
]
