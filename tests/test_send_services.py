import os
from app.services.sendPdfForEmployees_service import send_payslip_email, fetch_payslip_pdf
from app.services.sendAggregatedEmployeeData_service import send_manager_aggregated_csv_email, get_aggregate_filepath


def test_send_payslip_archives_and_deletes_original(monkeypatch, tmp_path):
    # Prepare fake pdf file path and content
    fake_media = tmp_path / 'media'
    payslip_dir = fake_media / 'payslips' / '2025-11'
    payslip_dir.mkdir(parents=True)
    pdf_path = payslip_dir / 'employee_1_report.pdf'
    pdf_path.write_bytes(b'PDFDATA')

    # Monkeypatch get_payslip_filepath to point to our fake path
    monkeypatch.setattr('app.services.createPdfForEmployees_service.get_payslip_filepath', lambda emp_id: str(pdf_path))

    # Monkeypatch Employee model lookup
    class DummyEmp:
        id = 1
        email = 'e@example.com'
        cnp = '1234567890123'
        first_name = 'John'
    monkeypatch.setattr('app.services.sendPdfForEmployees_service.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyEmp())})}))

    # Monkeypatch send_email to return a fake response
    monkeypatch.setattr('app.services.sendPdfForEmployees_service.send_email', lambda **kw: {'sent': True, 'id': 'test'})

    # Monkeypatch archive_bytes to write into our fake_media archives directory
    def fake_archive_bytes(b, subfolder, y, m, filename, metadata):
        arch_dir = fake_media / 'archives' / subfolder / f"{y}-{m:02d}"
        arch_dir.mkdir(parents=True, exist_ok=True)
        p = arch_dir / filename
        p.write_bytes(b)
        (p.with_suffix('.json')).write_text('{}')
        return str(p)

    monkeypatch.setattr('app.services.sendPdfForEmployees_service.archive_bytes', fake_archive_bytes)

    resp = send_payslip_email(1)
    assert resp.get('archive_path') is not None
    # Original should be deleted
    assert not pdf_path.exists()


def test_send_manager_aggregate_deletes_original(monkeypatch, tmp_path):
    fake_media = tmp_path / 'media'
    agg_dir = fake_media / 'aggregates' / '2025-11'
    agg_dir.mkdir(parents=True)
    path = agg_dir / 'manager_80_team_aggregate.csv'
    path.write_text('a,b,c')

    # Monkeypatch settings for MEDIA_ROOT used in service
    monkeypatch.setenv('MEDIA_ROOT', str(fake_media))

    # Monkeypatch Employee lookup for manager
    class DummyMgr:
        id = 80
        email = 'm@example.com'
        first_name = 'Manager'
    monkeypatch.setattr('app.services.sendAggregatedEmployeeData_service.Employee', type('E', (), {'objects': type('o', (), {'get': staticmethod(lambda id: DummyMgr())})}))

    # Monkeypatch send_email and archive_bytes
    monkeypatch.setattr('app.services.sendAggregatedEmployeeData_service.send_email', lambda **kw: {'sent': True})
    def fake_archive(b, subfolder, y, m, filename, metadata):
        arch_dir = fake_media / 'archives' / subfolder / f"{y}-{m:02d}"
        arch_dir.mkdir(parents=True, exist_ok=True)
        p = arch_dir / filename
        p.write_bytes(b)
        (p.with_suffix('.json')).write_text('{}')
        return str(p)
    monkeypatch.setattr('app.services.sendAggregatedEmployeeData_service.archive_bytes', fake_archive)

    resp = send_manager_aggregated_csv_email(80, 2025, 11, 'm@example.com')
    assert resp.get('archive_path') is not None
    assert not path.exists()
