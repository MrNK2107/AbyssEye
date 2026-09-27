from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from typing import Dict, Any, List, Optional
import os
import tempfile

from backend.app.api.endpoints.contacts import CONTACTS_STORE
from backend.app.services.report_exporter import MissionReportExporter

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
