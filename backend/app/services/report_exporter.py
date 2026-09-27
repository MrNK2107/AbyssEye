import os
import json
import csv
from typing import Dict, List, Any
from datetime import datetime, timezone

class MissionReportExporter:
    """
    Generates structured mission intelligence reports and CSV/GeoJSON exports
    for marine survey commanders and ocean cleanup dive teams.
    """

    @staticmethod
    def generate_json_report(survey_id: str, contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        high_conf_cnt = sum(1 for c in contacts if c.get("triage_state") == "HIGH_CONFIDENCE")
        review_cnt = sum(1 for c in contacts if c.get("triage_state") == "REVIEW")
        ghost_nets = sum(1 for c in contacts if c.get("target_type_hint") == "GHOST_NET")

        return {
            "report_title": f"ABYSSEYE Mission Intelligence Report - {survey_id}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "survey_id": survey_id,
            "mission_summary": {
                "total_contacts_surfaced": len(contacts),
                "high_confidence_debris": high_conf_cnt,
                "review_queue_contacts": review_cnt,
                "ghost_nets_identified": ghost_nets
            },
            "contacts_inventory": contacts
        }

    @staticmethod
    def export_csv(contacts: List[Dict[str, Any]], output_filepath: str):
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
        fields = [
            "contact_id", "survey_id", "triage_state", "target_type_hint",
            "p_anthropogenic", "latitude", "longitude", "slant_range_m",
            "estimated_target_height_m", "collinearity_score", "persistence_ratio"
        ]

        with open(output_filepath, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()

            for c in contacts:
                probs = c.get("fusion_decision", {}).get("calibrated_probabilities", {})
                physics = c.get("evidence_graph", {}).get("acoustic_physics", {})
                tracking = c.get("evidence_graph", {}).get("temporal_tracking") or {}
                telemetry = c.get("spatial_telemetry", {})

                row = {
                    "contact_id": c.get("contact_id"),
                    "survey_id": c.get("survey_id"),
                    "triage_state": c.get("triage_state"),
                    "target_type_hint": c.get("target_type_hint"),
                    "p_anthropogenic": probs.get("p_anthropogenic", 0.0),
                    "latitude": telemetry.get("latitude"),
                    "longitude": telemetry.get("longitude"),
                    "slant_range_m": telemetry.get("slant_range_m"),
                    "estimated_target_height_m": physics.get("estimated_target_height_m", 0.0),
                    "collinearity_score": physics.get("collinearity_score", 0.0),
                    "persistence_ratio": tracking.get("persistence_ratio", 1.0)
                }
                writer.writerow(row)
