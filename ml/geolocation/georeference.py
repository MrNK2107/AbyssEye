import numpy as np
from typing import Optional, Tuple, Dict, Any

class SonarGeoreferencer:
    """
    Georeferencing & Navigation Ray-Tracing Engine.
    Transforms side-scan sonar image coordinates (ping, col) into WGS84 (latitude, longitude)
    using vessel position, heading, altitude, and across-track ground range.
    """

    # Earth radius in meters (WGS84 approx)
    EARTH_RADIUS_M = 6378137.0

    @classmethod
    def calculate_contact_coordinates(
        cls,
        vessel_lat: Optional[float],
        vessel_lon: Optional[float],
        heading_deg: Optional[float],
        across_track_m: float,
        is_starboard: bool,
        pixel_error_m: float = 2.0
    ) -> Dict[str, Any]:
        """
        Ray-traces target position from vessel telemetry.
        """
        if vessel_lat is None or vessel_lon is None:
            return {
                "latitude": None,
                "longitude": None,
                "position_error_radius_m": None,
                "geolocation_quality": "UNAVAILABLE",
                "across_track_m": round(across_track_m, 2)
            }

        if heading_deg is None:
            heading_deg = 0.0

        # Sonar beam angle perpendicular to vessel track
        # Starboard is +90 deg relative to heading, Port is -90 deg
        beam_bearing_deg = (heading_deg + 90.0) if is_starboard else (heading_deg - 90.0)
        beam_bearing_rad = np.radians(beam_bearing_deg % 360.0)

        # Distance offset along beam bearing
        dist_m = abs(across_track_m)
        angular_dist = dist_m / cls.EARTH_RADIUS_M

        lat1 = np.radians(vessel_lat)
        lon1 = np.radians(vessel_lon)

        lat2 = np.arcsin(np.sin(lat1) * np.cos(angular_dist) + np.cos(lat1) * np.sin(angular_dist) * np.cos(beam_bearing_rad))
        lon2 = lon1 + np.arctan2(
            np.sin(beam_bearing_rad) * np.sin(angular_dist) * np.cos(lat1),
            np.cos(angular_dist) - np.sin(lat1) * np.sin(lat2)
        )

        target_lat = float(np.degrees(lat2))
        target_lon = float(np.degrees(lon2))

        # Geolocation error estimate increases with range
        est_error_m = float(pixel_error_m + 0.03 * dist_m)

        return {
            "latitude": round(target_lat, 6),
            "longitude": round(target_lon, 6),
            "position_error_radius_m": round(est_error_m, 1),
            "geolocation_quality": "HIGH" if dist_m < 75.0 else "MEDIUM",
            "across_track_m": round(across_track_m, 2)
        }
