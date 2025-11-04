from django.db import models


class IdempotencyRecord(models.Model):
    """Stores idempotent request outcomes keyed by client-provided Idempotency-Key."""
    endpoint = models.CharField(max_length=100)
    key = models.CharField(max_length=200)
    # Optional owner to scope idempotency keys per user/employee
    owner = models.ForeignKey('app.Employee', on_delete=models.CASCADE, null=True, blank=True)
    request_hash = models.CharField(max_length=64)
    response_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        # Scope uniqueness by owner so different users can reuse the same Idempotency-Key
        unique_together = ("endpoint", "key", "owner")

    def __str__(self):
        owner_part = f":{self.owner_id}" if self.owner_id else ""
        return f"Idem {self.endpoint}:{self.key}{owner_part}"

