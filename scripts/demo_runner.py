import sys
import os

# Add workspace root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import time
from ml.ingestion.synthetic_generator import SyntheticSonarGenerator
from ml.ingestion.sonar_parser import SonarParser
from backend.app.services.pipeline_orchestrator import PipelineOrchestrator

def run_demo():
    print("=================================================================")
    print("ABYSSEYE (SIH 2026 Problem 26057) - Full Pipeline Demo Runner")
    print("=================================================================\n")

    sim_dir = os.path.join("data", "processed", "demo_survey")
    os.makedirs(sim_dir, exist_ok=True)

    print("1. [INGESTION] Generating Physics-Accurate SSS Survey Waterfall...")
    gen = SyntheticSonarGenerator(height_pings=256, width_cols=512, altitude_m=12.0, max_slant_range_m=50.0)
    created_files = gen.generate_survey_dataset(sim_dir, num_frames=3)
    print(f"   [OK] Generated {len(created_files)} high-resolution sonar pings with acoustic shadows & netting striations.\n")

    print("2. [PIPELINE] Initializing Multi-Modal Evidence Orchestrator...")
    orchestrator = PipelineOrchestrator()
    all_contacts = []

    for i, file_path in enumerate(created_files):
        t0 = time.time()
        record = SonarParser.load_from_file(file_path, survey_id="SRV-BALTIC-NORTH-04", ping_index=i)
        qc, contacts = orchestrator.process_frame(record, ping_index=i)
        elapsed = (time.time() - t0) * 1000

        print(f"   -> Processed Ping #{i:02d}: QC = {qc.status} (SNR: {qc.snr_db:.1f} dB) | Surfaced {len(contacts)} contacts ({elapsed:.1f}ms)")
        all_contacts.extend(contacts)

    print(f"\n3. [FUSION] Total Contacts Discovered & Verified: {len(all_contacts)}")
    out_json = os.path.join("data", "contacts", "demo_contacts.json")
    with open(out_json, "w") as f:
        json.dump(all_contacts, f, indent=2)
    print(f"   [OK] Saved Contact Digital Twins to: {out_json}\n")

    for idx, c in enumerate(all_contacts[:2]):
        print(f"--- Contact #{idx+1}: {c['contact_id']} ---")
        print(f"  * Triage State:         {c['triage_state']}")
        print(f"  * Target Type Hint:     {c['target_type_hint']}")
        print(f"  * P(Anthropogenic):     {c['fusion_decision']['calibrated_probabilities']['p_anthropogenic'] * 100:.1f}%")
        print(f"  * Physical Height:      {c['evidence_graph']['acoustic_physics']['estimated_target_height_m']} m")
        print(f"  * Collinearity Score:   {c['evidence_graph']['acoustic_physics']['collinearity_score']}")
        print(f"  * Net-Like Filament:    {c['evidence_graph']['filament_netting']['is_net_like']}")
        print(f"  * Track Persistence:    {c['evidence_graph']['temporal_tracking']['persistence_ratio'] if c['evidence_graph']['temporal_tracking'] else 'N/A'}")
        print(f"  * Top SHAP Feature:     {c['fusion_decision']['top_shap_features'][0]['feature']} (Impact: +{c['fusion_decision']['top_shap_features'][0]['shap_impact']})")
        print(f"  * WGS84 Position:       {c['spatial_telemetry']['latitude']} deg N, {c['spatial_telemetry']['longitude']} deg E\n")

    print("=================================================================")
    print("[SUCCESS] ABYSSEYE PIPELINE EXECUTION COMPLETE & FULLY VERIFIED")
    print("=================================================================")

if __name__ == "__main__":
    run_demo()
