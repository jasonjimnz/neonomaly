# Neonomaly API

A REST API for anomaly detection in server metrics, built with FastAPI and Neo4j.

## Features

- Service management (create, list services)
- Metrics tracking (create metrics, add readings, list metrics)
- Anomaly detection based on statistical methods

## Tech Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Neo4j**: Graph database for storing users, services, metrics, and time-series data
- **Docker**: Containerization for easy deployment

## Setup

### Prerequisites

- Docker and Docker Compose
- Python 3.9+

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jasonjimnz/neonomaly.git
   cd neonomaly
   ```

2. Start the services using Docker Compose:
   ```bash
   docker-compose up -d
   ```

3. The API will be available at http://localhost:8000

### Manual Setup (without Docker)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run the API:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

3. Having your Neo4J instance running, hop over http://127.0.0.1:7474/browser/ and run
 the following Cypher query for having a user in database:
```cypher
CREATE (u:User{id: "1"})
```

## API Documentation

Once the API is running, you can access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API Endpoints


### Services
- `POST /api/services`: Create a new service
- `GET /api/services`: List all services
- `GET /api/services/{service_id}`: Get a specific service

### Metrics
- `POST /api/metrics`: Create a new metric
- `GET /api/metrics/service/{service_id}`: List metrics for a service
- `POST /api/metrics/{metric_id}/readings`: Add a reading for a metric
- `POST /api/metrics/anomaly-detection`: Detect anomalies in a metric

## Data Model

The API uses a graph data model in Neo4j:

- **User**: Represents a user of the system
- **Service**: Represents a server or service being monitored
- **Metric**: Represents a type of metric for a service (e.g., CPU usage)
- **MetricReading**: Represents a single data point at a specific time

### Relationships

- `[:OWNS]`: Connects a User to a Service
- `[:MONITORS]`: Connects a Service to a Metric
- `[:LATEST_READING]`: Points from a Metric to its most recent MetricReading
- `[:NEXT]`: Connects one MetricReading to the next in chronological order