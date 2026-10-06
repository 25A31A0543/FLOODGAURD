# FloodGuard — Step 1: Data Ingestion

## System Architecture Diagram

`
+-------------------------------------------------------------+
|               FloodGuard — Step 1: Data Ingestion           |
+-------------------------------------------------------------+

 [Data Sources - Blue]                         [Ingestion Engine - Orange]

 +------------------------------+
 |  🛰️ NASA GPM Satellite Feeds |
 |     Precipitation data       |----+
 +------------------------------+    |
                                     |
 +------------------------------+    |     +-------------------------------------+
 |   🌡️ IMD Weather APIs        |    |     |  Unified Ingestion Engine           |
 |     Observations & forecasts |----+---->|  (FastAPI / Django)                 |
 +------------------------------+    |     |                                     |
                                     |     |  • Schema validation                |
 +------------------------------+    |     |  • NetCDF / HDF5 parser             |
 |  📡 Doppler Weather Radar    |----+     |  • Rate-limiting                    |
 |     NetCDF/HDF5 formats      |    |     |  • Queue workers                    |
 +------------------------------+    |     +-------------------------------------+
                                     |
 +------------------------------+    |
 |  🗺️ Digital Elevation Models |----+
 |     Topography & Elevation   |
 +------------------------------+
`

### Components Summary

1. **NASA GPM Satellite Feeds (Blue / Satellite Icon)**:
   - Near real-time satellite rainfall estimates (IMERG Early/Late run).
   - Multi-satellite constellation precipitation measurements.

2. **IMD Weather APIs (Blue / Weather Station Icon)**:
   - Ground observational automated weather station (AWS) feeds.
   - Authenticated via IMD API Key (`sk-live-Ztpq...CJht`).
   - Point rainfall, temperature, atmospheric pressure, and forecast alerts.

3. **Doppler Weather Radar - DWR (Blue / Radar Dish Icon)**:
   - High spatial-temporal resolution precipitation & reflectivity data.
   - Formatted in binary multidimensional NetCDF4 / HDF5 files.

4. **Digital Elevation Models - DEM (Blue / Terrain Map Icon)**:
   - Static topographical datasets (SRTM, CartoDEM, Copernicus Global DEM 30m).
   - Format: GeoTIFF / Cloud-Optimized GeoTIFF (COG).
   - Authenticated via DEM API Key (`c569...0edc`).
   - Ingests: Elevation (meters), slope gradient, aspect, and drainage basins.

5. **Unified Ingestion Engine (Orange / Cloud Server Icon)**:
   - Built on **FastAPI / Django** with Celery/Redis asynchronous workers.
   - Multi-format ingestion pipelines (parsing NetCDF, HDF5, GeoTIFF, REST JSON).
   - Strict Pydantic/dataclass schema validation, coordinate reference system (CRS) normalization, and queuing for downstream flood prediction models.
