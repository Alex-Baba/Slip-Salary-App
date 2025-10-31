from django.db import models


class Employee(models.Model):
    email = models.CharField(max_length=50, unique=True)
    password = models.CharField(max_length=256)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    # Romanian CNP: 13 digits. We enforce length & digits only (no checksum for now).
    cnp = models.CharField(max_length=13, unique=True)
    role = models.ForeignKey('app.EmployeeRole', on_delete=models.PROTECT)
    manager = models.ForeignKey('self', related_name='subordinates', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey('app.Department', on_delete=models.SET_NULL, null=True, blank=True)
    base_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    expected_working_days = models.IntegerField(null=True, blank=True, default=22, help_text="Override default business days for proration (default 22)")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

