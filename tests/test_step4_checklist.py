"""
Comprehensive verification test suite for Step 4 Checklist:
1. Citizen Mobile App:
   - Flood maps (GeoJSON polygons)
   - Push notifications (Firebase)
   - SOS button for emergency help
2. Authority Control Panel:
   - Analytics (rainfall, inundation, population at risk)
   - Geofenced alert dispatch
   - Infrastructure risk dashboard
3. Public Web Dashboard:
   - Live rainfall charts
   - Flood polygons overlay
   - CAP alerts feed
4. Data Source:
   - PostGIS + APIs feeding all dashboards
"""

import pytest
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.storage.spatial_db import spatial_db
from floodguard.services.alert_service import alert_service

client = TestClient(app)


# ==========================================
# 1. CITIZEN MOBILE APP CHECKLIST
# ==========================================

def test_checklist_citizen_mobile_app_flood_maps():
    """Verify Citizen Mobile App: Flood maps (GeoJSON polygons)."""
    res = client.get("/api/v1/mobile/flood-map")
    assert res.status_code == 200
    data = res.json()
    assert "polygons" in data
    assert isinstance(data["polygons"], list)
    assert "depth_legend" in data
    assert "center" in data
    assert "districts_monitored" in data


def test_checklist_citizen_mobile_app_push_notifications():
    """Verify Citizen Mobile App: Push notifications (Firebase FCM)."""
    # In-app push alert payload
    res = client.get("/api/v1/mobile/alerts")
    assert res.status_code == 200
    data = res.json()
    assert "push_title" in data
    assert "push_body" in data
    assert "languages" in data
    assert "od" in data["languages"]
    assert "hi" in data["languages"]
    assert "en" in data["languages"]

    # Direct Firebase FCM targeted push method
    tokens = ["token_device_citizen_1", "token_device_citizen_2"]
    fcm_res = alert_service.send_targeted_fcm_push(tokens, "Flood Warning", "Move to high ground")
    assert fcm_res["channel"] == "Firebase_Targeted_FCM"
    assert fcm_res["status"] in ["SENT", "ATTEMPTED", "SIMULATED", "DISPATCH_FALLBACK"]


def test_checklist_citizen_mobile_app_sos_button():
    """Verify Citizen Mobile App: SOS button for emergency help with GPS coordinates."""
    res = client.post(
        "/api/v1/mobile/sos?phone_number=%2B919876543210&latitude=21.467&longitude=83.985&message=Trapped+in+flooded+house"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SOS_DISPATCHED"
    assert "sos_id" in data
    assert data["gps_coordinates"]["latitude"] == 21.467
    assert data["gps_coordinates"]["longitude"] == 83.985
    assert "google_maps_link" in data
    assert "nearest_rescue_team" in data
    assert data["nearest_rescue_team"]["eta_minutes"] > 0
    assert "helpline" in data


# ==========================================
# 2. AUTHORITY CONTROL PANEL CHECKLIST
# ==========================================

def test_checklist_authority_analytics():
    """Verify Authority Control Panel: Analytics (rainfall, inundation, population at risk)."""
    res = client.get("/api/v1/authority/analytics")
    assert res.status_code == 200
    data = res.json()
    # Rainfall accuracy metrics
    assert "rainfall_rmse_mm" in data["model_accuracy"]
    assert "rainfall_mae_mm" in data["model_accuracy"]
    assert "rainfall_nse" in data["model_accuracy"]
    # Inundation accuracy metrics
    assert "inundation_iou" in data["model_accuracy"]
    assert "inundation_dice" in data["model_accuracy"]
    assert data["model_accuracy"]["inundation_iou"] >= 0.70
    assert data["model_accuracy"]["rainfall_nse"] >= 0.85
    # Subsystem health
    assert "model_health" in data


def test_checklist_authority_population_at_risk():
    """Verify Authority Control Panel: Population and citizens at risk calculation."""
    res = client.get("/api/v1/authority/geofenced-citizens")
    assert res.status_code == 200
    data = res.json()
    assert "total_registered_citizens" in data
    assert "citizens_inside_flood_zone" in data
    assert "citizens_at_risk" in data
    assert data["total_registered_citizens"] >= 1


def test_checklist_authority_geofenced_alert_dispatch():
    """Verify Authority Control Panel: Geofenced alert dispatch across multiple channels."""
    res = client.post("/api/v1/alerts/geofenced-dispatch")
    assert res.status_code == 200
    data = res.json()
    assert "dispatch_id" in data
    assert "alert_id" in data
    assert "total_registered_citizens" in data
    assert "geofenced_citizens_inside_flood_zone" in data
    assert "channels_triggered" in data
    assert "fcm_push" in data["channels_triggered"]
    assert "twilio_whatsapp" in data["channels_triggered"]
    assert "fast2sms" in data["channels_triggered"]
    assert "sendgrid_email" in data["channels_triggered"]


def test_checklist_authority_infrastructure_risk_dashboard():
    """Verify Authority Control Panel: Infrastructure risk dashboard."""
    res = client.get("/api/v1/authority/infrastructure-risk")
    assert res.status_code == 200
    data = res.json()
    assert data["dashboard"] == "Infrastructure Risk Assessment"
    assert "total_facilities_monitored" in data
    assert "threatened_facilities" in data
    assert "advisory_facilities" in data
    assert "safe_facilities" in data
    assert "evacuation_capacity_total" in data
    assert "recommended_actions" in data
    assert len(data["recommended_actions"]) >= 1


# ==========================================
# 3. PUBLIC WEB DASHBOARD CHECKLIST
# ==========================================

def test_checklist_public_dashboard_live_rainfall_charts():
    """Verify Public Web Dashboard: Live rainfall charts dataset."""
    res = client.get("/api/v1/public/rainfall-chart")
    assert res.status_code == 200
    data = res.json()
    assert data["chart_type"] == "line"
    assert "x_labels" in data
    assert len(data["x_labels"]) == 25  # 72 hours in 3-hour increments
    assert len(data["datasets"]) == 4    # LSTM, GRU, Transformer, Ensemble Mean
    labels = [d["label"] for d in data["datasets"]]
    assert any("LSTM" in l for l in labels)
    assert any("GRU" in l for l in labels)
    assert any("Transformer" in l for l in labels)
    assert any("Ensemble" in l for l in labels)


def test_checklist_public_dashboard_flood_polygons_overlay():
    """Verify Public Web Dashboard: Flood polygons overlay (GeoJSON)."""
    res = client.get("/api/v1/public/inundation-polygons")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert "metadata" in data
    assert data["metadata"]["projection"] == "WGS84 EPSG:4326"


def test_checklist_public_dashboard_cap_alerts_feed():
    """Verify Public Web Dashboard: OASIS CAP v1.2 alerts feed."""
    res = client.get("/api/v1/public/cap-feed")
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "OASIS CAP v1.2"
    assert "alerts" in data
    assert len(data["alerts"]) >= 1
    first_alert = data["alerts"][0]
    assert "headline" in first_alert
    assert "severity" in first_alert
    assert "instruction" in first_alert
    assert "color_map" in first_alert


# ==========================================
# 4. DATA SOURCE: POSTGIS + APIS CHECKLIST
# ==========================================

def test_checklist_datasource_postgis_and_apis():
    """Verify Data Source: PostGIS spatial storage and REST API querying."""
    # 1. PostGIS stores flood polygons
    inund = spatial_db.get_latest_inundation()
    assert inund is not None
    assert "features" in inund
    assert len(inund["features"]) >= 1

    # 2. PostGIS spatial query ST_Area
    st_area_res = client.get("/api/v1/spatial/st-area")
    assert st_area_res.status_code == 200
    st_area_data = st_area_res.json()
    assert "results" in st_area_data
    assert "postgis_query" in st_area_data

    # 3. PostGIS citizen directory
    citizens = spatial_db.list_citizens()
    assert len(citizens) >= 1

    # 4. Ray-casting point-in-polygon algorithm
    poly_box = [[83.0, 20.0], [85.0, 20.0], [85.0, 22.0], [83.0, 22.0], [83.0, 20.0]]
    assert spatial_db.is_point_in_polygon(84.0, 21.0, poly_box) is True
    assert spatial_db.is_point_in_polygon(90.0, 30.0, poly_box) is False

    # 5. APIs feeding Authority System Status
    sys_status_res = client.get("/api/v1/authority/system-status")
    assert sys_status_res.status_code == 200
    sys_data = sys_status_res.json()
    assert sys_data["pipeline_stages"]["step1_ingestion"]["status"] == "OPERATIONAL"
    assert sys_data["pipeline_stages"]["step2_forecast"]["status"] == "OPERATIONAL"
    assert sys_data["pipeline_stages"]["step3_alert"]["status"] == "OPERATIONAL"
    assert sys_data["pipeline_stages"]["step4_dashboard"]["status"] == "OPERATIONAL"
