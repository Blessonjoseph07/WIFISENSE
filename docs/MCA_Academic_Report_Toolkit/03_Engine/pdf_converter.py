import os
import time

def convert_docx_to_pdf(docx_path, output_pdf_path=None):
    """
    Converts a single DOCX document to high-fidelity PDF using Microsoft Word COM automation.
    Requires Microsoft Word to be installed on the host Windows system.
    """
    import win32com.client
    import pythoncom

    if output_pdf_path is None:
        output_pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

    os.makedirs(os.path.dirname(os.path.abspath(output_pdf_path)), exist_ok=True)
    pythoncom.CoInitialize()
    word = None
    doc = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        abs_docx = os.path.abspath(docx_path)
        abs_pdf = os.path.abspath(output_pdf_path)

        doc = word.Documents.Open(abs_docx)
        # 17 represents wdFormatPDF in Word Object Model
        doc.SaveAs(abs_pdf, FileFormat=17)
        return abs_pdf
    finally:
        if doc is not None:
            try:
                doc.Close(SaveChanges=False)
            except Exception:
                pass
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

def batch_convert_to_pdf(docx_files, output_dir=None):
    """
    Converts a list of DOCX files to PDF using a SINGLE Word instance for maximum speed and stability.
    """
    import win32com.client
    import pythoncom

    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    converted = []
    print(f"\n--- Converting {len(docx_files)} Documents to PDF (Single Word COM Instance) ---")
    
    pythoncom.CoInitialize()
    word = None
    try:
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = False

        for docx_path in docx_files:
            t0 = time.time()
            base_name = os.path.splitext(os.path.basename(docx_path))[0]
            if output_dir:
                pdf_path = os.path.join(output_dir, base_name + ".pdf")
            else:
                pdf_path = os.path.splitext(docx_path)[0] + ".pdf"

            abs_docx = os.path.abspath(docx_path)
            abs_pdf = os.path.abspath(pdf_path)

            doc = None
            try:
                doc = word.Documents.Open(abs_docx)
                doc.SaveAs(abs_pdf, FileFormat=17)
                dt = time.time() - t0
                print(f"  [PDF OK] {os.path.basename(docx_path)} -> {os.path.basename(pdf_path)} ({dt:.2f}s)")
                converted.append(abs_pdf)
            except Exception as e:
                print(f"  [PDF ERROR] {os.path.basename(docx_path)}: {e}")
            finally:
                if doc is not None:
                    try:
                        doc.Close(SaveChanges=False)
                    except Exception:
                        pass
    finally:
        if word is not None:
            try:
                word.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()

    return converted
