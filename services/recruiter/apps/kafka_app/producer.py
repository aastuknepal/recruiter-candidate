# =============================================================================
# apps/kafka_app/producer.py  — Recruiter Service
#
# Thin wrapper around confluent-kafka Producer.
# Usage:
#     from apps.kafka_app.producer import publish
#     publish(KafkaTopics.JOB_POSTED, key=str(job.id), payload={...})
# =============================================================================
import json
import logging

from confluent_kafka import Producer
from django.conf import settings

logger = logging.getLogger(__name__)

_producer: Producer | None = None


def _get_producer() -> Producer:
    """Singleton producer — reuse the connection across requests."""
    global _producer
    if _producer is None:
        _producer = Producer({
            'bootstrap.servers': settings.KAFKA_BOOTSTRAP_SERVERS,
            'client.id': 'recruiter-service',
        })
    return _producer


def _delivery_report(err, msg):
    """Callback invoked by confluent-kafka after each produce()."""
    if err is not None:
        logger.error("Kafka delivery failed: topic=%s err=%s", msg.topic(), err)
    else:
        logger.debug(
            "Kafka message delivered: topic=%s partition=%s offset=%s",
            msg.topic(), msg.partition(), msg.offset(),
        )


def publish(topic: str, key: str, payload: dict) -> None:
    """
    Publish a JSON message to a Kafka topic.

    Args:
        topic:   Kafka topic name (use KafkaTopics constants).
        key:     Message key — used for partition routing (e.g., str(job.id)).
        payload: Dictionary to be JSON-serialised as the message value.
    """
    producer = _get_producer()
    producer.produce(
        topic=topic,
        key=key.encode('utf-8'),
        value=json.dumps(payload).encode('utf-8'),
        callback=_delivery_report,
    )
    # flush() makes the call synchronous — remove for high-throughput async
    producer.flush()
    logger.info("Published to topic=%s key=%s", topic, key)
