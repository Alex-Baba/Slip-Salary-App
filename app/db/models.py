from django.db import models

# EmployeeRole model for roles: employee, manager, admin

class EmployeeRole(models.Model):
	id = models.AutoField(primary_key=True)
	role = models.CharField(max_length=20, unique=True)


class Manager(models.Model):
    id=models.AutoField(primary_key=True)
    department=models.CharField(max_length=50)
    employees=models.ManyToManyField('Users', related_name='managers')


class Employee(models.Model):
    id=models.AutoField(primary_key=True)
    email=models.CharField(max_length=50, unique=True)
    password=models.CharField(max_length=256)
    first_name=models.CharField(max_length=30)
    last_name=models.CharField(max_length=30)
    cnp=models.CharField(max_length=1000, unique=True)
    role=models.ForeignKey(EmployeeRole, on_delete=models.CASCADE)
    manager=models.ForeignKey(Manager, on_delete=models.CASCADE, null=True, blank=True)


class Salary(models.Model):
    id=models.AutoField(primary_key=True)
    employee=models.ForeignKey(Employee, on_delete=models.CASCADE)
    amount=models.DecimalField(max_digits=10, decimal_places=2)
    date=models.DateField()


# trebuie sa te mai gandesti ucm faci
class Attendance(models.Model):
    id=models.AutoField(primary_key=True)
    employee=models.ForeignKey(Employee, on_delete=models.CASCADE)
    working_days=models.IntegerField()
    leave_days=models.IntegerField()


