from confluent_kafka.cimpl import Producer, KafkaException
from src.utils.logger import logger
import time

KAFKA_BROKER = 'kafka:9092'
ORDERS_TOPIC = 'orders'
DEAD_LETTER_QUEUE = "dead_letter_queue"
MAX_RETRIES = 5
BACKOFF_FACTOR = 2

config = {
    'bootstrap.servers': KAFKA_BROKER,
    'client.id': 'cart-service-group',
    'retries': 1,
    'retry.backoff.ms': 1000,
    'acks': 'all',
    'enable.idempotence': True
}

producer = None  # Global producer instance


def initialize_producer():
    global producer

    for attempt in range(MAX_RETRIES):
        try:
            producer = Producer(config)
            metadata = producer.list_topics(timeout=5)
            logger.info("Connected to Kafka")
            break

        except KafkaException as e:
            logger.error(f"Failed to connect to Kafka (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")
        except Exception as e:  # Catch other exceptions (e.g., network errors)
            logger.error(f"Unexpected error while connecting to Kafka: {e}")

        if attempt < MAX_RETRIES - 1:
            sleep_time = BACKOFF_FACTOR ** attempt  # Exponential backoff
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.error("Exceeded max retries. Kafka connection failed.")
            producer = None


def produce_message_to_kafka(message: str, message_key: str):
    if producer is None:
        raise KafkaException("Kafka producer is not initialized. Message not sent.")

    for attempt in range(MAX_RETRIES):
        try:
            producer.produce(ORDERS_TOPIC, key=message_key, value=message, callback=delivery_callback)
            producer.flush()
            return  # Message is sent successfully

        except KafkaException as e:
            logger.error(f"Failed to send message (Attempt {attempt + 1}/{MAX_RETRIES}): {e}")

        if attempt < MAX_RETRIES - 1:
            sleep_time = BACKOFF_FACTOR ** attempt
            logger.info(f"Retrying in {sleep_time} seconds...")
            time.sleep(sleep_time)
        else:
            logger.error(f"Exceeded max retries. Message not sent: {message_key}")


def delivery_callback(err, msg):
    if err is not None:
        logger.error(f"Message delivery failed: {err}")
    else:
        logger.info(f"Message delivered to '{msg.topic()}' topic")
