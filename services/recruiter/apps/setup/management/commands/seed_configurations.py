"""
Seed command for configurations.
Usage: python manage.py seed_configurations
"""

from apps.setup.models import Configuration
from django.core.management import BaseCommand


class Command(BaseCommand):
    """
    Command to seed the Configuration model with default settings.
    Usage: python manage.py seed_configurations
    """

    def handle(self, *args, **options):
        CONFIGS = [
            # Dev Configuration
            {
                "name": "Allow Debug Toolbar for permissioned users",
                "display_name": "Allow Debug Toolbar",
                "config_key": "allow_debug_toolbar",
                "value": "False",
                "config_type": "boolean",
                "description": "Allow access to the debug toolbar for permissioned users",
            },
            {
                "name": "Allow Swagger Docs URL",
                "display_name": "Allow Swagger Docs URL",
                "config_key": "allow_swagger_url",
                "value": "False",
                "config_type": "boolean",
                "description": "Allow access to the Swagger docs URL",
            },
        ]

        for config in CONFIGS:
            obj, created = Configuration.objects.get_or_create(
                config_key=config["config_key"],
                defaults=config
            )

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created {obj.config_key}"))

        self.stdout.write(self.style.SUCCESS(
            "Configuration seeding completed."))
