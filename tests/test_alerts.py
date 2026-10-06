import asyncio
import pytest
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.services.alert_service import alert_service
from floodguard.services.forecast_service import forecast_service

client = TestClient(app)


def test_cap_alert_generation():
    alert = alert_service.generate_cap_alert()
    assert alert.identifier.startswith("CAP_INUND_")
    assert alert.status == "Actual"
    assert alert.msg_type == "Alert"
    assert alert.scope == "Public"
    assert alert.category == "Met"
    assert alert.event == "Flash Flood Inundation Warning"
    assert alert.urgency in ["Immediate", "Expected"]
    assert alert.severity in ["Extreme", "Severe", "Moderate", "Minor"]
    assert len(alert.affected_districts) > 0
    assert alert.affected_population_estimate > 0
    assert len(alert.critical_facilities_at_risk) > 0

    # Verify critical facilities schema
    fac = alert.critical_facilities_at_risk[0]
    assert fac.facility_name is not None
    assert fac.risk_status in ["SECURE", "ADVISORY", "THREATENED", "INUNDATED"]


def test_alert_dispatch():
    alert = alert_service.generate_cap_alert(force_severity="Extreme")
    receipt = alert_service.dispatch_alert(alert)
    assert receipt.dispatch_id.startswith("DISP_")
    assert receipt.alert_id == alert.identifier
    assert receipt.status == "DISPATCHED"
    assert len(receipt.channels_contacted) >= 3
    assert receipt.sirens_activated > 0


def test_alerts_api_endpoints():
    # 1. Generate alert endpoint
    res_gen = client.post("/api/v1/alerts/generate?force_severity=Severe")
    assert res_gen.status_code == 200
    assert res_gen.json()["severity"] == "Severe"

    # 2. Dispatch alert endpoint
    res_disp = client.post("/api/v1/alerts/dispatch")
    assert res_disp.status_code == 200
    assert res_disp.json()["status"] == "DISPATCHED"

    # 3. Latest alert endpoint
    res_latest = client.get("/api/v1/alerts/latest")
    assert res_latest.status_code == 200
    assert res_latest.json()["identifier"] is not None

    # 4. Master Full Pipeline endpoint (Steps 1, 2, and 3)
    res_full = client.post("/api/v1/pipeline/full-run?storm_intensity=1.2")
    assert res_full.status_code == 200
    data = res_full.json()
    assert data["status"] == "SUCCESS"
    assert "step1_ingestion" in data
    assert "step2_forecast_inundation" in data
    assert "step3_early_warning" in data
    assert data["step2_forecast_inundation"]["postgis_records_saved"] == 4
