"""
Master Report Builder — Front Matter & Preliminary Pages
MCA Academic Report Toolkit — Amal Jyothi College of Engineering Autonomous
Department of Computer Applications | Course: 24MCAR295
"""

import os
import re
import datetime
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

try:
    from .styles import (
        add_styled_table, set_table_borders,
        get_bookmark_name, add_internal_hyperlink
    )
except ImportError:
    from styles import (
        add_styled_table, set_table_borders,
        get_bookmark_name, add_internal_hyperlink
    )

def load_and_prepare_front_matter(template_path=None, cfg=None):
    """
    Loads the official College Format DOCX directly to ensure:
    - Exact layout, margins, and typography from the prescribed college template.
    - Embedded official Amal Jyothi College emblem on Cover and Certificate is preserved.
    - Updates student name, registration number, project title, and faculty details dynamically from cfg.
    - Prepares Table of Contents with clickable internal bookmarks.
    """
    if cfg is None:
        cfg = {}

    inst = cfg.get("institution", {})
    st = cfg.get("student", {})
    fc = cfg.get("faculty", {})
    pj = cfg.get("project", {})

    student_name = st.get("full_name", "BLESSON JOSEPH BYJU")
    reg_number = st.get("reg_number", "AJC25MCA-2023")
    project_title = pj.get("title", "Wi-Fi Sense: AI-Powered Indoor Monitoring and Facility Intelligence Platform Using Wi-Fi CSI")
    short_name = pj.get("short_name", "WIFISENSE")
    guide_name = fc.get("project_guide_name", "Mr. Binumon Joseph")
    guide_desig = fc.get("project_guide_designation", "Assistant Professor")
    coord_name = fc.get("coordinator_name", "Ms. Meera Rose Mathew")
    coord_desig = fc.get("coordinator_designation", "Assistant Professor")
    hod_name = fc.get("hod_name", "Dr. Juby Mathew")
    hod_desig = fc.get("hod_designation", "Professor & Head of Department")
    college_name = inst.get("college_name", "AMAL JYOTHI COLLEGE OF ENGINEERING AUTONOMOUS")

    if template_path is None or not os.path.exists(template_path):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        template_path = os.path.join(base_dir, "02_Benchmarks_And_Templates", "College_Official_Report_Format_24MCAR295.docx")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"College format template not found at: {template_path}")

    doc = docx.Document(template_path)

    # Standardize margins across all template sections
    s0 = doc.sections[0]
    s0.top_margin = Inches(1.0)
    s0.bottom_margin = Inches(1.0)
    s0.left_margin = Inches(1.0)
    s0.right_margin = Inches(1.0)

    for s in doc.sections[1:]:
        s.top_margin = Inches(1.0)
        s.bottom_margin = Inches(1.0)
        s.left_margin = Inches(1.18)
        s.right_margin = Inches(1.0)

    # -------------------------------------------------------------
    # 1. UPDATE COVER PAGE (Paragraphs 0 to 25)
    # -------------------------------------------------------------
    doc.paragraphs[1].text = "WIFISENSE"
    doc.paragraphs[1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[1].paragraph_format.space_before = Pt(14)
    doc.paragraphs[1].paragraph_format.space_after = Pt(2)
    for r in doc.paragraphs[1].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(20)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[2].text = "AI-POWERED INDOOR MONITORING AND\nFACILITY INTELLIGENCE PLATFORM USING WI-FI CSI"
    doc.paragraphs[2].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[2].paragraph_format.space_after = Pt(16)
    for r in doc.paragraphs[2].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[4].text = "24MCAR295 - Mini Project"
    doc.paragraphs[4].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[4].paragraph_format.space_after = Pt(14)
    for r in doc.paragraphs[4].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[8].text = student_name
    doc.paragraphs[8].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[8].paragraph_format.space_after = Pt(2)
    for r in doc.paragraphs[8].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(14)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[9].text = f"Reg. No.: {reg_number}"
    doc.paragraphs[9].alignment = WD_ALIGN_PARAGRAPH.CENTER
    doc.paragraphs[9].paragraph_format.space_after = Pt(14)
    for r in doc.paragraphs[9].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(13)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # -------------------------------------------------------------
    # 2. UPDATE CERTIFICATE PAGE (Paragraphs 26 to 53)
    # -------------------------------------------------------------
    doc.paragraphs[36].text = (
        f"This is to certify that the Project report titled “Wi-Fi Sense: AI-Powered Indoor Monitoring and "
        f"Facility Intelligence Platform Using Wi-Fi CSI” is the bona fide work of {student_name} "
        f"(Regno: {reg_number}) carried out in partial fulfillment of the requirements for the award of "
        f"the Degree of Master of Computer Applications at Amal Jyothi College of Engineering Autonomous, "
        f"Kanjirappally. The project was undertaken during the period from July 01, 2026 to October 26, 2026."
    )
    doc.paragraphs[36].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.paragraphs[36].paragraph_format.line_spacing = 1.5
    for r in doc.paragraphs[36].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Signatures: Internal Guide & Coordinator
    doc.paragraphs[41].text = f"               {guide_name}                                                                       \t\t{coord_name}                           "
    for r in doc.paragraphs[41].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[42].text = f"               Internal Guide                                                                     \t\t     Coordinator             "
    for r in doc.paragraphs[42].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[49].text = hod_name
    doc.paragraphs[49].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in doc.paragraphs[49].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[50].text = hod_desig
    doc.paragraphs[50].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for r in doc.paragraphs[50].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(11)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # -------------------------------------------------------------
    # 3. UPDATE DECLARATION & ACKNOWLEDGEMENT (Paragraphs 54 to 87)
    # -------------------------------------------------------------
    doc.paragraphs[60].text = (
        f"I hereby declare that the project report “Wi-Fi Sense: AI-Powered Indoor Monitoring and Facility Intelligence "
        f"Platform Using Wi-Fi CSI” is a bona fide work done at Amal Jyothi College of Engineering Autonomous, "
        f"Kanjirappally, towards the partial fulfilment of the requirements for the award of the Master of "
        f"Computer Applications (MCA) during the period from July 01, 2026 to October 26, 2026."
    )
    doc.paragraphs[60].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.paragraphs[60].paragraph_format.line_spacing = 1.5
    for r in doc.paragraphs[60].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[68].text = f"             Date: 26/10/2026                                                                    {student_name}"
    doc.paragraphs[69].text = f"             KANJIRAPPALLY                                                                       Reg: {reg_number}"
    for p_dec in [doc.paragraphs[68], doc.paragraphs[69]]:
        for r in p_dec.runs:
            r.font.name = "Times New Roman"
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Acknowledgement text
    doc.paragraphs[80].text = (
        "First and foremost, I thank God almighty for his eternal love and protection throughout the project. "
        "I take this opportunity to express my gratitude to all who helped me in completing this project successfully. "
        "I wish to express my sincere gratitude to our Director (Administration) Rev. Fr. Dr. Roy Abraham Pazhayaparampil "
        "and Principal Dr. Lillykutty Jacob for providing good faculty for guidance.\n\n"
        f"I owe a great depth of gratitude towards our Head of the Department {hod_name} for helping us. "
        f"I extend my wholehearted thanks to the project coordinator {coord_name} for her valuable suggestions "
        "and for overwhelming concern and guidance from the beginning to the end of the project. "
        f"I would also express sincere gratitude to my guide {guide_name} for his inspiration and helping hand.\n\n"
        "I thank our beloved teachers for their cooperation and suggestions that helped me throughout the project. "
        "I express my thanks to all my friends and classmates for their interest, dedication, and encouragement shown "
        "towards the project. I convey my hearty thanks to my family for the moral support, suggestions, and encouragement "
        "to make this venture a success."
    )
    doc.paragraphs[80].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.paragraphs[80].paragraph_format.line_spacing = 1.5
    for r in doc.paragraphs[80].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.paragraphs[87].text = f"\t\t {student_name}"

    # -------------------------------------------------------------
    # 4. ABSTRACT (Paragraphs 88 to 90)
    # -------------------------------------------------------------
    doc.paragraphs[90].text = (
        "Wi-Fi Sense is an AI-powered indoor monitoring and facility intelligence platform designed to centralise "
        "contactless human presence sensing, real-time fall detection, room occupancy tracking, and space utilization analytics "
        "within a unified web-based interface. By analyzing Channel State Information (CSI) from commercial Wi-Fi devices, "
        "the platform detects physical activities and emergencies without requiring cameras or wearable sensors, protecting user privacy "
        "in sensitive environments such as bedrooms and restrooms. The platform serves caregivers, facility directors, corporate staff, and family members.\n\n"
        "The frontend is built with React 18, Vite, and Tailwind CSS, featuring HTML5 Canvas-based 64-subcarrier spectrogram waterfalls. "
        "The backend is developed with Python and FastAPI in an asynchronous ASGI architecture, while PostgreSQL hosted on Supabase Cloud "
        "stores organizations, buildings, rooms, devices, sensing events, alerts, and audit records. Hardware sensing utilizes dual-core "
        "ESP32-S3 transceivers streaming raw CSI packets over UART to a PySerial gateway at 921600 baud. The system is hosted across "
        "Render Cloud (backend API) and Vercel Global Edge (frontend web application).\n\n"
        "Browser-based login, fall incident escalation, data sharing policy management, family portal wellness checks, and corporate space analytics "
        "were automated with Selenium WebDriver and pytest, and their recorded test runs passed. Full regression testing covering 51 backend tests "
        "passed in 11.65 seconds. Multi-antenna spatial coordinate tracking and micro-Doppler contactless vital sign extraction are described as "
        "planned extensions and are not presented as completed features."
    )
    doc.paragraphs[90].alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    doc.paragraphs[90].paragraph_format.line_spacing = 1.5
    for r in doc.paragraphs[90].runs:
        r.font.name = "Times New Roman"
        r.font.size = Pt(12)
        r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # -------------------------------------------------------------
    # 5. REMOVE OLD TEMPLATE TABLES & INSTRUCTIONAL PLACEHOLDERS
    # -------------------------------------------------------------
    body = doc._body._element
    while len(doc.tables) > 0:
        tbl = doc.tables[0]._tbl
        tbl.getparent().remove(tbl)

    for p in doc.paragraphs[93:]:
        body.remove(p._element)

    if len(doc.sections) > 4:
        s4 = doc.sections[4]
        s4.header.is_linked_to_previous = False
        s4.footer.is_linked_to_previous = False
        for p in list(s4.header.paragraphs):
            p._element.getparent().remove(p._element)
        for p in list(s4.footer.paragraphs):
            p._element.getparent().remove(p._element)
        s4.top_margin = Inches(1.0)
        s4.bottom_margin = Inches(1.0)
        s4.left_margin = Inches(1.18)
        s4.right_margin = Inches(1.0)

    # -------------------------------------------------------------
    # 6. ADD INTERACTIVE CLICKABLE TABLE OF CONTENTS (CONTENT)
    # -------------------------------------------------------------
    toc_entries = [
        ["1", "INTRODUCTION", "1"],
        ["1.1", "PROJECT OVERVIEW", "2"],
        ["1.2", "PROJECT SPECIFICATION", "4"],
        ["2", "SYSTEM STUDY", "18"],
        ["2.1", "INTRODUCTION", "19"],
        ["2.2", "LITERATURE REVIEW", "21"],
        ["2.2.1", "NATURAL SYSTEM STUDIED", "24"],
        ["2.2.2", "DESIGNED SYSTEM STUDIED", "28"],
        ["2.3", "DRAWBACKS OF EXISTING SYSTEM", "32"],
        ["2.4", "PROPOSED SYSTEM", "35"],
        ["2.5", "ADVANTAGES OF PROPOSED SYSTEM", "37"],
        ["3", "REQUIREMENT ANALYSIS", "40"],
        ["3.1", "FEASIBILITY STUDY", "41"],
        ["3.1.1", "ECONOMICAL FEASIBILITY", "41"],
        ["3.1.2", "TECHNICAL FEASIBILITY", "43"],
        ["3.1.3", "BEHAVIORAL FEASIBILITY", "46"],
        ["3.1.4", "FEASIBILITY STUDY QUESTIONNAIRE", "49"],
        ["3.1.5", "GEOTAGGED PHOTOGRAPH", "52"],
        ["3.2", "SYSTEM SPECIFICATION", "53"],
        ["3.2.1", "HARDWARE SPECIFICATION", "53"],
        ["3.2.2", "SOFTWARE SPECIFICATION", "53"],
        ["3.3", "SOFTWARE DESCRIPTION", "58"],
        ["3.3.1", "REACT.JS AND VITE", "59"],
        ["3.3.2", "PYTHON AND FASTAPI", "59"],
        ["3.3.3", "POSTGRESQL (SUPABASE MANAGED)", "60"],
        ["3.3.4", "ESP-IDF AND C++ FIRMWARE", "61"],
        ["3.3.5", "TAILWIND CSS AND DESIGN SYSTEM", "62"],
        ["3.3.6", "HTML5 CANVAS SPECTROGRAM API", "63"],
        ["3.3.7", "PYSERIAL INGESTION DAEMON", "64"],
        ["3.3.8", "RENDER AND VERCEL CLOUD HOSTING", "65"],
        ["4", "SYSTEM DESIGN", "66"],
        ["4.1", "INTRODUCTION", "67"],
        ["4.2", "UML DIAGRAM", "67"],
        ["4.2.1", "USE CASE DIAGRAM", "68"],
        ["4.2.2", "SEQUENCE DIAGRAM", "70"],
        ["4.2.3", "STATE CHART DIAGRAM", "72"],
        ["4.2.4", "ACTIVITY DIAGRAM", "72"],
        ["4.2.5", "CLASS DIAGRAM", "74"],
        ["4.2.6", "OBJECT DIAGRAM", "75"],
        ["4.2.7", "COMPONENT DIAGRAM", "76"],
        ["4.2.8", "DEPLOYMENT DIAGRAM", "78"],
        ["4.2.9", "COLLABORATION DIAGRAM", "80"],
        ["4.3", "USER INTERFACE DESIGN USING FIGMA", "80"],
        ["4.4", "DATABASE DESIGN", "88"],
        ["4.4.1", "RELATIONAL DATABASE MANAGEMENT SYSTEM (RDBMS)", "88"],
        ["4.4.2", "NORMALIZATION", "89"],
        ["4.4.3", "SANITIZATION", "92"],
        ["4.4.4", "INDEXING", "92"],
        ["4.5", "TABLE DESIGN", "93"],
        ["5", "SYSTEM TESTING", "109"],
        ["5.1", "INTRODUCTION", "110"],
        ["5.2", "TEST PLAN", "111"],
        ["5.2.1", "UNIT TESTING", "117"],
        ["5.2.2", "INTEGRATION TESTING", "119"],
        ["5.2.3", "VALIDATION TESTING OR SYSTEM TESTING", "122"],
        ["5.2.4", "OUTPUT TESTING OR USER ACCEPTANCE TESTING", "124"],
        ["5.2.5", "AUTOMATION TESTING", "126"],
        ["5.2.6", "SELENIUM TESTING", "126"],
        ["6", "IMPLEMENTATION", "141"],
        ["6.1", "INTRODUCTION", "142"],
        ["6.2", "IMPLEMENTATION PROCEDURES", "142"],
        ["6.2.1", "USER TRAINING", "145"],
        ["6.2.2", "TRAINING ON THE APPLICATION SOFTWARE", "145"],
        ["6.2.3", "SYSTEM MAINTENANCE", "146"],
        ["6.2.4", "HOSTING", "149"],
        ["7", "CONCLUSION AND FUTURE SCOPE", "152"],
        ["7.1", "CONCLUSION", "153"],
        ["7.2", "FUTURE SCOPE", "154"],
        ["8", "BIBLIOGRAPHY", "157"],
        ["9", "APPENDIX", "160"],
        ["9.1", "SAMPLE CODE", "161"],
        ["9.2", "SCREEN SHOTS", "166"],
        ["9.3", "GIT LOG", "169"]
    ]

    add_interactive_toc_table(doc, toc_entries, col_widths=[0.9, 4.25, 0.85])
    return doc

def add_interactive_toc_table(doc, toc_entries, col_widths=[0.9, 4.25, 0.85]):
    """Builds the official Table of Contents with active internal hyperlinks."""
    table = doc.add_table(rows=1, cols=3)
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    table.autofit = False
    set_table_borders(table)

    headers = ["SL. NO", "TOPIC", "PAGE NO"]
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        for r in p.runs:
            r.font.name = 'Times New Roman'
            r.font.size = Pt(11)
            r.font.bold = True
            r.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    shd = parse_xml(r'<w:shd {} w:fill="EAEAEA"/>'.format(nsdecls('w')))
    for cell in hdr_cells:
        cell._tc.get_or_add_tcPr().append(shd)

    for row_data in toc_entries:
        sl_no, topic, page_no = row_data[0], row_data[1], row_data[2]
        bm_name = get_bookmark_name(sl_no)
        is_chapter = ("." not in sl_no)
        row_cells = table.add_row().cells

        # Col 0: SL. NO
        p0 = row_cells[0].paragraphs[0]
        p0.alignment = WD_ALIGN_PARAGRAPH.LEFT if "." in sl_no else WD_ALIGN_PARAGRAPH.CENTER
        add_internal_hyperlink(p0, sl_no, bm_name, font_size=Pt(11) if is_chapter else Pt(10), is_bold=is_chapter)

        # Col 1: TOPIC
        p1 = row_cells[1].paragraphs[0]
        p1.alignment = WD_ALIGN_PARAGRAPH.LEFT
        indent = "    " if sl_no.count(".") >= 2 else ("  " if "." in sl_no else "")
        add_internal_hyperlink(p1, indent + topic, bm_name, font_size=Pt(11) if is_chapter else Pt(10), is_bold=is_chapter)

        # Col 2: PAGE NO
        p2 = row_cells[2].paragraphs[0]
        p2.alignment = WD_ALIGN_PARAGRAPH.CENTER
        add_internal_hyperlink(p2, page_no, bm_name, font_size=Pt(11) if is_chapter else Pt(10), is_bold=is_chapter)

    for row in table.rows:
        for idx, width in enumerate(col_widths):
            row.cells[idx].width = Inches(width)
            tcPr = row.cells[idx]._tc.get_or_add_tcPr()
            tcMar = OxmlElement('w:tcMar')
            for m, val in [('top', '100'), ('bottom', '100'), ('left', '140'), ('right', '140')]:
                node = OxmlElement(f'w:{m}')
                node.set(qn('w:w'), val)
                node.set(qn('w:type'), 'dxa')
                tcMar.append(node)
            tcPr.append(tcMar)

def add_preliminary_lists(doc):
    """Adds the clean List of Abbreviations right after Table of Contents matching the benchmark report."""
    doc.add_page_break()

    p_ab = doc.add_paragraph()
    p_ab.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_ab.paragraph_format.space_before = Pt(14)
    p_ab.paragraph_format.space_after = Pt(20)
    r_ab = p_ab.add_run("List of Abbreviations")
    r_ab.font.name = "Times New Roman"
    r_ab.font.size = Pt(16)
    r_ab.font.bold = True
    r_ab.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    abbreviations = [
        ("AI", "Artificial Intelligence"),
        ("API", "Application Programming Interface"),
        ("ASGI", "Asynchronous Server Gateway Interface"),
        ("CFR", "Channel Frequency Response"),
        ("CFO", "Carrier Frequency Offset"),
        ("COTS", "Commercial Off-The-Shelf"),
        ("CSI", "Channel State Information"),
        ("DFS", "Doppler Frequency Shift"),
        ("ESP-IDF", "Espressif IoT Development Framework"),
        ("FFT", "Fast Fourier Transform"),
        ("HTML", "HyperText Markup Language"),
        ("HTTPS", "Hypertext Transfer Protocol Secure"),
        ("IoT", "Internet of Things"),
        ("JSON", "JavaScript Object Notation"),
        ("JWT", "JSON Web Token"),
        ("MAC", "Media Access Control"),
        ("MIMO", "Multiple-Input Multiple-Output"),
        ("ML", "Machine Learning"),
        ("OFDM", "Orthogonal Frequency Division Multiplexing"),
        ("PHY", "Physical Layer"),
        ("PIR", "Passive Infrared"),
        ("RBAC", "Role-Based Access Control"),
        ("RDBMS", "Relational Database Management System"),
        ("REST", "Representational State Transfer"),
        ("RF", "Radio Frequency"),
        ("RSSI", "Received Signal Strength Indicator"),
        ("SFO", "Sampling Frequency Offset"),
        ("SPA", "Single Page Application"),
        ("SQL", "Structured Query Language"),
        ("SSE", "Server-Sent Events"),
        ("STFT", "Short-Time Fourier Transform"),
        ("TCN", "Temporal Convolutional Network"),
        ("TLS", "Transport Layer Security"),
        ("UART", "Universal Asynchronous Receiver-Transmitter"),
        ("UAT", "User Acceptance Testing"),
        ("UI", "User Interface"),
        ("UML", "Unified Modeling Language"),
        ("URL", "Uniform Resource Locator"),
        ("UUID", "Universally Unique Identifier"),
        ("WSS", "WebSocket Secure"),
        ("1NF", "First Normal Form"),
        ("2NF", "Second Normal Form"),
        ("3NF", "Third Normal Form")
    ]

    for abbr, expansion in abbreviations:
        p = doc.add_paragraph()
        p.paragraph_format.line_spacing = 1.3
        p.paragraph_format.space_after = Pt(3)
        p.paragraph_format.left_indent = Inches(0.5)
        r1 = p.add_run(f"{abbr:<12} :  ")
        r1.font.name = "Times New Roman"
        r1.font.size = Pt(11)
        r1.font.bold = True
        r2 = p.add_run(expansion)
        r2.font.name = "Times New Roman"
        r2.font.size = Pt(11)
