import json
from rest_framework.test import APIRequestFactory
from app.api.routers.createPdfEmployees import CreatePdfEmployeesView
from app.api.routers.sendPdfToEmployees import SendPayslipEmailView
from app.api.routers.sendManagerAggregatedCsvEmail import SendManagerAggregatedCsvEmailView


def test_create_pdf_endpoint_generate(monkeypatch):
    factory = APIRequestFactory()
    # Monkeypatch create_pdf_for_employee to return bytes and save_payslip_pdf to be a no-op
    monkeypatch.setattr('app.api.routers.createPdfEmployees.create_pdf_for_employee', lambda employee_id: b'%PDF-1.4 test')
    monkeypatch.setattr('app.api.routers.createPdfEmployees.save_payslip_pdf', lambda emp_id, data: '/tmp/fake.pdf')

    request = factory.get('/api/create_pdf?employee_id=1&generate=1')
    view = CreatePdfEmployeesView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response['Content-Type'].startswith('application/pdf')


def test_send_payslip_endpoint_post_no_key(monkeypatch):
    factory = APIRequestFactory()
    # Prepare get_current_employee to return a dummy user with id=1
    class Caller:
        id = 1
        email = 'caller@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    # Monkeypatch send_payslip_email to return a predictable dict
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.send_payslip_email', lambda emp_id: {'sent': True, 'employee_id': emp_id})

    # Monkeypatch Employee.objects.get used for logging to avoid DB access
    class DummyEmp:
        email = 'e@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyEmp())})}))

    data = {'employee_id': 1}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json')
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert isinstance(response.data, dict)


def test_send_manager_aggregate_with_idempotency(monkeypatch):
    factory = APIRequestFactory()
    # Monkeypatch auth helpers
    class Caller:
        id = 99
        email = 'manager@example.com'
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.get_current_employee', lambda req: Caller())
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.employee_is_manager', lambda caller: True)
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.employee_is_admin', lambda caller: False)

    # Monkeypatch idempotency service to return cached-like structure
    def fake_get_or_create(endpoint, key, payload, builder):
        return {'data': {'archive_path': '/fake/path.zip'}, 'idempotent': True, 'cached': False}
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.get_or_create_idempotent', fake_get_or_create)

    # Monkeypatch Employee.objects.get for recipient lookup
    class DummyMgr:
        email = 'm@example.com'
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyMgr())})}))

    data = {'manager_id': 80}
    # Include Idempotency header
    request = factory.post('/api/employees/send_manager_aggregated_csv_email/', data=json.dumps(data), content_type='application/json', **{'HTTP_IDEMPOTENCY_KEY': 'abc-123'})
    view = SendManagerAggregatedCsvEmailView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert isinstance(response.data, dict)
    assert response.data.get('archive_path') == '/fake/path.zip' or response.data.get('archive_path') is not None
