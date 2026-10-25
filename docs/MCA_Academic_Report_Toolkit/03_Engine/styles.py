import os
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import qn, nsdecls

def setup_document_styles(doc):
    """Sets up standard A4 page layout and Times New Roman typographic baseline."""
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(1.0)
    section.bottom_margin = Inches(1.0)
    section.left_margin = Inches(1.25)   # standard academic binding margin
    section.right_margin = Inches(1.0)

    # Base Normal Style
    normal_style = doc.styles['Normal']
    normal_style.font.name = 'Times New Roman'
    normal_style.font.size = Pt(12)
    normal_style.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

import re

_bookmark_counter = 1000

def get_bookmark_name(sl_no):
    """Generates a valid OpenXML bookmark name from a section or chapter number."""
    clean = sl_no.strip().replace(".", "_").replace(" ", "_")
    if "_" in clean:
        return f"bm_sec_{clean}"
    else:
        return f"bm_ch_{clean}"

def add_bookmark_to_paragraph(paragraph, bookmark_name):
    """Attaches a bookmarkStart and bookmarkEnd to the paragraph for internal hyperlink navigation."""
    global _bookmark_counter
    _bookmark_counter += 1
    bm_id = str(_bookmark_counter)
    
    b_start = OxmlElement('w:bookmarkStart')
    b_start.set(qn('w:id'), bm_id)
    b_start.set(qn('w:name'), bookmark_name)
    paragraph._p.insert(0, b_start)
    
    b_end = OxmlElement('w:bookmarkEnd')
    b_end.set(qn('w:id'), bm_id)
    paragraph._p.append(b_end)

def add_internal_hyperlink(paragraph, text, bookmark_name, font_name="Times New Roman", font_size=Pt(11), is_bold=False, color="000000"):
    """Creates a clickable internal hyperlink run pointing to an internal document bookmark."""
    hl = OxmlElement('w:hyperlink')
    hl.set(qn('w:anchor'), bookmark_name)
    hl.set(qn('w:history'), '1')
    
    r = OxmlElement('w:r')
    rPr = OxmlElement('w:rPr')
    
    rf = OxmlElement('w:rFonts')
    rf.set(qn('w:ascii'), font_name)
    rf.set(qn('w:hAnsi'), font_name)
    rPr.append(rf)
    
    if is_bold:
        rPr.append(OxmlElement('w:b'))
    sz = OxmlElement('w:sz')
    sz.set(qn('w:val'), str(int(font_size.pt * 2)))
    rPr.append(sz)
    
    col = OxmlElement('w:color')
    col.set(qn('w:val'), color)
    rPr.append(col)
    
    u = OxmlElement('w:u')
    u.set(qn('w:val'), 'none')
    rPr.append(u)
    
    t = OxmlElement('w:t')
    t.text = text
    r.append(rPr)
    r.append(t)
    hl.append(r)
    paragraph._p.append(hl)

def add_chapter_heading(doc, chapter_num, chapter_title, page_break=True, is_first_body_chapter=False):
    """
    Renders a standalone academic Chapter Divider Page centered vertically and horizontally,
    matching the autonomous college format and previous year report:
    
                        CHAPTER X

                      CHAPTER TITLE

    Followed immediately by a page break so the chapter content starts cleanly on the next page.
    """
    if page_break and not is_first_body_chapter:
        doc.add_page_break()

    # Spacer paragraph with fixed line spacing (Pt 320) to guarantee 100% reliable
    # vertical centering across all chapters, immune to Word top-of-page space suppression
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_before = Pt(0)
    p_spacer.paragraph_format.space_after = Pt(0)
    p_spacer.paragraph_format.line_spacing = Pt(320)
    r_sp = p_spacer.add_run(" ")
    r_sp.font.size = Pt(1)

    p_num = doc.add_paragraph()
    p_num.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_num.paragraph_format.space_before = Pt(0)
    p_num.paragraph_format.space_after = Pt(14)
    p_num.paragraph_format.keep_with_next = True
    run_num = p_num.add_run(f"CHAPTER {chapter_num}")
    run_num.font.name = 'Times New Roman'
    run_num.font.size = Pt(16)
    run_num.font.bold = True
    run_num.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Attach chapter bookmark for TOC navigation
    add_bookmark_to_paragraph(p_num, f"bm_ch_{chapter_num}")

    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(0)
    p_title.paragraph_format.space_after = Pt(0)
    run_title = p_title.add_run(chapter_title.upper())
    run_title.font.name = 'Times New Roman'
    run_title.font.size = Pt(16)
    run_title.font.bold = True
    run_title.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    doc.add_page_break()

def add_heading_1(doc, text):
    """Primary Section Heading (e.g. 1.1 PROJECT OVERVIEW)"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text.upper())
    run.font.name = 'Times New Roman'
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Attach section bookmark for TOC navigation
    m = re.match(r"^(\d+\.\d+(\.\d+)?)", text.strip())
    if m:
        add_bookmark_to_paragraph(p, get_bookmark_name(m.group(1)))

    return p

def add_heading_2(doc, text):
    """Secondary Subsection Heading (e.g. 3.1.1 Economical Feasibility)"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Attach subsection bookmark for TOC navigation
    m = re.match(r"^(\d+\.\d+(\.\d+)?)", text.strip())
    if m:
        add_bookmark_to_paragraph(p, get_bookmark_name(m.group(1)))

    return p

def add_heading_3(doc, text):
    """Tertiary Heading (e.g. A. Customer Booking Interface)"""
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(8)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Times New Roman'
    run.font.size = Pt(12)
    run.font.italic = True
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    m = re.match(r"^(\d+\.\d+(\.\d+)?)", text.strip())
    if m:
        add_bookmark_to_paragraph(p, get_bookmark_name(m.group(1)))

    return p

def add_body_p(doc, text, bold_prefix=None):
    """
    Adds body paragraph(s) with standard 1.5 line spacing.
    Splits multi-line strings on newlines so that soft breaks (<w:br/>) never cause
    Word's full-justification engine to stretch lines across the entire page.
    Short lines (< 65 chars) are left-aligned, while normal paragraphs are justified.
    """
    lines = text.split('\n')
    last_p = None
    for idx, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
        p = doc.add_paragraph()
        # Prevent Word from stretching short lines across the page margin
        if len(line) < 65:
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.5
        p.paragraph_format.space_after = Pt(6)

        if idx == 0 and bold_prefix:
            r_prefix = p.add_run(bold_prefix + " ")
            r_prefix.font.name = 'Times New Roman'
            r_prefix.font.size = Pt(12)
            r_prefix.font.bold = True
            r_prefix.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

        r_text = p.add_run(line)
        r_text.font.name = 'Times New Roman'
        r_text.font.size = Pt(12)
        r_text.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
        last_p = p
    return last_p

def add_bullet_p(doc, text, bold_prefix=None):
    """Adds an indented bullet point with 1.3 line spacing."""
    p = doc.add_paragraph()
    if len(text) < 65:
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.line_spacing = 1.3
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.left_indent = Inches(0.25)

    # Bullet point symbol
    r_bullet = p.add_run("\u2022 ")
    r_bullet.font.name = 'Times New Roman'
    r_bullet.font.size = Pt(11.5)
    r_bullet.font.bold = True
    r_bullet.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    if bold_prefix:
        r_prefix = p.add_run(bold_prefix + ": ")
        r_prefix.font.name = 'Times New Roman'
        r_prefix.font.size = Pt(11.5)
        r_prefix.font.bold = True
        r_prefix.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    r_text = p.add_run(text)
    r_text.font.name = 'Times New Roman'
    r_text.font.size = Pt(11.5)
    r_text.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    return p

def set_table_borders(table):
    """Applies standard thin black single borders to all sides and inside cells of a table."""
    tblPr = table._tbl.tblPr
    borders_xml = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>\n'
        f'  <w:top w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:left w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:bottom w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:right w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'  <w:insideV w:val="single" w:sz="4" w:space="0" w:color="000000"/>\n'
        f'</w:tblBorders>'
    )
    tblPr.append(borders_xml)

def add_styled_table(doc, headers, rows, col_widths=None, caption=None):
    """
    Creates a standard academic table matching the previous year benchmark report:
    - Clean black and white styling (strictly NO colored background or colored headers).
    - Compact row padding (standard normal header height, no oversized headers).
    - Times New Roman font (10.5pt bold headers, 10pt regular data cells).
    - Clean single black border grid.
    """
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p_cap.paragraph_format.space_before = Pt(8)
        p_cap.paragraph_format.space_after = Pt(3)
        p_cap.paragraph_format.keep_with_next = True
        run_cap = p_cap.add_run(caption)
        run_cap.font.name = 'Times New Roman'
        run_cap.font.size = Pt(11)
        run_cap.font.bold = True
        run_cap.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    table = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    table.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table)

    # Format Header Row (Academic standard: Bold black text, NO colored background fill, compact spacing)
    header_tr = table.rows[0]
    for i, h_text in enumerate(headers):
        cell = header_tr.cells[i]
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        p.paragraph_format.space_before = Pt(3)
        p.paragraph_format.space_after = Pt(3)
        run = p.add_run(h_text)
        run.font.name = 'Times New Roman'
        run.font.size = Pt(10.5)
        run.font.bold = True
        run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Format Data Rows (Regular black text, plain white background, compact spacing)
    for r_idx, row_data in enumerate(rows):
        row_tr = table.rows[r_idx + 1]
        for c_idx, cell_data in enumerate(row_data):
            cell = row_tr.cells[c_idx]
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            p.paragraph_format.space_before = Pt(2)
            p.paragraph_format.space_after = Pt(2)
            run = p.add_run(str(cell_data))
            run.font.name = 'Times New Roman'
            run.font.size = Pt(10)
            run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

    # Set Column Widths if provided
    if col_widths and len(col_widths) == len(headers):
        for row in table.rows:
            for idx, width in enumerate(col_widths):
                row.cells[idx].width = Inches(width)

    # Space after table
    p_spacer = doc.add_paragraph()
    p_spacer.paragraph_format.space_after = Pt(6)
    return table

def add_figure_image(doc, img_path, caption_text, width_inches=5.6, max_height_inches=5.2):
    """
    Embeds an image centered with academic figure caption.
    Automatically detects portrait images (e.g. mobile screenshots) and scales them
    to ensure they fit within single-page margins without spilling over.
    """
    if not os.path.exists(img_path):
        p_err = doc.add_paragraph(f"[Image Not Found: {img_path}]")
        p_err.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return

    # Auto-scale tall portrait mobile screenshots
    final_width = width_inches
    try:
        from PIL import Image
        with Image.open(img_path) as im:
            w, h = im.size
            if h > w:  # Portrait phone screenshot
                calc_h = width_inches * (h / w)
                if calc_h > max_height_inches:
                    final_width = max_height_inches * (w / h)
    except Exception:
        pass

    p_img = doc.add_paragraph()
    p_img.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_img.paragraph_format.space_before = Pt(8)
    p_img.paragraph_format.space_after = Pt(4)
    run_img = p_img.add_run()
    run_img.add_picture(img_path, width=Inches(final_width))

    p_cap = doc.add_paragraph()
    p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_cap.paragraph_format.space_before = Pt(2)
    p_cap.paragraph_format.space_after = Pt(10)
    run_cap = p_cap.add_run(caption_text)
    run_cap.font.name = 'Times New Roman'
    run_cap.font.size = Pt(11)
    run_cap.font.italic = True
    run_cap.font.bold = True
    run_cap.font.color.rgb = RGBColor(0x00, 0x00, 0x00)

def add_code_block(doc, code_str, caption=None):
    """
    Renders an academic code container with a subtle background (#F4F6F9),
    deep navy left accent border (#1B365D), monospaced Consolas font, and caption.
    """
    if caption:
        p_cap = doc.add_paragraph()
        p_cap.paragraph_format.space_before = Pt(8)
        p_cap.paragraph_format.space_after = Pt(3)
        p_cap.paragraph_format.keep_with_next = True
        r_cap = p_cap.add_run(caption)
        r_cap.font.name = 'Times New Roman'
        r_cap.font.size = Pt(10)
        r_cap.font.bold = True
        r_cap.font.color.rgb = RGBColor(0x1B, 0x36, 0x5D)

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = docx.enum.table.WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.0)

    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="F4F6F9"/>')
    tcPr.append(shd)

    tcBorders = parse_xml(f'''
        <w:tcBorders {nsdecls("w")}>
            <w:top w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>
            <w:left w:val="single" w:sz="18" w:space="0" w:color="1B365D"/>
            <w:bottom w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>
            <w:right w:val="single" w:sz="4" w:space="0" w:color="D0D7DE"/>
        </w:tcBorders>
    ''')
    tcPr.append(tcBorders)

    tcMar = parse_xml(f'''
        <w:tcMar {nsdecls("w")}>
            <w:top w:w="120" w:type="dxa"/>
            <w:left w:w="160" w:type="dxa"/>
            <w:bottom w:w="120" w:type="dxa"/>
            <w:right w:w="160" w:type="dxa"/>
        </w:tcMar>
    ''')
    tcPr.append(tcMar)

    if isinstance(code_str, list):
        code_str = "\n".join(code_str)
    lines = code_str.strip().split('\n')
    p = cell.paragraphs[0]
    p.paragraph_format.space_before = Pt(0)
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = Pt(12)

    for idx, l in enumerate(lines):
        if idx > 0:
            p = cell.add_paragraph()
            p.paragraph_format.space_before = Pt(0)
            p.paragraph_format.space_after = Pt(0)
            p.paragraph_format.line_spacing = Pt(12)
        r = p.add_run(l)
        r.font.name = 'Consolas'
        r.font.size = Pt(8.5)
        r.font.color.rgb = RGBColor(0x24, 0x29, 0x2F)

    p_sp = doc.add_paragraph()
    p_sp.paragraph_format.space_before = Pt(0)
    p_sp.paragraph_format.space_after = Pt(4)

def configure_body_header_footer(section, project_title='Project Report'):
    """
    Configures standardized academic running header and footer for body chapters:
    - Running Header: Project Title (left) with thin bottom border.
    - Running Footer: College Name & Department with thin top border.
    """
    section.header.is_linked_to_previous = False
    section.footer.is_linked_to_previous = False

    # 1. Clean and configure Running Header
    hdr = section.header
    for p in list(hdr.paragraphs):
        p._element.getparent().remove(p._element)

    p_hdr = hdr.add_paragraph()
    p_hdr.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_hdr.paragraph_format.space_before = Pt(0)
    p_hdr.paragraph_format.space_after = Pt(3)
    p_hdr.paragraph_format.tab_stops.add_tab_stop(Inches(6.09), docx.enum.text.WD_TAB_ALIGNMENT.RIGHT)

    r_proj = p_hdr.add_run(project_title)
    r_proj.font.name = "Times New Roman"
    r_proj.font.size = Pt(9.5)
    r_proj.font.bold = True
    r_proj.font.color.rgb = RGBColor(0x22, 0x22, 0x22)

    r_tab = p_hdr.add_run("\t")
    r_pg = p_hdr.add_run()
    r_pg.font.name = "Times New Roman"
    r_pg.font.size = Pt(9.5)
    r_pg.font.bold = True
    r_pg.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    fldChar1 = parse_xml(r'<w:fldChar %s w:fldCharType="begin"/>' % nsdecls('w'))
    instrText = parse_xml(r'<w:instrText %s xml:space="preserve"> PAGE </w:instrText>' % nsdecls('w'))
    fldChar2 = parse_xml(r'<w:fldChar %s w:fldCharType="separate"/>' % nsdecls('w'))
    fldChar3 = parse_xml(r'<w:fldChar %s w:fldCharType="end"/>' % nsdecls('w'))
    r_pg._r.append(fldChar1)
    r_pg._r.append(instrText)
    r_pg._r.append(fldChar2)
    r_pg._r.append(fldChar3)

    # Add a clean, single thin bottom border to header paragraph
    pPr = p_hdr._element.get_or_add_pPr()
    pBdr = OxmlElement('w:pBdr')
    bottom = OxmlElement('w:bottom')
    bottom.set(qn('w:val'), 'single')
    bottom.set(qn('w:sz'), '4')
    bottom.set(qn('w:space'), '2')
    bottom.set(qn('w:color'), '000000')
    pBdr.append(bottom)
    pPr.append(pBdr)

    # 2. Clean and configure Running Footer
    ftr = section.footer
    for p in list(ftr.paragraphs):
        p._element.getparent().remove(p._element)

    p_ftr = ftr.add_paragraph()
    p_ftr.alignment = WD_ALIGN_PARAGRAPH.LEFT
    p_ftr.paragraph_format.space_before = Pt(4)
    p_ftr.paragraph_format.space_after = Pt(0)
    # Right-aligned tab stop exactly at right margin boundary (6.09 in)
    p_ftr.paragraph_format.tab_stops.add_tab_stop(Inches(6.09), docx.enum.text.WD_TAB_ALIGNMENT.RIGHT)

    # Top border on footer paragraph
    pPr_f = p_ftr._element.get_or_add_pPr()
    pBdr_f = OxmlElement('w:pBdr')
    top = OxmlElement('w:top')
    top.set(qn('w:val'), 'single')
    top.set(qn('w:sz'), '4')
    top.set(qn('w:space'), '2')
    top.set(qn('w:color'), '000000')
    pBdr_f.append(top)
    pPr_f.append(pBdr_f)

    r_col = p_ftr.add_run("Amal Jyothi College of Engineering Autonomous, Kanjirappally")
    r_col.font.name = "Times New Roman"
    r_col.font.size = Pt(8.5)
    r_col.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

    r_tab = p_ftr.add_run("\t")
    r_dept = p_ftr.add_run("Department of Computer Applications")
    r_dept.font.name = "Times New Roman"
    r_dept.font.size = Pt(8.5)
    r_dept.font.color.rgb = RGBColor(0x33, 0x33, 0x33)
