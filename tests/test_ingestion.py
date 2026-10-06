import asyncio
from fastapi.testclient import TestClient
from floodguard.main import app
from floodguard.connectors.nasa_gpm import NASAGPMConnector
from floodguard.connectors.imd_weather import IMDWeatherConnector
from floodguard.connectors.radar_dwr import DopplerRadarConnector
from floodguard.connectors.dem_terrain import DEMTerrainConnector
from floodguard.services.engine import ingestion_engine

client = TestClient(app)


def test_nasa_gpm_connector():
    async def _test():
        connector = NASAGPMConnector()
        payload = await connector.fetch_swath_data(simulated_monsoon_intensity=1.2)
        assert payload.granule_id is not None
        assert payload.mean_precipitation_mm_hr >= 0.0
        assert payload.max_precipitation_mm_hr >= payload.mean_precipitation_mm_hr
        assert len(payload.grid_cells) == 25  # 5x5 grid
        assert payload.grid_cells[0].precipitation_rate >= 0.0
        assert payload.metadata["token_authenticated"] is True
        assert payload.metadata["earthdata_user"] == "abhishekmallina"
    asyncio.run(_test())


def test_imd_weather_connector():
    async def _test():
        connector = IMDWeatherConnector()
        payload = await connector.fetch_station_telemetry(storm_boost=1.5)
        assert payload.total_stations == len(connector.STATION_CATALOG)
        assert payload.max_station_rain_24h_mm > 0.0
        assert payload.metadata["api_key_authenticated"] is True
        assert payload.metadata["key_masked"].startswith("sk-live-Ztpq")
        assert payload.metadata["key_masked"].endswith("CJht")
        for st in payload.stations:
            assert st.rainfall_last_1h_mm >= 0.0
            assert st.rainfall_last_24h_mm >= st.rainfall_last_1h_mm
            assert st.imd_alert_level in ["Green", "Yellow", "Orange", "Red"]
    asyncio.run(_test())


def test_radar_dwr_connector():
    async def _test():
        connector = DopplerRadarConnector(preferred_site="DWR_PARADIP")
        # Test NetCDF4 format
        nc_payload = await connector.ingest_volume_scan(format_type="NetCDF4", intensity_factor=1.3)
        assert nc_payload.source_format == "NetCDF4"
        assert nc_payload.file_name.endswith(".nc")
        assert len(nc_payload.sweeps) > 0
        assert nc_payload.peak_reflectivity_dbz >= 5.0
        assert nc_payload.storm_severity in [
            "Normal / Light Showers",
            "Moderate Rain Cell",
            "Severe Storm / Intense Torrent",
            "Convective Cloudburst"
        ]

        # Test HDF5 format
        h5_payload = await connector.ingest_volume_scan(format_type="HDF5", intensity_factor=1.0)
        assert h5_payload.source_format == "HDF5"
        assert h5_payload.file_name.endswith(".h5")
    asyncio.run(_test())


def test_dem_terrain_connector():
    async def _test():
        connector = DEMTerrainConnector()
        payload = await connector.ingest_dem_raster(resolution_m=30.0)
        assert payload.min_elevation_m <= payload.max_elevation_m
        assert payload.mean_slope_degrees >= 0.0
        assert 0.0 <= payload.flood_susceptibility_index <= 1.0
        assert payload.sample_elevation_matrix is not None
        assert len(payload.sample_elevation_matrix) == 6
        assert payload.metadata["api_key_authenticated"] is True
        assert payload.metadata["key_masked"].startswith("c569")
        assert payload.metadata["key_masked"].endswith("0edc")
        assert "Elevation (meters)" in payload.metadata["topography_parameters"]
        assert "Slope gradient" in payload.metadata["topography_parameters"]
        assert "Aspect (azimuth)" in payload.metadata["topography_parameters"]
        assert "Drainage basins (catchment routing)" in payload.metadata["topography_parameters"]
    asyncio.run(_test())


def test_unified_engine_full_cycle():
    async def _test():
        frame = await ingestion_engine.run_unified_ingestion_cycle(storm_intensity=1.4)
        assert frame.frame_id.startswith("FRAME_")
        assert frame.gpm_satellite is not None
        assert frame.imd_weather is not None
        assert frame.dwr_radar is not None
        assert frame.dem_terrain is not None
        assert frame.composite_rainfall_rate_mm_hr >= 0.0
        assert frame.flood_warning_grade in ["NORMAL", "WATCH", "WARNING", "SEVERE EMERGENCY"]
    asyncio.run(_test())


def test_api_status_endpoint():
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert "nasa_gpm" in data["pipeline_sources"]
    assert "imd_weather" in data["pipeline_sources"]
    assert "dwr_radar" in data["pipeline_sources"]
    assert "dem_terrain" in data["pipeline_sources"]


def test_api_ingest_endpoints():
    # 1. GPM endpoint
    res_gpm = client.post("/api/v1/ingest/nasa-gpm?storm_intensity=1.0")
    assert res_gpm.status_code == 200
    assert res_gpm.json()["status"] == "SUCCESS"

    # 2. IMD endpoint
    res_imd = client.post("/api/v1/ingest/imd?storm_boost=1.0")
    assert res_imd.status_code == 200
    assert res_imd.json()["status"] == "SUCCESS"

    # 3. DWR NetCDF endpoint
    res_dwr = client.post("/api/v1/ingest/dwr?format_type=NetCDF4&storm_intensity=1.1")
    assert res_dwr.status_code == 200
    assert res_dwr.json()["status"] == "SUCCESS"

    # 4. DEM endpoint
    res_dem = client.post("/api/v1/ingest/dem")
    assert res_dem.status_code == 200
    assert res_dem.json()["status"] == "SUCCESS"

    # 5. Full sync endpoint
    res_sync = client.post("/api/v1/ingest/sync-all?storm_intensity=1.3")
    assert res_sync.status_code == 200
    assert "frame_id" in res_sync.json()

    # 6. Latest telemetry endpoint
    res_latest = client.get("/api/v1/telemetry/latest")
    assert res_latest.status_code == 200
    assert res_latest.json() is not None

    # 7. Dashboard endpoint
    res_dash = client.get("/dashboard")
    assert res_dash.status_code == 200
    assert "FloodGuard" in res_dash.text
