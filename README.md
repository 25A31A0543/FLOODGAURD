# FloodGuard AI Platform

An end-to-end AI-powered flood forecasting, inundation mapping, and data ingestion platform built with **FastAPI**, **Deep Learning (LSTM/GRU/Transformer, CNN U-Net)**, and **PostGIS Spatial Database**.

---

## Architecture

### Step 1: Data Ingestion Architecture
![FloodGuard Step 1: Data Ingestion](C:\Users\sony\.gemini\antigravity\brain\2d71bd09-ffca-4e58-9c67-b1f93850262e\floodguard_ingestion_arch_1788497641079.jpg)

### Step 2: Forecast & Inundation Modeling Architecture
![FloodGuard Step 2: Forecast & Inundation Modeling](C:\Users\sony\.gemini\antigravity\brain\2d71bd09-ffca-4e58-9c67-b1f93850262e\floodguard_step2_forecast_arch_1788508548799.jpg)

### Step 3: Serve & Alert Architecture
![FloodGuard Step 3: Serve & Alert](C:\Users\sony\.gemini\antigravity\brain\2d71bd09-ffca-4e58-9c67-b1f93850262e\floodguard_step3_serve_alert_arch_1788516858295.jpg)

### Step 4: Outputs & Dashboards Architecture
![FloodGuard Step 4: Outputs & Dashboards](C:\Users\sony\.gemini\antigravity\brain\2d71bd09-ffca-4e58-9c67-b1f93850262e\floodguard_step4_outputs_dashboards_arch_1788519307678.jpg)

### Step 5: Integration & Scaling Architecture
![FloodGuard Step 5: Integration & Scaling](C:\Users\sony\.gemini\antigravity\brain\2d71bd09-ffca-4e58-9c67-b1f93850262e\floodguard_step5_integration_scaling_arch_1788521574422.jpg)

```
+---------------------------------------------------------------------------------------------------------+
|                                    FloodGuard AI System Pipeline                                        |
+---------------------------------------------------------------------------------------------------------+

 [STEP 1: Ingestion Feeds - Blue]         [STEP 2: AI/ML Models - Orange]          [STEP 2: Outputs - Green/Purple]

 +---------------------------------+      +-------------------------------+        +-------------------------------+
 | 🛰️ NASA GPM Satellite Feeds    |      | 🧠 Rainfall Forecasting       |        | 🟢 Flood GeoJSON Polygons     |
 |    • IMERG V07B precipitation   |      |    • LSTM / GRU / Transformer |------->|    • Depth contours (0.5m-4m) |
 |    • Earthdata Bearer JWT Auth  |----->|    • NWP Bias Correction      |        |    • Risk severity zones      |
 +---------------------------------+  |   |    • 72-hr hourly forecast    |        |    • RFC 7946 GeoJSON format  |
                                      |   +-------------------------------+        +-------------------------------+
 +---------------------------------+  |                   |                                        |
 | 🌡️ IMD Weather Station APIs    |  |                   v                                        v
 |    • AWS ground observations   |--+    +-------------------------------+        +-------------------------------+
 |    • Live IMD API Key Auth     |  |    | 🌊 Flood Inundation Mapping   |        | 🟣 PostGIS Spatial Database   |
 +---------------------------------+  |    |    • SCS-CN Runoff Engine     |------->|    • Spatiotemporal storage   |
                                      |--->|    • CNN / U-Net Segmentation |        |    • GIST spatial indexing    |
 +---------------------------------+  |    |    • DEM Topographical Grid   |        |    • Temporal versioning      |
 | 📡 Doppler Weather Radar (DWR)  |  |    +-------------------------------+        +-------------------------------+
 |    • NetCDF4 / HDF5 sweeps      |--+
 +---------------------------------+  |
                                      |
 +---------------------------------+  |
 | 🗺️ Digital Elevation Models DEM |-+
 |    • CartoDEM / Copernicus 30m  |
 |    • DEM Topography API Key Auth|
 +---------------------------------+
```

---

## Core Capabilities

### Step 1: Heterogeneous Telemetry Ingestion (Blue & Orange)
- **NASA GPM Satellite**: Authenticated with NASA Earthdata Login Bearer JWT token (`abhishekmallina`). Ingests IMERG V07B precipitation rates.
- **IMD Weather APIs**: Authenticated via IMD API Key (`sk-live-Ztpq...CJht`). Ingests Automatic Weather Station (AWS) rain gauge telemetry.
- **Doppler Radar (DWR)**: Binary volume scans (NetCDF4 / HDF5 ODIM_H5). Marshall-Palmer reflectivity conversion ($Z = 200 \cdot R^{1.6}$).
- **Digital Elevation Models (DEM)**: Authenticated via DEM API Key (`c569...0edc`). Ingests 30m topography, slope, aspect, and drainage basins.
- **Unified Ingestion Engine**: Fast asynchronous multi-feed coordinator and staging circular storage buffer.

### Step 2: Forecast & Inundation Modeling (Orange, Green & Purple)
- **Rainfall Forecasting (Orange)**:
  - Multi-model ensemble: **LSTM** (hydrological persistence) + **GRU** (convective pulses) + **Transformer** (spatial-temporal self-attention).
  - **NWP Residual Bias Correction**: Corrects raw Numerical Weather Prediction errors against ground truth observations.
  - Generates calibrated 72-hour precipitation forecast curves with uncertainty bounds.
- **Flood Inundation Mapping (Orange)**:
  - **SCS Curve Number (CN)** hydrological runoff conversion ($Q = (P - I_a)^2 / (P - I_a + S)$).
  - **CNN / U-Net Semantic Segmentation** over high-resolution DEM grids.
- **Flood GeoJSON Outputs (Green)**:
  - RFC 7946 GeoJSON FeatureCollections containing closed polygon contours with water depth ($m$), inundated area ($km^2$), and risk tiers (Low, Moderate, High, Extreme).
- **PostGIS Spatial Database (Purple)**:
  - Relational vector storage with GIST spatial indexing, polygon query filters, and spatiotemporal versioning.

### Step 3: Serve, Alert & Early Warning System (Red & Green)
- **OASIS CAP v1.2 Protocol**: Generates international standard Common Alerting Protocol emergency alert payloads (NDMA, IMD, FEMA, WMO compliant).
- **Twilio Multi-Channel**: SMS alerts, WhatsApp Business API messages (sandbox: `+14155238886`), and Voice IVR emergency calls via Twilio Media Streams.
- **Firebase FCM Push Notifications**: Targeted device push notifications via Firebase Admin SDK (`firebase_admin.messaging.send_each`).
- **SendGrid Email Alerts**: HTML SITREP emergency bulletins dispatched to government agencies and first responders.
- **Fast2SMS Bulk SMS**: India-specific bulk SMS broadcasting to district emergency coordinators.
- **WebSocket Live Alerts**: Real-time bidirectional stream (`ws://host/ws/v1/live-alerts`) for dashboard subscriptions.
- **Citizen Emergency Directory**: PostGIS-backed citizen registry with GPS coordinates, FCM tokens, WhatsApp opt-in, and preferred language (Odia/Hindi/English) for 6 pre-seeded districts (Cuttack, Sambalpur, Burla, Hirakud, Jharsuguda, Bargarh).
- **Geofenced Dispatch Pipeline**: Full spatial geofencing — flood polygon → ray-casting point-in-polygon → matched citizens → multi-channel fire (FCM + WhatsApp + Fast2SMS + SendGrid).

---

## Quick Start

### 1. Requirements
Ensure Python 3.10+ is installed:
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment Secrets
Credentials are securely configured in `.env`:
```env
FLOODGUARD_NASA_EARTHDATA_TOKEN=<your_nasa_jwt_token>
FLOODGUARD_IMD_API_KEY=<your_imd_api_key>
FLOODGUARD_DEM_API_KEY=<your_dem_api_key>
TWILIO_ACCOUNT_SID=<your_twilio_account_sid>
TWILIO_API_KEY=<your_twilio_api_key>
TWILIO_API_SECRET=<your_twilio_api_secret>
TWILIO_PHONE_NUMBER=<your_twilio_phone_number>
SENDGRID_API_KEY=<your_sendgrid_api_key>
FAST2SMS_API_KEY=<your_fast2sms_api_key>
```

### 3. Launch FloodGuard Platform
```powershell
python run_server.py
```

- **Interactive Telemetry & Flood Map Dashboard**: [http://127.0.0.1:8000/dashboard](http://127.0.0.1:8000/dashboard)
  - Features real-time tab switching between Step 1 (Ingestion), Step 2 (Forecast & Inundation), and Step 3 (Alert Engine).
  - Interactive Leaflet map rendering PostGIS flood polygons with depth popups.
  - Interactive Chart.js 72-hour multi-model rainfall forecast curves.
- **Interactive OpenAPI Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## API Reference

### Step 1: Ingestion Endpoints
- `POST /api/v1/ingest/nasa-gpm`: Ingest NASA GPM satellite feed.
- `POST /api/v1/ingest/imd`: Ingest IMD AWS weather telemetry.
- `POST /api/v1/ingest/dwr`: Ingest Doppler radar NetCDF4/HDF5 volume scans.
- `POST /api/v1/ingest/dem`: Ingest Digital Elevation Models (DEM).
- `POST /api/v1/ingest/sync-all`: Unified multi-source synchronization.
- `GET /api/v1/status`: Health check and status of all 4 feeds.
- `GET /api/v1/telemetry/latest`: Latest harmonized telemetry snapshot.
- `GET /api/v1/receipts`: Ingestion transaction audit receipts.

### Step 2: Forecast & Inundation Endpoints
- `POST /api/v1/forecast/rainfall`: Execute LSTM/GRU/Transformer 72h rainfall forecast.
- `POST /api/v1/forecast/inundation`: Run SCS-CN runoff & U-Net inundation segmentation on DEM.
- `POST /api/v1/forecast/pipeline`: End-to-end pipeline (Telemetry → Forecast → Runoff → U-Net → GeoJSON → PostGIS).
- `GET /api/v1/forecast/latest`: Retrieve latest forecast & inundation result.
- `GET /api/v1/forecast/status`: Model health monitor (LSTM/U-Net/NWP/PostGIS/Registry).
- `GET /api/v1/spatial/polygons`: Query PostGIS spatial database for flood polygons.
- `GET /api/v1/spatial/st-area`: PostGIS `ST_Area` spatial aggregation queries.
- `GET /api/v1/spatial/rainfall-forecasts`: PostGIS stored rainfall forecast summaries.
- `POST /api/v1/forecast/validate`: Historical backtesting benchmark (IoU, Dice, RMSE, NSE).
- `POST /api/v1/forecast/fallback`: Synthetic fallback demo pipeline (live feed failure safe).
- `GET /api/v1/forecast/tile-inference`: Tile-based 1km grid inference performance metrics.
- `GET /api/v1/models/registry`: Model weight registry with SHA-256 and cloud bucket URIs.
- `GET /api/v1/models/nwp-config`: NWP bias correction parameters.
- `GET /api/v1/models/transfer-learning`: LoRA transfer learning adaptation metrics.

### Step 3: Alert, Serve & Early Warning Endpoints
- `POST /api/v1/alerts/generate`: Generate OASIS CAP v1.2 flood alert with infrastructure exposure.
- `POST /api/v1/alerts/dispatch`: Multi-channel dispatch (Twilio SMS, WhatsApp Business API, Firebase FCM Push, Twilio Voice IVR, Sirens).
- `GET /api/v1/alerts/latest`: Retrieve latest CAP emergency alert.
- `POST /api/v1/alerts/sendgrid-test?to_email=<email>`: Send SendGrid HTML SITREP email to agency.
- `POST /api/v1/alerts/fast2sms-test`: Fast2SMS bulk SMS broadcast to district coordinators.
- `GET /api/v1/alerts/whatsapp-setup`: WhatsApp sandbox & production onboarding guide.
- `POST /api/v1/alerts/geofenced-dispatch`: Geofenced alert dispatch — flood polygon → matched citizens → multi-channel fire.
- `POST /api/v1/pipeline/full-run`: Master pipeline running Steps 1, 2, and 3 in sequence.
- `WS /ws/v1/live-alerts`: Real-time bidirectional WebSocket stream for live emergency alerts.

### Step 4: Outputs, Dashboards & Mobile Endpoints
- `GET /api/v1/mobile/flood-map`: Inundation polygons formatted for mobile app display.
- `POST /api/v1/mobile/sos`: One-tap SOS broadcast notifying nearest SDRF/NDRF rescue team with GPS coordinates.
- `GET /api/v1/mobile/alerts`: Multilingual emergency push notifications (Odia, Hindi, English).
- `GET /api/v1/mobile/citizen-profile`: Personalized citizen registration and district profile lookup.
- `GET /api/v1/authority/analytics`: Model accuracy metrics (IoU, Dice, RMSE, NSE) and subsystem health.
- `GET /api/v1/authority/infrastructure-risk`: Real-time risk exposure for hospitals, bridges, substations, and shelters.
- `GET /api/v1/authority/geofenced-citizens`: Spatial query of citizens currently inside active flood zones.
- `GET /api/v1/authority/system-status`: Complete operational status of all 4 pipeline stages.
- `GET /api/v1/public/rainfall-chart`: 72-hour multi-model ensemble forecast data formatted for Chart.js.
- `GET /api/v1/public/cap-feed`: Public OASIS CAP v1.2 emergency alert bulletin feed.
- `GET /api/v1/public/inundation-polygons`: Public GeoJSON inundation contours for web mapping.
- `GET /`: FloodGuard Home Gateway with 3D "Enter FloodGuard" button and dual dashboard gateway.
- `GET /public`: Public Flood Information Dashboard (Citizen Web — 100% responsive, real-time flood map, 4 action buttons, SOS help, rainfall chart, alerts feed).
- `GET /authority`: Authority Control Dashboard (Incident Analytics, geofenced alerts map, infrastructure risk matrix).
- `GET /dashboard`: Master Enterprise Operations Dashboard (Dark glassmorphism command center).
- `GET /mobile`: Interactive Citizen Mobile App Preview Simulator with SOS broadcast.


### Step 5: Integration, Scaling & Deployment Endpoints
- `GET /api/v1/scaling/health`: Multi-region cluster health aggregation (India, Southeast Asia, Africa).
- `GET /api/v1/scaling/metrics`: Prometheus-compatible platform KPI metrics summary.
- `GET /api/v1/scaling/regions`: Active multi-cloud deployment regions status, basin coverage & latencies.
- `GET /api/v1/scaling/cicd-status`: GitHub Actions CI/CD pipeline status, test results & Docker image registry.
- `GET /metrics`: Prometheus scraping target exposing request latency, counts, and active connections.
- `POST /api/v1/auth/token`: OAuth2-compatible JWT access token generation for authority roles.
- `GET /api/v1/auth/verify`: Bearer token validation and claims verification.

### Citizen Directory Endpoints
- `POST /api/v1/citizens/register`: Register citizen with GPS, FCM token, WhatsApp opt-in, language preference.
- `GET /api/v1/citizens`: List all registered citizens (filter by `district` query param).

---

## Deployment & Production Scaling (Step 5)

### 1. Docker Multi-Stage Containerization
Build the optimized production Docker image:
```powershell
docker build -f docker/Dockerfile -t ghcr.io/floodguard-ai/floodguard:latest .
```

Run local multi-container stack (FastAPI + Redis + PostGIS + Prometheus + Grafana):
```powershell
cd docker
docker-compose up -d --build
```

### 2. Kubernetes Cluster Deployment
Deploy all microservices, services, autoscaling, and ingress into your Kubernetes cluster:
```powershell
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

### 3. Monitoring & Observability
- **Prometheus Scrape Config**: Located at `monitoring/prometheus.yml`, preconfigured to scrape `/metrics` across all pods.
- **Grafana Dashboard**: Import `monitoring/grafana_dashboard.json` into Grafana for real-time visualization of request rates, P99 latency heatmaps, error codes, and active connections.

---

## Verification & Automated Tests

Run the complete test suite across all modules:
```powershell
python -m pytest tests/ -v
```
**Result**: **109 passed**, 0 failures, 0 warnings — 100% pass rate across all 5 steps!

| Test Suite | Tests | Coverage |
|---|---|---|
| `test_ingestion.py` | 7 | Step 1 — NASA GPM, IMD, DWR, DEM, Ingestion Engine, API |
| `test_forecast_inundation.py` | 6 | Step 2 — LSTM/U-Net/PostGIS core |
| `test_step2_checklist.py` | 24 | Step 2 — Full checklist (bias, IoU, RMSE, registry, fallback, tile, LoRA) |
| `test_alerts.py` | 3 | Step 3 — CAP v1.2 generation & dispatch |
| `test_serve_alert.py` | 6 | Step 3 — Twilio SMS/WhatsApp/Voice, FCM, WebSocket |
| `test_checklist_step3.py` | 8 | Step 3 — Citizens, geofence, FCM, SendGrid, Fast2SMS |
| `test_step4_dashboards.py` | 12 | Step 4 — Mobile app, SOS, Authority panel, Public dashboard, HTML UI |
| `test_step4_checklist.py` | 11 | Step 4 Checklist — Mobile, Authority, Public, PostGIS & APIs |
| `test_step5_scaling.py` | 32 | Step 5 — Multi-region health, Prometheus metrics, K8s manifests, Docker, CI/CD, Auth |
| **Total** | **109** | **All Steps 1 + 2 + 3 + 4 + 5 Fully Verified** |



