"""India Operational Layer: Maritime Recovery & Coastal Port Logistics for MoES / NIOT.

Calculates Great Circle distances and estimated vessel transit times from
side-scan survey detections to major Indian ports & naval bases.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

M_PER_NM = 1852.0  # metres per nautical mile

INDIAN_PORTS = [
    {"name": "Chennai Port (NIOT HQ)", "lat": 13.1000, "lon": 80.2965, "state": "Tamil Nadu"},
    {"name": "Visakhapatnam (Vizag) Port", "lat": 17.6868, "lon": 83.2185, "state": "Andhra Pradesh"},
    {"name": "Kochi Port", "lat": 9.9656, "lon": 76.2629, "state": "Kerala"},
    {"name": "Mormugao Port (Goa)", "lat": 15.4107, "lon": 73.8055, "state": "Goa"},
    {"name": "Port Blair (Andaman & Nicobar)", "lat": 11.6680, "lon": 92.7380, "state": "Andaman & Nicobar"},
    {"name": "Mumbai Port", "lat": 18.9438, "lon": 72.8358, "state": "Maharashtra"},
    {"name": "Paradip Port", "lat": 20.2644, "lon": 86.6738, "state": "Odisha"},
    {"name": "Tuticorin (V.O.C) Port", "lat": 8.7528, "lon": 78.1884, "state": "Tamil Nadu"},
]

@dataclass
class PortDistance:
    port_name: str
    state: str
    distance_nm: float
    distance_km: float
    est_transit_hours: float  # Assumes standard 12 knot NIOT survey vessel speed


def haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in Nautical Miles between two lat/lon points."""
    r_nm = 3440.065  # Earth radius in nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)

    a = math.sin(dphi / 2.0) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r_nm * c


def find_nearest_indian_ports(lat: float, lon: float, top_k: int = 3, cruise_knots: float = 12.0) -> list[PortDistance]:
    """Return top_k nearest Indian operational ports with distance & transit time."""
    results: list[PortDistance] = []
    for port in INDIAN_PORTS:
        dist_nm = haversine_nm(lat, lon, port["lat"], port["lon"])
        dist_km = dist_nm * 1.852
        transit_hours = dist_nm / cruise_knots if cruise_knots > 0 else 0.0

        results.append(
            PortDistance(
                port_name=port["name"],
                state=port["state"],
                distance_nm=round(dist_nm, 1),
                distance_km=round(dist_km, 1),
                est_transit_hours=round(transit_hours, 1),
            )
        )

    results.sort(key=lambda p: p.distance_nm)
    return results[:top_k]
