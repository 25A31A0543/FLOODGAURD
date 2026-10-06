from datetime import datetime, timezone
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from floodguard.schemas.common import GeoBoundingBox


class RainfallForecastPoint(BaseModel):
    """Hourly forecast point output by the AI/ML ensemble."""
    timestamp: datetime
    hours_ahead: int
    raw_nwp_rain_mm: float = Field(..., ge=0.0, description="Numerical Weather Prediction baseline")
    lstm_pred_mm: float = Field(..., ge=0.0, description="LSTM temporal sequence prediction")
    gru_pred_mm: float = Field(..., ge=0.0, description="GRU sequence prediction")
    transformer_pred_mm: float = Field(..., ge=0.0, description="Transformer multi-head attention prediction")
    bias_correction_offset_mm: float = Field(default=0.0, description="NWP residual bias correction")
    calibrated_ensemble_rain_mm: float = Field(..., ge=0.0, description="Weighted bias-corrected ensemble forecast")
    uncertainty_bound_mm: float = Field(default=0.0, ge=0.0)


class RainfallForecastResult(BaseModel):
    """Ensemble 72-hr rainfall prediction result."""
    forecast_id: str
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    horizon_hours: int = 72
    basin_name: str
    bbox: GeoBoundingBox
    peak_hourly_rain_mm: float
    total_accumulated_72h_mm: float
    time_series: List[RainfallForecastPoint]
    model_weights: Dict[str, float] = {"LSTM": 0.35, "GRU": 0.25, "Transformer": 0.40}
    metadata: Dict[str, Any] = {}


class FloodPolygonProperties(BaseModel):
    """Attributes associated with each vectorized flood inundation polygon."""
    polygon_id: str
    risk_level: str = Field(..., description="Low, Moderate, High, Extreme Inundation")
    mean_depth_meters: float = Field(..., ge=0.0)
    max_depth_meters: float = Field(..., ge=0.0)
    area_sq_km: float = Field(..., ge=0.0)
    estimated_water_volume_m3: float = Field(..., ge=0.0)
    runoff_depth_mm: float = Field(..., ge=0.0)
    color_hex: str = "#ef4444"


class GeoJSONPolygonGeometry(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class GeoJSONFeature(BaseModel):
    type: str = "Feature"
    id: str
    geometry: GeoJSONPolygonGeometry
    properties: FloodPolygonProperties


class FloodInundationGeoJSON(BaseModel):
    """Standard RFC 7946 GeoJSON FeatureCollection storing flood inundation zones."""
    type: str = "FeatureCollection"
    inundation_run_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    basin_name: str
    total_inundated_area_km2: float
    critical_inundation_area_km2: float
    max_depth_recorded_m: float
    features: List[GeoJSONFeature]
    metadata: Dict[str, Any] = {}


class Step2ForecastInundationResult(BaseModel):
    """Unified result packaging Step 2 AI/ML forecasts and PostGIS spatial storage status."""
    execution_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    rainfall_forecast: RainfallForecastResult
    inundation_geojson: FloodInundationGeoJSON
    spatial_db_stored: bool
    postgis_records_count: int
    postgis_table_name: str
    alert_summary: str
