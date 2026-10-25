# 🚀 STARTUP GUIDE — MCA PROJECT REPORT GENERATOR (AI-POWERED)
**Amal Jyothi College of Engineering Autonomous, Kanjirappally**  
*Department of Computer Applications | Course: 24MCAR295 (Software Project Part 1)*

---

## ⚡ TURNKEY AI USAGE (2 SIMPLE STEPS)

### Step 1: Place This Folder in Your Project Root
Unzip and place the `MCA_Academic_Report_Toolkit/` folder directly into your project workspace root (right next to your source code or app files).

*(Alternatively, if working standalone, drop your codebase/repo clone into `01_Inputs/project_source/`).*

---

### Step 2: Copy & Paste the Master Prompt into AI Chat
> **Easiest Option**: Open **`COPY_PASTE_PROMPT.txt`** in the folder (opens in Notepad), press **Ctrl+A** then **Ctrl+C**, and paste into AI Chat!
>
> Or copy the prompt directly below into **Antigravity AI**, **Cursor**, **VS Code Copilot**, or **Claude Code**:

```text
You are the MCA Academic Project Report Generator embedded in this project toolkit.
Please perform an end-to-end automated academic project report generation for my project:

1. **Inspect My Codebase**:
   - Scan my repository source code (or 01_Inputs/project_source/) to identify my project domain, frontend/mobile frameworks, programming languages, database architecture, and major features.
   - Check 01_Inputs/reference_materials/ (base papers, notes) and 01_Inputs/images_and_evidence/ if present.

2. **Verify Student Details**:
   - Ask me directly in chat for:
     • Full Legal Name
     • University Register Number (e.g., AJC25MCA-XXXX)
     • Class Roll Number
     • Project Guide / Faculty Mentor Name
     • Official Project Title
   - Once I provide them, update `01_Inputs/config.json` with my authentic project parameters.

3. **UML Diagrams**:
   - Tailor all 9 publication-grade monochrome UML 2.5 diagrams (Use Case, Sequence, State, Activity, Class, Object, Component, Deployment, Collaboration) to my project architecture and verify them at 300 DPI in `01_Inputs/diagrams/`.

4. **Build Autonomous College Report**:
   - Run `python MCA_Academic_Report_Toolkit/generate_all.py --scan` (or `python generate_all.py --scan` from within the toolkit directory) to audit my codebase, extract real git logs, and compile:
   - Ensure full adherence to Autonomous College guidelines:
     • Times New Roman font (12 pt body, 1.5 line spacing, fully justified)
     • Exact margins: 1.18" (30 mm) Left binding margin, 1.0" (25.4 mm) Top/Bottom/Right
     • Centered chapter title pages
     • Single solid black table borders with zero colorful backgrounds
     • Zero mockup data policy
   - Produce both `.docx` and high-fidelity `.pdf` in `04_Outputs/Project_Report/`.

5. **Deliver Summary**:
   - Provide clickable file links to the generated documents so I can inspect and submit them immediately.
```

---

## 📁 OUTPUTS GENERATED

All documents are automatically compiled and delivered into:
📁 **`04_Outputs/Project_Report/`**

| Document | Target Location | Description |
|---|---|---|
| `Project_Report_<Name>.docx` | `04_Outputs/Project_Report/` | Full 7-Chapter Master Academic Report in Microsoft Word format with authentic front matter and 9 UML diagrams. |
| `Project_Report_<Name>.pdf` | `04_Outputs/Project_Report/` | Publication-grade high-fidelity PDF formatted for institutional evaluation. |

---

## ⚙️ OPTIONAL CLI COMMANDS (FOR AI AGENTS)

The AI agent will invoke the generation engine using standard CLI flags:
```bash
# Full build (DOCX + Word COM high-fidelity PDF)
python generate_all.py

# Fast build (DOCX only — skips PDF conversion)
python generate_all.py --skip-pdf

# Force re-rendering of all 9 UML architecture diagrams (300 DPI)
python generate_all.py --regenerate-diagrams
```
