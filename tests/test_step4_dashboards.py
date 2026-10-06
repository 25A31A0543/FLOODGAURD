import pytest
from fastapi.testclient import TestClient
from floodguard.main import app

client = TestClient(app)


def test_mobile_flood_map_endpoint():
    """Step 4: Verify mobile app flood map endpoint returns optimized polygons."""
    res = client.get("/api/v1/mobile/flood-map")
    assert res.status_code == 200
    data = res.json()
    assert data["layer"] == "FloodGuard_InundationPolygons_v1"
    assert data["catchment"] == "Mahanadi-Hirakud"
    assert "polygons" in data
    assert "depth_legend" in data
    assert "center" in data


def test_mobile_sos_endpoint():
    """Step 4: Verify mobile SOS one-tap broadcast alerts rescue teams with GPS."""
    res = client.post(
        "/api/v1/mobile/sos?phone_number=%2B919876543210&latitude=21.467&longitude=83.985&message=Emergency+help"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "SOS_DISPATCHED"
    assert data["sos_id"].startswith("SOS-")
    assert "google_maps_link" in data
    assert "nearest_rescue_team" in data
    assert len(data["rescue_teams_alerted"]) >= 1


def test_mobile_alerts_endpoint():
    """Step 4: Verify mobile alert endpoint returns multilingual push notifications."""
    res = client.get("/api/v1/mobile/alerts")
    assert res.status_code == 200
    data = res.json()
    assert "alert_id" in data
    assert "push_title" in data
    assert "languages" in data
    assert "od" in data["languages"]
    assert "hi" in data["languages"]
    assert "en" in data["languages"]


def test_mobile_citizen_profile_endpoint():
    """Step 4: Verify citizen lookup by phone for personalized mobile experience."""
    res = client.get("/api/v1/mobile/citizen-profile?phone_number=%2B919876543210")
    assert res.status_code == 200
    data = res.json()
    assert "found" in data


def test_authority_analytics_endpoint():
    """Step 4: Verify authority control panel model analytics and accuracy metrics."""
    res = client.get("/api/v1/authority/analytics")
    assert res.status_code == 200
    data = res.json()
    assert "model_accuracy" in data
    assert data["model_accuracy"]["inundation_iou"] >= 0.70
    assert data["model_accuracy"]["rainfall_nse"] >= 0.85
    assert "model_health" in data
    assert "system_uptime" in data


def test_authority_infrastructure_risk_endpoint():
    """Step 4: Verify authority infrastructure risk dashboard."""
    res = client.get("/api/v1/authority/infrastructure-risk")
    assert res.status_code == 200
    data = res.json()
    assert data["dashboard"] == "Infrastructure Risk Assessment"
    assert "total_facilities_monitored" in data
    assert "threatened_facilities" in data
    assert "recommended_actions" in data


def test_authority_geofenced_citizens_endpoint():
    """Step 4: Verify authority view of citizens inside active flood zone."""
    res = client.get("/api/v1/authority/geofenced-citizens")
    assert res.status_code == 200
    data = res.json()
    assert "total_registered_citizens" in data
    assert "citizens_inside_flood_zone" in data
    assert "all_citizens" in data


def test_authority_system_status_endpoint():
    """Step 4: Verify authority full system operational status."""
    res = client.get("/api/v1/authority/system-status")
    assert res.status_code == 200
    data = res.json()
    assert data["pipeline_stages"]["step1_ingestion"]["status"] == "OPERATIONAL"
    assert data["pipeline_stages"]["step2_forecast"]["status"] == "OPERATIONAL"
    assert data["pipeline_stages"]["step3_alert"]["status"] == "OPERATIONAL"
    assert data["pipeline_stages"]["step4_dashboard"]["status"] == "OPERATIONAL"


def test_public_rainfall_chart_endpoint():
    """Step 4: Verify public dashboard 72h rainfall chart dataset."""
    res = client.get("/api/v1/public/rainfall-chart")
    assert res.status_code == 200
    data = res.json()
    assert data["chart_type"] == "line"
    assert len(data["datasets"]) == 4
    assert len(data["x_labels"]) == 25


def test_public_cap_feed_endpoint():
    """Step 4: Verify public OASIS CAP v1.2 emergency alert bulletin feed."""
    res = client.get("/api/v1/public/cap-feed")
    assert res.status_code == 200
    data = res.json()
    assert data["format"] == "OASIS CAP v1.2"
    assert len(data["alerts"]) >= 1


def test_public_inundation_polygons_endpoint():
    """Step 4: Verify public GeoJSON inundation polygons for web mapping."""
    res = client.get("/api/v1/public/inundation-polygons")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data


def test_html_dashboard_pages():
    """Step 4: Verify all dashboard UI views return valid 200 HTML."""
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "html" in res_dash.headers["content-type"]

    res_auth = client.get("/authority")
    assert res_auth.status_code == 200
    assert "html" in res_auth.headers["content-type"]
    assert "Authority Control Panel" in res_auth.text

    res_mob = client.get("/mobile")
    assert res_mob.status_code == 200
    assert "html" in res_mob.headers["content-type"]
    assert "FloodGuard" in res_mob.text
