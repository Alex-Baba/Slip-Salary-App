from django.apps import AppConfig as DjangoAppConfig
import os
from django.db.utils import OperationalError


class AppConfig(DjangoAppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app'

    def ready(self):
        """Seed an admin user from environment variables if not present.

        Environment variables (example):
        ADMIN_EMAIL, ADMIN_PASSWORD (plain for now; ideally hashed beforehand or replaced with a hash),
        ADMIN_FIRST_NAME, ADMIN_LAST_NAME, ADMIN_CNP, ADMIN_DEPARTMENT.
        Department is optional; will create if missing.
        Safe to run multiple times; uses get_or_create semantics.
        """
        from django.conf import settings
        if getattr(settings, 'TESTING', False):
            return  # Skip in tests if flagged
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_first = os.getenv('ADMIN_FIRST_NAME', 'Admin')
        admin_last = os.getenv('ADMIN_LAST_NAME', 'User')
        admin_cnp = os.getenv('ADMIN_CNP')
        admin_dept_name = os.getenv('ADMIN_DEPARTMENT', 'Administration')
        if not (admin_email and admin_password and admin_cnp):
            return  # Not configured
        try:
            from app.db.models import Employee, EmployeeRole, Department
            role_obj, _ = EmployeeRole.objects.get_or_create(role='admin')
            dept_obj, _ = Department.objects.get_or_create(name=admin_dept_name)
            from django.contrib.auth.hashers import make_password, identify_hasher
            raw_pass = admin_password
            # Determine if we need to hash: if user exists and stored password not recognized by Django hasher, re-hash.
            emp, created = Employee.objects.get_or_create(
                email=admin_email,
                defaults={
                    'password': make_password(raw_pass),
                    'first_name': admin_first,
                    'last_name': admin_last,
                    'cnp': admin_cnp,
                    'role': role_obj,
                    'department': dept_obj,
                    'base_salary': 0,
                }
            )
            if not created:
                # Ensure role stays admin in case manual changes happened
                if emp.role != role_obj:
                    emp.role = role_obj
                    emp.save(update_fields=['role'])
                # Upgrade password if raw provided differs or appears unhashed
                needs_hash = False
                try:
                    identify_hasher(emp.password)
                except Exception:
                    needs_hash = True
                if not needs_hash and raw_pass and emp.password == raw_pass:
                    # stored password equals raw string (unhashed)
                    needs_hash = True
                if needs_hash and raw_pass:
                    emp.password = make_password(raw_pass)
                    emp.save(update_fields=['password'])
        except OperationalError:
            # Database not ready (e.g., migrate step). Silently ignore.
            return