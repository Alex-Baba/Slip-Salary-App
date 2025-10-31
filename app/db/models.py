from django.db import models
from django.utils import timezone


def current_year():
    return timezone.now().year


def current_month():
    return timezone.now().month


class EmployeeRole(models.Model):
    role = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.role


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Employee(models.Model):
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=256)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    # Romanian CNP: 13 digits. We enforce length & digits only (no checksum for now).
    cnp = models.CharField(max_length=13, unique=True)
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT)
    manager = models.ForeignKey('self', related_name='subordinates', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_working_days = models.IntegerField(null=True, blank=True, default=22, help_text="Override default business days for proration (default 22)")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Salary(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"Salary {self.employee_id} {self.date}"


class Attendance(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
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


class Bonus(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()

    def __str__(self):
        return f"Bonus {self.employee_id} {self.amount}"


class IdempotencyRecord(models.Model):
    """Stores idempotent request outcomes keyed by client-provided Idempotency-Key.

    endpoint: canonical path or logical name (e.g. 'send-payslip')
    key: user-supplied idempotency key header value
    request_hash: hash of normalized request payload (avoid returning different responses for same key+different body)
    response_json: saved serialized response dict
    created_at: timestamp
    last_accessed: updated when reused
    """
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


