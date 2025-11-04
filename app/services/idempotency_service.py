import hashlib, json
from typing import Any, Dict, Optional
from django.db import transaction
from app.db.models import IdempotencyRecord

def _hash_payload(payload: Dict[str, Any]) -> str:
    # Deterministic JSON serialization
    data = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()

@transaction.atomic
def get_or_create_idempotent(endpoint: str, key: str, request_payload: Dict[str, Any], response_builder, owner=None) -> Dict[str, Any]:
    """Return existing stored response if key exists & payload matches; otherwise create.

    response_builder: callable returning fresh response dict if not cached.
    """
    payload_hash = _hash_payload(request_payload)
    try:
        qs = IdempotencyRecord.objects.select_for_update().filter(endpoint=endpoint, key=key)
        if owner is None:
            qs = qs.filter(owner__isnull=True)
        else:
            qs = qs.filter(owner=owner)
        record = qs.get()
        if record.request_hash != payload_hash:
            # Payload changed under same key -> treat as conflict
            return {
                "idempotent": False,
                "conflict": True,
                "error": "Idempotency-Key reused with different payload",
                "stored_request_hash": record.request_hash,
                "incoming_request_hash": payload_hash,
            }
        record.last_accessed = record.last_accessed  # touch via save at end if needed
        return {"idempotent": True, "cached": True, "data": record.response_json}
    except IdempotencyRecord.DoesNotExist:
        fresh = response_builder()
        record = IdempotencyRecord(
            endpoint=endpoint,
            key=key,
            owner=owner,
            request_hash=payload_hash,
            response_json=fresh,
        )
        record.save()
        return {"idempotent": False, "cached": False, "data": fresh}

__all__ = ["get_or_create_idempotent"]
