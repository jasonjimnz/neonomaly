import datetime
import uuid
from typing import Any, List

from fastapi import FastAPI, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from api.models.service import ServiceCreate, ServiceResponse, MetricResponse, MetricCreate, MetricReading, \
    AnomalyDetectionResponse, AnomalyDetectionRequest
from db.neo4j import db
from db.cypher import CypherQueriesEnum

app = FastAPI(
    title="Neonomaly API",
    description="API for anomaly detection in server metrics",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Neonomaly API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Services Router
@app.post("/api/services", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(
        service_in: ServiceCreate
) -> Any:
    """
    Create a new service.
    Creates a new service owned by the authenticated user.

    Parameters:
    - **service_in**: Service information including name and optional description

    Returns:
    - Created service information including ID and creation timestamp

    Raises:
    - 401: Not authenticated
    - 500: Failed to create service
    """
    service_id = str(uuid.uuid4())
    params = {
        "user_id": "1",
        "id": service_id,
        "name": service_in.name,
        "description": service_in.description or "",
        "created_at": datetime.datetime.now(datetime.UTC).isoformat()
    }
    result = db.execute_write_query(CypherQueriesEnum.CREATE_SERVICE_QUERY, params)
    if not result or not result[0].get("s"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create service",
        )

    service = result[0]["s"]
    return ServiceResponse(
        id=service["id"],
        name=service["name"],
        description=service["description"],
        created_at=datetime.datetime.fromisoformat(service["created_at"]),
        owner_id="1"
    )


@app.get("/api/services", response_model=List[ServiceResponse])
async def list_services() -> Any:
    """
    List all services owned by the current user.

    Retrieves all services that belong to the authenticated user, ordered by creation date.

    Returns:
    - List of services owned by the user

    Raises:
    - 401: Not authenticated
    """
    result = db.execute_read_query(
        CypherQueriesEnum.LIST_SERVICES_QUERY, {"user_id": "1"}
    )

    services = []
    for item in result:
        service = item["s"]
        services.append(ServiceResponse(
            id=service["id"],
            name=service["name"],
            description=service.get("description", ""),
            created_at=datetime.datetime.fromisoformat(service["created_at"]),
            owner_id="1"
        ))

    return services


@app.get("/api/services/{service_id}", response_model=ServiceResponse)
async def get_service(
        service_id: str
) -> Any:
    """
    Get a specific service by ID.

    Retrieves detailed information about a specific service owned by the authenticated user.

    Parameters:
    - **service_id**: The unique identifier of the service to retrieve

    Returns:
    - Service information including name, description, and creation timestamp

    Raises:
    - 401: Not authenticated
    - 404: Service not found or not owned by the user
    """
    result = db.execute_read_query(CypherQueriesEnum.GET_SERVICE_QUERY, {
        "user_id": "1",
        "service_id": service_id
    })

    if not result or not result[0].get("s"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    service = result[0]["s"]
    return ServiceResponse(
        id=service["id"],
        name=service["name"],
        description=service.get("description", ""),
        created_at=datetime.fromisoformat(service["created_at"]),
        owner_id="1"
    )


@app.post("/api/metrics", response_model=MetricResponse, status_code=status.HTTP_201_CREATED)
async def create_metric(
        metric_in: MetricCreate
) -> Any:
    """
    Create a new metric for a service.

    Creates a new metric type to monitor for a specific service owned by the authenticated user.

    Parameters:
    - **metric_in**: Metric information including name, description, and service_id

    Returns:
    - Created metric information including ID

    Raises:
    - 400: Metric with this name already exists for this service
    - 401: Not authenticated
    - 404: Service not found or not owned by the user
    - 500: Failed to create metric
    """
    # Check if service exists and belongs to the user
    result = db.execute_read_query(CypherQueriesEnum.GET_SERVICE_QUERY, {
        "user_id": "1",
        "service_id": metric_in.service_id
    })

    if not result or not result[0].get("s"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or you don't have access to it",
        )

    # Check if metric with this name already exists for the service
    result = db.execute_read_query(CypherQueriesEnum.CHECK_EXISTING_METRIC, {
        "service_id": metric_in.service_id,
        "name": metric_in.name
    })

    if result and result[0].get("m"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Metric with this name already exists for this service",
        )
    # Create new metric
    metric_id = str(uuid.uuid4())
    params = {
        "service_id": metric_in.service_id,
        "id": metric_id,
        "name": metric_in.name,
        "description": metric_in.description or ""
    }
    result = db.execute_write_query(CypherQueriesEnum.CREATE_METRIC_QUERY, params)

    if not result or not result[0].get("m"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create metric",
        )

    metric = result[0]["m"]
    return MetricResponse(
        id=metric["id"],
        name=metric["name"],
        description=metric["description"],
        service_id=metric_in.service_id
    )


@app.get("/api/metrics/service/{service_id}", response_model=List[MetricResponse])
async def list_metrics(
        service_id: str
) -> Any:
    """
    List all metrics for a service.

    Retrieves all metrics configured for a specific service owned by the authenticated user.

    Parameters:
    - **service_id**: The unique identifier of the service

    Returns:
    - List of metrics with their latest readings (if available)

    Raises:
    - 401: Not authenticated
    - 404: Service not found or not owned by the user
    """
    # Check if service exists and belongs to the user
    result = db.execute_read_query(CypherQueriesEnum.GET_SERVICE_QUERY, {
        "user_id": "1",
        "service_id": service_id
    })

    if not result or not result[0].get("s"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or you don't have access to it",
        )
    # Get all metrics for the service
    result = db.execute_read_query(
        CypherQueriesEnum.GET_METRICS_FROM_SERVICE_QUERY, {"service_id": service_id}
    )
    metrics = []
    for item in result:
        metric = item["m"]
        reading = item.get("r")

        latest_reading = None
        if reading:
            latest_reading = {
                "id": reading.get("id", str(uuid.uuid4())),
                "value": reading["value"],
                "timestamp": datetime.datetime.fromtimestamp(reading["timestamp"] / 1000)  # Convert from milliseconds
            }
        metrics.append(MetricResponse(
            id=metric["id"],
            name=metric["name"],
            description=metric.get("description", ""),
            service_id=service_id,
            latest_reading=latest_reading
        ))
    return metrics


@app.post("/api/metrics/{metric_id}/readings", status_code=status.HTTP_201_CREATED)
async def add_metric_reading(
        metric_id: str,
        reading: MetricReading
) -> Any:
    """
    Add a new reading for a metric.

    Records a new data point for a specific metric, storing it in a linked list structure for efficient time-series analysis.

    Parameters:
    - **metric_id**: The unique identifier of the metric
    - **reading**: The metric reading data including value and optional timestamp

    Returns:
    - Confirmation message

    Raises:
    - 401: Not authenticated
    - 404: Metric not found or not owned by the user
    - 500: Failed to add metric reading
    """
    # Check if metric exists and belongs to a service owned by the user
    result = db.execute_read_query(CypherQueriesEnum.GET_METRIC_READING_SERVICE_QUERY, {
        "user_id": "1",
        "metric_id": metric_id
    })

    if not result or not result[0].get("m"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Metric not found or you don't have access to it",
        )

    service_id = result[0]["service_id"]

    # Add the new reading using the Cypher query from Prompt.md
    timestamp = int(datetime.datetime.now(datetime.UTC).timestamp() * 1000)  # Convert to milliseconds
    if reading.timestamp:
        reading_timestamp: datetime.datetime = reading.timestamp
        timestamp = int(reading_timestamp.timestamp() * 1000)
    reading_id = str(uuid.uuid4())
    result = db.execute_write_query(CypherQueriesEnum.CREATE_METRIC_READING_QUERY, {
        "service_id": service_id,
        "metric_id": metric_id,
        "metric_value": reading.value,
        "timestamp": timestamp,
        "reading_id": reading_id
    })

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add metric reading",
        )

    return {"message": "Metric reading added successfully"}


@app.post("/api/metrics/anomaly-detection", response_model=AnomalyDetectionResponse)
async def detect_anomaly(
        request: AnomalyDetectionRequest
) -> Any:
    """
    Detect anomalies in a metric's readings.

    Analyzes metric readings within a specified time window to detect anomalies using statistical methods.
    Uses the 3-sigma rule (or custom threshold) to identify outliers.

    Parameters:
    - **request**: Anomaly detection parameters including service_id, metric_name, time_window_seconds, and sigma_threshold
    - **current_user**: Authenticated user (automatically injected from token)

    Returns:
    - Anomaly detection results including timestamp, value, window mean, window standard deviation, and anomaly flag

    Raises:
    - 401: Not authenticated
    - 404: Service not found, not owned by the user, or no data found for the metric
    """
    # Check if service exists and belongs to the user
    result = db.execute_read_query(CypherQueriesEnum.GET_SERVICE_QUERY, {
        "user_id": "1",
        "service_id": request.service_id
    })

    if not result or not result[0].get("s"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found or you don't have access to it",
        )

    result = db.execute_read_query(CypherQueriesEnum.CHECK_ANOMALY_DETECTION, {
        "service_id": request.service_id,
        "metric_name": request.metric_name,
        "time_window_seconds": request.time_window_seconds,
        "sigma_threshold": request.sigma_threshold
    })

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No data found for the specified metric",
        )

    data = result[0]

    return AnomalyDetectionResponse(
        timestamp=datetime.datetime.fromtimestamp(data["timestamp"] / 1000),
        value=data["value"],
        window_mean=data["windowMean"],
        window_std_dev=data["windowStdDev"],
        is_anomaly=data["isAnomaly"]
    )
