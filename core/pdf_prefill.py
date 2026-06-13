"""
pdf_prefill.py — Glory Nursing
Fills CNA_app.pdf (via canvas layer mapping) and CMA_app.pdf (via form field dictionary mapping).
"""

import io
import os
from pypdf import PdfReader, PdfWriter
from pypdf.generic import NameObject, BooleanObject

# Imports for drawing structural text on flattened/signed documents
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter


def _get_pdf_path(filename):
    """Resolve path to PDF in static files."""
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'static', 'core', 'documents', filename)


def _fill_fields_interactive(input_path, field_values: dict) -> bytes:
    """
    Standard interactive filler used for standard PDFs (like CMA_app.pdf).
    """
    reader = PdfReader(input_path)
    writer = PdfWriter()
    writer.append(reader)

    writer.update_page_form_field_values(
        None, 
        field_values,
        auto_regenerate=True
    )

    try:
        catalog = writer._root_object
        if "/AcroForm" in catalog:
            acroform = catalog["/AcroForm"].get_object()
            acroform.update({
                NameObject("/NeedAppearances"): BooleanObject(True)
            })
    except Exception:
        pass

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def _embed_signature(writer, page_idx, sig_data_url, x, y, width=200, height=50):
    """Embed a base64 signature image onto a PDF page."""
    if not sig_data_url or not sig_data_url.startswith('data:image'):
        return
    try:
        import base64
        from PIL import Image as PILImage
        from reportlab.lib.utils import ImageReader
        header, b64data = sig_data_url.split(',', 1)
        img_bytes = base64.b64decode(b64data)
        img_buf = io.BytesIO(img_bytes)
        img_reader = ImageReader(img_buf)

        overlay_buf = io.BytesIO()
        can = canvas.Canvas(overlay_buf, pagesize=letter)
        can.drawImage(img_reader, x, y, width=width, height=height, mask='auto')
        can.save()
        overlay_buf.seek(0)

        overlay_reader = PdfReader(overlay_buf)
        page = writer.pages[page_idx]
        page.merge_page(overlay_reader.pages[0])
    except Exception as e:
        print(f"Signature embed error: {e}")


def prefill_cna_pdf(data: dict) -> bytes:
    """
    Pre-fill the CNA application PDF.
    Since the template is digitally certified/flattened by Adobe Acrobat Sign,
    we visually overlay the text directly onto the page canvas coordinate system.
    """
    input_path = _get_pdf_path('CNA_app.pdf')

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing required baseline document: {input_path}")

    # 1. Generate an overlay PDF containing data positioned matching Page 1 layout blocks
    packet = io.BytesIO()
    can = canvas.Canvas(packet, pagesize=letter)
    
    # Configure font aesthetics
    can.setFont("Helvetica", 10)
    
    # --- PAGE 1 POSITION COORDINATES (X, Y) ---
    # These map to standard letter page dimensions (8.5 x 11 inches -> 612 x 792 points)
    can.drawString(140, 615, data.get('last_name', ''))       # Last Name
    can.drawString(285, 615, data.get('first_name', ''))      # First Name
    can.drawString(440, 615, data.get('middle_initial', '')) # MI
    
    can.drawString(140, 580, data.get('dob', ''))             # Date of Birth
    can.drawString(340, 580, data.get('ssn', ''))             # SS#
    
    can.drawString(140, 532, data.get('street', ''))          # Street Address
    can.drawString(460, 532, data.get('apt', ''))             # Apt/Unit
    
    can.drawString(140, 502, f"{data.get('city', '')}, {data.get('state', 'OK')} {data.get('zip', '')}") # City, State, Zip
    can.drawString(140, 472, data.get('phone', ''))           # Phone
    can.drawString(340, 472, data.get('email', ''))           # Email
    
    can.drawString(220, 442, data.get('referral', ''))        # Referral Source
    can.drawString(220, 412, 'Certified Nursing Assistant (CNA)') # Course Title
    
    # Emergency Contact Block
    can.drawString(220, 360, data.get('emergency_name', ''))
    can.drawString(460, 360, data.get('emergency_phone', ''))
    can.drawString(140, 330, data.get('emergency_address', ''))
    can.drawString(460, 330, data.get('emergency_relationship', ''))
    
    # Education Layout Data Strings
    can.drawString(140, 262, data.get('hs_name', ''))
    can.drawString(140, 240, data.get('hs_address', ''))
    can.drawString(140, 218, f"From: {data.get('hs_from', '')}  To: {data.get('hs_to', '')}")
    can.drawString(460, 218, data.get('hs_diploma', ''))
    
    can.drawString(140, 168, data.get('college_name', ''))
    can.drawString(140, 145, data.get('college_address', ''))
    can.drawString(140, 122, f"From: {data.get('college_from', '')}  To: {data.get('college_to', '')}")
    can.drawString(460, 122, data.get('college_degree', ''))
    
    can.save()
    packet.seek(0)
    
    # 2. Extract layers using pypdf and merge the overlay stream into page 1
    reader = PdfReader(input_path)
    writer = PdfWriter()
    overlay_reader = PdfReader(packet)
    
    # Merge visual data on page 1
    page_1 = reader.pages[0]
    page_1.merge_page(overlay_reader.pages[0])
    writer.add_page(page_1)
    
    # Append the remaining untouched template pages (e.g. guidelines, policies)
    for remaining_page in reader.pages[1:]:
        writer.add_page(remaining_page)
        
    import datetime
    today = datetime.date.today().strftime('%m/%d/%Y')
    full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()

    # ── Page 2: Affidavit of Lawful Presence ──────────────────────────
    overlay2 = io.BytesIO()
    c2 = canvas.Canvas(overlay2, pagesize=letter)
    c2.setFont("Helvetica", 11)
    lawful = data.get('lawful_presence', '')
    if lawful == 'citizen':
        c2.drawString(28, 544, '✓')
    elif lawful == 'alien':
        c2.drawString(28, 505, '✓')
        c2.drawString(127, 486, data.get('alien_number', ''))
    c2.drawString(48, 352, today)
    c2.drawString(197, 352, full_name)
    c2.drawString(48, 333, 'Oklahoma City, OK')
    c2.drawString(197, 333, full_name)
    c2.save()
    overlay2.seek(0)
    writer.pages[1].merge_page(PdfReader(overlay2).pages[0])

    # ── Page 4: Authorized Tasks Acknowledgment ────────────────────────
    overlay4 = io.BytesIO()
    c4 = canvas.Canvas(overlay4, pagesize=letter)
    c4.setFont("Helvetica", 11)
    c4.drawString(102, 238, full_name)
    c4.drawString(102, 155, today)
    c4.save()
    overlay4.seek(0)
    writer.pages[3].merge_page(PdfReader(overlay4).pages[0])

    # ── Page 5: Photo/Media Release ────────────────────────────────────
    overlay5 = io.BytesIO()
    c5 = canvas.Canvas(overlay5, pagesize=letter)
    c5.setFont("Helvetica", 11)
    c5.drawString(127, 656, full_name)
    c5.drawString(127, 634, data.get('dob', ''))
    c5.drawString(127, 612, data.get('phone', ''))
    c5.drawString(127, 589, data.get('email', ''))
    photo = data.get('photo_release', '')
    if photo == 'consent':
        c5.setFont("Helvetica", 14)
        c5.drawString(28, 448, '✓')
    elif photo == 'decline':
        c5.setFont("Helvetica", 14)
        c5.drawString(28, 384, '✓')
    c5.setFont("Helvetica", 11)
    c5.drawString(48, 104, today)
    c5.save()
    overlay5.seek(0)
    writer.pages[4].merge_page(PdfReader(overlay5).pages[0])

    # ── Page 17: Grievance/Refund acknowledgment ───────────────────────
    overlay17 = io.BytesIO()
    c17 = canvas.Canvas(overlay17, pagesize=letter)
    c17.setFont("Helvetica", 11)
    c17.drawString(200, 726, full_name)
    c17.drawString(430, 726, today)
    c17.save()
    overlay17.seek(0)
    writer.pages[16].merge_page(PdfReader(overlay17).pages[0])

    # ── Page 19: Background Check ──────────────────────────────────────
    overlay19 = io.BytesIO()
    c19 = canvas.Canvas(overlay19, pagesize=letter)
    c19.setFont("Helvetica", 14)
    bg = data.get('background_check', 'no')
    if bg == 'yes':
        c19.drawString(340, 608, '✓')
    else:
        c19.drawString(340, 570, '✓')
    c19.setFont("Helvetica", 11)
    c19.drawString(102, 238, full_name)
    c19.drawString(102, 155, today)
    c19.save()
    overlay19.seek(0)
    writer.pages[18].merge_page(PdfReader(overlay19).pages[0])

    # ── Page 21: Second Authorized Tasks ──────────────────────────────
    overlay21 = io.BytesIO()
    c21 = canvas.Canvas(overlay21, pagesize=letter)
    c21.setFont("Helvetica", 11)
    c21.drawString(102, 238, full_name)
    c21.drawString(102, 155, today)
    c21.save()
    overlay21.seek(0)
    writer.pages[20].merge_page(PdfReader(overlay21).pages[0])

    # ── Embed signature on all signature pages ─────────────────────────
    sig_data = data.get('signature_data', '')
    if sig_data:
        _embed_signature(writer, 0, sig_data, x=130, y=78, width=180, height=40)    # Page 1
        _embed_signature(writer, 1, sig_data, x=197, y=342, width=150, height=35)   # Page 2
        _embed_signature(writer, 3, sig_data, x=102, y=186, width=150, height=35)   # Page 4
        _embed_signature(writer, 4, sig_data, x=48, y=113, width=150, height=35)    # Page 5
        _embed_signature(writer, 18, sig_data, x=102, y=186, width=150, height=35)  # Page 19
        _embed_signature(writer, 20, sig_data, x=102, y=186, width=150, height=35)  # Page 21

    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def prefill_cma_pdf(data: dict) -> bytes:
    """
    Pre-fill the CMA application PDF with form submission data.
    """
    input_path = _get_pdf_path('CMA_app.pdf')

    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing required baseline document: {input_path}")

    full_name = f"{data.get('first_name', '')} {data.get('last_name', '')}".strip()
    lawful = data.get('lawful_presence', '')

    field_values = {
        'Checkbox 9':   '/Yes',   
        'Checkbox 10':  '/Yes',   
        'Checkbox 11':  '/Yes',   
        'Checkbox 12':  '/Yes',   
        'Checkbox 13':  '/Yes',   
        'Typed or Printed Name of Applicant': full_name,
        'Social Security Number of Applicant': data.get('ssn', ''),
        'Checkbox 7':   '/Yes' if lawful == 'citizen' else '/Off',   
        'Checkbox 8':   '/Yes' if lawful == 'alien' else '/Off',     
        'efield68_Text1': data.get('alien_number', ''),              
        'Text2':        full_name,       
        'Text7':        f"{data.get('city', '')}, {data.get('state', 'OK')}",  
        'Text8':        full_name,       
        'Text Field 3':  data.get('last_name', ''),
        'Text Field 1':  data.get('first_name', ''),
        'Text Field 4':  data.get('middle_initial', ''),
        'Text Field 2':  data.get('referral', ''),
        'Date Field 1':  data.get('dob', ''),
        'Text Field 5':  data.get('ssn', ''),
        'Text Field 6':  data.get('street', ''),
        'Text Field 11': data.get('apt', ''),
        'Text Field 7':  data.get('city', ''),
        'Text Field 8':  data.get('state', 'OK'),
        'Text Field 9':  data.get('zip', ''),
        'Text Field 10': data.get('phone', ''),
        'Text Field 12': data.get('email', ''),
        'Text Field 13': 'Certified Medication Aide (CMA)',  
        'Text Field 14': data.get('schedule', ''),
        'Text Field 15': data.get('emergency_name', ''),
        'Text Field 16': data.get('emergency_phone', ''),
        'Text Field 17': data.get('emergency_address', ''),
        'Text Field 18': data.get('emergency_relationship', ''),
        'Text Field 27': full_name,
        'Text Field 28': full_name,
        'Date Field 3':  data.get('dob', ''),
        'Number Field 1': data.get('phone', ''),
        'Text Field 29': data.get('email', ''),
        'Text4':         full_name,
        'Text1':         full_name,
        'Text Field 30': full_name,
        'Text Field 31': full_name,
        'Checkbox 4':    '/Yes' if data.get('background_check') == 'yes' else '/Off',
        'Checkbox 3':    '/Yes' if data.get('background_check') == 'no' else '/Off',
        'Text Field 32': full_name,
    }

    pdf_bytes = _fill_fields_interactive(input_path, field_values)
    
    # Embed signature if provided
    sig_data = data.get('signature_data', '')
    if sig_data:
        reader = PdfReader(io.BytesIO(pdf_bytes))
        writer = PdfWriter()
        writer.append(reader)
        _embed_signature(writer, 0, sig_data, x=300, y=55, width=200, height=45)
        output = io.BytesIO()
        writer.write(output)
        return output.getvalue()
    
    return pdf_bytes