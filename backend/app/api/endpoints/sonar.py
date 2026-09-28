from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
import shutil
import cv2
import time
import asyncio
import numpy as np

from backend.app.core.config import settings
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator
from backend.app.services.mission_streamer import mission_streamer
from ml.ingestion.sonar_parser import SonarParser
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator
from backend.app.api.endpoints.contacts import CONTACTS_STORE
from backend.app.api.endpoints.ws import manager

router = APIRouter()
orchestrator = PipelineOrchestrator()

class ProcessSurveyRequest(BaseModel):
    survey_id: str
    file_path: str
    altitude_m: Optional[float] = 12.0
    slant_range_m: Optional[float] = 50.0

class GenerateSurveyRequest(BaseModel):
    survey_id: Optional[str] = "SRV-BALTIC-ACOUSTIC-01"
    num_pings: Optional[int] = 5
    seabed_type: Optional[str] = "sand_ripples"
    target_type: Optional[str] = "ghost_net"

class SelectMissionRequest(BaseModel):
    mission_key: str

class SeekPingRequest(BaseModel):
    ping_index: int

@router.get("/missions")
def list_missions():
    """Lists all preconfigured AUV missions and custom uploaded surveys."""
    return {
        "active_mission": mission_streamer.active_mission_key,
        "current_ping": mission_streamer.current_ping_idx,
        "missions": mission_streamer.get_available_missions()
    }

@router.post("/missions/select")
def select_mission(req: SelectMissionRequest):
    """Switches the active AUV simulation mission."""
    ok = mission_streamer.set_active_mission(req.mission_key)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Mission '{req.mission_key}' not found or empty.")
    
    payload = mission_streamer.get_current_frame_payload()
    if payload:
        for c in payload.get("contacts", []):
            CONTACTS_STORE[c["contact_id"]] = c
    return {
        "status": "SUCCESS",
        "active_mission": mission_streamer.active_mission_key,
        "current_ping": mission_streamer.current_ping_idx,
        "initial_payload": payload
    }

@router.post("/missions/seek")
def seek_mission_ping(req: SeekPingRequest):
    """Seeks to a specific ping in the active mission."""
    idx = mission_streamer.seek_ping(req.ping_index)
    payload = mission_streamer.get_current_frame_payload()
    if payload:
        for c in payload.get("contacts", []):
            CONTACTS_STORE[c["contact_id"]] = c
    return {
        "status": "SUCCESS",
        "ping_index": idx,
        "payload": payload
    }

@router.post("/missions/step")
async def step_mission_ping():
    """Advances one ping in the active mission and broadcasts to all WebSocket clients."""
    payload = mission_streamer.get_current_frame_payload()
    if payload:
        for c in payload.get("contacts", []):
            CONTACTS_STORE[c["contact_id"]] = c
        await manager.broadcast_json(payload)
    mission_streamer.advance_ping()
    return {"status": "SUCCESS", "payload": payload}

@router.post("/upload-zip-stream")
async def upload_zip_sonar_stream(
    file: UploadFile = File(...),
    survey_title: str = Form("Custom Side-Scan Sonar Survey")
):
    """
    Accepts a ZIP archive of sonar waterfall frames, extracts it,
    indexes navigation coordinates, and launches it as an active mission.
    """
    upload_dir = os.path.join(settings.UPLOAD_DIR, "zip_uploads")
    os.makedirs(upload_dir, exist_ok=True)
    temp_zip_path = os.path.join(upload_dir, file.filename)

    with open(temp_zip_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    try:
        mission_key = mission_streamer.ingest_zip_survey(temp_zip_path, survey_title)
        initial_payload = mission_streamer.get_current_frame_payload()
        return {
            "status": "SUCCESS",
            "message": "Custom sonar survey ingested and activated successfully.",
            "mission_key": mission_key,
            "missions": mission_streamer.get_available_missions(),
            "initial_payload": initial_payload
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/upload")
async def upload_sonar_file(
    file: UploadFile = File(...),
    survey_id: str = Form("SRV-UPLOAD-01")
):
    upload_dir = os.path.join(settings.UPLOAD_DIR, "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    saved_path = os.path.join(upload_dir, file.filename)

    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "status": "UPLOADED",
        "survey_id": survey_id,
        "filename": file.filename,
        "file_path": saved_path
    }

@router.post("/process")
def process_survey_file(req: ProcessSurveyRequest):
    if not os.path.exists(req.file_path):
        raise HTTPException(status_code=404, detail="Sonar file not found")

    record = SonarParser.load_from_file(
        image_path=req.file_path,
        survey_id=req.survey_id,
        altitude_m=req.altitude_m,
        slant_range_m=req.slant_range_m
    )

    qc_report, contacts = orchestrator.process_frame(record, ping_index=0)
    for c in contacts:
        CONTACTS_STORE[c["contact_id"]] = c

    return {
        "status": "COMPLETED",
        "survey_id": req.survey_id,
        "qc_report": qc_report.to_dict(),
        "contacts_count": len(contacts),
        "contacts": contacts
    }

@router.post("/generate-simulation")
async def generate_simulation_survey(req: GenerateSurveyRequest):
    """
    Generates a synthetic sonar survey with acoustic ray tracing.
    """
    survey_id = req.survey_id or "SRV-SIM-01"
    survey_dir = os.path.join("data", "simulations", survey_id)
    os.makedirs(survey_dir, exist_ok=True)

    gen = SyntheticSonarGenerator(
        height_pings=384,
        width_cols=768,
        altitude_m=12.0,
        max_slant_range_m=50.0
    )

    base_lat = 13.0827
    base_lon = 80.2707
    heading = 180.0

    created_contacts = []
    all_qc_reports = []

    for p_idx in range(req.num_pings or 5):
        t0 = time.time()
        canvas = gen.generate_seabed_background(seabed_type=req.seabed_type or "sand_ripples", seed=p_idx + 42)

        target_h = 1.2
        target_col = int(gen.width * 0.72)
        canvas_with_target, target_meta = gen.insert_target(
            canvas,
            target_type=req.target_type or "ghost_net",
            center_ping=gen.height // 2,
            center_col=target_col,
            target_height_m=target_h
        )

        file_path = os.path.join(survey_dir, f"ping_{p_idx:04d}.png")
        cv2.imwrite(file_path, canvas_with_target)

        cur_lat = base_lat - (p_idx * 0.00035)
        cur_lon = base_lon + (p_idx * 0.00008)

        record = SonarParser.load_from_file(
            image_path=file_path,
            survey_id=survey_id,
            ping_index=p_idx,
            altitude_m=gen.altitude_m,
            slant_range_m=gen.max_slant_range_m,
            heading_deg=heading,
            latitude=cur_lat,
            longitude=cur_lon
        )

        qc_report, contacts = orchestrator.process_frame(record, ping_index=p_idx)
        elapsed_ms = (time.time() - t0) * 1000

        for c in contacts:
            CONTACTS_STORE[c["contact_id"]] = c
            created_contacts.append(c)

        all_qc_reports.append(qc_report.to_dict())

        await manager.broadcast_json({
            "event_type": "PING_PROCESSED",
            "survey_id": survey_id,
            "ping_index": p_idx,
            "total_pings": req.num_pings or 5,
            "qc_status": qc_report.status,
            "snr_db": qc_report.snr_db,
            "contacts_found_in_ping": len(contacts),
            "total_contacts_so_far": len(CONTACTS_STORE),
            "processing_time_ms": round(elapsed_ms, 1),
            "vessel_telemetry": {
                "latitude": round(cur_lat, 6),
                "longitude": round(cur_lon, 6),
                "heading_deg": heading,
                "altitude_m": gen.altitude_m,
                "slant_range_m": gen.max_slant_range_m
            },
            "new_contacts": contacts
        })
        await asyncio.sleep(0.15)

    return {
        "status": "COMPLETED",
        "survey_id": survey_id,
        "pings_processed": req.num_pings or 5,
        "contacts_surfaced": len(created_contacts),
        "total_store_contacts": len(CONTACTS_STORE),
        "contacts": created_contacts,
        "qc_reports": all_qc_reports
    }
