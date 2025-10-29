from django.core.management.base import BaseCommand
from app.db.models import EmployeeRole


DEFAULT_ROLES = ["employee", "manager", "admin"]


class Command(BaseCommand):
    help = "Seed default employee roles"

    def handle(self, *args, **options):
        created = 0
        for role in DEFAULT_ROLES:
            obj, was_created = EmployeeRole.objects.get_or_create(role=role)
            if was_created:
                created += 1
        self.stdout.write(self.style.SUCCESS(f"Seeded roles. Newly created: {created}"))