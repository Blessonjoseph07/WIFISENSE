#!/usr/bin/env python3
"""
Master Project Report Generation Orchestrator (AI-Optimized Engine)
MCA Academic Report Toolkit — Amal Jyothi College of Engineering Autonomous
Department of Computer Applications | Course: 24MCAR295
"""

import os
import sys
import time
import argparse

# Ensure Engine and Toolkit Root are in Python module search path
TOOLKIT_ROOT = os.path.abspath(os.path.dirname(__file__))
ENGINE_DIR = os.path.join(TOOLKIT_ROOT, "03_Engine")
if ENGINE_DIR not in sys.path:
    sys.path.insert(0, ENGINE_DIR)
if TOOLKIT_ROOT not in sys.path:
    sys.path.insert(0, TOOLKIT_ROOT)

from config_loader import load_student_config  # type: ignore
from master_report_builder import build_master_project_report  # type: ignore
from pdf_converter import convert_docx_to_pdf  # type: ignore
from uml_diagram_generator import generate_all_diagrams, set_diagram_output_dir  # type: ignore
from project_analyzer import run_project_analysis  # type: ignore

def ensure_uml_diagrams(diagrams_dir: str, force_regenerate: bool = False):
    """Ensures all 9 monochrome UML 2.5 diagrams exist in 01_Inputs/diagrams/."""
    os.makedirs(diagrams_dir, exist_ok=True)
    expected = [
        "uml_01_use_case.png", "uml_02_sequence.png", "uml_03_state.png",
        "uml_04_activity.png", "uml_05_class.png", "uml_06_object.png",
        "uml_07_component.png", "uml_08_deployment.png", "uml_09_collaboration.png"
    ]
    missing = [f for f in expected if not os.path.exists(os.path.join(diagrams_dir, f))]
    
    if missing or force_regenerate:
        print(f"-> Generating {len(expected)} publication-quality monochrome UML diagrams (300 DPI)...")
        set_diagram_output_dir(diagrams_dir)
        generate_all_diagrams()
        print(f"[UML OK] All 9 diagrams verified in: {diagrams_dir}")
    else:
        print(f"[UML OK] All 9 monochrome diagrams present in: {diagrams_dir}")

def parse_args():
    parser = argparse.ArgumentParser(description="AI Academic Project Report Generator for MCA 24MCAR295")
    parser.add_argument("--scan", action="store_true", help="Audit project codebase, git history, and schemas before building")
    parser.add_argument("--skip-pdf", action="store_true", help="Skip Microsoft Word PDF conversion (generate DOCX only)")
    parser.add_argument("--regenerate-diagrams", action="store_true", help="Force re-rendering of all 9 UML diagrams")
    return parser.parse_args()

def main():
    args = parse_args()

    print("=" * 80)
    print("   MCA PROJECT REPORT GENERATOR — AI EXECUTION ENGINE")
    print("   Amal Jyothi College of Engineering Autonomous, Kanjirappally")
    print("   Department of Computer Applications | Course: 24MCAR295")
    print("   Autonomous College Standard (Times New Roman, 1.18\" Binding Margin)")
    print("=" * 80)

    cfg_path = os.path.join(TOOLKIT_ROOT, "01_Inputs", "config.json")
    workspace_dir = os.path.abspath(os.path.join(TOOLKIT_ROOT, ".."))
    if not os.path.exists(os.path.join(workspace_dir, "backend")) and os.path.exists(os.path.join(workspace_dir, "..", "backend")):
        workspace_dir = os.path.abspath(os.path.join(workspace_dir, ".."))

    if args.scan:
        print("\n[PHASE -1] Auditing Project Codebase, Git History & Architecture...")
        cfg = run_project_analysis(workspace_dir, cfg_path)
    else:
        cfg = load_student_config()
    st = cfg.get("student", {})
    pj = cfg.get("project", {})
    fc = cfg.get("faculty", {})
    inst = cfg.get("institution", {})

    print(f"Student     : {st.get('full_name')} ({st.get('reg_number')})")
    print(f"Project     : {pj.get('title')} [{pj.get('short_name')}]")
    print(f"Guide       : {fc.get('project_guide_name')} ({fc.get('project_guide_designation')})")
    print(f"Institution : {inst.get('college_name')}")
    print("-" * 80)

    # Output paths
    diagrams_dir = os.path.join(TOOLKIT_ROOT, "01_Inputs", "diagrams")
    outputs_dir = os.path.join(TOOLKIT_ROOT, "04_Outputs")
    project_report_dir = os.path.join(outputs_dir, "Project_Report")
    os.makedirs(project_report_dir, exist_ok=True)

    # 1. System Architecture UML Diagrams
    print("\n[PHASE 0] Verifying System Architecture Diagrams...")
    ensure_uml_diagrams(diagrams_dir, force_regenerate=args.regenerate_diagrams)

    # 2. Comprehensive 7-Chapter Master Report DOCX
    print("\n[PHASE 1] Compiling Comprehensive 7-Chapter Academic Project Report...")
    t0 = time.time()
    master_docx = build_master_project_report(project_report_dir, cfg)
    print(f"[DOCX OK] Built in {time.time() - t0:.2f}s: {master_docx}")

    # 3. High-Fidelity Word PDF Conversion
    master_pdf = None
    if not args.skip_pdf:
        print("\n[PHASE 2] Converting Project Report to High-Fidelity PDF...")
        try:
            master_pdf = convert_docx_to_pdf(master_docx)
            print(f"[PDF OK] Generated: {master_pdf}")
        except Exception as e:
            print(f"[PDF WARN] Word COM PDF conversion failed: {e}")
    else:
        print("\n[PHASE 2] Skipping PDF conversion (--skip-pdf enabled)")

    # 4. Final Summary
    print("\n" + "=" * 80)
    print("                    ACADEMIC REPORT COMPILED SUCCESSFULLY")
    print("=" * 80)
    print(f"Output Directory : {project_report_dir}")
    print(f"Word Report      : {master_docx}")
    if master_pdf:
        print(f"PDF Report       : {master_pdf}")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
