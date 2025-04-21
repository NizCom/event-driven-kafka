from flask import Flask, request, jsonify
from src.connections.mongodb_connection import get_order_by_id, get_all_orders_by_topic_name

app = Flask(__name__)


@app.route('/order-details', methods=['GET'])
def get_order_details():
    try:
        order_id = request.args.get('orderId')

        if not order_id:
            raise ValueError("Missing 'orderId' query parameter.")

        order = get_order_by_id(order_id)

        return jsonify({
            "order details": order
        }), 200

    except (KeyError, TypeError) as e:
        return jsonify({
            "error": "Validation Error",
            "message": str(e)
        }), 400

    except ValueError as e:
        return jsonify({
            "error": "Order Error",
            "message": str(e)
        }), 404

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/getAllOrderIdsFromTopic', methods=['GET'])
def get_all_orders_from_topic():
    try:
        topic_name = request.args.get('topic_name')

        if not topic_name:
            raise ValueError("Missing 'topic_name' query parameter.")

        order_ids = get_all_orders_by_topic_name(topic_name)

        if not order_ids:
            return jsonify({"message": f"No orderIds found for topic '{topic_name}'"}), 404

        return jsonify({"orderIds": order_ids}), 200

    except (KeyError, TypeError) as e:
        return jsonify({
            "error": "Validation Error",
            "message": str(e)
        }), 400

    except ValueError as e:
        return jsonify({
            "error": "Topic Error",
            "message": str(e)
        }), 404

    except Exception as e:
        return jsonify({
            "error": "Internal Server Error",
            "message": str(e)
        }), 500


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"OK": True}), 200
