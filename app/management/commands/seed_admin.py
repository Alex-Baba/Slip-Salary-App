from django.core.management.base import BaseCommand
import os, time
from django.db import OperationalError


class Command(BaseCommand):
    help = "Seed a single admin from environment variables (idempotent). Adds retry support if DB not yet ready."

    def add_arguments(self, parser):
        parser.add_argument('--retries', type=int, default=int(os.getenv('ADMIN_SEED_RETRIES', '5')), help='Number of connection retry attempts if DB unavailable.')
        parser.add_argument('--interval', type=float, default=float(os.getenv('ADMIN_SEED_RETRY_INTERVAL', '2.0')), help='Seconds between retries.')

    def handle(self, *args, **options):
        from app.db.models import Employee, EmployeeRole, Department
        from django.contrib.auth.hashers import make_password, identify_hasher
        retries = options['retries']
        interval = options['interval']
        admin_email = os.getenv('ADMIN_EMAIL')
        admin_password = os.getenv('ADMIN_PASSWORD')
        admin_first = os.getenv('ADMIN_FIRST_NAME', 'Admin')
        admin_last = os.getenv('ADMIN_LAST_NAME', 'User')
        admin_cnp = os.getenv('ADMIN_CNP')
        admin_dept_name = os.getenv('ADMIN_DEPARTMENT', 'Administration')
        if not (admin_email and admin_password and admin_cnp):
            self.stdout.write(self.style.WARNING('Missing required ADMIN_* env vars; aborting'))
            return

        attempt = 0
        while True:
            try:
                role_obj, _ = EmployeeRole.objects.get_or_create(role='admin')
                dept_obj, _ = Department.objects.get_or_create(name=admin_dept_name)
                raw_pass = admin_password
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
                if created:
                    self.stdout.write(self.style.SUCCESS(f"Admin user created: {admin_email}"))
                else:
                    if emp.role != role_obj:
                        emp.role = role_obj
                        emp.save(update_fields=['role'])
                    # Password rotation / upgrade if env changed or stored appears unhashed
                    needs_hash = False
                    try:
                        identify_hasher(emp.password)
                    except Exception:
                        needs_hash = True
                    if not needs_hash and raw_pass and emp.password == raw_pass:
                        needs_hash = True
                    if needs_hash and raw_pass:
                        emp.password = make_password(raw_pass)
                        emp.save(update_fields=['password'])
                        self.stdout.write(self.style.WARNING("Admin password updated (hashed)."))
                    self.stdout.write(self.style.NOTICE(f"Admin user already exists: {admin_email}"))
                break
            except OperationalError as e:
                attempt += 1
                if attempt > retries:
                    self.stdout.write(self.style.ERROR(f"Failed to connect to DB after {retries} retries: {e}"))
                    raise
                self.stdout.write(self.style.WARNING(f"DB not ready (attempt {attempt}/{retries}); retrying in {interval}s"))
                time.sleep(interval)