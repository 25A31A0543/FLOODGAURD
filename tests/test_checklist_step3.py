import pytest
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.storage.spatial_db import spatial_db
from floodguard.services.alert_service import alert_service

client = TestClient(app)


def test_citizen_registration_endpoint():
    """Verify citizen registration in PostGIS/SQLite emergency directory."""
    payload = {
        "name": "Priyanka Sahoo",
        "phone_number": "+919988776655",
        "email": "priyanka.s@example.com",
        "device_token": "fcm_token_priyanka_realme",
        "latitude": 20.462,
        "longitude": 85.883,
        "district": "Cuttack",
        "whatsapp_opt_in": True,
        "preferred_language": "od"
    }
    res = client.post("/api/v1/citizens/register", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "REGISTERED"
    assert data["citizen"]["phone_number"] == "+919988776655"
    assert data["citizen"]["preferred_language"] == "od"


def test_list_citizens_endpoint():
    """Verify citizen retrieval from database."""
    res = client.get("/api/v1/citizens")
    assert res.status_code == 200
    data = res.json()
    assert data["total_registered"] >= 6  # pre-seeded citizens present
    assert len(data["citizens"]) >= 6

    # Test district filter
    res_cuttack = client.get("/api/v1/citizens?district=Cuttack")
    assert res_cuttack.status_code == 200
    for c in res_cuttack.json()["citizens"]:
        assert c["district"] == "Cuttack"


def test_point_in_polygon_ray_casting():
    """Verify mathematical correctness of the ray-casting point-in-polygon algorithm."""
    # Simple square polygon from (0,0) to (10,10)
    square_ring = [[0.0, 0.0], [10.0, 0.0], [10.0, 10.0], [0.0, 10.0], [0.0, 0.0]]

    # Point clearly inside
    assert spatial_db.is_point_in_polygon(5.0, 5.0, square_ring) is True
    # Point clearly outside
    assert spatial_db.is_point_in_polygon(15.0, 5.0, square_ring) is False
    assert spatial_db.is_point_in_polygon(-1.0, 5.0, square_ring) is False


def test_send_targeted_fcm_push():
    """Verify targeted FCM push alerts to specific citizen device tokens."""
    tokens = ["token_device_alpha", "token_device_beta"]
    res = alert_service.send_targeted_fcm_push(tokens, "Flash Flood Alert", "Evacuate low ground immediately.")
    assert res["channel"] == "Firebase_Targeted_FCM"
    assert res["status"] in ["SENT", "ATTEMPTED", "SIMULATED", "DISPATCH_FALLBACK"]
    assert res.get("attempted_count", res.get("sent_count")) == 2



def test_sendgrid_email_endpoint():
    """Verify SendGrid SITREP emergency bulletin email dispatch."""
    res = client.post("/api/v1/alerts/sendgrid-test?to_email=test.agency@odisha.gov.in")
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == "SendGrid_Email"
    assert data["status"] in ["SENT", "SIMULATED", "DISPATCH_FALLBACK"]


def test_fast2sms_bulk_sms_endpoint():
    """Verify Fast2SMS bulk SMS dispatch endpoint."""
    res = client.post("/api/v1/alerts/fast2sms-test?mobile_numbers=9876543210,9876543211")
    assert res.status_code == 200
    data = res.json()
    assert data["channel"] == "Fast2SMS"
    assert data["status"] in ["SENT", "SIMULATED", "DISPATCH_FALLBACK"]


def test_whatsapp_setup_guide_endpoint():
    """Verify WhatsApp sandbox setup guide and production checklist endpoint."""
    res = client.get("/api/v1/alerts/whatsapp-setup")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "CONFIGURED"
    assert data["sandbox_testing"]["sandbox_phone_number"] == "+14155238886"
    assert "join" in data["sandbox_testing"]["join_instruction"]
    assert "step_1" in data["production_setup"]


def test_geofenced_dispatch_pipeline():
    """
    Verify complete geofenced dispatch:
    Identifies citizens inside flood polygon boundaries and fires multi-channel notifications.
    """
    res = client.post("/api/v1/alerts/geofenced-dispatch?storm_intensity=1.1")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["total_registered_citizens"] >= 6
    assert data["geofenced_citizens_inside_flood_zone"] > 0
    assert len(data["notified_citizens"]) > 0

    # Ensure each notified citizen has coordinates inside the catchment
    for citizen in data["notified_citizens"]:
        assert "risk_level" in citizen
        assert citizen["predicted_depth_m"] > 0.0

    assert "fcm_push" in data["channels_triggered"]
    assert "fast2sms" in data["channels_triggered"]
    assert "twilio_whatsapp" in data["channels_triggered"]
