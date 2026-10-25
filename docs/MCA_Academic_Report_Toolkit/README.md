# MCA Academic Project Report Toolkit (AI-First Edition)
**Amal Jyothi College of Engineering Autonomous, Kanjirappally**  
*Department of Computer Applications | Course: 24MCAR295 (Software Project Part 1)*

---

## Overview

This toolkit is an AI-orchestrated, production-grade academic project report generator. Designed specifically to work seamlessly with AI coding assistants (**Antigravity AI**, **Cursor**, **VS Code Copilot**, **Claude Code**), it enables any student or research team to produce:

- **The Comprehensive 7-Chapter Master Project Report** (Front matter, Chapters 1–7, References, and Appendices in both `.docx` and high-fidelity `.pdf`).
- **9 Publication-Grade Monochrome UML 2.5 Architecture Diagrams** (300 DPI, conforming strictly to formal UML standards).

All generated documents adhere strictly to autonomous college guidelines:
- **Paper Size**: International A4
- **Margins**: 1.18" (30 mm) Left binding margin; 1.0" (25.4 mm) Top, Bottom, Right
- **Typography**: Times New Roman (12 pt body text, 1.5 line spacing, fully justified)
- **Front Matter**: Dedicated centered chapter pages, formal declarations, certificates, and acknowledgments
- **Tables & Figures**: Solid single black borders, academic captions, zero mockup data policy

---

## Folder Structure

```text
MCA_Academic_Report_Toolkit/
├── .agents/                            <-- Auto-detected by Antigravity AI IDE
│   ├── AGENTS.md                       <-- Rules & automated workflow instructions
│   └── skills/mca-academic-report/     <-- Embedded academic documentation agent skill
├── 01_Inputs/
│   ├── config.json                     <-- Single source of truth (Student, Project, Guide info)
│   ├── reference_materials/            <-- Drop base papers, syllabus, notes, or SRS docs here
│   ├── project_source/                 <-- Place project source code or git clone here
│   ├── images_and_evidence/            <-- Screenshots and geotagged field survey photos
│   └── diagrams/                       <-- 9 Monochrome UML 2.5 diagrams (300 DPI)
├── 02_Benchmarks_And_Templates/
│   ├── benchmark_style_guide.md        <-- Exact font, margin, and layout specifications
│   ├── College_Official_Report_Format_24MCAR295.docx <-- Official autonomous college syllabus format
│   └── Previous_Year_Benchmark_Serenity_Styles.pdf   <-- Approved benchmark report from previous year
├── 03_Engine/                          <-- Modular Python report generation engine
│   ├── __init__.py                     <-- Package marker
│   ├── styles.py                       <-- Academic margin, heading, table, and image placement rules
│   ├── config_loader.py                <-- Configuration parser and validator
│   ├── master_report_builder.py        <-- 7-Chapter master project report builder
│   ├── uml_diagram_generator.py        <-- Monochrome Matplotlib UML 2.5 diagram generator
│   └── pdf_converter.py                <-- Word COM single-instance high-fidelity PDF converter
├── 04_Outputs/                         <-- Generated reports appear here
│   └── Project_Report/
│       ├── Project_Report_<Name>.docx
│       └── Project_Report_<Name>.pdf
├── prompts/                            <-- Ready-made prompts for AI assistants
│   ├── 01_SCAN_PROJECT_AND_CONFIGURE.md
│   ├── 02_BUILD_PROJECT_REPORT.md
│   └── 03_CUSTOMIZE_SECTIONS.md
├── generate_all.py                     <-- AI execution engine & orchestrator
├── pyrightconfig.json                  <-- Language server configuration
├── requirements.txt                    <-- Python dependencies
├── STARTUP.md                          <-- 2-step quick startup guide
└── README.md                           <-- This guide
```

---

## How It Works (AI Agent Workflow)

1. **Add Toolkit to Project Root**:
   Copy the `MCA_Academic_Report_Toolkit/` directory into your project repository.
2. **Paste Master Prompt**:
   Copy the prompt from `STARTUP.md` and paste it into your AI assistant chat.
3. **AI Autonomous Execution**:
   - The AI inspects your project code to determine your tech stack, database schemas, and personas.
   - The AI prompts you for your name, university register number, and guide name.
   - The AI updates `01_Inputs/config.json`.
   - The AI generates custom diagrams and compiles the complete `.docx` and `.pdf` reports into `04_Outputs/Project_Report/`.
