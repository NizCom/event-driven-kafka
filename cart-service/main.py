from src.app import app
from src.utils.kafka_connection import initialize_producer

if __name__ == "__main__":
    initialize_producer()
    app.run(host='0.0.0.0', port=5000)
