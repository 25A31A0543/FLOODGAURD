from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class InfrastructureExposure(BaseModel):
    """Critical community asset exposed to flood hazard."""
    facility_id: str
    facility_name: str
    facility_type: str = Field(..., description="Hospital, School / Shelter, Power Substation, Bridge")
    latitude: float
    longitude: float
    elevation_m: float
    predicted_flood_depth_m: float
    risk_status: str = Field(..., description="SECURE, ADVISORY, THREATENED, INUNDATED")
    evacuation_capacity: Optional[int] = None


class CAPAlertPayload(BaseModel):
    """
    OASIS Common Alerting Protocol (CAP v1.2) compliant alert standard.
    Used by NDMA, IMD, FEMA, and WMO emergency response networks.
    """
    identifier: str
    sender: str = "FloodGuard Early Warning Directorate"
    sent: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "Actual"
    msg_type: str = "Alert"
    scope: str = "Public"
    category: str = "Met"
    event: str = "Flash Flood Inundation Warning"
    urgency: str = Field(..., description="Immediate, Expected, Future, Past")
    severity: str = Field(..., description="Extreme, Severe, Moderate, Minor")
    certainty: str = Field(..., description="Observed, Likely, Possible, Unlikely")
    headline: str
    description: str
    instruction: str
    affected_districts: List[str]
    affected_population_estimate: int
    critical_facilities_at_risk: List[InfrastructureExposure] = []
    metadata: Dict[str, Any] = {}


class AlertDispatchReceipt(BaseModel):
    """Log record of multi-channel emergency broadcast."""
    dispatch_id: str
    alert_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    channels_contacted: List[str]
    total_citizens_notified: int
    sms_status: str
    sirens_activated: int
    cap_xml_endpoint: str
    status: str = "DISPATCHED"


class CitizenRegistration(BaseModel):
    """Citizen emergency registry payload for geo-targeted alerting."""
    name: str = Field(..., json_schema_extra={"example": "Aarav Patnaik"})
    phone_number: str = Field(..., json_schema_extra={"example": "+919876543210"})
    email: Optional[str] = Field(None, json_schema_extra={"example": "aarav.patnaik@example.com"})
    device_token: Optional[str] = Field(None, description="FCM device push token for mobile app")
    latitude: float = Field(..., json_schema_extra={"example": 20.52})
    longitude: float = Field(..., json_schema_extra={"example": 85.82})
    district: str = Field(default="Cuttack")
    whatsapp_opt_in: bool = Field(default=True)
    preferred_language: str = Field(default="en", description="en, hi, od")


class CitizenProfile(BaseModel):
    """Citizen profile stored in PostGIS/SQLite."""
    id: int
    name: str
    phone_number: str
    email: Optional[str] = None
    device_token: Optional[str] = None
    latitude: float
    longitude: float
    district: str
    whatsapp_opt_in: bool
    preferred_language: str
    created_at: str


class GeofencedDispatchResult(BaseModel):
    """Result of spatial geofence matching and multi-channel notification dispatch."""
    dispatch_id: str
    alert_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    inundation_run_id: str
    total_registered_citizens: int
    geofenced_citizens_inside_flood_zone: int
    notified_citizens: List[Dict[str, Any]]
    channels_triggered: Dict[str, Any]
    status: str = "COMPLETED"

