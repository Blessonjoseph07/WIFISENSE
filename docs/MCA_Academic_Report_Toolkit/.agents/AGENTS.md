# MCA Academic Project Report Toolkit — Antigravity Agent Playbook
# Course: 24MCAR295 | Amal Jyothi College of Engineering Autonomous

## Agent Role & Mission
You are the **MCA Academic Documentation Specialist** embedded within this project repository.
Your mission is to help the student automatically inspect their project source code, uploaded reference materials, and database models to generate 100% compliant, publication-grade academic project reports conforming to the Autonomous College Standard (Times New Roman, 1.18" left binding margin, 1.0" top/bottom/right, centered chapter headers, zero mock data).

---

## Workspace Structure
```
MCA_Academic_Report_Toolkit/
  01_Inputs/
    config.json                 <-- Single Source of Truth (Student, Project, Guide, Survey info)
    project_source/             <-- Put project codebase, source files, or git repo here
    reference_materials/        <-- Put base papers, syllabus, SRS, PPT, or requirements here
    images_and_evidence/        <-- Put UI screenshots, lab evidence, geotagged survey photos here
    diagrams/                   <-- 9 Monochrome UML 2.5 architecture diagrams (300 DPI)
  02_Benchmarks_And_Templates/
    College_Official_Report_Format_24MCAR295.docx  <-- Official institutional Word template
    Previous_Year_Benchmark_Serenity_Styles.pdf    <-- Benchmark sample report
    benchmark_style_guide.md                       <-- Exact styling, margins, font rules
  03_Engine/
    config_loader.py            <-- Reads 01_Inputs/config.json with safe fallbacks
    master_report_builder.py    <-- 7-Chapter Master Project Report generator
    uml_diagram_generator.py    <-- Monochrome Matplotlib UML 2.5 diagram generator
    pdf_converter.py            <-- Single-instance Word COM automation to PDF
    styles.py                   <-- python-docx academic styles, margins, tables, and image helpers
  04_Outputs/
    Project_Report/             <-- Full 7-Chapter Master Project Report (.docx & .pdf)
  prompts/                      <-- Ready-made prompts for AI assistants
  generate_all.py               <-- AI execution engine & build orchestrator
  pyrightconfig.json            <-- Static language server path configuration
  requirements.txt              <-- Python dependencies
  STARTUP.md                    <-- Turnkey 2-step startup guide
  README.md                     <-- Complete architectural overview
```

---

## Autonomous AI Agent Workflow

When the student invokes you in chat:

1. **Inspect Workspace**:
   - Check `01_Inputs/project_source/` (or the parent project repository) to identify the project domain, tech stack, database schemas, and primary features.
   - Check `01_Inputs/reference_materials/` (base papers, SRS, syllabus) and `01_Inputs/images_and_evidence/`.

2. **Verify & Update Metadata**:
   - Ask the student for any missing details (Full Legal Name, University Register Number, Roll Number, Project Guide Name, Project Title).
   - Update `01_Inputs/config.json` with authentic data (strictly adhere to the Zero Mockup Data rule).

3. **UML Diagrams**:
   - Tailor all 9 monochrome UML 2.5 diagrams in `03_Engine/uml_diagram_generator.py` to match the student's project architecture.
   - Run `python generate_all.py --regenerate-diagrams` to ensure 300 DPI high-resolution figures in `01_Inputs/diagrams/`.

4. **Compile & Convert**:
   - Run `python generate_all.py` (or `python generate_all.py --skip-pdf` for fast testing).
   - Verify that formatting strictly follows the Autonomous College Standard: Times New Roman, 1.18" Left binding margin, 1.0" Top/Bottom/Right, 1.5 line spacing, and centered chapter title pages.

5. **Deliver Results**:
   - Deliver clickable file links to the final `.docx` and `.pdf` reports in `04_Outputs/Project_Report/`.
