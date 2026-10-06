import uuid
from datetime import datetime, timezone
from typing import Optional, Dict, Any

from floodguard.config import settings
from floodguard.schemas.common import GeoBoundingBox
from floodguard.schemas.forecast import (
    RainfallForecastResult,
    FloodInundationGeoJSON,
    Step2ForecastInundationResult
)
from floodguard.services.engine import ingestion_engine
from floodguard.storage.buffer import storage_buffer
from floodguard.storage.spatial_db import spatial_db
from floodguard.models.rainfall_forecast import rainfall_engine
from floodguard.models.inundation_unet import unet_engine


class ForecastInundationPipelineService:
    """
    Orchestration service for FloodGuard Step 2: Forecast & Inundation Modeling.
    Glues Step 1 data ingestion outputs with Step 2 AI/ML forecasting models
    and PostGIS spatial vector database storage.
    """

    def __init__(self):
        self.rainfall_engine = rainfall_engine
        self.unet_engine = unet_engine
        self.spatial_db = spatial_db
        self.latest_result: Optional[Step2ForecastInundationResult] = None

    async def execute_forecast_pipeline(
        self,
        storm_intensity: float = 1.0,
        custom_bbox: Optional[GeoBoundingBox] = None
    ) -> Step2ForecastInundationResult:
        """
        Executes complete Step 2 pipeline:
        1. Ingests or retrieves latest Step 1 Unified Telemetry Frame.
        2. Forecasts 72-hr rainfall using LSTM/GRU/Transformer + NWP bias correction.
        3. Transforms rainfall into surface runoff via SCS-CN.
        4. Runs U-Net CNN segmentation over DEM to map flood polygons.
        5. Persists GeoJSON polygons into PostGIS spatial database.
        """
        now = datetime.now(timezone.utc)
        exec_id = f"EXEC_STEP2_{now.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:4].upper()}"

        # 1. Fetch latest Step 1 telemetry frame or trigger fresh cycle
        telemetry = storage_buffer.get_latest_frame()
        if not telemetry:
            telemetry = await ingestion_engine.run_unified_ingestion_cycle(storm_intensity=storm_intensity)

        # 2. Run Rainfall Forecasting
        rf_result: RainfallForecastResult = self.rainfall_engine.forecast_72h(
            latest_telemetry=telemetry,
            custom_bbox=custom_bbox,
            intensity_factor=storm_intensity
        )

        # 3. Run Inundation Segmentation on DEM
        dem_payload = telemetry.dem_terrain
        inundation_result: FloodInundationGeoJSON = self.unet_engine.segment_inundation_zones(
            rainfall_accumulation_72h_mm=rf_result.total_accumulated_72h_mm,
            dem_data=dem_payload,
            bbox=custom_bbox
        )

        # 4a. Persist rainfall forecast summary into PostGIS
        self.spatial_db.store_rainfall_forecast_summary(
            forecast_id=rf_result.forecast_id,
            peak_rain=rf_result.peak_hourly_rain_mm,
            acc_rain=rf_result.total_accumulated_72h_mm,
            basin=rf_result.basin_name
        )

        # 4b. Store vectorized flood polygons into PostGIS spatial store
        records_stored = self.spatial_db.store_flood_inundation(inundation_result)

        # 5. Evaluate alert summary
        if inundation_result.critical_inundation_area_km2 > 100.0 or rf_result.peak_hourly_rain_mm > 50.0:
            summary = "CRITICAL: Severe flood inundation detected. Red alert triggered for low-lying floodplains."
        elif inundation_result.critical_inundation_area_km2 > 40.0:
            summary = "WARNING: Moderate-to-high inundation anticipated along primary river drainage corridors."
        else:
            summary = "WATCH: Localized low-risk water logging; minor runoff across drainage basins."

        result = Step2ForecastInundationResult(
            execution_id=exec_id,
            timestamp=now,
            rainfall_forecast=rf_result,
            inundation_geojson=inundation_result,
            spatial_db_stored=True,
            postgis_records_count=records_stored,
            postgis_table_name=self.spatial_db.table_name,
            alert_summary=summary
        )

        self.latest_result = result
        return result

    async def execute_synthetic_fallback_pipeline(
        self, storm_intensity: float = 1.0
    ) -> Step2ForecastInundationResult:
        """
        Synthetic Fallback Pipeline – Demo-safe mode.
        Uses pre-calibrated synthetic rainfall and DEM data when live satellite/IMD feeds
        are unavailable. Ensures the system always returns valid GeoJSON flood outputs.
        """
        # Synthetic rainfall values representative of Mahanadi monsoon climatology
        rf_result = self.rainfall_engine.forecast_72h(intensity_factor=storm_intensity)

        # Synthetic DEM-based inundation using typical catchment flood depth
        inundation_result = self.unet_engine.segment_inundation_zones(
            rainfall_accumulation_72h_mm=rf_result.total_accumulated_72h_mm
        )

        self.spatial_db.store_rainfall_forecast_summary(
            forecast_id=rf_result.forecast_id + "_SYNTHETIC",
            peak_rain=rf_result.peak_hourly_rain_mm,
            acc_rain=rf_result.total_accumulated_72h_mm,
            basin="Mahanadi Catchment [Synthetic]"
        )
        records_stored = self.spatial_db.store_flood_inundation(inundation_result)

        now = datetime.now(timezone.utc)
        return Step2ForecastInundationResult(
            execution_id=f"SYNTHETIC_{now.strftime('%Y%m%d_%H%M%S')}",
            timestamp=now,
            rainfall_forecast=rf_result,
            inundation_geojson=inundation_result,
            spatial_db_stored=True,
            postgis_records_count=records_stored,
            postgis_table_name=self.spatial_db.table_name,
            alert_summary="[SYNTHETIC DEMO] Pre-calibrated catchment flood scenario – live feeds temporarily unavailable."
        )

    def get_model_health_status(self) -> Dict[str, Any]:
        """
        /api/v1/forecast/status endpoint data provider.
        Reports health of all Step 2 AI/ML model components.
        """
        from floodguard.models.registry import model_registry
        from floodguard.models.validation import validation_engine
        import json, pathlib

        # Load NWP config
        nwp_config_path = pathlib.Path("floodguard/config/nwp_bias_config.json")
        try:
            nwp_config = json.loads(nwp_config_path.read_text())
            nwp_status = "LOADED"
            nwp_version = nwp_config.get("version", "unknown")
        except Exception:
            nwp_status = "CONFIG_NOT_FOUND"
            nwp_version = "N/A"

        catalog = model_registry.get_model_catalog()
        db_polygon_count = self.spatial_db.count_total_polygons()
        rf_summary = self.spatial_db.get_latest_rainfall_forecast_summary()

        return {
            "service": "FloodGuard Step 2 Forecast & Inundation Modeling Engine",
            "status": "OPERATIONAL",
            "components": {
                "rainfall_forecasting": {
                    "status": "READY",
                    "architecture": "LSTM / GRU / Transformer Ensemble",
                    "transfer_learning": self.rainfall_engine.apply_transfer_learning_adaptation(),
                    "checkpoint": catalog["models"]["rainfall_forecasting"]
                },
                "inundation_mapping": {
                    "status": "READY",
                    "architecture": "CNN / U-Net Segmentation on DEM (ResNet-34)",
                    "tile_inference": self.unet_engine.run_tile_based_inference(),
                    "checkpoint": catalog["models"]["flood_inundation"]
                },
                "nwp_bias_correction": {
                    "status": nwp_status,
                    "config_version": nwp_version,
                    "providers": ["ECMWF_IFS", "NOAA_GFS", "NCMRWF_UM"]
                },
                "postgis_spatial_database": {
                    "status": "CONNECTED",
                    "total_flood_polygons_stored": db_polygon_count,
                    "latest_rainfall_forecast": rf_summary
                },
                "model_weight_registry": {
                    "cloud_bucket": catalog["cloud_storage"]["primary_bucket"],
                    "sync_status": catalog["cloud_storage"]["sync_status"],
                    "encryption": catalog["cloud_storage"]["encryption"]
                },
                "synthetic_fallback": {
                    "status": "READY",
                    "description": "Pre-calibrated synthetic monsoon rainfall pipeline for demo when live feeds fail."
                }
            }
        }

    def get_latest_result(self) -> Optional[Step2ForecastInundationResult]:
        return self.latest_result


# Global pipeline service instance
forecast_service = ForecastInundationPipelineService()
