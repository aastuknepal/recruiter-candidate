from django.apps import AppConfig


class KafkaAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.kafka_app'
    label = 'kafka_app'
