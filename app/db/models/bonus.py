from django.db import models


class Bonus(models.Model):
    employee = models.ForeignKey('app.Employee', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()

    def __str__(self):
        return f"Bonus {self.employee_id} {self.amount}"

