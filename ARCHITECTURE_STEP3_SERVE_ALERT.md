# FloodGuard — Step 3: Serve & Alert System Architecture

## Architecture Diagram
The architecture design incorporates outputs from Step 2 (rainfall forecasts and flood polygons) flowing into backend services, multi-channel alerting networks, and citizen response interfaces.

```
+-----------------------------------------------------------------------------------------------------------------------------+
|                                              FloodGuard — Step 3: Serve & Alert                                             |
+-----------------------------------------------------------------------------------------------------------------------------+

 [STEP 2: Model Outputs]    [BACKEND APIs - Blue]               [MULTI-CHANNEL ALERTS - Red]        [CITIZEN INTERFACES - Green]

 +------------------------+   +-------------------------------+   +-------------------------------+   +-----------------------+
 | 🌧️ 72-hr Rainfall      |-->| 🌐 API Gateway                |-->| 📱 Twilio SMS / Fast2SMS      |-->| 📲 Citizen Mobile App |
 |    Forecast Ensemble   |   |    • Rate limiting & security |   |    • Geo-targeted SMS alerts  |   |    • Risk radar & GPS |
 +------------------------+   |                               |   +-------------------------------+   |    • Evacuation route |
                              | ⚡ FastAPI REST APIs          |                                       +-----------------------+
 +------------------------+   |    • Vector tile map service  |   +-------------------------------+               |
 | 🟢 Flood Inundation    |-->|    • PostGIS spatial queries  |-->| 💬 WhatsApp Business API      |               |
 |    Polygons (GeoJSON)  |   |                               |   |    • Rich media bulletins     |               v
 +------------------------+   | 🔄 WebSocket Live Engine      |   +-------------------------------+   +-----------------------+
                              |    • Real-time broadcast push |                                       | 💻 Emergency Ops      |
                              |                               |   +-------------------------------+   |    Dashboards (NDRF)  |
                              | 🚨 Alert Orchestration Engine |-->| 🔔 Firebase FCM Push          |-->|    • Live status map  |
                              |    • OASIS CAP v1.2 generator |   |    • Low-latency mobile push  |   |    • Rescue dispatch  |
                              |    • Infrastructure exposure  |   +-------------------------------+   +-----------------------+
                              +-------------------------------+                                               |
                                              |                   +-------------------------------+           |
                                              |------------------>| ✉️ SendGrid Email             |           v
                                              |                   |    • Official agency reports  |   +-----------------------+
                                              |                   +-------------------------------+   | 📢 Community          |
                                              |                                                       |    Loudspeakers       |
                                              |                   +-------------------------------+   |    & Sirens           |
                                              |------------------>| 📞 Twilio Voice Calls         |-->|    • Acoustic warning |
                                              |                   |    • Automated TTS voice IVR  |   |    • Offline radio    |
                                              |                   +-------------------------------+   +-----------------------+
                                              |                                                               ^
                                              |                   +-------------------------------+           |
                                              +------------------>| 🚨 Emergency Sirens & Radio   |-----------+
                                                                  |    • VHF/FM broadcast towers  |
                                                                  +-------------------------------+
```

---

## 1. Backend APIs & Ingress (Blue)
- **API Gateway & Fast Routing**: Orchestrates requests across API instances with rate limiting, SSL termination, and caching.
- **REST APIs (FastAPI)**:
  - Vector tile generation for Mapbox/Leaflet mapping engines (`/api/v1/spatial/polygons`).
  - Spatial aggregation via PostGIS `ST_Area` queries (`/api/v1/spatial/st-area`).
  - Forecast time series retrieval (`/api/v1/forecast/latest`).
- **WebSocket Live Channels**:
  - Pushes sub-second telemetry, gauge sensor spikes, and polygon updates to web dashboards and mobile clients.
- **Alert Orchestration Engine**:
  - Implements **OASIS Common Alerting Protocol (CAP v1.2)** standards.
  - Computes structural risk exposure across critical facilities (Hospitals, Bridges, Power Substations, Cyclone Shelters).

---

## 2. Multi-Channel Alerting Services (Red)
- **Twilio SMS & Fast2SMS**: Cellular broadcast alerts to mobile devices within threatened floodplains.
- **WhatsApp Business API**: Evacuation route cards, live shelter locations, and multi-lingual emergency bulletins.
- **Firebase Cloud Messaging (FCM)**: Urgent push banners for Android and iOS devices (`flooddaurd` project).
- **Twilio Media Stream (Voice IVR)**: Text-to-speech outbound calls for high-risk rural areas and landlines.
- **SendGrid Email**: Comprehensive situational reports (SITREPs) with CAP XML attachments for government authorities.
- **Offline Radio Towers & Sirens**: VHF radio triggers for public address siren networks during cellular tower blackouts.

---

## 3. Citizen Interfaces & Public Safety (Green)
- **Citizen Mobile Applications**: Real-time proximity hazard alerts, offline emergency guidelines, and safe muster points.
- **Emergency Operation Center (EOC) Dashboards**: Interactive GIS tactical interface for NDRF and State Disaster Management.
- **Community Loudspeakers**: Decibel-boosted sirens and siren sequences signaling immediate evacuation.

---

## 4. Credentials & Configuration
- **Twilio Account SID**: Set via `TWILIO_ACCOUNT_SID` environment variable
- **Twilio Phone**: Set via `TWILIO_PHONE_NUMBER` environment variable
- **Firebase Project**: `flooddaurd` (`floodguard/config/firebase_credentials.json`)
