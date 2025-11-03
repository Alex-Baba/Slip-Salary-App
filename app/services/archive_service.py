import os
import json
import hashlib
from datetime import datetime
from django.conf import settings
from typing import Dict, Any


def _archive_base() -> str:
    base = getattr(settings, 'MEDIA_ROOT', None) or os.path.join(settings.BASE_DIR, 'media')
    return os.path.join(base, 'archives')


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _sha256_bytes(b: bytes) -> str:
    h = hashlib.sha256()
    h.update(b)
    return h.hexdigest()


def archive_bytes(bytes_content: bytes, subfolder: str, year: int, month: int, filename: str, metadata: Dict[str, Any]) -> str:
    """Write bytes to an archive folder and a companion metadata JSON.

    Returns the path to the archived file (string).
    """
    base = _archive_base()
    dirpath = os.path.join(base, subfolder, f"{year}-{month:02d}")
    _ensure_dir(dirpath)
    path = os.path.join(dirpath, filename)
    with open(path, 'wb') as fh:
        fh.write(bytes_content)
    # compute checksum and size
    checksum = _sha256_bytes(bytes_content)
    size = len(bytes_content)
    # prepare metadata
    meta = {
        'archived_at': datetime.utcnow().isoformat() + 'Z',
        'filename': filename,
        'path': path,
        'checksum_sha256': checksum,
        'size_bytes': size,
    }
    meta.update(metadata or {})
    meta_path = path + '.json'
    with open(meta_path, 'w', encoding='utf-8') as mf:
        json.dump(meta, mf, ensure_ascii=False, indent=2)
    return path


def archive_file_on_disk(src_path: str, subfolder: str, year: int, month: int, filename: str, metadata: Dict[str, Any]) -> str:
    """Copy an existing file into the archive and write metadata. Returns new path."""
    with open(src_path, 'rb') as fh:
        data = fh.read()
    return archive_bytes(data, subfolder, year, month, filename, metadata)
