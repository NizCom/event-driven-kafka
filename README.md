
# Order and Cart Service

This project is a microservices-based application for managing orders and carts. It uses Python, Flask, Kafka, and MongoDB to handle order creation, updates, and message processing.

## Features

- **Cart Service**:
  - Create new orders.
  - Update order statuses.
  - Input validation using Pydantic.

- **Order Service**:
  - Consume messages from Kafka.
  - Process orders and update their statuses.
  - Handle errors and send problematic messages to a Dead Letter Queue (DLQ).

- **Kafka Integration**:
  - Topics for `orders` and `dead_letter_queue`.
  - Retry mechanism for Kafka connections.

- **MongoDB**:
  - Store and update order data.

## Technologies Used

- **Languages**: Python
- **Frameworks**: Flask
- **Message Broker**: Kafka
- **Database**: MongoDB
- **Containerization**: Docker, Docker Compose

## Prerequisites

- Docker and Docker Compose installed.
- Python 3.8+ installed (for local development).

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/NizCom/your-repo-name.git
   cd your-repo-name
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up --build
   ```

3. Access the services:
   - **Cart Service**: `http://localhost:5000`
   - **Order Service**: `http://localhost:8080`

## API Endpoints

### Cart Service

- **Create Order**: `POST /create-order`
  - Request Body:
    ```json
    {
      "orderId": "string",
      "itemsNum": 1
    }
    ```

- **Update Order**: `PUT /update-order`
  - Request Body:
    ```json
    {
      "orderId": "string",
      "status": "pending" | "confirmed"
    }
    ```

### Order Service

- **Order Details**: `GET /order-details`
  - Query Params: `orderId`

- **Get Order IDs by Topic Name**: `GET /getAllOrderIdsFromTopic`
  - Query Params: `topic_name`

## Environment Variables

- `FLASK_APP`: Entry point for Flask applications.
- `FLASK_RUN_HOST`: Host for Flask to run on.
- `FLASK_RUN_PORT`: Port for Flask to run on.

## Kafka Topics

- `orders`: Handles all order-related actions, including creating and updating orders.
- `dead_letter_queue`: Stores messages that failed processing due to errors, allowing for debugging.

## Error Handling

- **Connection Errors**: Automatically retrying with exponential backoff to handle transient failures.
- **Message Delivery Failures**: Logs the error and retries with backoff.
- **Topic Not Found**: Exception raised to the user. Topics are pre-created in the `docker-compose.yml` file.
- **Value Errors in Messages**: Logs the error and stores the message in the `dead_letter_queue` topic for debugging.


