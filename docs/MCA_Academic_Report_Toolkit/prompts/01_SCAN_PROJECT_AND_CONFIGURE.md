# Prompt 01: Scan Project and Auto-Configure

Copy and paste the prompt below to **Antigravity AI** in your IDE to automatically inspect your codebase or connected GitHub repository and configure your project details:

---

```markdown
Please inspect my project repository/source code located in `01_Inputs/project_source/` (or the connected GitHub workspace repository) and update `01_Inputs/config.json` with authentic details based on my actual project:

1. **Student & Institutional Info**:
   - Confirm my Full Name, University Register Number, Roll Number, and Email.
   - Set Course Code to `24MCAR295 — Master of Computer Applications`.
   - Set College to `Amal Jyothi College of Engineering Autonomous, Kanjirappally`.

2. **Technical Stack Analysis**:
   - Scan my source code files to determine the exact Frontend/Mobile Framework, Programming Language, Backend/Database, and Cloud APIs.
   - Update `project.title`, `project.short_name`, `project.primary_language`, and `project.backend_infrastructure` in `01_Inputs/config.json`.

3. **Subsystems & Data Schemas**:
   - Extract real database models/tables, API routes, and primary UI screens.
   - Strictly follow the **Zero Mockup Data** rule — do not invent dummy entities.

Once `config.json` is verified and updated, let me know so I can proceed to generate my reports.
```
