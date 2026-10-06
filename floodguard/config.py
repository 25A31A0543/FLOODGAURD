import os
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field, ConfigDict


class Settings(BaseSettings):
    """Configuration settings for FloodGuard Ingestion Engine."""
    model_config = ConfigDict(
        env_prefix="FLOODGUARD_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False
    )

    PROJECT_NAME: str = "FloodGuard Ingestion Engine"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = True

    # NASA Earthdata Authentication (Bearer JWT Token)
    NASA_EARTHDATA_TOKEN: str = Field(
        default_factory=lambda: os.getenv("NASA_EARTHDATA_TOKEN", ""),
        description="Bearer JWT Token for NASA Earthdata GES DISC / CMR API"
    )

    # IMD Weather APIs Authentication Key
    IMD_API_KEY: str = Field(
        default_factory=lambda: os.getenv("IMD_API_KEY", ""),
        description="API Key for India Meteorological Department (IMD) Weather Station Telemetry API"
    )

    # DEM Topographical Raster API Key (OpenTopography / Copernicus / CartoDEM)
    DEM_API_KEY: str = Field(
        default_factory=lambda: os.getenv("DEM_API_KEY", ""),
        description="API Key for Digital Elevation Models (DEM) Topography & Elevation APIs"
    )

    # Twilio Telecommunications Integration (SMS, WhatsApp, Voice Calls)
    TWILIO_ACCOUNT_SID: str = Field(
        default_factory=lambda: os.getenv("TWILIO_ACCOUNT_SID", ""),
        description="Twilio Account SID"
    )
    TWILIO_API_KEY: str = Field(
        default_factory=lambda: os.getenv("TWILIO_API_KEY", ""),
        description="Twilio API Key"
    )
    TWILIO_API_SECRET: str = Field(
        default_factory=lambda: os.getenv("TWILIO_API_SECRET", ""),
        description="Twilio API Secret"
    )
    TWILIO_PHONE_NUMBER: str = Field(
        default_factory=lambda: os.getenv("TWILIO_PHONE_NUMBER", ""),
        description="Twilio Outbound Phone Number"
    )

    # CARTO Basemaps API Key (Watermark-Free Raster Tiles)
    CARTO_API_KEY: str = Field(
        default_factory=lambda: os.getenv("CARTO_API_KEY", "cb1_2xm7_1_7f41667ad0188b79dff91e16"),
        description="API Key for CARTO Basemaps (Watermark-free raster tiles)"
    )

    # Firebase Cloud Messaging & Google Cloud Platform (GCP)
    FIREBASE_PROJECT_ID: str = Field(
        default_factory=lambda: os.getenv("FLOODGUARD_FIREBASE_PROJECT_ID", "flooddaurd"),
        description="Firebase Project ID"
    )
    FIREBASE_CREDENTIALS_PATH: str = Field(
        default="floodguard/config/firebase_credentials.json",
        description="Path to Firebase service account JSON key"
    )
    GCP_PROJECT_ID: str = Field(
        default_factory=lambda: os.getenv("GCP_PROJECT_ID", "flooddaurd"),
        description="Google Cloud Platform Project ID"
    )
    GCP_SERVICE_ACCOUNT_JSON: str = Field(
        default="floodguard/config/gcp_service_account.json",
        description="Path to GCP service account JSON key"
    )
    GOOGLE_APPLICATION_CREDENTIALS: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "floodguard/config/firebase_credentials.json"),
        description="Standard Google application credentials environment variable"
    )

    # SendGrid Email Alerting
    SENDGRID_API_KEY: str = Field(
        default_factory=lambda: os.getenv("SENDGRID_API_KEY", "SG.mock_sendgrid_key_floodguard"),
        description="SendGrid API Key for situational emergency bulletin emails"
    )
    SENDGRID_FROM_EMAIL: str = Field(
        default="alerts@floodguard.in",
        description="Authorised sender address for disaster alerts"
    )

    # Fast2SMS (Optional Bulk SMS Gateway for India)
    FAST2SMS_API_KEY: str = Field(
        default_factory=lambda: os.getenv("FAST2SMS_API_KEY", "fast2sms_demo_key"),
        description="Fast2SMS API Key for high-volume cellular SMS in India"
    )

    # WhatsApp Disaster Channel
    WHATSAPP_SANDBOX_NUMBER: str = "+14155238886"
    WHATSAPP_SANDBOX_JOIN_CODE: str = "join flood-alert"


    # Primary Monitored Catchment Basin (Default: Mahanadi / Yamuna floodplain coordinates)
    DEFAULT_BBOX_MIN_LAT: float = Field(default=20.0, description="Min Latitude (Deg N)")
    DEFAULT_BBOX_MAX_LAT: float = Field(default=22.5, description="Max Latitude (Deg N)")
    DEFAULT_BBOX_MIN_LON: float = Field(default=82.0, description="Min Longitude (Deg E)")
    DEFAULT_BBOX_MAX_LON: float = Field(default=86.5, description="Max Longitude (Deg E)")
    DEFAULT_REGION_NAME: str = "Mahanadi-Hirakud Catchment Basin"

    # Ingestion Polling Intervals (in seconds)
    POLL_INTERVAL_GPM_SECONDS: int = 1800  # 30 minutes
    POLL_INTERVAL_IMD_SECONDS: int = 3600  # 1 hour
    POLL_INTERVAL_DWR_SECONDS: int = 600   # 10 minutes
    POLL_INTERVAL_DEM_SECONDS: int = 86400 # 24 hours (static/semi-static)

    # Storage paths for raw telemetry
    DATA_DIR: Path = Path("data")
    RAW_NETCDF_DIR: Path = Path("data/raw/dwr_netcdf")
    RAW_HDF5_DIR: Path = Path("data/raw/gpm_hdf5")
    RAW_DEM_DIR: Path = Path("data/raw/dem")
    BUFFER_STORAGE_DIR: Path = Path("data/processed/staging_buffer")


settings = Settings()

# Ensure required storage directories exist
for folder in [
    settings.DATA_DIR,
    settings.RAW_NETCDF_DIR,
    settings.RAW_HDF5_DIR,
    settings.RAW_DEM_DIR,
    settings.BUFFER_STORAGE_DIR
]:
    folder.mkdir(parents=True, exist_ok=True)
