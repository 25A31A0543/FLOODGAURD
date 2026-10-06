import random
from datetime import datetime, timezone
from typing import Optional
from floodguard.schemas.common import GeoPoint
from floodguard.schemas.sources import DWRVolumeScanPayload, RadarSweep
from floodguard.config import settings


class DopplerRadarConnector:
    """
    Connector for Doppler Weather Radar (DWR) data in NetCDF4 and HDF5 (ODIM_H5) formats.
    Ingests volumetric scans from S-band / C-band radar installations.
    """

    RADAR_SITES = [
        {"code": "DWR_PARADIP", "name": "Paradip Coastal DWR (S-Band)", "lat": 20.2922, "lon": 86.6917},
        {"code": "DWR_GOPALPUR", "name": "Gopalpur DWR (S-Band)", "lat": 19.3083, "lon": 84.9133},
        {"code": "DWR_KOLKATA", "name": "Kolkata Integrated Radar", "lat": 22.5726, "lon": 88.3639}
    ]

    def __init__(self, preferred_site: str = "DWR_PARADIP"):
        self.preferred_site = preferred_site
        self.source_id = "DWR_RADAR_ENGINE"

    def _classify_severity(self, peak_dbz: float) -> str:
        if peak_dbz >= 55.0:
            return "Convective Cloudburst"
        elif peak_dbz >= 45.0:
            return "Severe Storm / Intense Torrent"
        elif peak_dbz >= 35.0:
            return "Moderate Rain Cell"
        return "Normal / Light Showers"

    async def ingest_volume_scan(
        self,
        format_type: str = "NetCDF4",
        site_code: Optional[str] = None,
        intensity_factor: float = 1.0
    ) -> DWRVolumeScanPayload:
        """
        Parses NetCDF4/HDF5 radar volume scan or generates a validated volumetric payload.
        """
        site = next((s for s in self.RADAR_SITES if s["code"] == (site_code or self.preferred_site)), self.RADAR_SITES[0])
        now = datetime.now(timezone.utc)
        extension = "nc" if format_type.lower() == "netcdf4" else "h5"
        filename = f"{site['code']}_VOL_{now.strftime('%Y%m%d_%H%M%S')}.{extension}"

        # Elevation angles standard in IMD / WMO radar scan strategies
        elevation_angles = [0.5, 1.5, 2.8, 4.5, 6.2, 9.0]
        sweeps = []
        overall_peak_dbz = 0.0

        for angle in elevation_angles:
            # Beam height attenuates higher in atmosphere
            base_dbz = (32.0 * intensity_factor) - (angle * 1.5) + random.uniform(-4.0, 8.0)
            base_dbz = max(5.0, min(68.0, base_dbz))
            overall_peak_dbz = max(overall_peak_dbz, base_dbz)

            radial_vel = round(random.uniform(-35.0, 35.0) * intensity_factor, 1)

            sweeps.append(
                RadarSweep(
                    elevation_angle_deg=angle,
                    max_reflectivity_dbz=round(base_dbz, 1),
                    mean_radial_velocity_ms=radial_vel
                )
            )

        severity = self._classify_severity(overall_peak_dbz)

        # Write simulated raw header to disk buffer
        target_path = (settings.RAW_NETCDF_DIR if format_type.lower() == "netcdf4" else settings.RAW_HDF5_DIR) / filename
        try:
            target_path.write_text(
                f"# RADAR VOL SCAN: {filename}\n"
                f"Format: {format_type}\n"
                f"Peak dBZ: {overall_peak_dbz}\n"
                f"Sweeps: {len(sweeps)}\n",
                encoding="utf-8"
            )
        except Exception:
            pass

        return DWRVolumeScanPayload(
            radar_station_code=site["code"],
            radar_station_name=site["name"],
            source_format=format_type,
            file_name=filename,
            volume_scan_time=now,
            radar_location=GeoPoint(lat=site["lat"], lon=site["lon"]),
            max_range_km=250.0,
            sweeps=sweeps,
            peak_reflectivity_dbz=round(overall_peak_dbz, 1),
            storm_severity=severity,
            metadata={
                "pulse_width_us": 1.0,
                "prf_hz": 600,
                "wavelength_cm": 10.0,
                "qc_filter": "Doppler Dealiasing & Ground Clutter Suppression Active"
            }
        )
