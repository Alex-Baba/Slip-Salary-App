import json
from rest_framework.test import APIRequestFactory
from app.api.routers.sendPdfToEmployees import SendPayslipEmailView


def test_idempotency_cached_response(monkeypatch):
    factory = APIRequestFactory()
    class Caller:
        id = 1
        email = 'caller@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    # Simulate idempotency returning cached data
    def fake_get_or_create(endpoint, key, request_payload, response_builder, owner=None):
        return {'data': {'provider_response': {'sent': True}}, 'idempotent': True, 'cached': True}

    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_or_create_idempotent', fake_get_or_create)
    # Patch Employee lookup for logging
    class DummyEmp:
        email = 'e@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyEmp())})}))

    data = {'employee_id': 1}
    headers = {'HTTP_IDEMPOTENCY_KEY': 'same-key'}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json', **headers)
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 200
    assert response.data.get('idempotent') is True
    assert response.data.get('cached') is True


def test_idempotency_conflict(monkeypatch):
    factory = APIRequestFactory()
    class Caller:
        id = 1
        email = 'caller@example.com'
    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_current_employee', lambda req: Caller())

    # Simulate idempotency conflict
    def fake_get_or_create_conflict(endpoint, key, request_payload, response_builder, owner=None):
        return {'conflict': True, 'message': 'Conflict detected'}

    monkeypatch.setattr('app.api.routers.sendPdfToEmployees.get_or_create_idempotent', fake_get_or_create_conflict)
    data = {'employee_id': 1}
    headers = {'HTTP_IDEMPOTENCY_KEY': 'same-key'}
    request = factory.post('/api/employees/send_payslip/', data=json.dumps(data), content_type='application/json', **headers)
    view = SendPayslipEmailView.as_view()
    response = view(request)
    assert response.status_code == 409
