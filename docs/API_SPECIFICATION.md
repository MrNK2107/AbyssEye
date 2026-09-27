# ABYSSEYE — Backend REST & WebSocket API Specification

**Document Version:** v3.0  
**Target:** SIH 2026 Problem Statement 26057  
**Base URL:** `http://localhost:8000/api/v1`  
**Protocol:** REST (JSON) + WebSocket (Real-time contact alerts)

---

## 1. API Endpoints Overview

| Method | Endpoint | Description | Request Body | Response |
|---|---|---|---|---|
| `POST` | `/sonar/upload` | Upload raw sonar file (XTF, JSF, GeoTIFF, PNG) | `multipart/form-data` | `UploadJobResponse` |
| `POST` | `/sonar/process` | Trigger ML processing job on uploaded survey | `ProcessRequest` | `JobStatusResponse` |
| `GET` | `/jobs/{job_id}` | Poll background processing status | None | `JobProgress` |
| `GET` | `/surveys` | List all ingested surveys and tracklines | Query params | `List[SurveySummary]` |
| `GET` | `/surveys/{id}` | Get survey details and swath geometry | None | `SurveyDetail` |
| `GET` | `/contacts` | Filter and query detected contacts | `status, min_conf, class` | `List[ContactSummary]` |
| `GET` | `/contacts/{id}` | Fetch complete Contact Digital Twin & Evidence Card | None | `ContactDigitalTwin` |
| `POST` | `/contacts/{id}/review` | Submit human review decision (Active Learning) | `ReviewSubmission` | `ReviewConfirmation` |
| `GET` | `/gis/geojson/tracks` | Fetch survey trackline GeoJSON for Leaflet | `survey_id` | `GeoJSONFeatureCollection` |
| `GET` | `/gis/geojson/contacts`| Fetch geolocated contact markers GeoJSON | Filters | `GeoJSONFeatureCollection` |
| `POST` | `/reports/export` | Generate PDF / GeoPackage / CSV mission report | `ReportConfig` | `FileDownload` |
| `WS` | `/ws/live-stream` | WebSocket feed for real-time contact alerts | None | Stream of `ContactEvent` |

---

## 2. Request & Response Schemas (Pydantic / TypeScript)

### 2.1 Process Sonar Request (`POST /sonar/process`)

```json
{
  "survey_id": "SRV-BALTIC-NORTH-04",
  "pipeline_config": {
    "enable_patchcore": true,
    "enable_detector": true,
    "enable_physics_verification": true,
    "enable_tracking": true,
    "enable_context_analysis": true,
    "fusion_model": "lightgbm-v3.0.4",
    "calibration_method": "isotonic",
    "confidence_threshold": 0.40
  }
}
```

### 2.2 Review Submission (`POST /contacts/{id}/review`)

```json
{
  "reviewer_id": "OP-NAV-77",
  "decision": "ANTHROPOGENIC",
  "target_subtype": "GHOST_NET",
  "confidence_rating": 4,
  "flagged_for_cleanup": true,
  "notes": "Clear netting texture with continuous linear shadow along coral edge.",
  "evidence_feedback": {
    "shadow_assessment": "ACCURATE",
    "tracking_assessment": "ACCURATE",
    "seabed_isolation": "HIGH"
  }
}
```

---

## 3. WebSocket Real-Time Alert Specification (`WS /ws/live-stream`)

When processing real-time or streaming sonar feeds, alerts are broadcast to connected GIS frontend clients.

```json
{
  "event_type": "NEW_CONTACT_SURFACED",
  "timestamp": "2026-09-27T12:45:00.120Z",
  "payload": {
    "contact_id": "CONT-2026-0927-00142",
    "triage_state": "REVIEW",
    "p_anthropogenic": 0.812,
    "latitude": 54.821945,
    "longitude": 18.734201,
    "estimated_height_m": 1.73,
    "thumbnail_url": "/api/v1/contacts/CONT-2026-0927-00142/crop.png",
    "primary_evidence": "Highlight-shadow collinearity: 0.94; Persistence: 7/8 pings"
  }
}
```
