import time
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from werkzeug.exceptions import NotFound

from src.utils.logger import logger


def get_mongo_client():
    client = None
    while not client:
        try:
            client = MongoClient('mongodb://mongo:27017/')
            logger.info("Connected to MongoDB")
        except ConnectionFailure:
            logger.warning("MongoDB is not ready. Retrying in 5 seconds...")
            time.sleep(5)
    return client


client = get_mongo_client()
db = client['orders_db']
orders_collection = db['orders']


def save_order_in_db(order_to_add):
    existing_order = orders_collection.find_one({'orderId': order_to_add['orderId']})

    if existing_order:
        raise ValueError(f"Order with ID {order_to_add['orderId']} already exists.")

    # Insert the new order if no duplicate is found
    orders_collection.insert_one(order_to_add)
    logger.info(f"Order with ID {order_to_add['orderId']} added successfully.")


def get_order_by_id(order_id: str):
    order = orders_collection.find_one({'orderId': order_id})

    if not order:
        raise ValueError(f"OrderId '{order_id}' does not exist.")

    order.pop('_id', None)

    return order


def get_all_orders_by_topic_name(topic_name: str):
    orders = orders_collection.find({"topic_name": topic_name}, {"_id": 0, "orderId": 1})
    order_ids = [order.get("orderId") for order in orders]

    return order_ids


def update_order_in_db(order_id: str, status: str):
    result = orders_collection.update_one(
        {"orderId": order_id},
        {"$set": {"status": status}}
    )

    if result.matched_count <= 0:
        raise NotFound("Order not found")
