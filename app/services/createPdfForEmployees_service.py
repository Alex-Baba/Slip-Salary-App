from fpdf import FPDF
from datetime import datetime
from app.db.models import Employee, Attendance, Bonus
from django.db.models import Sum
from app.services.salary_service import compute_monthly_salary, _business_days_in_month
from django.core.exceptions import ValidationError

def create_pdf_for_employee(employee_id: int) -> bytes:
    """Generate a minimal monthly payslip PDF for an employee"""
    today = datetime.today()
    year, month = today.year, today.month

    # Fetch employee
    try:
        employee = Employee.objects.get(id=employee_id)
    except Employee.DoesNotExist:
        raise ValidationError({"employee_id": "Employee not found"})

    attendance = Attendance.objects.filter(employee=employee, year=year, month=month).first()
    working_days = attendance.working_days if attendance else 0
    leave_days = attendance.leave_days if attendance else 0

    # Compute salary with bonuses (total_salary) using existing service
    total_salary = compute_monthly_salary(employee, year, month)

    # Gather bonuses for month
    bonuses_qs = Bonus.objects.filter(employee=employee, date__year=year, date__month=month).order_by('date')
    bonuses = [f"{b.date.isoformat()} - {b.description}: {float(b.amount):.2f}" for b in bonuses_qs]
    total_bonus = sum(float(b.amount) for b in bonuses_qs)

    # Create PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, txt=f"Payslip {year}-{month:02d}", ln=True, align='C')
    pdf.ln(4)

    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, txt=f"Employee: {employee.first_name} {employee.last_name}", ln=True)
    pdf.cell(0, 8, txt=f"Role: {employee.role.role}", ln=True)
    if employee.department:
        pdf.cell(0, 8, txt=f"Department: {employee.department.name}", ln=True)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, txt="Monthly Summary", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 8, txt=f"Working days: {working_days}", ln=True)
    pdf.cell(0, 8, txt=f"Vacation days: {leave_days}", ln=True)
    pdf.cell(0, 8, txt=f"Additional bonuses: {total_bonus:.2f}", ln=True)
    pdf.cell(0, 8, txt=f"Salary to be paid (EUR): {total_salary:.2f}", ln=True)
    pdf.ln(4)

    if bonuses:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, txt="Bonuses Detail", ln=True)
        pdf.set_font("Arial", size=11)
        for line in bonuses:
            pdf.multi_cell(0, 6, txt=line)

    # Footer
    pdf.set_y(-30)
    pdf.set_font("Arial", size=9)
    pdf.cell(0, 6, txt="Generated automatically.", ln=True, align='C')

    return pdf.output(dest='S').encode('latin1')
