"""
Seed command for Custom Permissions.
Usage: python manage.py seed_permissions
"""

from apps.users.models import Permissions
from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    Command to seed the Custom Permissions model.
    """

    def handle(self, *args, **options):
        PERMISSIONS = [
            {
                "name": "View Dashboard",
                "key": "dashboard.view",
                "module": "Dashboard",
                "description": "Can view the main dashboard analytics and summaries"
            },

            # ---- User Module ----
            {
                "name": "View Users",
                "key": "users.view",
                "module": "Users",
                "description": "Can view users"
            },
            {
                "name": "Create Users",
                "key": "users.create",
                "module": "Users",
                "description": "Can create users"
            },
            {
                "name": "Edit Users",
                "key": "users.edit",
                "module": "Users",
                "description": "Can edit users"
            },
            {
                "name": "Activate/Deactivate Users",
                "key": "users.activate_deactivate",
                "module": "Users",
                "description": "Can activate/deactivate users"
            },
            {
                "name": "View Roles",
                "key": "users.roles.view",
                "module": "Users",
                "description": "Can view roles"
            },
            {
                "name": "Create Roles",
                "key": "users.roles.create",
                "module": "Users",
                "description": "Can create roles"
            },
            {
                "name": "Edit Roles",
                "key": "users.roles.edit",
                "module": "Users",
                "description": "Can edit roles"
            },
            {
                "name": "Search Roles",
                "key": "users.roles.search",
                "module": "Users",
                "description": "Can search roles"
            },
            # ----- Configurations -----
            {
                "name": "View Configurations",
                "key": "setup.view.configurations",
                "module": "Setup",
                "description": "Can view system configurations"
            },
            {
                "name": "Edit Configurations",
                "key": "setup.edit.configurations",
                "module": "Setup",
                "description": "Can edit system configurations"
            },

            # Developer Tools
            {
                "name": "View Debugger",
                "key": "dev.view.debugger",
                "module": "Dev",
                "description": "Can view developer debugger"
            },
            # ----- API Keys -----
            {
                "name": "View API Keys",
                "key": "setup.view.api_keys",
                "module": "Setup",
                "description": "Can view API keys"
            },
            {
                "name": "Create API Key",
                "key": "setup.create.api_key",
                "module": "Setup",
                "description": "Can create API keys"
            },
            {
                "name": "Edit API Key",
                "key": "setup.edit.api_key",
                "module": "Setup",
                "description": "Can edit API keys"
            },
            {
                "name": "Delete API Key",
                "key": "setup.delete.api_key",
                "module": "Setup",
                "description": "Can delete API keys"
            },
        ]

        for p_data in PERMISSIONS:
            obj, created = Permissions.objects.get_or_create(
                key=p_data["key"],
                defaults=p_data
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created Permission: {obj.key}"))

        self.stdout.write(self.style.SUCCESS(
            "Permission seeding completed successfully."))
