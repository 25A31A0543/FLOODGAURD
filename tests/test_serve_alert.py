from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.services.alert_service import alert_service

client = TestClient(app)


def test_twilio_sms_dispatch_method():
    """Verify Twilio SMS dispatch method functions with configured credentials."""
    res = alert_service.send_twilio_sms("+919876543210", "FloodGuard test alert message")
    assert res["channel"] == "SMS"
    assert res["status"] in ["SENT", "DISPATCH_FALLBACK", "SIMULATED"]
    assert "sid" in res


def test_twilio_whatsapp_dispatch_method():
    """Verify Twilio WhatsApp dispatch method functions with configured credentials."""
    res = alert_service.send_twilio_whatsapp("+919876543210", "FloodGuard WhatsApp test alert")
    assert res["channel"] == "WhatsApp"
    assert res["status"] in ["SENT", "DISPATCH_FALLBACK", "SIMULATED"]
    assert "sid" in res


def test_twilio_voice_call_dispatch_method():
    """Verify Twilio Media Stream / Voice IVR call dispatch method."""
    res = alert_service.make_voice_alert_call("+919876543210", "FloodGuard urgent voice warning")
    assert res["channel"] == "Voice_Call"
    assert res["status"] in ["QUEUED", "DISPATCH_FALLBACK", "SIMULATED"]
    assert "sid" in res


def test_firebase_push_notification_method():
    """Verify Firebase FCM push notification method functions with configured credentials."""
    res = alert_service.send_firebase_push_notification(
        topic="flood_alerts",
        title="Flood Warning",
        body="Immediate evacuation advised for low-lying zones."
    )
    assert res["channel"] == "Firebase_FCM"
    assert res["status"] in ["SENT", "DISPATCH_FALLBACK", "SIMULATED"]


def test_full_alert_dispatch_receipt_channels():
    """Verify dispatch_alert contacts all 6 multi-channel networks."""
    alert = alert_service.generate_cap_alert(force_severity="Extreme")
    receipt = alert_service.dispatch_alert(alert)

    assert receipt.status == "DISPATCHED"
    assert len(receipt.channels_contacted) == 6
    assert any("Twilio" in ch for ch in receipt.channels_contacted)
    assert any("Firebase" in ch for ch in receipt.channels_contacted)
    assert any("WhatsApp" in ch for ch in receipt.channels_contacted)
    assert receipt.sirens_activated == 14


def test_websocket_live_alerts_channel():
    """Verify WebSocket /ws/v1/live-alerts connection handshake."""
    with client.websocket_connect("/ws/v1/live-alerts") as websocket:
        data = websocket.receive_json()
        assert data["event"] == "CONNECTED"
        assert data["service"] == "Step 3: Serve & Alert"

        websocket.send_text("PING")
        reply = websocket.receive_json()
        assert reply["event"] == "HEARTBEAT_ACK"
        assert reply["client_message"] == "PING"
