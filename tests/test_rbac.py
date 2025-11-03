import json
from rest_framework.test import APIRequestFactory
from app.api.routers.sendPdfToEmployees import SendPayslipEmailView
from app.api.routers.sendManagerAggregatedCsvEmail import SendManagerAggregatedCsvEmailView


def test_send_payslip_employee_own_allowed(monkeypatch):
    factory = APIRequestFactory()

    class Caller:
        id = 1
        email = 'caller@example.com'

    # caller is employee id=1
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    # monkeypatch send_payslip_email to avoid side effects
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.send_payslip_email', lambda emp_id: {'sent': True, 'employee_id': emp_id})

    # monkeypatch Employee.objects.get for logging
    class DummyEmp:
        email = 'e@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyEmp())})}))

    data = {'employee_id': 1}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json')
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 200


def test_send_payslip_employee_other_forbidden(monkeypatch):
    factory = APIRequestFactory()

    class Caller:
        id = 1
        email = 'caller@example.com'

    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    # target exists but caller cannot manage
    class Target:
        id = 2
        email = 'target@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: Target())})}))

    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.can_manage_employee', lambda caller, target: False)

    data = {'employee_id': 2}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json')
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 403


def test_send_payslip_manager_allowed(monkeypatch):
    factory = APIRequestFactory()

    class Caller:
        id = 10
        email = 'manager@example.com'

    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())
    class Target:
        id = 2
        email = 'target@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: Target())})}))
    # manager can manage
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.can_manage_employee', lambda caller, target: True)
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.send_payslip_email', lambda emp_id: {'sent': True})

    data = {'employee_id': 2}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json')
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 200


def test_manager_aggregate_endpoint_role_enforcement(monkeypatch):
    factory = APIRequestFactory()

    class Caller:
        id = 99
        email = 'user@example.com'

    # Case: not manager and not admin -> forbidden
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.get_current_employee', lambda req: Caller())
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.employee_is_manager', lambda caller: False)
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.employee_is_admin', lambda caller: False)

    data = {'manager_id': 80}
    request = factory.post('/api/employees/send_manager_aggregated_csv_email/', data=json.dumps(data), content_type='application/json')
    view = SendManagerAggregatedCsvEmailView.as_view()
    response = view(request)
    assert response.status_code == 403

    # Case: manager -> allowed (mock idempotency return path or direct call)
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.get_current_employee', lambda req: Caller())
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.employee_is_manager', lambda caller: True)
    # monkeypatch idempotency to simple return
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.get_or_create_idempotent', lambda *a, **k: {'data': {'archive_path': '/fake.zip'}, 'idempotent': True, 'cached': False})
    class DummyMgr:
        email = 'm@example.com'
    monkeypatch.setattr('app.api.routers.sendManagerAggregatedCsvEmail.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyMgr())})}))

    request = factory.post('/api/employees/send_manager_aggregated_csv_email/', data=json.dumps(data), content_type='application/json', **{'HTTP_IDEMPOTENCY_KEY': 'abc'})
    response = view(request)
    assert response.status_code == 200
