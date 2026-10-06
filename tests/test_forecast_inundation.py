import asyncio
import pytest
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.models.rainfall_forecast import rainfall_engine
from floodguard.models.inundation_unet import unet_engine
from floodguard.storage.spatial_db import spatial_db
from floodguard.services.forecast_service import forecast_service

client = TestClient(app)


def test_rainfall_forecasting_engine():
    result = rainfall_engine.forecast_72h(intensity_factor=1.2)
    assert result.forecast_id.startswith("FCST_")
    assert result.horizon_hours == 72
    assert len(result.time_series) == 72
    assert result.peak_hourly_rain_mm > 0.0
    assert result.total_accumulated_72h_mm >= result.peak_hourly_rain_mm

    # Verify LSTM, GRU, Transformer, NWP components
    p1 = result.time_series[0]
    assert p1.hours_ahead == 1
    assert p1.raw_nwp_rain_mm >= 0.0
    assert p1.lstm_pred_mm >= 0.0
    assert p1.gru_pred_mm >= 0.0
    assert p1.transformer_pred_mm >= 0.0
    assert p1.calibrated_ensemble_rain_mm >= 0.0
    assert p1.uncertainty_bound_mm >= 0.0


def test_scs_cn_runoff_model():
    # Precipitation below initial abstraction gives 0 runoff
    zero_runoff = unet_engine.compute_scs_runoff(precipitation_mm=5.0, curve_number=78.0)
    assert zero_runoff == 0.0

    # High precipitation gives direct runoff
    high_runoff = unet_engine.compute_scs_runoff(precipitation_mm=120.0, curve_number=78.0)
    assert high_runoff > 0.0
    assert high_runoff < 120.0


def test_unet_inundation_segmentation():
    inun = unet_engine.segment_inundation_zones(rainfall_accumulation_72h_mm=140.0)
    assert inun.type == "FeatureCollection"
    assert inun.inundation_run_id.startswith("INUND_")
    assert inun.total_inundated_area_km2 > 0.0
    assert inun.max_depth_recorded_m > 0.0
    assert len(inun.features) == 4

    risk_levels = [f.properties.risk_level for f in inun.features]
    assert "Extreme Inundation" in risk_levels
    assert "High" in risk_levels
    assert "Moderate" in risk_levels
    assert "Low" in risk_levels

    # Check valid closed GeoJSON polygon ring
    for f in inun.features:
        coords = f.geometry.coordinates[0]
        assert len(coords) >= 4
        # First point equals last point
        assert coords[0] == coords[-1]


def test_postgis_spatial_storage():
    inun = unet_engine.segment_inundation_zones(rainfall_accumulation_72h_mm=160.0)
    records = spatial_db.store_flood_inundation(inun)
    assert records == 4

    latest = spatial_db.get_latest_inundation()
    assert latest is not None
    assert latest["type"] == "FeatureCollection"
    assert latest["inundation_run_id"] == inun.inundation_run_id
    assert len(latest["features"]) == 4

    total_count = spatial_db.count_total_polygons()
    assert total_count >= 4


def test_step2_forecast_service():
    async def _test():
        res = await forecast_service.execute_forecast_pipeline(storm_intensity=1.3)
        assert res.execution_id.startswith("EXEC_STEP2_")
        assert res.spatial_db_stored is True
        assert res.postgis_records_count == 4
        assert res.rainfall_forecast.total_accumulated_72h_mm > 0.0
        assert res.inundation_geojson.total_inundated_area_km2 > 0.0
        assert "CRITICAL" in res.alert_summary or "WARNING" in res.alert_summary or "WATCH" in res.alert_summary
    asyncio.run(_test())


def test_step2_api_endpoints():
    # 1. 72h Rainfall forecast endpoint
    res_rf = client.post("/api/v1/forecast/rainfall?storm_intensity=1.1")
    assert res_rf.status_code == 200
    assert res_rf.json()["horizon_hours"] == 72
    assert len(res_rf.json()["time_series"]) == 72

    # 2. Inundation mapping endpoint
    res_inun = client.post("/api/v1/forecast/inundation?rainfall_72h_mm=130.0")
    assert res_inun.status_code == 200
    assert res_inun.json()["type"] == "FeatureCollection"
    assert len(res_inun.json()["features"]) == 4

    # 3. Full Step 2 pipeline endpoint
    res_pipe = client.post("/api/v1/forecast/pipeline?storm_intensity=1.2")
    assert res_pipe.status_code == 200
    data = res_pipe.json()
    assert data["spatial_db_stored"] is True
    assert data["postgis_records_count"] == 4

    # 4. Latest forecast endpoint
    res_latest = client.get("/api/v1/forecast/latest")
    assert res_latest.status_code == 200
    assert res_latest.json() is not None

    # 5. Spatial polygons endpoint
    res_poly = client.get("/api/v1/spatial/polygons")
    assert res_poly.status_code == 200
    assert res_poly.json()["type"] == "FeatureCollection"
    assert len(res_poly.json()["features"]) == 4
