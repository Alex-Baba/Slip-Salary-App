from django.db import models


class EmployeeRole(models.Model):
    role = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.role

