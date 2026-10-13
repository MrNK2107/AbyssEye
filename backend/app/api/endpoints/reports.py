from fastapi import APIRouter, HTTPException, Query, Response
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Optional
import os
import tempfile
import json

from backend.app.api.endpoints.contacts import CONTACTS_STORE
from backend.app.services.report_exporter import MissionReportExporter
from backend.app.services.reports_pdf import generate_pdf_report

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
def get_mission_summary(survey_id: Optional[str] = "SRV-BALTIC-NORTH-04"):
    contacts_list = list(CONTACTS_STORE.values())
    report = MissionReportExporter.generate_json_report(survey_id or "SURVEY-ALL", contacts_list)
    return report

@router.get("/export/csv")
def export_csv_report(survey_id: Optional[str] = "SRV-BALTIC-NORTH-04"):
    contacts_list = list(CONTACTS_STORE.values())
    temp_dir = tempfile.gettempdir()
    csv_file = os.path.join(temp_dir, f"abysseye_report_{survey_id}.csv")
    MissionReportExporter.export_csv(contacts_list, csv_file)

    return FileResponse(
        path=csv_file,
        filename=f"abysseye_debris_report_{survey_id}.csv",
        media_type="text/csv"
    )

@router.get("/export/pdf")
def export_pdf_report(survey_id: Optional[str] = "SRV-BALTIC-NORTH-04"):
    contacts_list = list(CONTACTS_STORE.values())
    pdf_bytes = generate_pdf_report(contacts_list, survey_title=f"Survey {survey_id}")
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="abysseye_survey_report_{survey_id}.pdf"'}
    )

@router.get("/export/geojson")
def export_geojson_report(survey_id: Optional[str] = "SRV-BALTIC-NORTH-04"):
    contacts_list = list(CONTACTS_STORE.values())
    features = []
    for c in contacts_list:
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
                    "target_type": c.get("target_type_hint"),
                    "triage_state": c.get("triage_state"),
                    "confidence": c.get("fusion_decision", {}).get("calibrated_probabilities", {}).get("p_anthropogenic", 0.0),
                    "estimated_height_m": c.get("evidence_graph", {}).get("acoustic_physics", {}).get("estimated_target_height_m", 0.0)
                }
            })

    geojson_doc = {
        "type": "FeatureCollection",
        "features": features
    }

    return Response(
        content=json.dumps(geojson_doc, indent=2),
        media_type="application/geo+json",
        headers={"Content-Disposition": f'attachment; filename="abysseye_contacts_{survey_id}.geojson"'}
    )
