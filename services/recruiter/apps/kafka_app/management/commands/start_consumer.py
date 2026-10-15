from django.core.management.base import BaseCommand

from apps.kafka_app.consumer import run_consumer
from apps.kafka_app.handlers import handle_event
from shared.kafka.topics import KafkaTopics


class Command(BaseCommand):
    help = 'Start the Kafka consumer for the Recruiter service'

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(
                f"Starting Recruiter Kafka consumer...\n"
                f"Listening on topics: {KafkaTopics.RECRUITER_CONSUMES}"
            )
        )
        run_consumer(KafkaTopics.RECRUITER_CONSUMES, handle_event)
