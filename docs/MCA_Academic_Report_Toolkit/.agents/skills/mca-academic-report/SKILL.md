---
name: mca-academic-report
description: Automated generation of 100% compliant MCA academic project reports and UML diagrams for Amal Jyothi College of Engineering Autonomous (Course 24MCAR295).
---

# MCA Academic Project Report Documentation Skill

## Overview
This skill guides the automated extraction, synthesis, and compilation of academic documentation for Master of Computer Applications (MCA) students at Amal Jyothi College of Engineering Autonomous (Course 24MCAR295).

## Instructions for Antigravity AI

### Step 1: Scan Student Input Files
Check the contents of the following directories:
- `01_Inputs/project_source/`: Source code files, package manifests (`package.json`, `build.gradle`, `requirements.txt`), database models, or repository clones.
- `01_Inputs/reference_materials/`: PDFs, Word docs, SRS, syllabus, PPT slides, base papers, or notes uploaded by the student.
- `01_Inputs/images_and_evidence/`: UI screenshots, field survey photos, lab images.

### Step 2: Auto-Populate `01_Inputs/config.json`
Update `01_Inputs/config.json` with the student's authentic project details:
- **Student**: Full Name, University Reg. No, Roll No, Class Section, Email.
- **Faculty**: Project Guide Name & Designation, HOD Name.
- **Project**: Title, Short Name / Acronym, Tagline, Target Platform, Primary Language, Backend Infrastructure.
- **Field Investigation**: Organization Name, Business Nature, Survey Location, Key Informant.

### Step 3: Architecture & UML Customization
- If the project requires customized diagrams, update or run `03_Engine/uml_diagram_generator.py`.
- Ensure all 9 monochrome UML 2.5 diagrams are generated at 300 DPI in `01_Inputs/diagrams/`.

### Step 4: Build Outputs
Run the orchestrator:
```bash
python generate_all.py
```
Or for fast DOCX-only:
```bash
python generate_all.py --skip-pdf
```

### Step 5: Verify Outputs
Check `04_Outputs/`:
- `04_Outputs/Project_Report/`: Full 7-chapter Master Project Report (`.docx` and `.pdf`).
