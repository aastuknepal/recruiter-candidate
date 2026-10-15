# =============================================================================
# apps/kafka_app/consumer.py  — Candidate Service
# =============================================================================
import json
import logging

from confluent_kafka import Consumer, KafkaError, KafkaException
from django.conf import settings

logger = logging.getLogger(__name__)


def _create_consumer(group_id: str | None = None) -> Consumer:
    return Consumer({
        'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
        'group.id': group_id or settings.KAFKA_CONSUMER_GROUP_ID,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': True,
    })


def run_consumer(topics: list[str], handler_fn) -> None:
    """Block and poll Kafka forever."""
    consumer = _create_consumer()
    consumer.subscribe(topics)
    logger.info("Candidate consumer started. Subscribed to: %s", topics)

    try:
        while True:
            msg = consumer.poll(timeout=1.0)

            if msg is None:
                continue

            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                raise KafkaException(msg.error())

            topic   = msg.topic()
            payload = json.loads(msg.value().decode('utf-8'))

            logger.info("Received message: topic=%s key=%s", topic, msg.key())

            try:
                handler_fn(topic, payload)
            except Exception as exc:
                logger.exception("Handler error for topic=%s: %s", topic, exc)

    except KeyboardInterrupt:
        logger.info("Consumer interrupted — shutting down.")
    finally:
        consumer.close()
        logger.info("Kafka consumer closed.")
