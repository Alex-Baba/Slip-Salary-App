from django.db import models
from django.utils import timezone


class RevokedToken(models.Model):
    token = models.TextField(unique=True)
    revoked_at = models.DateTimeField(default=timezone.now)
    expires_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"RevokedToken(token=<redacted>, revoked_at={self.revoked_at})"


__all__ = ['RevokedToken']
