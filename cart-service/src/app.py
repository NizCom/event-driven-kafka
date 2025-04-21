import json
from urllib import request
from flask import Flask, request, jsonify
from pydantic import BaseModel, ValidationError, Field
from typing import Literal
from confluent_kafka.cimpl import KafkaException
from werkzeug.exceptions import NotFound
from src.utils.kafka_connection import produce_message_to_kafka
from src.utils.order import Order


app = Flask(__name__)


class CreateOrderModel(BaseModel):
    orderId: str
    itemsNum: int = Field(..., ge=1, description="Number of items must be at least 1")


class UpdateOrderModel(BaseModel):
    orderId: str
    status: Literal['pending', 'confirmed']


@app.route('/create-order', methods=['POST'])
def create_order():
    try:
        data = request.get_json()
        validated_data = CreateOrderModel(**data)
        new_order = Order(validated_data.orderId, validated_data.itemsNum)
        new_order_json_str = json.dumps(new_order.to_dict(), indent=4)
        produce_message_to_kafka(new_order_json_str, validated_data.orderId)

        return jsonify({
            "message": "OK",
            "data": validated_data.model_dump()
        }), 201

    except ValidationError as e:
        error_details = e.errors()
        msg = error_details[0]["msg"]
        error_message = {
                "error": "Validation Error",
                "message": msg
            }

        if "unable to parse string as an integer" in msg:
            error_message["required_structure"] = {
                "orderId": "str",
                "itemsNum": "int"
            }

        return jsonify(error_message), 400
    except KafkaException as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/update-order', methods=['PUT'])
def update_order():
    try:
        data = request.get_json()
        validated_data = UpdateOrderModel(**data)
        validated_data_str = json.dumps(validated_data.model_dump())
        produce_message_to_kafka(validated_data_str, validated_data.orderId)

        return jsonify({
            "message": "OK",
            "data": validated_data.model_dump()
        }), 200

    except ValidationError as e:
        return jsonify({
            "error": "Validation error",
            "message": str(e)
        }), 400

    except NotFound as e:
        return jsonify({"error": str(e)}), 404
    except KafkaException as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": "Internal Server Error", "message": str(e)}), 500


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"OK": True}), 200