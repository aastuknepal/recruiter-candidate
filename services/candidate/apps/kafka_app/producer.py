# =============================================================================
# apps/kafka_app/producer.py  — Candidate Service
# =============================================================================
import json
import logging

from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def _get_producer() -> Producer:
    global _producer
    if _producer is None:
        _producer = Producer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'candidate-service',
        })
    return _producer


def _delivery_report(err, msg):
    if err is not None:
        logger.error("Kafka delivery failed: topic=%s err=%s", msg.topic(), err)
    else:
        logger.debug(
            "Kafka message delivered: topic=%s partition=%s offset=%s",
            msg.topic(), msg.partition(), msg.offset(),
        )


def publish(topic: str, key: str, payload: dict) -> None:
    """Publish a JSON message to a Kafka topic."""
    producer = _get_producer()
    producer.produce(
        topic=topic,
        key=key.encode('utf-8'),
        value=json.dumps(payload).encode('utf-8'),
        callback=_delivery_report,
    )
    producer.flush()
    logger.info("Published to topic=%s key=%s", topic, key)
