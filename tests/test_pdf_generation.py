from app.services.createPdfForEmployees_service import create_pdf_for_employee
from app.services.createPdfForEmployees_service import save_payslip_pdf, get_payslip_filepath
import os


class DummyEmployee:
    def __init__(self):
        self.id = 1
        self.first_name = 'John'
        self.last_name = 'Doe'
        class Role: role = 'Developer'
        self.role = Role()
        self.department = None


def test_create_pdf_for_employee_generates_bytes(monkeypatch, tmp_path):
    # Monkeypatch Employee.objects.get to return a dummy employee
    dummy = DummyEmployee()

    class DummyQSet:
        def first(self):
            return None

    monkeypatch.setattr('app.services.createPdfForEmployees_service.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: dummy), 'filter': staticmethod(lambda **kw: DummyQSet())})}))

    pdf_bytes = create_pdf_for_employee(1)
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes.startswith(b'%PDF') or len(pdf_bytes) > 0
