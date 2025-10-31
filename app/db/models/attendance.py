from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


def current_month():
    return timezone.now().month


class Attendance(models.Model):
    employee = models.ForeignKey('app.Employee', on_delete=models.CASCADE)
    working_days = models.IntegerField()
    leave_days = models.IntegerField()
    # Temporarily provide defaults so existing rows can be migrated without prompt.
    # After data clean-up you can remove defaults or enforce uniqueness.
    year = models.IntegerField(default=current_year)
    month = models.IntegerField(default=current_month)

    def __str__(self):
        return f"Attendance {self.employee_id}"

    class Meta:
        unique_together = ("employee", "year", "month")

