import json

from confluent_kafka.cimpl import Consumer, KafkaException, KafkaError, Producer
import time
import sys
from src.utils.logger import logger
from .mongodb_connection import save_order_in_db, update_order_in_db
from werkzeug.exceptions import NotFound

KAFKA_BROKER = 'kafka:9092'
ORDERS_TOPIC = 'orders'
DEAD_LETTER_QUEUE = 'dead_letter_queue'
STATUS_NEW = 'new'
STATUS_PENDING = 'pending'
STATUS_CONFIRMED = 'confirmed'


consumer_config = {
    'bootstrap.servers': KAFKA_BROKER,
    'group.id': 'order-service-group',
    'enable.auto.commit': False,
    'auto.offset.reset': 'latest',
    'retries': 0,
}


dlq_producer_config = {
    'bootstrap.servers': KAFKA_BROKER,
    'enable.idempotence': True
}

MAX_RETRIES = 5  # Maximum number of retry attempts
RETRY_DELAY = 5  # Delay between retries in seconds
dlq_producer = None


def connect_to_kafka():
    global dlq_producer
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            consumer = Consumer(consumer_config)
            metadata = consumer.list_topics(timeout=5)
            dlq_producer = Producer(dlq_producer_config)
            metadata = dlq_producer.list_topics(timeout=5)
            logger.info("Connected to Kafka")
            return consumer
        except KafkaException as e:
            logger.error(f"Attempt {attempt}/{MAX_RETRIES} failed: {e}")
            if attempt < MAX_RETRIES:
                logger.info(f"Retrying in {RETRY_DELAY} seconds...")
                time.sleep(RETRY_DELAY)
            else:
                logger.critical("Max retries reached. Exiting...")
                sys.exit(1)


def consume_messages():
    consumer = connect_to_kafka()
    if consumer is None:
        return

    try:
        consumer.subscribe([ORDERS_TOPIC])
        while True:
            exception_occurred = False  # Flag to track exceptions
            try:
                msg = consumer.poll(1.0)

                if msg is None:
                    logger.info("Waiting for message...")
                elif msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.info(f"End of partition reached {msg.partition()}")
                    else:
                        raise KafkaException(msg.error())
                else:
                    msg_key = msg.key().decode('utf-8') if msg.key() else None
                    if msg_key is None:
                        raise ValueError("Message key is missing")

                    logger.info(f"Order received with message key: '{msg_key}'")
                    process_message(msg)
                    consumer.commit()
                    logger.info(f"ACK sent for message with key: '{msg_key}'")

            except (ValueError, NotFound) as e:
                logger.error(f"Error processing message: {e}")
                exception_occurred = True
                error_reason = str(e)
            except KafkaException as e:
                logger.error(f"Kafka error: {e}")
                exception_occurred = True
                error_reason = str(e)
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                exception_occurred = True
                error_reason = str(e)

            time.sleep(0.1)

            if exception_occurred:
                send_to_dead_letter_queue(msg, error_reason)

    except KeyboardInterrupt:
        logger.warning("Consumer interrupted by user.")
    finally:
        consumer.close()


def process_message(msg):
    msg_value = json.loads(msg.value().decode('utf-8'))
    status = msg_value['status']

    if status == STATUS_NEW:
        create_new_order(msg_value, msg.topic())
    elif status == STATUS_PENDING or status == STATUS_CONFIRMED:
        update_order(msg_value)
    else:
        raise ValueError(f"Unexpected status: {status}")


def create_new_order(msg_value, topic):
    order = msg_value
    order['shippingCost'] = calculate_shipping_cost(order['totalAmount'])
    order['topic_name'] = topic

    save_order_in_db(order)
    del order['_id']  # No need for '_id' field from MongoDB
    logger.info(f"Order stored with ID {order['orderId']}."
                f" Order details: {json.dumps(order, indent=4)}")


def calculate_shipping_cost(total_amount: float) -> float:
    shipping_cost = total_amount * 0.02
    return round(shipping_cost, 2)


def update_order(msg_value):
    order_id = msg_value.get("orderId")
    status = msg_value.get("status")
    update_order_in_db(order_id, status)
    logger.info(f"Order ID: {order_id} was successfully updated to status: '{status}'")


def send_to_dead_letter_queue(msg, error_reason):
    try:
        dlq_message = {
            "original_key": msg.key().decode('utf-8') if msg.key() else None,
            "original_value": msg.value().decode('utf-8'),
            "error": error_reason
        }

        dlq_producer.produce(DEAD_LETTER_QUEUE, key=msg.key(), value=json.dumps(dlq_message))
        logger.info("Message sent to dead_letter_queue")
    except Exception as e:
        logger.error(f"Failed to send to dead_letter_queue: {e}")