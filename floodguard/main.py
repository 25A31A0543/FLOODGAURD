from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from floodguard.middleware.metrics import PrometheusMiddleware

from floodguard.config import settings
from floodguard.api.routes import router as api_router
from floodguard.services.engine import ingestion_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager: seed the buffer on startup."""
    try:
        await ingestion_engine.run_unified_ingestion_cycle(storm_intensity=1.0)
    except Exception as e:
        print(f"Startup ingestion sync failed: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="FloodGuard Step 1: Unified Ingestion Engine for NASA GPM, IMD, Doppler Radar & DEM.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Enable CORS for cross-origin dashboard widgets or web integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Prometheus metrics middleware (Step 5)
app.add_middleware(PrometheusMiddleware)
# Register API Router
app.include_router(api_router)

# Mount static files directory
from fastapi.staticfiles import StaticFiles
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")




# ------------------ LIVE WEBSOCKET CHANNELS ------------------
from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

class LiveAlertConnectionManager:
    """Manages real-time bidirectional WebSocket connections for instant alert broadcasts."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                self.disconnect(connection)

ws_alert_manager = LiveAlertConnectionManager()


@app.websocket("/ws/v1/live-alerts")
async def websocket_live_alerts_endpoint(websocket: WebSocket):
    """
    WebSocket channel for real-time live alert and hydrological telemetry push.
    Clients receive instant broadcasts when new flood alerts or emergency orders are published.
    """
    await ws_alert_manager.connect(websocket)
    try:
        # Send initial connection handshake
        await websocket.send_json({
            "event": "CONNECTED",
            "message": "Connected to FloodGuard Real-Time Live Alert Channel",
            "service": "Step 3: Serve & Alert"
        })
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({"event": "HEARTBEAT_ACK", "client_message": data})
    except WebSocketDisconnect:
        ws_alert_manager.disconnect(websocket)



@app.get("/", response_class=HTMLResponse, include_in_schema=False)
@app.get("/home", response_class=HTMLResponse, include_in_schema=False)
async def home_page():
    """Serve the FloodGuard Home Landing Gateway."""
    template_path = Path(__file__).parent / "templates" / "home.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>Home template not found</h3>", status_code=404)


@app.get("/public", response_class=HTMLResponse, include_in_schema=False)
async def public_dashboard():
    """Serve the Public Flood Information Dashboard (Citizen Web)."""
    template_path = Path(__file__).parent / "templates" / "public.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>Public dashboard template not found</h3>", status_code=404)


@app.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard():
    """Serve the interactive Step 4 Public Web Monitoring Dashboard."""
    template_path = Path(__file__).parent / "templates" / "dashboard.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>Dashboard template not found</h3>", status_code=404)


@app.get("/authority", response_class=HTMLResponse, include_in_schema=False)
async def authority_panel():
    """Serve the interactive Step 4 Authority Control Panel."""
    template_path = Path(__file__).parent / "templates" / "authority.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>Authority template not found</h3>", status_code=404)


@app.get("/mobile", response_class=HTMLResponse, include_in_schema=False)
@app.get("/citizen", response_class=HTMLResponse, include_in_schema=False)
async def mobile_app():
    """Serve the interactive FloodGuard Citizen Alert & SOS Interface (Web & Mobile)."""
    template_path = Path(__file__).parent / "templates" / "citizen.html"
    if not template_path.exists():
        template_path = Path(__file__).parent / "templates" / "mobile.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>Citizen alert interface template not found</h3>", status_code=404)


@app.get("/sos", response_class=HTMLResponse, include_in_schema=False)
async def sos_page():
    """Serve the FloodGuard Real-Time SOS Communication System (Twilio integrated)."""
    template_path = Path(__file__).parent / "templates" / "sos.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>SOS interface template not found</h3>", status_code=404)


@app.get("/3d", response_class=HTMLResponse, include_in_schema=False)
@app.get("/flood-intelligence", response_class=HTMLResponse, include_in_schema=False)
async def flood_intelligence_3d_page():
    """Serve the FloodGuard 3D Flood Intelligence & Early Warning System."""
    template_path = Path(__file__).parent / "templates" / "flood_intelligence_3d.html"
    if template_path.exists():
        return HTMLResponse(content=template_path.read_text(encoding="utf-8"))
    return HTMLResponse("<h3>3D Flood Intelligence template not found</h3>", status_code=404)



from fastapi.responses import FileResponse

@app.get("/download-zip", summary="Download Complete FloodGuard Project Zip")
async def download_project_zip():
    """Download the complete FloodGuard project as a zip file."""
    zip_path = Path("C:/Users/sony/Desktop/FLOODGUARD_COMPLETE.zip")
    if zip_path.exists():
        return FileResponse(
            path=str(zip_path),
            filename="FLOODGUARD_COMPLETE.zip",
            media_type="application/zip"
        )
    return HTMLResponse("<h3>Zip file not found</h3>", status_code=404)





if __name__ == "__main__":
    import uvicorn
    uvicorn.run("floodguard.main:app", host="127.0.0.1", port=8000, reload=True)


# ------------------ PROMETHEUS METRICS ENDPOINT ------------------
from fastapi.responses import Response as FastAPIResponse
from floodguard.middleware.metrics import get_metrics_response

@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """Prometheus scrape endpoint â€” exposes FloodGuard platform metrics."""
    return get_metrics_response()

