from django.apps import AppConfig


class KafkaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kafka_app'
    label = 'kafka_app'

    def ready(self):
        """
        Called when Django is fully loaded.
        Do NOT start the consumer here — run it via:
            python manage.py start_consumer
        """
        pass
