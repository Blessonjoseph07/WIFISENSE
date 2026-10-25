import os
import docx

try:
    from .front_matter import load_and_prepare_front_matter, add_preliminary_lists
    from .styles import configure_body_header_footer
    from .chapters_1_3 import add_chapters_1_to_3
    from .chapter_4_design import add_chapter_4_design
    from .chapters_5_7 import add_chapters_5_to_7
    from .back_matter import add_back_matter
except ImportError:
    from front_matter import load_and_prepare_front_matter, add_preliminary_lists
    from styles import configure_body_header_footer
    from chapters_1_3 import add_chapters_1_to_3
    from chapter_4_design import add_chapter_4_design
    from chapters_5_7 import add_chapters_5_to_7
    from back_matter import add_back_matter

def build_master_project_report(output_dir, cfg):
    """
    Builds the comprehensive 7-Chapter (plus Bibliography & Appendices) Master Project Report
    conforming strictly to the Amal Jyothi College of Engineering Autonomous specifications:
    - Official College Format DOCX loaded directly, preserving the official college emblem on Cover and Certificate.
    - Title, student details, register number, and faculty details dynamically populated from cfg.
    - Interactive Table of Contents with clickable internal bookmarks for all chapters and sections.
    - Dedicated body section with Running Header (Project Title) and Running Footer (College Name & Dept) with divider borders.
    - Dedicated standalone Chapter Divider Pages centered vertically and horizontally for all chapters.
    - Full comprehensive academic content, literature review, hardware/software specs, database schemas, formal test cases, and references.
    """
    os.makedirs(output_dir, exist_ok=True)

    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_path = os.path.join(base_dir, "02_Benchmarks_And_Templates", "College_Official_Report_Format_24MCAR295.docx")
    diagrams_dir = os.path.join(base_dir, "01_Inputs", "diagrams")

    st = cfg.get("student", {})
    pj = cfg.get("project", {})
    student_name = st.get("full_name", "Student")
    project_title = pj.get("title", "Project Report")

    # Clean filename
    safe_name = "".join(c for c in student_name if c.isalnum() or c in (' ', '_', '-')).strip().replace(' ', '_')
    if not safe_name:
        safe_name = "Student"
    docx_filename = f"Project_Report_{safe_name}.docx"
    docx_path = os.path.join(output_dir, docx_filename)

    print("  [1/6] Loading College Format Template & Initializing Front Matter...")
    doc = load_and_prepare_front_matter(template_path=template_path, cfg=cfg)

    print("  [2/6] Building Preliminary Lists (TOC, LOT, LOF, Abbreviations with Bookmarks)...")
    add_preliminary_lists(doc)

    print("  [3/6] Configuring Body Section (Running Header & Footer, Centered Chapter 1-3 Pages)...")
    body_section = doc.add_section(docx.enum.section.WD_SECTION.NEW_PAGE)
    body_section.top_margin = docx.shared.Inches(1.0)
    body_section.bottom_margin = docx.shared.Inches(1.0)
    body_section.left_margin = docx.shared.Inches(1.18)
    body_section.right_margin = docx.shared.Inches(1.0)
    short_name = pj.get("short_name", "Wi-Fi Sense")
    configure_body_header_footer(body_section, project_title=short_name)
    add_chapters_1_to_3(doc, cfg=cfg)

    print("  [4/6] Building Chapter 4: System Design (9 UML Diagrams, Schemas)...")
    add_chapter_4_design(doc, cfg=cfg, diagrams_dir=diagrams_dir)

    print("  [5/6] Building Chapters 5 to 7 (Testing Cases, Implementation, Conclusion & Check Matrix)...")
    add_chapters_5_to_7(doc, cfg=cfg)

    print("  [6/6] Building Chapters 8 to 9 (IEEE Bibliography, Appendices & Commit Audit)...")
    add_back_matter(doc, cfg=cfg)

    print(f"  Saving Master DOCX to: {docx_path}...")
    doc.save(docx_path)
    return docx_path
