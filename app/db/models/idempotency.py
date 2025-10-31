from django.db import models


class IdempotencyRecord(models.Model):
    """Stores idempotent request outcomes keyed by client-provided Idempotency-Key."""
    endpoint = models.CharField(max_length=100)
    key = models.CharField(max_length=200)
    request_hash = models.CharField(max_length=64)
    response_json = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_accessed = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("endpoint", "key")

    def __str__(self):
        return f"Idem {self.endpoint}:{self.key}"

