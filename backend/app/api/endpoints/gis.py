from fastapi import APIRouter
from typing import Dict, Any, List
from backend.app.api.endpoints.contacts import CONTACTS_STORE

router = APIRouter()

@router.get("/contacts", response_model=Dict[str, Any])
def get_contacts_geojson():
    features = []
    for c in CONTACTS_STORE.values():
        telemetry = c.get("spatial_telemetry", {})
        lat = telemetry.get("latitude")
        lon = telemetry.get("longitude")

        if lat is not None and lon is not None:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": {
                    "contact_id": c.get("contact_id"),
                    "survey_id": c.get("survey_id"),
                    "triage_state": c.get("triage_state"),
                    "target_type_hint": c.get("target_type_hint"),
                    "p_anthropogenic": c.get("fusion_decision", {}).get("calibrated_probabilities", {}).get("p_anthropogenic", 0.0),
                    "estimated_height_m": c.get("evidence_graph", {}).get("acoustic_physics", {}).get("estimated_target_height_m", 0.0),
                    "error_radius_m": telemetry.get("position_error_radius_m", 2.0)
                }
            })

    return {
        "type": "FeatureCollection",
        "features": features
    }

@router.get("/tracks", response_model=Dict[str, Any])
def get_survey_tracks_geojson():
    # Baltic Sea survey demonstration tracklines
    trackline_coords = [
        [18.7300, 54.8200],
        [18.7320, 54.8210],
        [18.7340, 54.8220],
        [18.7360, 54.8230],
        [18.7380, 54.8240]
    ]

    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": {
                    "type": "LineString",
                    "coordinates": trackline_coords
                },
                "properties": {
                    "survey_id": "SRV-BALTIC-NORTH-04",
                    "vessel": "RV OceanExplorer",
                    "sensor": "EdgeTech 4200-MP (900kHz)",
                    "swath_width_m": 100.0
                }
            }
        ]
    }
