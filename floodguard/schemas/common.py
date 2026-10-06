from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, model_validator


class IngestionStatusEnum(str, Enum):
    SUCCESS = "SUCCESS"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    RUNNING = "RUNNING"


class GeoBoundingBox(BaseModel):
    """Geographic Bounding Box in WGS84 coordinates."""
    min_lat: float = Field(..., ge=-90.0, le=90.0, description="Minimum Latitude")
    max_lat: float = Field(..., ge=-90.0, le=90.0, description="Maximum Latitude")
    min_lon: float = Field(..., ge=-180.0, le=180.0, description="Minimum Longitude")
    max_lon: float = Field(..., ge=-180.0, le=180.0, description="Maximum Longitude")

    @model_validator(mode="after")
    def check_bounds(self):
        if self.min_lat > self.max_lat:
            raise ValueError(f"min_lat ({self.min_lat}) cannot exceed max_lat ({self.max_lat})")
        if self.min_lon > self.max_lon:
            raise ValueError(f"min_lon ({self.min_lon}) cannot exceed max_lon ({self.max_lon})")
        return self


class GeoPoint(BaseModel):
    """Geographic point coordinate."""
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)


class IngestionReceipt(BaseModel):
    """Receipt returned after processing an ingestion batch."""
    source_name: str
    feed_type: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    records_count: int
    status: IngestionStatusEnum
    processing_time_ms: float
    message: str
    metadata: Optional[Dict[str, Any]] = None
