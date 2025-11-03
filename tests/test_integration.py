import os
import json
import tempfile
import shutil
import pytest
from django.urls import reverse

# If Docker Postgres host 'db' is not resolvable, skip the whole module to avoid
# pytest-django trying to create a test DB against a non-existent Docker service.
import socket
try:
    socket.gethostbyname('db')
except Exception:
    pytest.skip("Skipping integration tests because Docker Postgres host 'db' is not available", allow_module_level=True)


@pytest.mark.django_db(transaction=True)
def test_generate_and_send_payslip_integration(client, settings, monkeypatch, tmp_path):
    # Configure a temporary MEDIA_ROOT for the test
    media_dir = tmp_path / 'media'
    settings.MEDIA_ROOT = str(media_dir)

    # If Docker Postgres host 'db' is not resolvable, skip this integration test (CI will run this with compose)
    import socket
    try:
        socket.gethostbyname('db')
    except Exception:
        pytest.skip("Skipping integration test because Docker Postgres host 'db' is not available")

    # Create required minimal data: Role, Department, Employee
    from app.db.models import EmployeeRole, Department, Employee
    role = EmployeeRole.objects.create(role='developer')
    dept = Department.objects.create(name='eng')
    emp = Employee.objects.create(email='e@example.com', password='x', first_name='E', last_name='X', cnp='1234567890123', role=role, department=dept, base_salary=1000)

    # Monkeypatch send_email to avoid external providers
    monkeypatch.setattr('app.services.email_provider_service.send_email', lambda **kw: {'sent': True, 'id': 'test'})

    # Call generate PDF endpoint (uses create_pdf_for_employee and saves file)
    url = reverse('create-pdf-employees')
    resp = client.get(url, {'employee_id': emp.id, 'generate': '1'})
    assert resp.status_code == 200
    # Ensure the file exists
    payslip_path = os.path.join(settings.MEDIA_ROOT, 'payslips', f"{emp.id}")
    # Use glob to find file under payslips/YYYY-MM
    import glob
    matches = glob.glob(os.path.join(settings.MEDIA_ROOT, 'payslips', '*', f'employee_{emp.id}_report.pdf'))
    assert matches, "Payslip PDF not found on disk"

    # Now call send payslip endpoint as manager or admin: monkeypatch auth to allow
    # Patch the symbol used by the router so the view sees the monkeypatch during import
    class Caller:
        id = emp.id
        email = emp.email
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    send_url = reverse('send-payslip-email')
    res = client.post(send_url, {'employee_id': emp.id}, content_type='application/json')
    assert res.status_code == 200
    data = res.json()
    assert data.get('archive_path') or data.get('provider_response')
