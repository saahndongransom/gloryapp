import io
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from .models import Program

PROGRAMS = [
    {
        'slug': 'cna',
        'title': 'Certified Nursing Assistant (CNA)',
        'short': 'CNA',
        'icon': '🏥',
        'duration': '2–4 Weeks',
        'hours': '77 Clock Hours',
        'description': 'The CNA program prepares students with the knowledge and hands-on clinical skills needed to pass the Oklahoma CNA certification exam and become certified Long-Term Care Nurse Aides.',
        'schedules': ['Weekday Classes', 'Evening Classes', 'Weekend Classes', 'Online Hybrid'],
        'category': 'nursing',
    },
    {
        'slug': 'cma',
        'title': 'Certified Medication Aide (CMA)',
        'short': 'CMA',
        'icon': '💊',
        'duration': '2–3 Weeks',
        'hours': '50 Clock Hours',
        'description': 'The CMA program trains students to safely administer medications under licensed nurse supervision, preparing them for the Oklahoma CMA certification exam.',
        'schedules': ['Weekday Classes', 'Evening Classes', 'Weekend Classes', 'Online Hybrid'],
        'category': 'nursing',
    },
    {
        'slug': 'hha',
        'title': 'Home Health Aide (HHA)',
        'short': 'HHA',
        'icon': '🏠',
        'duration': '1 Week',
        'hours': '16 Clock Hours',
        'description': 'Designed for CNAs who want to expand their skills and work as Certified Home Health Aides in home health or residential care settings.',
        'schedules': ['Weekday Classes', 'Online Hybrid'],
        'category': 'nursing',
    },
    {
        'slug': 'bls-cpr',
        'title': 'Basic Life Support (BLS) / CPR',
        'short': 'BLS/CPR',
        'icon': '❤️',
        'duration': '1 Day',
        'hours': '6 Clock Hours',
        'description': 'AHA-certified BLS/CPR course for healthcare providers. Initial and renewal options available, led by AHA-trained certified instructors.',
        'schedules': ['Weekday Classes', 'Weekend Classes'],
        'category': 'life_support',
    },
    {
        'slug': 'phlebotomy',
        'title': 'Certified Phlebotomy Technician',
        'short': 'Phlebotomy',
        'icon': '🩸',
        'duration': '6–8 Weeks',
        'hours': '130 Clock Hours',
        'description': 'Graduates are eligible to sit for the NHA National Certification Exam and pursue entry-level phlebotomy positions in hospitals, clinics, and diagnostic labs.',
        'schedules': ['Weekday Classes', 'Evening Classes', 'Weekend Classes', 'Online Hybrid'],
        'category': 'allied_health',
    },
    {
        'slug': 'ekg',
        'title': 'Certified EKG Technician',
        'short': 'EKG',
        'icon': '📈',
        'duration': '6–8 Weeks',
        'hours': '130 Clock Hours',
        'description': 'Prepares students to sit for the NHA Certified EKG Technician (CET) Exam and become nationally certified electrocardiograph technicians.',
        'schedules': ['Weekday Classes', 'Evening Classes', 'Weekend Classes', 'Online Hybrid'],
        'category': 'allied_health',
    },
    {
        'slug': 'medical-assistant',
        'title': 'Certified Clinical Medical Assistant',
        'short': 'CCMA',
        'icon': '🩺',
        'duration': '10–12 Weeks',
        'hours': '360 Clock Hours',
        'description': 'A comprehensive program preparing students to become Nationally Certified Clinical Medical Assistants (CCMA) through the NHA certification exam.',
        'schedules': ['Weekday Classes', 'Evening Classes', 'Weekend Classes', 'Online Hybrid'],
        'category': 'allied_health',
    },
    {
        'slug': 'medical-billing-coding',
        'title': 'Medical Billing & Coding Specialist',
        'short': 'CBCS',
        'icon': '💻',
        'duration': '7–9 Weeks',
        'hours': '160 Clock Hours',
        'description': 'Prepares students for the CBCS National Certification Exam through NHA, CPC (AAPC), or CCA (AHIMA) — available fully online.',
        'schedules': ['Online Hybrid Flex', '100% Online Self-Paced'],
        'category': 'allied_health',
    },
]

TESTIMONIALS = [
    {
        'name': 'Sarah M.',
        'program': 'CNA Graduate',
        'text': 'Glory Nursing gave me the confidence and skills to launch my healthcare career. The instructors were professional and caring. I passed my CNA exam on the first try!',
    },
    {
        'name': 'James K.',
        'program': 'BLS/CPR Graduate',
        'text': 'Quick, efficient, and very professional. The BLS class was thorough and the instructor made everything easy to understand. Highly recommend Glory Nursing!',
    },
    {
        'name': 'Adaeze O.',
        'program': 'CMA Graduate',
        'text': 'From CNA to CMA — Glory Nursing supported me every step of the way. Small class sizes meant I got personal attention. Now I work full-time in a nursing home!',
    },
]


def home(request):
    from .models import Program, BlogPost, Event
    from django.utils import timezone
    db_programs = Program.objects.filter(is_active=True)
    if db_programs.exists():
        featured_programs = db_programs[:6]
        use_db = True
    else:
        featured_programs = PROGRAMS[:6]
        use_db = False

    latest_posts = BlogPost.objects.filter(is_published=True)[:3]
    upcoming_events = Event.objects.filter(
        is_active=True,
        event_date__gte=timezone.now().date()
    )[:3]

    # Resume where you left off (for logged-in students)
    continue_lesson = None
    continue_course = None
    if request.user.is_authenticated and not request.user.is_staff:
        from lms.models import LessonProgress, Enrollment
        last_progress = LessonProgress.objects.filter(
            student=request.user
        ).select_related('lesson__module__course').order_by('-updated_at').first()

        if last_progress:
            continue_lesson = last_progress.lesson
            continue_course = last_progress.lesson.module.course
        else:
            # No progress yet - point to first lesson of first enrollment
            enrollment = Enrollment.objects.filter(student=request.user).select_related('course').first()
            if enrollment:
                first_module = enrollment.course.modules.order_by('order').first()
                if first_module:
                    continue_lesson = first_module.lessons.order_by('order').first()
                    continue_course = enrollment.course

    return render(request, 'core/home.html', {
        'programs': featured_programs,
        'use_db': use_db,
        'testimonials': TESTIMONIALS,
        'latest_posts': latest_posts,
        'upcoming_events': upcoming_events,
        'continue_lesson': continue_lesson,
        'continue_course': continue_course,
        'page': 'home',
    })


def programs(request):
    from .models import Program
    db_programs = Program.objects.filter(is_active=True)
    if db_programs.exists():
        return render(request, 'core/programs.html', {
            'programs': db_programs,
            'use_db': True,
            'page': 'programs',
        })
    return render(request, 'core/programs.html', {
        'programs': PROGRAMS,
        'use_db': False,
        'page': 'programs',
    })


def program_detail(request, slug):
    from .models import Program
    from lms.models import Course, CourseReview
    from django.db.models import Avg

    # Get approved reviews matching this program code (e.g. "CNA", "CMA")
    program_code = slug.upper()
    reviews = CourseReview.objects.filter(
        is_approved=True,
        course__program=program_code
    ).select_related('student', 'course').order_by('-created_at')[:10]

    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] if reviews else None
    review_count = CourseReview.objects.filter(is_approved=True, course__program=program_code).count()

    db_program = Program.objects.filter(slug=slug, is_active=True).first()
    if db_program:
        return render(request, 'core/program_detail.html', {
            'program': db_program,
            'use_db': True,
            'page': 'programs',
            'reviews': reviews,
            'avg_rating': avg_rating,
            'review_count': review_count,
        })
    program = next((p for p in PROGRAMS if p['slug'] == slug), None)
    if not program:
        from django.http import Http404
        raise Http404
    return render(request, 'core/program_detail.html', {
        'program': program,
        'use_db': False,
        'page': 'programs',
        'reviews': reviews,
        'avg_rating': avg_rating,
        'review_count': review_count,
    })


def admissions(request):
    return render(request, 'core/admissions.html', {'page': 'admissions'})


def about(request):
    return render(request, 'core/about.html', {'page': 'about'})


def contact(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you! Your message has been received. We will contact you shortly.')
    return render(request, 'core/contact.html', {'page': 'contact'})


def apply(request):
    if request.method == 'POST':
        messages.success(request, 'Application submitted! Our admissions team will reach out within 1–2 business days.')
    return render(request, 'core/apply.html', {'page': 'apply'})



def admissions(request):
    programs = Program.objects.filter(is_active=True)

    return render(request, 'core/admissions.html', {
        'page': 'admissions',
        'programs': programs,
    })


def admissions_tuition(request):
    programs = Program.objects.filter(is_active=True)

    return render(request, 'core/admissions_tuition.html', {
        'page': 'admissions',
        'programs': programs,
    })
 
def admissions_financial_aid(request):
    """Financial Aid subpage."""
    return render(request, 'core/admissions_financial_aid.html', {
        'page': 'admissions',
    })
 
 
def admissions_requirements(request):
    """Requirements subpage."""
    return render(request, 'core/admissions_requirements.html', {
        'page': 'admissions',
    })
 
 
def admissions_faq(request):
    """FAQ subpage."""
    return render(request, 'core/admissions_faq.html', {
        'page': 'admissions',
    })
 
 

def about_mission(request):
    return render(request, 'core/about/mission.html', {'page': 'about', 'about_page': 'mission'})
 
 
def about_team(request):
    return render(request, 'core/about/team.html', {'page': 'about', 'about_page': 'team'})
 
 
def about_accreditations(request):
    return render(request, 'core/about/accreditations.html', {'page': 'about', 'about_page': 'accreditations'})
 
 
def about_careers(request):
    if request.method == 'POST':
        messages.success(request, 'Thank you for your interest! We will be in touch soon.')
    return render(request, 'core/about/careers.html', {'page': 'about', 'about_page': 'careers'})
 
 
def apply_cna(request):
    if request.method == 'POST':
        messages.success(request, '✅ CNA Application submitted! We will contact you within 1–2 business days. Please download and complete the required documents below.')
        return redirect('apply_cna')  # ← add this line
    return render(request, 'core/apply_cna.html', {'page': 'apply'})
 
from django.shortcuts import redirect  # add to top imports

def apply_cma(request):
    if request.method == 'POST':
        messages.success(request, '✅ CMA Application submitted! We will contact you within 1–2 business days. Please download and complete the required documents below.')
        return redirect('apply_cma')  # ← redirect to GET, prevents double-submit
    return render(request, 'core/apply_cma.html', {'page': 'apply'})








# ── Add these imports at the top of views.py ──────────────────────────────────
from django.http import HttpResponse
from .pdf_prefill import prefill_cna_pdf, prefill_cma_pdf


# ── Replace apply_cna with this ───────────────────────────────────────────────
def apply_cna(request):
    if request.method == 'POST':
        # Collect all form data into session so the download view can use it
        data = {
            'last_name':                request.POST.get('last_name', ''),
            'first_name':               request.POST.get('first_name', ''),
            'middle_initial':           request.POST.get('middle_initial', ''),
            'dob':                      request.POST.get('dob', ''),
            'ssn':                      request.POST.get('ssn', ''),
            'phone':                    request.POST.get('phone', ''),
            'email':                    request.POST.get('email', ''),
            'street':                   request.POST.get('street', ''),
            'apt':                      request.POST.get('apt', ''),
            'city':                     request.POST.get('city', ''),
            'state':                    request.POST.get('state', 'OK'),
            'zip':                      request.POST.get('zip', ''),
            'schedule':                 request.POST.get('schedule', ''),
            'referral':                 request.POST.get('referral', ''),
            'emergency_name':           request.POST.get('emergency_name', ''),
            'emergency_phone':          request.POST.get('emergency_phone', ''),
            'emergency_relationship':   request.POST.get('emergency_relationship', ''),
            'emergency_address':        request.POST.get('emergency_address', ''),
            'hs_name':                  request.POST.get('hs_name', ''),
            'hs_address':               request.POST.get('hs_address', ''),
            'hs_from':                  request.POST.get('hs_from', ''),
            'hs_to':                    request.POST.get('hs_to', ''),
            'hs_graduated':             request.POST.get('hs_graduated', ''),
            'hs_diploma':               request.POST.get('hs_diploma', ''),
            'college_name':             request.POST.get('college_name', ''),
            'college_address':          request.POST.get('college_address', ''),
            'college_from':             request.POST.get('college_from', ''),
            'college_to':               request.POST.get('college_to', ''),
            'college_graduated':        request.POST.get('college_graduated', ''),
            'college_degree':           request.POST.get('college_degree', ''),
            'background_check':         request.POST.get('background_check', ''),
            'lawful_presence':          request.POST.get('lawful_presence', ''),
            'alien_number':             request.POST.get('alien_number', ''),
            'photo_release':            request.POST.get('photo_release', ''),
            'notes':                    request.POST.get('notes', ''),
            'signature_data':           request.POST.get('signature_data', ''),
        }
        request.session['cna_application_data'] = data
        messages.success(request, '✅ CNA Application submitted! Your pre-filled documents are ready to download, sign, and return.')
        return redirect('apply_cna')
    return render(request, 'core/apply_cna.html', {'page': 'apply'})


def download_cna_pdf(request):
    """Serve the pre-filled CNA application PDF."""
    data = request.session.get('cna_application_data', {})
    pdf_bytes = prefill_cna_pdf(data)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    last = data.get('last_name', 'Application')
    response['Content-Disposition'] = f'attachment; filename="CNA_Application_{last}.pdf"'
    return response


# ── Replace apply_cma with this ───────────────────────────────────────────────
def apply_cma(request):
    if request.method == 'POST':
        data = {
            'last_name':                request.POST.get('last_name', ''),
            'first_name':               request.POST.get('first_name', ''),
            'middle_initial':           request.POST.get('middle_initial', ''),
            'dob':                      request.POST.get('dob', ''),
            'ssn':                      request.POST.get('ssn', ''),
            'phone':                    request.POST.get('phone', ''),
            'email':                    request.POST.get('email', ''),
            'street':                   request.POST.get('street', ''),
            'apt':                      request.POST.get('apt', ''),
            'city':                     request.POST.get('city', ''),
            'state':                    request.POST.get('state', 'OK'),
            'zip':                      request.POST.get('zip', ''),
            'cna_cert_number':          request.POST.get('cna_cert_number', ''),
            'cna_cert_expiry':          request.POST.get('cna_cert_expiry', ''),
            'cna_months_experience':    request.POST.get('cna_months_experience', ''),
            'cna_employer':             request.POST.get('cna_employer', ''),
            'schedule':                 request.POST.get('schedule', ''),
            'referral':                 request.POST.get('referral', ''),
            'emergency_name':           request.POST.get('emergency_name', ''),
            'emergency_phone':          request.POST.get('emergency_phone', ''),
            'emergency_relationship':   request.POST.get('emergency_relationship', ''),
            'emergency_address':        request.POST.get('emergency_address', ''),
            'lawful_presence':          request.POST.get('lawful_presence', ''),
            'alien_number':             request.POST.get('alien_number', ''),
            'background_check':         request.POST.get('background_check', 'no'),
            'photo_release':            request.POST.get('photo_release', ''),
            'notes':                    request.POST.get('notes', ''),
            'signature_data':           request.POST.get('signature_data', ''),
        }
        request.session['cma_application_data'] = data
        messages.success(request, '✅ CMA Application submitted! Your pre-filled documents are ready to download, sign, and return.')
        return redirect('apply_cma')
    return render(request, 'core/apply_cma.html', {'page': 'apply'})


def download_cma_pdf(request):
    """Serve the pre-filled CMA application PDF."""
    data = request.session.get('cma_application_data', {})
    pdf_bytes = prefill_cma_pdf(data)
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    last = data.get('last_name', 'Application')
    response['Content-Disposition'] = f'attachment; filename="CMA_Application_{last}.pdf"'
    return response

import json
import base64
from django.views.decorators.csrf import csrf_exempt

def _get_pdf_page_count(pdf_path):
    from pypdf import PdfReader
    return len(PdfReader(pdf_path).pages)

def _render_page_as_base64(pdf_path, page_num, dpi=120):
    from pdf2image import convert_from_path
    imgs = convert_from_path(pdf_path, dpi=dpi, first_page=page_num, last_page=page_num)
    buf = io.BytesIO()
    imgs[0].save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode(), imgs[0].size

def fill_pdf_cna(request):
    import os
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', 'CNA_app.pdf')
    from pypdf import PdfReader
    page_count = len(PdfReader(pdf_path).pages)
    return render(request, 'core/fill_pdf.html', {
        'pdf_name': 'CNA',
        'page_count': page_count,
        'render_url': '/apply/cna/render-page/',
        'save_url': '/apply/cna/save/',
        'back_url': '/apply/cna/',
        'enroll_id': 1,
    })

def fill_pdf_cma(request):
    import os
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', 'CMA_app.pdf')
    from pypdf import PdfReader
    page_count = len(PdfReader(pdf_path).pages)
    return render(request, 'core/fill_pdf.html', {
        'pdf_name': 'CMA',
        'page_count': page_count,
        'render_url': '/apply/cma/render-page/',
        'save_url': '/apply/cma/save/',
        'back_url': '/apply/cma/',
        'enroll_id': 2,
    })

def render_pdf_page(request):
    import os
    page_num = int(request.GET.get('page', 1))
    dpi = int(request.GET.get('dpi', 120))
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', 'CNA_app.pdf')
    img_b64, size = _render_page_as_base64(pdf_path, page_num, dpi)
    return JsonResponse({'image': img_b64, 'width': size[0], 'height': size[1]})

def render_pdf_page_cma(request):
    import os
    page_num = int(request.GET.get('page', 1))
    dpi = int(request.GET.get('dpi', 120))
    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', 'CMA_app.pdf')
    img_b64, size = _render_page_as_base64(pdf_path, page_num, dpi)
    return JsonResponse({'image': img_b64, 'width': size[0], 'height': size[1]})

@csrf_exempt
def save_filled_pdf(request):
    return _save_pdf_with_annotations(request, 'CNA_app.pdf', 'CNA_Application_Filled.pdf')

@csrf_exempt
def save_filled_pdf_cma(request):
    return _save_pdf_with_annotations(request, 'CMA_app.pdf', 'CMA_Application_Filled.pdf')

def _save_pdf_with_annotations(request, pdf_filename, output_filename):
    import os
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.utils import ImageReader

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    data = json.loads(request.body)
    annotations = data.get('annotations', {})  # {page_num: [{type, x, y, text/imgData, fontSize, color}]}
    render_dpi = data.get('dpi', 120)

    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', pdf_filename)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    # PDF points per pixel at render_dpi
    scale = 72.0 / render_dpi

    for page_str, annots in annotations.items():
        page_idx = int(page_str) - 1
        if page_idx < 0 or page_idx >= len(writer.pages):
            continue

        page = writer.pages[page_idx]
        page_height = float(reader.pages[page_idx].mediabox[3])
        page_width = float(reader.pages[page_idx].mediabox[2])

        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(page_width, page_height))

        for annot in annots:
            # Convert canvas pixel coords to PDF points
            # Canvas: origin top-left, PDF: origin bottom-left
            pdf_x = annot['x'] * scale
            pdf_y = page_height - (annot['y'] * scale)

            if annot['type'] == 'text':
                font_size = annot.get('fontSize', 11)
                color = annot.get('color', '#000000')
                # Parse hex color
                r = int(color[1:3], 16) / 255
                g = int(color[3:5], 16) / 255
                b = int(color[5:7], 16) / 255
                c.setFillColorRGB(r, g, b)
                c.setFont("Helvetica", font_size)
                c.drawString(pdf_x, pdf_y - font_size, annot.get('text', ''))

            elif annot['type'] == 'signature':
                img_data = annot.get('imgData', '')
                if img_data and img_data.startswith('data:image'):
                    header, b64 = img_data.split(',', 1)
                    img_bytes = base64.b64decode(b64)
                    img_buf = io.BytesIO(img_bytes)
                    img_reader = ImageReader(img_buf)
                    w = annot.get('width', 150) * scale
                    h = annot.get('height', 40) * scale
                    c.drawImage(img_reader, pdf_x, pdf_y - h, width=w, height=h, mask='auto')

            elif annot['type'] == 'checkmark':
                c.setFont("Helvetica-Bold", 14)
                c.setFillColorRGB(0, 0, 0)
                c.drawString(pdf_x, pdf_y - 14, '✓')

        c.save()
        overlay_buf.seek(0)
        overlay_reader = PdfReader(overlay_buf)
        writer.pages[page_idx].merge_page(overlay_reader.pages[0])

    output_buf = io.BytesIO()
    writer.write(output_buf)
    output_buf.seek(0)
    pdf_bytes = output_buf.read()

    # Email the filled PDF to Glory Nursing
    action = data.get('action', 'download')  # 'submit' or 'download'

    if action == 'submit':
        try:
            from django.core.mail import EmailMessage
            student_email = data.get('student_email', '')
            program = data.get('program', 'Program')
            msg = EmailMessage(
                subject=f'New {program} Application Received',
                body=f'''A student has submitted their {program} application through the Glory Nursing website.

Student Email: {student_email if student_email else "Not provided"}

The completed application is attached.

Glory Nursing Online Portal''',
                from_email=None,
                to=['glorynursing@yahoo.com'],
            )
            msg.attach(output_filename, pdf_bytes, 'application/pdf')
            msg.send()

            # Also send confirmation to student
            if student_email:
                EmailMessage(
                    subject=f'Your Glory Nursing {program} Application Received',
                    body=f'''Thank you for submitting your {program} application to Glory Nursing!

We have received your completed application. Our admissions team will review it and contact you within 1-2 business days.

Next step: Complete your enrollment payment at glorynursing.com

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120''',
                    from_email=None,
                    to=[student_email],
                ).send()

        except Exception as e:
            print(f"Email error: {e}")

        return JsonResponse({'success': True, 'message': 'Application submitted successfully!'})

    # Default: download
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{output_filename}"'
    return response


def glory_nursing_bot(msg):
    m = msg.lower().strip()
    if any(w in m for w in ['hi','hello','hey','howdy','good morning']):
        return "Hello! Welcome to Glory Nursing! I can help with programs, costs, schedules, and enrollment. What would you like to know?"
    if any(w in m for w in ['cna','nursing assistant']):
        if any(w in m for w in ['cost','price','how much','fee','tuition']):
            return "The CNA program costs $299."
        if any(w in m for w in ['long','duration','weeks','hours']):
            return "The CNA program is 2-4 weeks with 77 clock hours. We offer Weekday, Evening, Weekend, and Online Hybrid schedules."
        if any(w in m for w in ['require','need','prerequisite','qualify']):
            return "CNA Requirements: Age 18+, High school diploma or GED, Valid ID, Social Security card, Background check, Immunization records."
        return "Our CNA program is $299 and takes 2-4 weeks (77 hours). Flexible schedules available. Want to know about requirements or how to enroll?"
    if any(w in m for w in ['cma','medication aide']):
        if any(w in m for w in ['cost','price','how much','fee','tuition']):
            return "The CMA program costs $399."
        if any(w in m for w in ['require','need','prerequisite','qualify']):
            return "CMA Prerequisites: Active Oklahoma CNA certification, minimum 6 months CNA experience, no abuse notations, Age 18+, High school diploma or GED."
        return "Our CMA program is $399 and takes 2-3 weeks (50 hours). You must be a certified CNA with 6 months experience."
    if any(w in m for w in ['program','course','offer','available']):
        return "Glory Nursing offers: CNA ($299, 2-4 weeks), CMA ($399, 2-3 weeks), HHA, BLS/CPR, Phlebotomy, EKG, Medical Assistant, Medical Billing. Call (405) 968-5004 for other program pricing."
    if any(w in m for w in ['enroll','apply','sign up','register']):
        return "To enroll: Visit glorynursing.com/apply/cna/ for CNA or /apply/cma/ for CMA. Fill and sign your application online, pay securely, and get instant LMS access by email!"
    if any(w in m for w in ['schedule','class','timing','weekend','evening']):
        return "We offer Weekday, Evening, Weekend, and Online Hybrid schedules. Call (405) 968-5004 for the next available start date."
    if any(w in m for w in ['location','address','where','located']):
        return "We are at 12032 N Pennsylvania Ave, Oklahoma City, OK 73120. Hours: Mon-Fri 8AM-6PM, Sat 9AM-2PM."
    if any(w in m for w in ['contact','phone','call','email','reach']):
        return "Contact us: Phone (405) 968-5004, Email glorynursing@yahoo.com, Hours Mon-Fri 8AM-6PM, Sat 9AM-2PM."
    if any(w in m for w in ['pay','payment','card','credit','cost','price','how much']):
        return "We accept credit/debit card payments online at enrollment. CNA is $299 and CMA is $399. We have a No Refund Policy."
    if any(w in m for w in ['background','criminal','check']):
        return "A background check is required before clinical placement. Glory Nursing can conduct it for $30 (optional), or you can provide your own."
    if any(w in m for w in ['thank','thanks','appreciate']):
        return "You are welcome! Call us at (405) 968-5004 anytime. We would love to help start your healthcare career!"
    return "I can help with program info, costs, schedules, and enrollment. Call (405) 968-5004 or email glorynursing@yahoo.com for specific questions."

def chatbot_response(request):
    """AI chatbot powered by Claude API."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    data = json.loads(request.body)
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return JsonResponse({'error': 'No message'}, status=400)

    import urllib.request
    import json as json_lib

    system_prompt = """You are a helpful admissions assistant for Glory Nursing Healthcare Training School in Oklahoma City, Oklahoma.

SCHOOL INFORMATION:
- Name: Glory Nursing Healthcare Training School
- Address: 12032 N Pennsylvania Ave, Oklahoma City, OK 73120
- Phone: (405) 968-5004
- Email: glorynursing@yahoo.com
- Hours: Mon-Fri 8AM-6PM, Sat 9AM-2PM

PROGRAMS:
1. CNA (Certified Nursing Assistant) - $299
   - Duration: 2-4 weeks, 77 clock hours
   - Requirements: 18+ years, high school diploma/GED, valid ID, SSN, background check, immunization records
   - Schedules: Weekday, Evening, Weekend, Online Hybrid

2. CMA (Certified Medication Aide) - $399
   - Duration: 2-3 weeks, 50 clock hours
   - Prerequisites: Active Oklahoma CNA certification, minimum 6 months CNA experience, no abuse notations
   - Requirements: 18+, high school diploma/GED
   - Schedules: Weekday, Evening, Weekend, Online Hybrid

3. HHA (Home Health Aide) - contact for price
   - Duration: 1 week, 16 clock hours
   - For CNAs wanting to expand skills

4. BLS/CPR - contact for price
   - Duration: 1 day, 6 clock hours
   - AHA-certified, initial and renewal

5. Phlebotomy - contact for price
   - Duration: 6-8 weeks, 130 clock hours

6. EKG Technician - contact for price
   - Duration: 6-8 weeks, 130 clock hours

7. Medical Assistant (CCMA) - contact for price
   - Duration: 10-12 weeks, 360 clock hours

8. Medical Billing & Coding - contact for price
   - Duration: 7-9 weeks, 160 clock hours, available fully online

ENROLLMENT PROCESS:
1. Fill and sign the application online at glorynursing.com/apply/cna/ or /apply/cma/
2. Submit the application digitally
3. Pay online securely via credit/debit card
4. Receive LMS login credentials by email instantly
5. Start learning immediately

PAYMENT: Secure online payment via credit/debit card. No refunds policy.

BACKGROUND CHECK: Required before clinical placement. Glory Nursing can conduct it for $30 (optional).

LMS: Students get access to online learning portal with lessons, quizzes, and certificates.

INSTRUCTIONS:
- Be friendly, helpful, and professional
- Answer questions about programs, costs, schedules, requirements
- For questions you cannot answer, direct them to call (405) 968-5004 or email glorynursing@yahoo.com
- Keep responses concise and helpful
- Encourage enrollment when appropriate
- Do not make up information not provided above"""

    messages = []
    for msg in history[-10:]:  # Keep last 10 messages for context
        messages.append({'role': msg['role'], 'content': msg['content']})
    messages.append({'role': 'user', 'content': user_message})

    payload = json_lib.dumps({
        'model': 'claude-sonnet-4-20250514',
        'max_tokens': 500,
        'system': system_prompt,
        'messages': messages
    }).encode()

    try:
        import os
        # Use rule-based bot
        reply = glory_nursing_bot(user_message)
        return JsonResponse({'reply': reply})

        # Try using requests if available
        try:
            import requests as req_lib
            resp = req_lib.post(
                'https://api.anthropic.com/v1/messages',
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                },
                json={
                    'model': 'claude-sonnet-4-5',
                    'max_tokens': 500,
                    'system': system_prompt,
                    'messages': messages
                },
                timeout=30
            )
            result = resp.json()
            reply = result['content'][0]['text']
        except ImportError:
            req = urllib.request.Request(
                'https://api.anthropic.com/v1/messages',
                data=payload,
                headers={
                    'Content-Type': 'application/json',
                    'x-api-key': api_key,
                    'anthropic-version': '2023-06-01',
                },
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                result = json_lib.loads(resp.read())
                reply = result['content'][0]['text']

        return JsonResponse({'reply': reply})
    except Exception as e:
        import traceback
        print(f"Chatbot error: {e}")
        print(traceback.format_exc())
        # Try to get response body
        try:
            print(f"Response body: {e.read()}")
        except:
            pass
        return JsonResponse({'reply': "I'm sorry, I'm having trouble connecting right now. Please call us at (405) 968-5004 or email glorynursing@yahoo.com for assistance."})


def privacy_policy(request):
    return render(request, 'core/legal/privacy.html', {'page': 'legal'})

def terms_of_service(request):
    return render(request, 'core/legal/terms.html', {'page': 'legal'})
