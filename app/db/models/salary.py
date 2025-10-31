from django.db import models


class Salary(models.Model):
    employee = models.ForeignKey('app.Employee', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"Salary {self.employee_id} {self.date}"

