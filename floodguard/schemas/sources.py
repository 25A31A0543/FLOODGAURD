from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from floodguard.schemas.common import GeoPoint, GeoBoundingBox, IngestionStatusEnum


# ---------------- NASA GPM Satellite Feeds ----------------
class GPMCellPoint(BaseModel):
    lat: float
    lon: float
    precipitation_rate: float = Field(..., description="Rainfall intensity in mm/hr", ge=0.0)
    quality_score: float = Field(default=1.0, ge=0.0, le=1.0)


class GPMSatellitePayload(BaseModel):
    satellite_name: str = "GPM Core Observatory"
    product_version: str = "IMERG-Early-V07"
    granule_id: str
    acquisition_time: datetime
    bbox: GeoBoundingBox
    mean_precipitation_mm_hr: float = Field(..., ge=0.0)
    max_precipitation_mm_hr: float = Field(..., ge=0.0)
    total_accumulated_volume_m3: float = Field(default=0.0, ge=0.0)
    grid_cells: List[GPMCellPoint] = []
    metadata: Dict[str, Any] = {}


# ---------------- IMD Weather Station Feeds ----------------
class IMDStationObservation(BaseModel):
    station_id: str
    station_name: str
    state: str = "Odisha"
    district: str
    location: GeoPoint
    timestamp: datetime
    rainfall_last_1h_mm: float = Field(default=0.0, ge=0.0)
    rainfall_last_24h_mm: float = Field(default=0.0, ge=0.0)
    temperature_c: float = Field(default=28.0)
    relative_humidity_pct: float = Field(default=85.0, ge=0.0, le=100.0)
    pressure_hpa: float = Field(default=1008.0)
    wind_speed_kmh: float = Field(default=12.0, ge=0.0)
    imd_alert_level: str = Field(default="Green", description="Green, Yellow, Orange, or Red")


class IMDWeatherPayload(BaseModel):
    report_batch_id: str
    timestamp: datetime
    total_stations: int
    stations: List[IMDStationObservation]
    max_station_rain_24h_mm: float
    metadata: Dict[str, Any] = {}


# ---------------- Doppler Weather Radar (DWR) ----------------
class RadarSweep(BaseModel):
    elevation_angle_deg: float
    max_reflectivity_dbz: float
    mean_radial_velocity_ms: float


class DWRVolumeScanPayload(BaseModel):
    radar_station_code: str
    radar_station_name: str
    source_format: str = Field(default="NetCDF4", description="NetCDF4 or HDF5")
    file_name: str
    volume_scan_time: datetime
    radar_location: GeoPoint
    max_range_km: float = 250.0
    sweeps: List[RadarSweep] = []
    peak_reflectivity_dbz: float = Field(..., ge=-30.0, le=95.0)
    storm_severity: str = Field(default="Normal", description="Normal, Moderate, Severe, Convective Cloudburst")
    metadata: Dict[str, Any] = {}


# ---------------- Digital Elevation Models (DEM) ----------------
class DEMTerrainPayload(BaseModel):
    dataset_name: str = "CartoDEM 30m"
    bbox: GeoBoundingBox
    resolution_meters: float = 30.0
    min_elevation_m: float
    max_elevation_m: float
    mean_elevation_m: float
    mean_slope_degrees: float
    flood_susceptibility_index: float = Field(..., ge=0.0, le=1.0, description="Topographical Wetness Index relative score")
    sample_elevation_matrix: Optional[List[List[float]]] = None
    metadata: Dict[str, Any] = {}


# ---------------- Unified Harmonized Telemetry Frame ----------------
class UnifiedTelemetryFrame(BaseModel):
    """
    Standardized multimodal snapshot combining satellite, ground sensors,
    radar volume scans, and topographical characteristics.
    """
    frame_id: str
    timestamp: datetime
    target_catchment: str
    bbox: GeoBoundingBox
    gpm_satellite: Optional[GPMSatellitePayload] = None
    imd_weather: Optional[IMDWeatherPayload] = None
    dwr_radar: Optional[DWRVolumeScanPayload] = None
    dem_terrain: Optional[DEMTerrainPayload] = None
    composite_rainfall_rate_mm_hr: float = Field(default=0.0, ge=0.0)
    flood_warning_grade: str = Field(default="NORMAL", description="NORMAL, WATCH, WARNING, SEVERE EMERGENCY")
    engine_status: IngestionStatusEnum = IngestionStatusEnum.SUCCESS
