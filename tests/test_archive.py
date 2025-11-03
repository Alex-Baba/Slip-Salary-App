import os
from app.services import archive_service


def test_archive_bytes_writes_file_and_metadata(tmp_path, monkeypatch):
    # Arrange: override archive base to temp dir
    base = tmp_path / 'archives'

    def fake_base():
        return str(base)

    monkeypatch.setattr(archive_service, '_archive_base', fake_base)

    content = b'hello world'
    path = archive_service.archive_bytes(content, 'payslips', 2025, 11, 'test.zip', {'note': 'x'})

    assert os.path.exists(path)
    assert path.endswith('test.zip')
    meta_path = path + '.json'
    assert os.path.exists(meta_path)
    with open(meta_path, 'r', encoding='utf-8') as mf:
        import json
        meta = json.load(mf)
    assert meta['filename'] == 'test.zip'
    assert meta['size_bytes'] == len(content)
