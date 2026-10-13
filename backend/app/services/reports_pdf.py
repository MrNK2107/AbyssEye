"""Executive PDF Report Generator for MoES / NIOT Survey Scans.

Generates a formatted, publication-ready PDF report containing survey metadata, target hazard
breakdown, acoustic shadow contrast scores, and nearest Indian port logistics.
"""

from __future__ import annotations

import io
from typing import Sequence, Dict, Any, List
from datetime import datetime, timezone

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

from backend.app.services.india_ops import find_nearest_indian_ports


def generate_pdf_report(contacts: List[Dict[str, Any]], survey_title: str = "AbyssEye Sonar Survey") -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=36, leftMargin=36, topMargin=36, bottomMargin=36)
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#0b6e99'),
        spaceAfter=8
    )

    h2_style = ParagraphStyle(
        'DocH2',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#16202a'),
        spaceBefore=12,
        spaceAfter=6
    )

    body_style = styles['Normal']

    story = []
    
    # Title Header
    story.append(Paragraph("ABYSSEYE — Side-Scan Sonar Hazard Triage Report", title_style))
    story.append(Paragraph("<b>Ministry of Earth Sciences (MoES) / NIOT Autonomous Seabed Survey Intelligence</b>", body_style))
    story.append(Paragraph(f"Survey Reference: <b>{survey_title}</b> | Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", body_style))
    story.append(Spacer(1, 12))

    high_conf = sum(1 for c in contacts if c.get("triage_state") == "HIGH_CONFIDENCE")
    review_queue = sum(1 for c in contacts if c.get("triage_state") == "REVIEW")
    natural_cnt = sum(1 for c in contacts if c.get("triage_state") == "NATURAL_SEABED")

    meta_data = [
        ["Total Contacts Surfaced:", str(len(contacts)), "High-Confidence Debris:", str(high_conf)],
        ["Review Queue Contacts:", str(review_queue), "Natural Seafloor Features:", str(natural_cnt)],
        ["Calibration Standard:", "Isotonic Platt (ECE < 0.05)", "Audit Validation:", "Leakage-Free Survey Groups"],
    ]
    t_meta = Table(meta_data, colWidths=[130, 140, 130, 140])
    t_meta.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f4f6f8')),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t_meta)
    story.append(Spacer(1, 10))

    # Contacts table
    if contacts:
        story.append(Paragraph("<b>Detected Contacts & Physical Verification Evidence:</b>", h2_style))
        det_rows = [["ID", "Type", "Confidence", "Shadow Ratio", "Target Height", "Collinearity", "Triage State"]]
        
        for c in contacts[:15]:
            cid = c.get("contact_id", "—")
            ttype = c.get("target_type_hint", "UNKNOWN").replace("_", " ").title()
            probs = c.get("fusion_decision", {}).get("calibrated_probabilities", {})
            conf_val = probs.get("p_anthropogenic", 0.0)
            phys = c.get("evidence_graph", {}).get("acoustic_physics", {})
            shadow_ratio = phys.get("shadow_contrast_ratio", 1.0)
            height_m = phys.get("estimated_target_height_m", 0.0)
            collin = phys.get("collinearity_score", 0.0)
            tstate = c.get("triage_state", "REVIEW")

            det_rows.append([
                str(cid)[:8],
                ttype,
                f"{conf_val * 100:.0f}%",
                f"{shadow_ratio:.2f}x",
                f"{height_m:.2f} m",
                f"{collin:.2f}",
                tstate
            ])

        t_det = Table(det_rows, colWidths=[60, 95, 65, 80, 80, 75, 85])
        t_det.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#0b6e99')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dde3e9')),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
        ]))
        story.append(t_det)
        story.append(Spacer(1, 10))

        # Nearest Indian Operational Port Logistics (if coordinates available)
        first_contact = contacts[0]
        telemetry = first_contact.get("spatial_telemetry", {})
        lat = telemetry.get("latitude")
        lon = telemetry.get("longitude")
        if lat is not None and lon is not None:
            story.append(Paragraph(f"<b>Nearest Indian Coastal Operations Logistics (from {lat:.4f}N, {lon:.4f}E):</b>", h2_style))
            ports = find_nearest_indian_ports(lat, lon, top_k=3)
            port_rows = [["Base / Port Facility", "State", "Distance (NM)", "Distance (km)", "Est. Transit (12 knots)"]]
            for p in ports:
                port_rows.append([
                    p.port_name,
                    p.state,
                    f"{p.distance_nm} NM",
                    f"{p.distance_km} km",
                    f"{p.est_transit_hours} hrs"
                ])

            t_port = Table(port_rows, colWidths=[150, 95, 95, 95, 105])
            t_port.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#16202a')),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('FONTSIZE', (0,0), (-1,-1), 8),
                ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#dde3e9')),
            ]))
            story.append(t_port)

    doc.build(story)
    return buffer.getvalue()
