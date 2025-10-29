from django.db import models


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
    cnp = models.CharField(max_length=1000, unique=True)
    role = models.ForeignKey(EmployeeRole, on_delete=models.PROTECT)
    manager = models.ForeignKey('self', related_name='subordinates', on_delete=models.SET_NULL, null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)


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

    def __str__(self):
        return f"Attendance {self.employee_id}"


class Bonus(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.CharField(max_length=255)
    date = models.DateField()

    def __str__(self):
        return f"Bonus {self.employee_id} {self.amount}"