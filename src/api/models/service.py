from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class ServiceBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class ServiceCreate(ServiceBase):
    pass

class ServiceResponse(ServiceBase):
    id: str
    created_at: datetime
    owner_id: str
    
    class Config:
        from_attributes = True

class MetricBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None

class MetricCreate(MetricBase):
    service_id: str

class MetricReading(BaseModel):
    value: float
    timestamp: Optional[datetime] = None  # If not provided, current time will be used

class MetricReadingResponse(MetricReading):
    id: str
    
    class Config:
        from_attributes = True

class MetricResponse(MetricBase):
    id: str
    service_id: str
    latest_reading: Optional[MetricReadingResponse] = None
    
    class Config:
        from_attributes = True

class AnomalyDetectionRequest(BaseModel):
    service_id: str
    metric_name: str
    time_window_seconds: int = 600  # Default 10 minutes
    sigma_threshold: float = 3.0  # Default 3 standard deviations

class AnomalyDetectionResponse(BaseModel):
    timestamp: datetime
    value: float
    window_mean: float
    window_std_dev: float
    is_anomaly: bool