
from src.app import app
import threading
from src.connections.kafka_connection import consume_messages

if __name__ == '__main__':
    # Start the Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=consume_messages, daemon=True)
    consumer_thread.start()

    # Run the Flask app
    app.run(host='0.0.0.0', port=8080)
