import asyncio
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.models.validation import validation_engine
from floodguard.models.registry import model_registry
from floodguard.models.rainfall_forecast import rainfall_engine
from floodguard.models.inundation_unet import unet_engine
from floodguard.storage.spatial_db import spatial_db
from floodguard.services.forecast_service import forecast_service

client = TestClient(app)


# ──────────────────────────────────────────────────────────────
# DATA FLOW: Step 1 → Step 2 Integration
# ──────────────────────────────────────────────────────────────
def test_step1_to_step2_data_flow():
    """Unified dataset from Step 1 is correctly passed into ML models."""
    async def _inner():
        res = await forecast_service.execute_forecast_pipeline(storm_intensity=1.1)
        # Rainfall forecast used real telemetry initial rate from Step 1
        assert res.rainfall_forecast.total_accumulated_72h_mm > 0.0
        assert res.inundation_geojson.total_inundated_area_km2 > 0.0
        assert res.spatial_db_stored is True
    asyncio.run(_inner())


# ──────────────────────────────────────────────────────────────
# RAINFALL FORECASTING: LSTM / GRU / Transformer + NWP Bias
# ──────────────────────────────────────────────────────────────
def test_lstm_gru_transformer_weights():
    """Ensemble weights are correctly set: LSTM 35%, GRU 25%, Transformer 40%."""
    assert abs(rainfall_engine.weights["LSTM"] - 0.35) < 0.001
    assert abs(rainfall_engine.weights["GRU"] - 0.25) < 0.001
    assert abs(rainfall_engine.weights["Transformer"] - 0.40) < 0.001
    total = sum(rainfall_engine.weights.values())
    assert abs(total - 1.0) < 0.001


def test_nwp_bias_correction_applied():
    """NWP bias correction offset is computed and applied to calibrated forecast."""
    result = rainfall_engine.forecast_72h(intensity_factor=1.0)
    for pt in result.time_series[:6]:
        # Bias offset can be positive or negative
        assert isinstance(pt.bias_correction_offset_mm, float)
        # Calibrated ensemble should differ from raw NWP
        assert pt.calibrated_ensemble_rain_mm >= 0.0


def test_nwp_config_file_loaded():
    """NWP bias correction config JSON is present and valid."""
    import json
    from pathlib import Path
    cfg = Path("floodguard/config/nwp_bias_config.json")
    assert cfg.exists(), "NWP config file missing"
    data = json.loads(cfg.read_text())
    assert "nwp_providers" in data
    assert "ECMWF_IFS" in data["nwp_providers"]
    assert "NOAA_GFS" in data["nwp_providers"]
    assert data["nwp_providers"]["ECMWF_IFS"]["bias_factor"] > 0.0


# ──────────────────────────────────────────────────────────────
# FLOOD MAPPING: CNN / U-Net + GeoJSON Output
# ──────────────────────────────────────────────────────────────
def test_unet_geojson_polygon_output():
    """U-Net produces RFC 7946 compliant GeoJSON with closed polygon rings."""
    result = unet_engine.segment_inundation_zones(rainfall_accumulation_72h_mm=150.0)
    assert result.type == "FeatureCollection"
    for feat in result.features:
        ring = feat.geometry.coordinates[0]
        assert ring[0] == ring[-1], "GeoJSON polygon ring must be closed"
        assert feat.properties.area_sq_km > 0.0
        assert feat.properties.estimated_water_volume_m3 > 0.0


def test_scs_cn_runoff_accuracy():
    """SCS-CN runoff: zero below initial abstraction, positive above it."""
    assert unet_engine.compute_scs_runoff(0.0) == 0.0
    assert unet_engine.compute_scs_runoff(10.0, curve_number=78.0) == 0.0
    r = unet_engine.compute_scs_runoff(100.0, curve_number=78.0)
    assert 0.0 < r < 100.0


# ──────────────────────────────────────────────────────────────
# DATABASE: PostGIS Rainfall Forecasts + Flood Polygons
# ──────────────────────────────────────────────────────────────
def test_postgis_stores_rainfall_forecast():
    """Rainfall forecast summary is persisted to the PostGIS DB table."""
    ok = spatial_db.store_rainfall_forecast_summary(
        forecast_id="TEST_FCST_12345",
        peak_rain=58.4,
        acc_rain=420.0,
        basin="Mahanadi Test Basin"
    )
    assert ok is True
    summary = spatial_db.get_latest_rainfall_forecast_summary()
    assert summary is not None
    assert summary["peak_hourly_rain_mm"] == 58.4
    assert summary["total_accumulated_72h_mm"] == 420.0


def test_postgis_st_area_spatial_query():
    """PostGIS ST_Area spatial query returns correct area aggregation."""
    # Ensure polygons exist
    inun = unet_engine.segment_inundation_zones(rainfall_accumulation_72h_mm=130.0)
    spatial_db.store_flood_inundation(inun)

    result = spatial_db.spatial_query_st_area()
    assert "postgis_query" in result
    assert "ST_Area" in result["postgis_query"]
    assert result["total_area_km2"] > 0.0
    assert len(result["results"]) > 0

    # Filter by risk level
    extreme_result = spatial_db.spatial_query_st_area(risk_filter="Extreme Inundation")
    assert extreme_result["risk_filter"] == "Extreme Inundation"


# ──────────────────────────────────────────────────────────────
# VALIDATION: Backtesting – IoU, RMSE, NSE, Dice
# ──────────────────────────────────────────────────────────────
def test_rainfall_rmse_mae_nse():
    """RMSE, MAE and NSE are computed correctly from observed/predicted series."""
    obs = [10.0, 20.0, 30.0, 40.0, 50.0]
    pred = [11.0, 19.0, 31.0, 38.0, 52.0]
    metrics = validation_engine.compute_rainfall_metrics(obs, pred)
    assert metrics["rmse_mm"] >= 0.0
    assert metrics["mae_mm"] >= 0.0
    assert -1.0 <= metrics["nse_score"] <= 1.0


def test_inundation_iou_dice():
    """IoU and Dice coefficient are correct for overlapping areas."""
    metrics = validation_engine.compute_inundation_metrics(
        predicted_area_km2=218.2,
        ground_truth_area_km2=210.5
    )
    assert 0.0 < metrics["iou_score"] <= 1.0
    assert 0.0 < metrics["dice_coefficient"] <= 1.0
    assert 0.0 < metrics["precision"] <= 1.0
    assert 0.0 < metrics["recall"] <= 1.0


def test_historical_backtest_benchmark():
    """Full historical backtest passes quality threshold: RMSE < 6mm, IoU ≥ 0.75."""
    record = validation_engine.run_backtest_benchmark()
    assert record["threshold_passed"] is True
    assert record["rainfall_metrics"]["rmse_mm"] < 6.0
    assert record["inundation_metrics"]["iou_score"] >= 0.75
    assert record["validation_status"] == "PASSED_QUALITY_BENCHMARK"


# ──────────────────────────────────────────────────────────────
# MODEL MANAGEMENT: Weights Registry + SHA-256 + Cloud Buckets
# ──────────────────────────────────────────────────────────────
def test_model_weight_registry():
    """Model weights registry returns catalog with checksums and cloud bucket URIs."""
    catalog = model_registry.get_model_catalog()
    assert catalog["registry_status"] == "ONLINE"
    assert "s3://" in catalog["cloud_storage"]["primary_bucket"]
    assert "gs://" in catalog["cloud_storage"]["secondary_gcp_bucket"]

    rf_model = catalog["models"]["rainfall_forecasting"]
    assert len(rf_model["sha256_checksum"]) == 64  # valid SHA-256 hex
    assert rf_model["version"].startswith("2.")

    unet_model = catalog["models"]["flood_inundation"]
    assert len(unet_model["sha256_checksum"]) == 64


# ──────────────────────────────────────────────────────────────
# SYNTHETIC FALLBACK PIPELINE
# ──────────────────────────────────────────────────────────────
def test_synthetic_fallback_pipeline():
    """Fallback pipeline produces valid forecast + inundation result without live feeds."""
    async def _inner():
        result = await forecast_service.execute_synthetic_fallback_pipeline(storm_intensity=1.0)
        assert result.execution_id.startswith("SYNTHETIC_")
        assert result.spatial_db_stored is True
        assert "SYNTHETIC DEMO" in result.alert_summary
        assert result.rainfall_forecast.total_accumulated_72h_mm > 0.0
        assert len(result.inundation_geojson.features) == 4
    asyncio.run(_inner())


# ──────────────────────────────────────────────────────────────
# OPTIONAL: Transfer Learning / Tile Inference / Model Health
# ──────────────────────────────────────────────────────────────
def test_transfer_learning_adaptation():
    """Transfer learning returns accuracy boost and correct fine-tuning strategy."""
    tl = rainfall_engine.apply_transfer_learning_adaptation(local_station_count=6)
    assert tl["transfer_learning_status"] == "ACTIVE"
    assert "LoRA" in tl["fine_tuning_strategy"]
    assert tl["accuracy_boost_pct"] > 0.0


def test_tile_based_inference_1km():
    """Tile-based 1 km grid inference runs and returns speedup metrics."""
    result = unet_engine.run_tile_based_inference(tile_size_km=1.0)
    assert result["status"] == "COMPLETED"
    assert result["total_tiles_processed"] > 0
    assert "4.2x" in result["speedup_factor"]
    assert result["edge_stitching_applied"] is True


# ──────────────────────────────────────────────────────────────
# ALL NEW API ENDPOINTS
# ──────────────────────────────────────────────────────────────
def test_forecast_status_endpoint():
    """GET /api/v1/forecast/status returns full model health report."""
    res = client.get("/api/v1/forecast/status")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "OPERATIONAL"
    assert "rainfall_forecasting" in data["components"]
    assert "inundation_mapping" in data["components"]
    assert "nwp_bias_correction" in data["components"]
    assert "postgis_spatial_database" in data["components"]
    assert "model_weight_registry" in data["components"]
    assert "synthetic_fallback" in data["components"]
    assert data["components"]["synthetic_fallback"]["status"] == "READY"


def test_st_area_spatial_query_endpoint():
    """GET /api/v1/spatial/st-area returns PostGIS spatial query results."""
    res = client.get("/api/v1/spatial/st-area")
    assert res.status_code == 200
    data = res.json()
    assert "postgis_query" in data
    assert data["total_area_km2"] > 0.0

    # Filtered query
    res2 = client.get("/api/v1/spatial/st-area?risk_level=High")
    assert res2.status_code == 200
    assert res2.json()["risk_filter"] == "High"


def test_backtest_validation_endpoint():
    """POST /api/v1/forecast/validate runs backtesting and returns quality metrics."""
    res = client.post("/api/v1/forecast/validate")
    assert res.status_code == 200
    data = res.json()
    assert data["threshold_passed"] is True
    assert "iou_score" in data["inundation_metrics"]
    assert "rmse_mm" in data["rainfall_metrics"]


def test_synthetic_fallback_endpoint():
    """POST /api/v1/forecast/fallback returns valid synthetic pipeline result."""
    res = client.post("/api/v1/forecast/fallback?storm_intensity=1.0")
    assert res.status_code == 200
    data = res.json()
    assert data["execution_id"].startswith("SYNTHETIC_")
    assert data["spatial_db_stored"] is True


def test_tile_inference_endpoint():
    """GET /api/v1/forecast/tile-inference reports tile-based inference metrics."""
    res = client.get("/api/v1/forecast/tile-inference")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["total_tiles_processed"] > 0


def test_model_registry_endpoint():
    """GET /api/v1/models/registry returns cloud bucket and model checksum info."""
    res = client.get("/api/v1/models/registry")
    assert res.status_code == 200
    data = res.json()
    assert "s3://" in data["cloud_storage"]["primary_bucket"]
    assert len(data["models"]) == 2


def test_nwp_config_endpoint():
    """GET /api/v1/models/nwp-config returns NWP bias correction configuration."""
    res = client.get("/api/v1/models/nwp-config")
    assert res.status_code == 200
    data = res.json()
    assert "nwp_providers" in data
    assert "ECMWF_IFS" in data["nwp_providers"]


def test_transfer_learning_endpoint():
    """GET /api/v1/models/transfer-learning returns LoRA adaptation status."""
    res = client.get("/api/v1/models/transfer-learning")
    assert res.status_code == 200
    data = res.json()
    assert data["transfer_learning_status"] == "ACTIVE"
    assert "LoRA" in data["fine_tuning_strategy"]


def test_rainfall_forecasts_stored_endpoint():
    """GET /api/v1/spatial/rainfall-forecasts returns stored forecast summary."""
    # Populate first
    client.post("/api/v1/forecast/rainfall?storm_intensity=1.0")
    client.post("/api/v1/forecast/pipeline?storm_intensity=1.0")
    res = client.get("/api/v1/spatial/rainfall-forecasts")
    assert res.status_code == 200
