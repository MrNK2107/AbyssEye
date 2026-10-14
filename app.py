"""
AbyssEye: AI-Powered Marine Debris & Underwater Anomaly Detection System
========================================================================
Smart India Hackathon (SIH 2026) — Problem Statement 26057
Unified Gradio Perception Studio with Live ML Backend:
  - Supervised YOLOv8 Sonar Object Detection
  - Acoustic Shadow Ray-Tracing & 3D Bathymetric Triangulation
  - Calibrated LightGBM Evidence Fusion with TreeSHAP Explanations
  - Embedded Next.js 14 Groundstation Dashboard at /dashboard
"""

import os
os.environ["GRADIO_SSR_MODE"] = "False"
os.environ["YOLO_CONFIG_DIR"] = "/tmp/Ultralytics"

import sys
import json
import cv2
import numpy as np
from typing import Tuple, Dict, Any, List
import gradio as gr
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure project root is in sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from ml.ingestion.sonar_parser import SonarFrameRecord
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator
from backend.app.api.router import api_router
from backend.app.core.config import settings

# Initialize Pipeline Orchestrator with trained models
orchestrator = PipelineOrchestrator(models_dir=os.path.join(BASE_DIR, "models"))

def run_abysseye_pipeline(
    input_image: np.ndarray,
    confidence_threshold: float = 0.01,
    altitude_m: float = 10.0,
    slant_range_m: float = 50.0
) -> Tuple[np.ndarray, str, str, str]:
    """
    Executes the complete 8-stage AbyssEye pipeline on any side-scan sonar image:
    Returns annotated image, formatted evidence dossier, TreeSHAP breakdown, and raw JSON telemetry.
    """
    if input_image is None:
        return None, "### ⚠️ Please upload or select a sonar image to analyze.", "", "{}"

    # Set real detection sensitivity
    orchestrator.detector.confidence_threshold = float(confidence_threshold)

    # Convert to SonarFrameRecord
    record = SonarFrameRecord(
        frame_id="SCAN-HF-LIVE",
        survey_id="SURV-DEMO",
        ping_index=0,
        image_array=input_image,
        slant_range_m=float(slant_range_m),
        altitude_m=float(altitude_m)
    )

    qc_report, contacts = orchestrator.process_frame(record)

    annotated = input_image.copy()
    if annotated.ndim == 2:
        annotated = cv2.cvtColor(annotated, cv2.COLOR_GRAY2BGR)

    H, W = annotated.shape[:2]
    nadir_col = W // 2

    # Draw Nadir track center line
    cv2.line(annotated, (nadir_col, 0), (nadir_col, H), (60, 60, 60), 1, cv2.LINE_AA)
    cv2.putText(annotated, "PORT CHANNEL", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)
    cv2.putText(annotated, "STARBOARD CHANNEL", (W - 170, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (180, 180, 180), 1)

    table_rows = []
    contact_data = []
    shap_summaries = []

    for c in contacts:
        x, y, w, h = c["bbox"]
        cls_name = c["target_type_hint"]
        triage = c["triage_state"]
        channel = c["channel"]
        phys = c["evidence_graph"]["acoustic_physics"]
        h_m = phys.get("estimated_target_height_m", 0.0)
        s_len = phys.get("shadow_length_m", 0.0)
        phys_score = phys.get("physical_consistency_score", 0.0)
        collin = phys.get("collinearity_score", 0.0)
        p_anth = c["fusion_decision"]["calibrated_probabilities"]["p_anthropogenic"]
        top_shap = c["fusion_decision"]["top_shap_features"]

        # Color coding: Green for High Confidence, Orange for Review, Gray for Natural Seabed
        if triage == "HIGH_CONFIDENCE":
            box_color = (0, 220, 0)
        elif triage == "REVIEW":
            box_color = (0, 165, 255)
        else:
            box_color = (110, 110, 110)

        # Draw target highlight bounding box
        cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 2)
        label_text = f"{cls_name} [{channel}] ({p_anth*100:.0f}%)"
        cv2.putText(annotated, label_text, (x, max(18, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1, cv2.LINE_AA)

        # Only highlight confirmed/review targets in primary table
        if triage != "NATURAL_SEABED":
            table_rows.append(
                f"| **{c['contact_id']}** | **{cls_name}** | `{channel}` | `{triage}` | **{h_m:.2f} m** | {s_len:.2f} m | {collin:.2f} | {phys_score:.2f} | **{p_anth*100:.1f}%** |"
            )

            # Build TreeSHAP explanation for target
            shap_lines = [f"**Contact {c['contact_id']} ({cls_name}):**"]
            for s in top_shap:
                impact_sign = "▲" if s["shap_impact"] > 0 else "▼"
                impact_color = "positive" if s["shap_impact"] > 0 else "negative"
                shap_lines.append(f"- {impact_sign} `{s['feature']}` = **{s['value']}** (SHAP impact: `{s['shap_impact']:+.3f}`)")
            shap_summaries.append("\n".join(shap_lines))

        contact_data.append({
            "contact_id": c["contact_id"],
            "target_type_hint": cls_name,
            "channel": channel,
            "triage_state": triage,
            "bbox_xywh": [x, y, w, h],
            "estimated_relief_height_m": round(h_m, 2),
            "acoustic_shadow_length_m": round(s_len, 2),
            "collinearity_score": round(collin, 2),
            "physical_consistency_score": round(phys_score, 2),
            "p_anthropogenic": round(p_anth, 3),
            "calibrated_probabilities": c["fusion_decision"]["calibrated_probabilities"],
            "top_shap_features": top_shap
        })

    if table_rows:
        md_table = "### 🎯 Discovered Anthropogenic Contacts & Bathymetric Relief\n\n"
        md_table += "| Contact ID | Classification | Channel | Triage State | 3D Relief Height | Shadow Length | Collinearity | Physical Consistency | Calibrated Confidence |\n"
        md_table += "|:---|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        md_table += "\n".join(table_rows)
    else:
        md_table = "### ℹ️ No high-confidence anthropogenic contacts discovered (Natural Seabed Backscatter)."

    shap_md = "### 🔬 TreeSHAP Interpretability & Evidence Attributions\n\n"
    if shap_summaries:
        shap_md += "\n\n".join(shap_summaries)
    else:
        shap_md += "No high-contrast physical contacts to attribute."

    return annotated, md_table, shap_md, json.dumps(contact_data, indent=2)

# Create Gradio Blocks UI
def create_app() -> gr.Blocks:
    # Discover available samples for quick testing
    sample_files = []
    samples_dir = os.path.join(BASE_DIR, "samples")
    curated_names = [
        "shipwreck_sonar.png",
        "sonar_wreck_wilson.jpg",
        "sonar_pipeline.jpg",
        "sonar_drum.jpg",
        "sonar_ghost_net.jpg"
    ]
    if os.path.exists(samples_dir):
        for name in curated_names:
            p = os.path.join(samples_dir, name)
            if os.path.exists(p):
                sample_files.append(p)
        if not sample_files:
            for fname in sorted(os.listdir(samples_dir)):
                if fname.lower().endswith((".png", ".jpg", ".jpeg")) and not fname.endswith("_annotated.jpg"):
                    sample_files.append(os.path.join(samples_dir, fname))

    with gr.Blocks(title="AbyssEye Acoustic Evidence Engine") as demo:
        gr.Markdown(
            """
            # 🌊 AbyssEye: AI-Powered Underwater Debris & Sonar Anomaly Detection
            ### Smart India Hackathon (SIH 2026) — Problem Statement 26057
            **Real-time Side-Scan Sonar (SSS) Perception Studio** executing un-hardcoded PyTorch YOLOv8 detection, 
            acoustic shadow ray-tracing (shadow length, relief height, collinearity), and calibrated LightGBM Evidence Fusion.
            
            🔗 **Quick Links:** [Open Full Groundstation Dashboard ↗](/dashboard/) | [Interactive REST API Docs ↗](/docs) | [System Health Check ↗](/health)
            ---
            """
        )

        with gr.Row():
            with gr.Column(scale=5):
                input_img = gr.Image(label="Upload Sonar Waterfall / Scan (PNG / JPG / TIFF)", type="numpy")
                with gr.Row():
                    conf_slider = gr.Slider(
                        minimum=0.005,
                        maximum=0.50,
                        value=0.01,
                        step=0.005,
                        label="YOLO Candidate Extraction Sensitivity",
                        info="Controls recall threshold for candidate contact proposals"
                    )
                    alt_slider = gr.Slider(
                        minimum=2.0,
                        maximum=30.0,
                        value=10.0,
                        step=1.0,
                        label="AUV Altitude (m)",
                        info="Sensor flight altitude above seafloor for ray tracing"
                    )
                    range_slider = gr.Slider(
                        minimum=10.0,
                        maximum=100.0,
                        value=50.0,
                        step=5.0,
                        label="Slant Range (m)",
                        info="Maximum sonar swath channel range"
                    )
                run_btn = gr.Button("⚡ Analyze Sonar Frame", variant="primary", size="lg")

            with gr.Column(scale=5):
                output_img = gr.Image(label="Annotated Sonar Contact Detections (Port / Starboard Overlay)")

        with gr.Row():
            dossier_box = gr.Markdown(label="Target Dossier")

        with gr.Row():
            shap_box = gr.Markdown(label="TreeSHAP Interpretability")

        with gr.Accordion("📋 Full Contact Digital Twin Telemetry (JSON)", open=False):
            json_box = gr.Code(label="Contact Digital Twins", language="json")

        # Example Gallery for instant 1-click evaluation
        if sample_files:
            gr.Examples(
                examples=[[sf, 0.01, 10.0, 50.0] for sf in sample_files],
                inputs=[input_img, conf_slider, alt_slider, range_slider],
                outputs=[output_img, dossier_box, shap_box, json_box],
                fn=run_abysseye_pipeline,
                cache_examples=False,
                label="📁 Curated Sonar Test Datasets (Click to load and analyze instantly)"
            )

        run_btn.click(
            fn=run_abysseye_pipeline,
            inputs=[input_img, conf_slider, alt_slider, range_slider],
            outputs=[output_img, dossier_box, shap_box, json_box]
        )

    return demo

demo = create_app()

# Enable CORS on FastAPI app
demo.app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health Check Route
@demo.app.get("/health")
def health_check():
    return {
        "status": "HEALTHY",
        "service": "ABYSSEYE-BACKEND",
        "version": "3.0.0",
        "pipeline_state": "READY"
    }

# Mount REST API
try:
    demo.app.include_router(api_router, prefix=settings.API_V1_STR)
except Exception as e:
    print(f"Could not mount API router: {e}")

# Mount Next.js static Groundstation dashboard at /dashboard
candidate_dirs = [
    os.path.join(BASE_DIR, "frontend", "out"),
    os.path.join(BASE_DIR, "out"),
    BASE_DIR
]
for fdir in candidate_dirs:
    if os.path.exists(fdir) and os.path.exists(os.path.join(fdir, "_next")):
        try:
            demo.app.mount("/dashboard", StaticFiles(directory=fdir, html=True), name="dashboard")
            print(f"Mounted Next.js dashboard at /dashboard from {fdir}")
            break
        except Exception as e:
            print(f"Could not mount static dashboard from {fdir}: {e}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port, ssr_mode=False)
