import cv2
import numpy as np
import json
from typing import Tuple, Dict, Any, List
import gradio as gr

from ml.ingestion.sonar_parser import SonarFrameRecord
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator

orchestrator = PipelineOrchestrator()

def process_sonar_image(
    input_image: np.ndarray,
    confidence_threshold: float = 0.01,
    altitude_m: float = 10.0,
    slant_range_m: float = 50.0
) -> Tuple[np.ndarray, str, str]:
    if input_image is None:
        return None, "### No image provided", "{}"

    orchestrator.detector.confidence_threshold = float(confidence_threshold)
    record = SonarFrameRecord(
        frame_id="gradio_upload",
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

    table_rows = []
    contact_data = []

    for c in contacts:
        x, y, w, h = c["bbox"]
        cls_name = c["target_type_hint"]
        triage = c["triage_state"]
        channel = c["channel"]
        phys = c["evidence_graph"]["acoustic_physics"]
        h_m = phys.get("estimated_target_height_m", 0.0)
        s_len = phys.get("shadow_length_m", 0.0)
        phys_score = phys.get("physical_consistency_score", 0.0)
        p_anth = c["fusion_decision"]["calibrated_probabilities"]["p_anthropogenic"]

        # Color coding
        if triage == "HIGH_CONFIDENCE":
            box_color = (0, 220, 0) # Green
        elif triage == "REVIEW":
            box_color = (0, 165, 255) # Orange
        else:
            box_color = (128, 128, 128) # Gray

        cv2.rectangle(annotated, (x, y), (x + w, y + h), box_color, 2)
        label_text = f"{cls_name} [{channel}]"
        cv2.putText(annotated, label_text, (x, max(18, y - 6)), cv2.FONT_HERSHEY_SIMPLEX, 0.45, box_color, 1)

        if triage != "NATURAL_SEABED":
            table_rows.append(
                f"| **{c['contact_id']}** | **{cls_name}** | {channel} | `{triage}` | {h_m:.2f} m | {s_len:.2f} m | {phys_score:.2f} | **{p_anth*100:.1f}%** |"
            )

        contact_data.append({
            "contact_id": c["contact_id"],
            "target_type": cls_name,
            "channel": channel,
            "triage_state": triage,
            "bbox": [x, y, w, h],
            "relief_height_m": round(h_m, 2),
            "shadow_length_m": round(s_len, 2),
            "collinearity_score": phys.get("collinearity_score", 0.0),
            "physical_consistency": round(phys_score, 2),
            "p_anthropogenic": round(p_anth, 3),
            "top_shap_features": c["fusion_decision"]["top_shap_features"]
        })

    if table_rows:
        md_table = "### 🎯 Detected Acoustic Contacts & Triangulated Evidence\n\n"
        md_table += "| Contact ID | Target Classification | Channel | Triage State | Relief Height | Shadow Length | Physics Consistency | Anthropogenic Confidence |\n"
        md_table += "|:---|:---|:---|:---|:---|:---|:---|:---|\n"
        md_table += "\n".join(table_rows)
    else:
        md_table = "### ℹ️ No high-contrast anthropogenic targets discovered (Clean Seabed Backscatter)."

    return annotated, md_table, json.dumps(contact_data, indent=2)

def create_gradio_interface() -> gr.Blocks:
    with gr.Blocks(title="AbyssEye Acoustic Evidence Engine") as demo:
        gr.Markdown(
            """
            # 🌊 AbyssEye: AI-Powered Marine Debris & Sonar Contact Analysis
            ### Real-Time Side-Scan Sonar ML Inference with Physics-Grounded Acoustic Ray-Tracing
            Upload any Side-Scan Sonar (SSS) image or waterfall strip to run the complete **YOLOv8 + Acoustic Shadow Triangulation + LightGBM Evidence Fusion** pipeline.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                input_image = gr.Image(label="Upload Sonar Image (PNG / JPG / TIFF)", type="numpy")
                with gr.Row():
                    conf_slider = gr.Slider(
                        minimum=0.005,
                        maximum=0.50,
                        value=0.01,
                        step=0.005,
                        label="YOLO Candidate Extraction Threshold"
                    )
                    alt_slider = gr.Slider(
                        minimum=2.0,
                        maximum=30.0,
                        value=10.0,
                        step=1.0,
                        label="AUV Altitude (m)"
                    )
                analyze_btn = gr.Button("⚡ Run Sonar Pipeline", variant="primary")

            with gr.Column(scale=1):
                output_image = gr.Image(label="Annotated Sonar Contact Detections")

        with gr.Row():
            output_table = gr.Markdown(label="Target Evidence Dossier")

        with gr.Accordion("📋 Raw Contact Telemetry & TreeSHAP Features (JSON)", open=False):
            output_json = gr.Code(label="Contact Digital Twins", language="json")

        analyze_btn.click(
            fn=process_sonar_image,
            inputs=[input_image, conf_slider, alt_slider],
            outputs=[output_image, output_table, output_json]
        )

    return demo
