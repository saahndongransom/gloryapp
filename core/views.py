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
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        phone = request.POST.get('phone', '')
        subject = request.POST.get('subject', 'Contact Form Message')
        message = request.POST.get('message', '')
        try:
            from django.core.mail import send_mail
            send_mail(
                subject=f'Contact Form: {subject} — {name}',
                message=f"""New message from the Glory Nursing contact form.

Name: {name}
Email: {email}
Phone: {phone}
Subject: {subject}

Message:
{message}

Glory Nursing Online Portal""",
                from_email=None,
                recipient_list=['glorynursing@yahoo.com'],
                fail_silently=True,
            )
        except Exception:
            pass
        messages.success(request, 'Thank you! Your message has been received. We will contact you shortly.')
    return render(request, 'core/contact.html', {'page': 'contact'})


def apply(request):
    if request.method == 'POST':
        messages.success(request, 'Application submitted! Our admissions team will reach out within 1–2 business days.')
    programs = Program.objects.filter(is_active=True)
    return render(request, 'core/apply.html', {'page': 'apply', 'programs': programs})



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
 
 









# ── Add these imports at the top of views.py ──────────────────────────────────
from django.http import HttpResponse
from .pdf_prefill import prefill_cna_pdf, prefill_cma_pdf


# ── Replace apply_cna with this ───────────────────────────────────────────────
def apply_cna(request):
    from lms.models import Course as LMSCourse
    from core.models import Program as CoreProgram
    program_slug = request.GET.get('program', '') or request.session.get('apply_program_slug', '')
    if request.GET.get('program'):
        request.session['apply_program_slug'] = request.GET.get('program')
    selected_program = None
    program_course = None
    cna_slugs = ['cna', 'cna-day-class', 'cna-evening-class', 'weekend-certified-nursing-assistant-class', 'onlinehybrid-certified-nursing-assistant']
    if program_slug and program_slug not in cna_slugs:
        selected_program = CoreProgram.objects.filter(slug=program_slug, is_active=True).first()
        if selected_program and selected_program.course:
            program_course = selected_program.course
    if program_course:
        request.session['apply_enroll_id'] = program_course.id
    elif not program_slug or program_slug in cna_slugs:
        request.session.pop('apply_enroll_id', None)
    cna_courses = LMSCourse.objects.filter(program__icontains='CNA', is_published=True).exclude(program__icontains='HHA').order_by('price')
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
    return render(request, 'core/apply_cna.html', {'page': 'apply', 'cna_courses': cna_courses, 'selected_program': selected_program, 'program_course': program_course})


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
    from lms.models import Course as LMSCourse
    cma_courses = LMSCourse.objects.filter(program__icontains='CMA', is_published=True).order_by('price')
    return render(request, 'core/apply_cma.html', {'page': 'apply', 'cma_courses': cma_courses})


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
    enroll_id = request.session.get('apply_enroll_id', 1)
    program_slug = request.session.get('apply_program_slug', '')
    back_url = f'/apply/cna/?program={program_slug}' if program_slug else '/apply/cna/'
    return render(request, 'core/fill_pdf.html', {
        'pdf_name': 'CNA',
        'page_count': page_count,
        'render_url': '/apply/cna/render-page/',
        'save_url': '/apply/cna/save/',
        'back_url': back_url,
        'enroll_id': enroll_id,
    })


def fill_form_cna(request):
    from lms.models import Course as LMSCourse
    enroll_id = request.session.get('apply_enroll_id', 1)
    program_slug = request.session.get('apply_program_slug', '')
    back_url = f'/apply/cna/?program={program_slug}' if program_slug else '/apply/cna/'
    cna_courses = LMSCourse.objects.filter(program__icontains='CNA', is_published=True).exclude(program__icontains='HHA').order_by('price')
    return render(request, 'core/fill_form_cna.html', {
        'enroll_id': enroll_id,
        'back_url': back_url,
        'cna_courses': cna_courses,
    })


@csrf_exempt
def submit_form_cna(request):
    import json
    import io
    import base64
    from django.http import JsonResponse
    from django.core.mail import EmailMessage
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    print("=== CMA FORM DATA RECEIVED ===")
    for k, v in data.items():
        if not str(v).startswith('data:image'):
            print(f"{k}: {v}")
    print("=== END ===")

    student_email = data.get('student_email', '').strip()
    if not student_email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    def get(key, default=''):
        v = data.get(key, default)
        return v if v else default

    def draw_sig(c, key, x, y, w, h):
        img_data = data.get(key, '')
        if img_data and img_data.startswith('data:image'):
            try:
                header, b64 = img_data.split(',', 1)
                img_bytes = base64.b64decode(b64)
                img_reader = ImageReader(io.BytesIO(img_bytes))
                c.drawImage(img_reader, x, y, width=w, height=h, mask='auto')
            except Exception:
                pass

    import os as _os
    full_name = f"{get('first_name')} {get('last_name')}".strip() or 'Applicant'

    buf = io.BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    width, height = letter

    logo_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'static', 'core', 'images', 'glorylogo.png')

    def header(title):
        c.setFillColor(HexColor('#ffffff'))
        c.rect(0, height - 75, width, 75, fill=1, stroke=0)
        try:
            if _os.path.exists(logo_path):
                c.drawImage(logo_path, 40, height - 68, width=160, height=58, mask='auto', preserveAspectRatio=True)
        except Exception:
            pass
        c.setFillColor(HexColor('#0f172a'))
        c.setFont('Helvetica', 9)
        c.drawRightString(width - 40, height - 22, '12032 N Pennsylvania Ave')
        c.drawRightString(width - 40, height - 34, 'Oklahoma City, OK 73120')
        c.drawRightString(width - 40, height - 46, 'Call/text: 405-968-5004')
        c.drawRightString(width - 40, height - 58, 'Email: glorynursing@yahoo.com')
        c.setStrokeColor(HexColor('#1a56db'))
        c.setLineWidth(2)
        c.line(40, height - 78, width - 40, height - 78)
        c.setFillColor(HexColor('#0f172a'))
        c.setFont('Helvetica-Bold', 14)
        c.drawString(40, height - 100, title)
        c.setStrokeColor(HexColor('#e2e8f0'))
        c.setLineWidth(1)
        c.line(40, height - 107, width - 40, height - 107)

    def field_line(label, value, x, y, label_w=140):
        c.setFont('Helvetica-Bold', 9)
        c.setFillColor(HexColor('#475569'))
        c.drawString(x, y, label)
        c.setFont('Helvetica', 10)
        c.setFillColor(HexColor('#0f172a'))
        c.drawString(x + label_w, y, str(value))

    def wrap_text(text, font='Helvetica', size=9.5, max_width=520):
        from reportlab.pdfbase.pdfmetrics import stringWidth
        lines = []
        for paragraph in text.split('\n'):
            if not paragraph.strip():
                lines.append('')
                continue
            words = paragraph.split(' ')
            cur = ''
            for word in words:
                test = (cur + ' ' + word).strip()
                if stringWidth(test, font, size) <= max_width:
                    cur = test
                else:
                    if cur:
                        lines.append(cur)
                    cur = word
            if cur:
                lines.append(cur)
        return lines

    def draw_paragraph(text, x, y, max_width=520, size=9.5, line_height=13):
        lines = wrap_text(text, size=size, max_width=max_width)
        c.setFont('Helvetica', size)
        c.setFillColor(HexColor('#334155'))
        for line in lines:
            if y < 60:
                c.showPage()
                y = height - 50
                c.setFont('Helvetica', size)
                c.setFillColor(HexColor('#334155'))
            c.drawString(x, y, line)
            y -= line_height
        return y

    # PAGE 1 — Application Information
    header('CNA Enrollment Application')
    y = height - 130
    field_line('Last Name:', get('last_name'), 40, y); field_line('First Name:', get('first_name'), 310, y)
    y -= 22
    field_line('M.I.:', get('middle_initial'), 40, y); field_line('Date of Birth:', get('dob'), 310, y)
    y -= 22
    field_line('SSN:', get('ssn'), 40, y); field_line('Phone:', get('phone'), 310, y)
    y -= 22
    field_line('Street Address:', get('street'), 40, y)
    y -= 22
    field_line('City:', get('city'), 40, y); field_line('State:', get('state'), 310, y)
    y -= 22
    field_line('Zip:', get('zip'), 40, y); field_line('How heard:', get('how_heard'), 310, y)
    y -= 22
    field_line('Course Applied For:', get('course_applied'), 40, y, label_w=150)
    y -= 35

    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(HexColor('#1a56db'))
    c.drawString(40, y, 'Emergency Contact')
    y -= 20
    field_line('Contact Name:', get('emergency_name'), 40, y); field_line('Phone:', get('emergency_phone'), 310, y)
    y -= 22
    field_line('Address:', get('emergency_address'), 40, y); field_line('Relationship:', get('emergency_relationship'), 310, y)
    y -= 35

    c.setFont('Helvetica-Bold', 12)
    c.setFillColor(HexColor('#1a56db'))
    c.drawString(40, y, 'Education')
    y -= 20
    field_line('High School:', get('hs_name'), 40, y); field_line('Address:', get('hs_address'), 310, y)
    y -= 22
    field_line('Years:', f"{get('hs_from')} - {get('hs_to')}", 40, y)
    field_line('Graduated:', get('hs_graduated'), 310, y)
    y -= 22
    field_line('Diploma/GED:', get('hs_diploma'), 40, y)
    y -= 30
    field_line('College/Other:', get('college_name'), 40, y); field_line('Address:', get('college_address'), 310, y)
    y -= 22
    field_line('Years:', f"{get('college_from')} - {get('college_to')}", 40, y)
    field_line('Graduated:', get('college_graduated'), 310, y)
    y -= 22
    field_line('Degree:', get('degree'), 40, y)

    c.showPage()

    # PAGE 2 — Affidavit of Lawful Presence
    header('Affidavit of Lawful Presence')
    y = height - 130
    presence = 'United States Citizen' if get('lawful_presence') == 'us_citizen' else 'Qualified Alien Lawfully Present'
    field_line('Status:', presence, 40, y, label_w=110)
    y -= 22
    if get('alien_number'):
        field_line('Alien/Admission #:', get('alien_number'), 40, y, label_w=150)
    c.showPage()

    # PAGE 3 — Clinical Tasks Policy
    header('Authorized Tasks at Clinical Sites')
    y = height - 125
    clinical_text = '''As a student enrolled in the Certified Nursing Assistant (CNA) program, your education and safety, as well as the safety of patients, are of utmost importance. Therefore, students are only permitted to perform tasks and procedures at clinical sites that have been explicitly taught and practiced during classroom and lab training at Glory Nursing CNA School.

Important Guidelines

1. No Unapproved Tasks: Under no circumstances should you attempt or perform any clinical task or procedure that has not been covered in your coursework. This includes tasks that you may observe staff or other healthcare professionals performing. If you are asked to perform such tasks, respectfully inform the staff that it is outside your current scope of training.

2. Supervised Tasks: All tasks performed at the clinical site must be done under the supervision of a qualified preceptor. This ensures both the correct application of skills and adherence to patient safety standards.

3. Ask for Clarification: If you are ever unsure whether a task is within your scope of training, do not hesitate to ask your clinical instructor for clarification. It is better to seek confirmation than to risk patient safety or your own performance.

4. Student Responsibility: Students are expected to always demonstrate professionalism and ethical responsibility. Engaging in unauthorized tasks could result in disciplinary action and may impact your standing in the program.

Consequences of Non-Compliance

Any student found performing unauthorized tasks will be subject to the following disciplinary actions:
- Immediate suspension from the clinical site
- Review of the incident by school administration
- Possible removal from the CNA program

Commitment to Safety and Learning

The clinical experience is designed to complement your education and provide a safe learning environment for practical application. Adhering to the tasks you have been taught ensures that you develop skills progressively and in a manner that protects the well-being of all involved.

Please remember that patient safety, as well as your professional integrity, depend on your adherence to these guidelines.'''
    y = draw_paragraph(clinical_text, 40, y)
    y -= 20
    if y < 110:
        c.showPage()
        header('Authorized Tasks at Clinical Sites - Acknowledgment')
        y = height - 130
    c.setFont('Helvetica-Bold', 11)
    c.setFillColor(HexColor('#1a56db'))
    c.drawString(40, y, 'Acknowledgment of Policy')
    y -= 18
    field_line('Agreement:', 'I have read and agree to follow this policy.' if get('agree_clinical_tasks') else 'Not agreed', 40, y, label_w=110)
    y -= 50
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Signature:')
    draw_sig(c, 'sig_clinical_tasks', 40, y - 60, 220, 50)
    c.showPage()

    # PAGE 4 — Media Release
    header('Photograph and Media Release Waiver')
    y = height - 125
    field_line('Student Name:', full_name_placeholder if False else f"{get('first_name')} {get('last_name')}", 40, y, label_w=110)
    y -= 18
    field_line('Date of Birth:', get('dob'), 40, y, label_w=110)
    y -= 18
    field_line('Phone Number:', get('phone'), 40, y, label_w=110)
    y -= 18
    field_line('Email:', student_email, 40, y, label_w=110)
    y -= 25
    media_text = '''As a student at Glory Nursing CNA School, I understand that photographs, videos, and other forms of media may be taken during my time at the school for educational, promotional, and marketing purposes. These images may be used in various formats including, but not limited to: websites and social media platforms (e.g., Facebook, Instagram), print and digital advertising materials, newsletters, brochures, and other promotional materials, and training materials and educational presentations.

I Consent: I, the undersigned, grant permission to Glory Nursing CNA School to use photographs, video recordings, and/or other media that may include my image, voice, or likeness for the purposes outlined above. I understand that these images may be used without compensation and will remain the property of Glory Nursing CNA School.

I Decline: I, the undersigned, do not grant permission to Glory Nursing CNA School to use photographs, video recordings, and/or other media that may include my image, voice, or likeness. I understand that if I decline, every effort will be made to exclude me from media content, and my decision will not affect my participation in school activities.

I understand that:
1. My participation is voluntary, and I may revoke or modify this consent at any time by providing written notice to the school.
2. My personal information (e.g., name, contact details) will not be disclosed in the use of such materials unless explicitly permitted by me.'''
    y = draw_paragraph(media_text, 40, y)
    y -= 15
    if y < 110:
        c.showPage()
        header('Photograph and Media Release Waiver (continued)')
        y = height - 130
    consent_label = 'I Consent' if get('media_consent') == 'Yes' else ('I Decline' if get('media_consent') == 'No' else 'Not specified')
    field_line('Selection:', consent_label, 40, y, label_w=110)
    y -= 50
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Signature:')
    draw_sig(c, 'sig_media_release', 40, y - 60, 220, 50)
    c.showPage()

    # PAGE 5 — Background Check
    header('Background Check Requirement')
    y = height - 125
    bg_text = '''All students enrolled in the Certified Nursing Assistant (CNA) program at Glory Nursing CNA School are required to undergo a criminal background check before participating in clinical training or graduating from the program. This background check is mandated to ensure compliance with healthcare facility policies and state regulations.

By signing this waiver, you acknowledge and agree to the following:

1. Clean Background Requirement: In order to qualify for clinical placement and graduation, students must pass a criminal background check per state and facility requirements.

5. Background Check Process:
- The background check will be conducted by an authorized third-party agency. You will be responsible for submitting all necessary information and payment for the background check as part of the enrollment process.
- You will be notified of the results, and any disqualifying findings may result in removal from the program.

Acknowledgment of Policy: By signing below, you acknowledge that you understand and agree to the terms of this waiver, including the requirement for a clean background check and the lack of any guarantee of employment after program completion.'''
    y = draw_paragraph(bg_text, 40, y)
    y -= 15
    if y < 110:
        c.showPage()
        header('Background Check Requirement (continued)')
        y = height - 130
    bg = 'Yes - Glory Nursing will conduct my background check' if get('background_check') == 'glory_conducts' else 'No - I will provide my own background check'
    field_line('Preference:', bg, 40, y, label_w=110)
    y -= 50
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Signature:')
    draw_sig(c, 'sig_background_check', 40, y - 60, 220, 50)
    c.showPage()

    # PAGE 6 — Grievance & Refund Policy
    header('Grievance & Refund Policy')
    y = height - 125
    refund_text = '''At Glory Nursing, we are committed to fostering a supportive and fair learning environment. Students who have concerns or complaints related to any aspect of their experience at the school are encouraged to follow the grievance process.

No Refund Policy

1. Tuition and Fees: All payments made for tuition, registration fees, materials, and any other associated costs are non-refundable.

2. Course Withdrawals or Cancellations: Payments will not be refunded under the following circumstances: voluntary withdrawal by the student, dismissal for academic or behavioral reasons, or schedule changes or conflicts. In the event of medical or serious family reasons, Glory Nursing will work with students to make up lost classes by joining the next available classes.

3. Non-Attendance: Failure to attend classes does not entitle the student to a refund. Students are encouraged to assess their availability before enrolling.

4. Payment Plans: Students enrolled in a payment plan are required to complete all scheduled payments, regardless of course completion or attendance.

5. Course Cancellations by Glory Nursing: If a course is canceled, students will be offered the option to reschedule or apply their payments toward another program. No refunds will be issued.

6. Disputes: All disputes regarding payments or the no-refund policy must be submitted in writing to the school administration within 30 days of the payment in question.

7. Acknowledgment: By enrolling in Glory Nursing CNA School, you acknowledge and agree to the terms of this No Refund Policy. Your enrollment and payment of tuition or fees serve as confirmation of your understanding and acceptance of this policy.'''
    y = draw_paragraph(refund_text, 40, y)
    y -= 15
    if y < 110:
        c.showPage()
        header('Grievance & Refund Policy (continued)')
        y = height - 130
    field_line('Agreement:', 'I have read and agree to the No Refund Policy.' if get('agree_refund_policy') else 'Not agreed', 40, y, label_w=110)
    y -= 50
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Signature:')
    draw_sig(c, 'sig_refund_policy', 40, y - 60, 220, 50)
    c.showPage()

    # PAGE 7 — NAR Rules
    header('OSDH / Nurse Aide Registry Rules - Acknowledgment')
    y = height - 130
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Signature:')
    draw_sig(c, 'sig_nar_rules', 40, y - 60, 220, 50)
    c.showPage()

    # PAGE 8 — Final Signature
    header('Final Acknowledgment & Signature')
    y = height - 130
    c.setFont('Helvetica', 10)
    c.setFillColor(HexColor('#334155'))
    c.drawString(40, y, 'I confirm that all information provided in this application is true and accurate,')
    y -= 14
    c.drawString(40, y, 'and that I agree to all policies outlined in this application.')
    y -= 50
    c.setFont('Helvetica-Bold', 9)
    c.setFillColor(HexColor('#475569'))
    c.drawString(40, y, 'Final Signature:')
    draw_sig(c, 'sig_final', 40, y - 60, 220, 50)
    field_line('Date:', get('signature_date'), 320, y, label_w=50)
    c.showPage()

    c.save()
    buf.seek(0)

    # Merge in original state-issued pages (Affidavit + Nurse Aide Registry) with signature overlay
    from pypdf import PdfReader, PdfWriter
    import os as _os

    generated_reader = PdfReader(buf)
    original_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'static', 'core', 'documents', 'CNA_app.pdf')
    original_reader = PdfReader(original_path)

    writer = PdfWriter()

    # Page 1 of generated = our Enrollment Application
    writer.add_page(generated_reader.pages[0])

    # State page: Affidavit of Lawful Presence (original page index 1) — overlay status/date/signature
    affidavit_page = original_reader.pages[1]
    overlay_buf = io.BytesIO()
    oc = rl_canvas.Canvas(overlay_buf, pagesize=(float(affidavit_page.mediabox[2]), float(affidavit_page.mediabox[3])))
    ph = float(affidavit_page.mediabox[3])
    oc.setFont('Helvetica-Bold', 11)
    oc.setFillColor(HexColor('#000000'))
    if get('lawful_presence') == 'us_citizen':
        oc.setFont('Helvetica-Bold', 13)
        oc.drawString(44, ph - 182, '\u2713')
    elif get('lawful_presence') == 'qualified_alien':
        oc.setFont('Helvetica-Bold', 13)
        oc.drawString(44, ph - 202, '\u2713')
    if get('alien_number'):
        oc.setFont('Helvetica', 10)
        oc.drawString(195, ph - 230, get('alien_number'))
    oc.setFont('Helvetica', 10)
    oc.drawString(72, ph - 305, get('signature_date'))
    draw_sig(oc, 'sig_final', 335, ph - 308, 170, 18)
    oc.drawString(100, ph - 332, f"{get('city')}, {get('state')}")
    oc.drawString(375, ph - 332, full_name)
    if get('renewal_number'):
        oc.setFont('Helvetica', 10)
        oc.drawString(395, ph - 364, get('renewal_number'))
    oc.save()
    overlay_buf.seek(0)
    overlay_reader = PdfReader(overlay_buf)
    affidavit_page.merge_page(overlay_reader.pages[0])
    writer.add_page(affidavit_page)

    # Glory pages 2-7 of generated (Clinical Tasks, Media Release, Background Check, Grievance/Refund)
    for i in range(1, 6):
        if i < len(generated_reader.pages):
            writer.add_page(generated_reader.pages[i])

    # State pages: Nurse Aide Registry (original page indices 6-13, 8 pages of regulations)
    for i in range(6, 14):
        nar_page = original_reader.pages[i]
        if i == 13:
            # Page 14 has the signature/date/printed name/training program section
            nar_overlay_buf = io.BytesIO()
            noc = rl_canvas.Canvas(nar_overlay_buf, pagesize=(float(nar_page.mediabox[2]), float(nar_page.mediabox[3])))
            nph = float(nar_page.mediabox[3])
            noc.setFont('Helvetica', 10)
            noc.setFillColor(HexColor('#000000'))
            draw_sig(noc, 'sig_nar_rules', 17, nph - 478, 160, 18)
            noc.drawString(266, nph - 472, get('signature_date'))
            noc.drawString(365, nph - 472, full_name)
            noc.drawString(25, nph - 503, get('course_applied') or 'Certified Nursing Assistant (CNA)')
            noc.save()
            nar_overlay_buf.seek(0)
            nar_overlay_reader = PdfReader(nar_overlay_buf)
            nar_page.merge_page(nar_overlay_reader.pages[0])
        writer.add_page(nar_page)

    # Glory final page (Final Signature)
    if len(generated_reader.pages) > 6:
        writer.add_page(generated_reader.pages[6])

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)
    pdf_bytes = final_buf.read()


    email_error = None
    try:
        msg = EmailMessage(
            subject=f'New CNA Application Received - {full_name}',
            body=f'''A student has submitted their CNA application through the Glory Nursing website.

Student: {full_name}
Email: {student_email}
Phone: {get("phone")}

The completed application is attached.

Glory Nursing Online Portal''',
            from_email=None,
            to=['glorynursing@yahoo.com'],
        )
        msg.attach('CNA_Application.pdf', pdf_bytes, 'application/pdf')
        msg.send()

        EmailMessage(
            subject='Your Glory Nursing CNA Application Received',
            body=f'''Thank you for submitting your CNA application to Glory Nursing!

We have received your completed application. Our admissions team will review it and contact you within 1-2 business days.

Next step: Complete your enrollment payment at glorynursing.com

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120''',
            from_email=None,
            to=[student_email],
        ).send()
    except Exception as e:
        email_error = str(e)
        print(f"Email error: {e}")

    # Auto-create student account
    from django.contrib.auth.models import User as AuthUser
    import secrets, string
    account_created = False
    temp_password = None
    try:
        if not AuthUser.objects.filter(email=student_email).exists():
            username = student_email.split('@')[0].lower().replace('.','_')[:30]
            base_username = username
            counter = 1
            while AuthUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))
            new_user = AuthUser.objects.create_user(
                username=username,
                email=student_email,
                password=temp_password,
                first_name=get('first_name'),
                last_name=get('last_name'),
            )
            account_created = True
            # Store pending course in user's first_name field as fallback
            # Create a pending enrollment so dashboard knows which course to pay for
            try:
                from lms.models import Course as LMSCourse2, Enrollment
                course_title = get('course_applied') or ''
                pending_c = LMSCourse2.objects.filter(title=course_title, is_published=True).first()
                if not pending_c:
                    pending_c = LMSCourse2.objects.filter(
                        program__icontains='CNA', is_published=True
                    ).exclude(program__icontains='HHA').order_by('price').first()
                if pending_c:
                    Enrollment.objects.get_or_create(
                        student=new_user,
                        course=pending_c,
                    )
            except Exception as enroll_err:
                print(f"Pending enrollment error: {enroll_err}")
            # Send credentials email
            try:
                EmailMessage(
                    subject='Your Glory Nursing Account Has Been Created',
                    body=f'''Welcome to Glory Nursing Healthcare Training School!

Your application has been received and your student account has been created.

Login Details:
Website: https://glorynursingok.com/lms/login/
Username: {username}
Password: {temp_password}

Please login and complete your enrollment payment to gain access to your course.

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120''',
                    from_email=None,
                    to=[student_email],
                ).send()
            except Exception as e:
                print(f"Credentials email error: {e}")
            # Create pending enrollment based on course_applied field
            try:
                from lms.models import Course as LMSCourse2, Enrollment
                course_title = data.get('course_applied', '').strip()
                pending_c = None
                if course_title:
                    pending_c = LMSCourse2.objects.filter(title=course_title, is_published=True).first()
                if not pending_c:
                    pending_c = LMSCourse2.objects.filter(is_published=True).order_by('price').first()
                if pending_c:
                    Enrollment.objects.get_or_create(student=new_user, course=pending_c)
            except Exception as enroll_err:
                print(f"Pending enrollment error: {enroll_err}")
    except Exception as e:
        print(f"Account creation error: {e}")

    request.session['application_submitted'] = True
    # Store pending course for payment redirect
    from lms.models import Course as LMSCourse
    pending_course = LMSCourse.objects.filter(
        program__icontains='CNA', is_published=True
    ).exclude(program__icontains='HHA').order_by('price').first()
    if pending_course:
        request.session['pending_course_id'] = pending_course.id

    from django.http import HttpResponse
    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CNA_Application_{full_name.replace(" ", "_")}.pdf"'
    if email_error:
        response['X-Email-Error'] = email_error[:200]
    return response

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


def fill_form_simple(request, program_code):
    from lms.models import Course as LMSCourse
    program_names = {
        'BLS': 'Basic Life Support (BLS) / CPR',
        'HHA': 'Home Health Aide (HHA)',
        'PHLEBOTOMY': 'Phlebotomy Technician',
        'EKG': 'EKG Technician',
        'CCMA': 'Certified Clinical Medical Assistant (CCMA)',
    }
    program_name = program_names.get(program_code.upper(), program_code)
    course = LMSCourse.objects.filter(program__iexact=program_code, is_published=True).order_by('price').first()
    course_id = course.id if course else ''
    return render(request, 'core/fill_form_simple.html', {
        'program_name': program_name,
        'program_code': program_code.upper(),
        'course_id': course_id,
        'back_url': '/contact/',
        'submit_url': f'/apply/simple/{program_code}/submit/',
    })


@csrf_exempt
def submit_form_simple(request, program_code):
    import json
    from django.http import JsonResponse
    from django.core.mail import EmailMessage

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    student_email = data.get('student_email', '').strip()
    if not student_email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    full_name = f"{data.get('first_name','')} {data.get('last_name','')}".strip() or 'Applicant'
    program_name = data.get('program_name', program_code)

    try:
        msg = EmailMessage(
            subject=f'New {program_name} Application Received - {full_name}',
            body=f"""A student has submitted an application for {program_name} through the Glory Nursing website.

Name: {full_name}
Email: {student_email}
Phone: {data.get('phone','')}
DOB: {data.get('dob','')}
SSN: {data.get('ssn','')}
Address: {data.get('street','')}, {data.get('city','')}, {data.get('state','')} {data.get('zip','')}
How heard: {data.get('how_heard','')}

Glory Nursing Online Portal""",
            from_email=None,
            to=['glorynursing@yahoo.com'],
        )
        msg.send()

        EmailMessage(
            subject=f'Your Glory Nursing {program_name} Application Received',
            body=f"""Thank you for submitting your {program_name} application to Glory Nursing!

We have received your application. Our admissions team will review it and contact you within 1-2 business days.

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120""",
            from_email=None,
            to=[student_email],
        ).send()
    except Exception as e:
        print(f"Email error: {e}")


    # Auto-create student account
    from django.contrib.auth.models import User as AuthUser
    import secrets, string
    try:
        if not AuthUser.objects.filter(email=student_email).exists():
            username = student_email.split('@')[0].lower().replace('.','_')[:30]
            base_username = username
            counter = 1
            while AuthUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))
            new_user = AuthUser.objects.create_user(
                username=username,
                email=student_email,
                password=temp_password,
                first_name=data.get('first_name',''),
                last_name=data.get('last_name',''),
            )
            try:
                EmailMessage(
                    subject='Your Glory Nursing Account Has Been Created',
                    body=f"""Welcome to Glory Nursing Healthcare Training School!

Your application has been received and your student account has been created.

Login Details:
Website: https://glorynursingok.com/lms/login/
Username: {username}
Password: {temp_password}

Please login and complete your enrollment payment to gain access to your course.

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School""",
                    from_email=None,
                    to=[student_email],
                ).send()
            except Exception as e:
                print(f"Credentials email error: {e}")
            # Create pending enrollment based on course_applied field
            try:
                from lms.models import Course as LMSCourse2, Enrollment
                course_title = data.get('course_applied', '').strip()
                pending_c = None
                if course_title:
                    pending_c = LMSCourse2.objects.filter(title=course_title, is_published=True).first()
                if not pending_c:
                    pending_c = LMSCourse2.objects.filter(is_published=True).order_by('price').first()
                if pending_c:
                    Enrollment.objects.get_or_create(student=new_user, course=pending_c)
            except Exception as enroll_err:
                print(f"Pending enrollment error: {enroll_err}")
    except Exception as e:
        print(f"Account creation error: {e}")

    request.session['application_submitted'] = True
    return JsonResponse({'success': True})


def fill_form_cma(request):
    from lms.models import Course as LMSCourse
    enroll_id = request.session.get('apply_enroll_id', 2)
    program_slug = request.session.get('apply_program_slug', '')
    back_url = f'/apply/cma/?program={program_slug}' if program_slug else '/apply/cma/'
    cma_courses = LMSCourse.objects.filter(program__icontains='CMA', is_published=True).order_by('price')
    return render(request, 'core/fill_form_cma.html', {
        'enroll_id': enroll_id,
        'back_url': back_url,
        'cma_courses': cma_courses,
    })


@csrf_exempt
def submit_form_cma(request):
    import json
    import io
    import base64
    from django.http import JsonResponse, HttpResponse
    from django.core.mail import EmailMessage
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import HexColor
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    from pypdf import PdfReader, PdfWriter
    from pypdf.generic import NameObject
    import os as _os

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({'error': 'Invalid data'}, status=400)

    student_email = data.get('student_email', '').strip()
    if not student_email:
        return JsonResponse({'error': 'Email is required'}, status=400)

    def get(key, default=''):
        v = data.get(key, default)
        return v if v else default

    def draw_sig_img(target_canvas, key, x, y, w, h):
        img_data = data.get(key, '')
        if img_data and img_data.startswith('data:image'):
            try:
                header, b64 = img_data.split(',', 1)
                img_bytes = base64.b64decode(b64)
                img_reader = ImageReader(io.BytesIO(img_bytes))
                target_canvas.drawImage(img_reader, x, y, width=w, height=h, mask='auto')
            except Exception:
                pass

    full_name = f"{get('first_name')} {get('last_name')}".strip() or 'Applicant'

    original_path = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), 'static', 'core', 'documents', 'CMA_app.pdf')
    original_reader = PdfReader(original_path)
    writer = PdfWriter()
    writer.append(original_reader)

    # ---- Fill real AcroForm text fields ----
    field_values = {
        # Page 1: CMA Attestation
        'Typed or Printed Name of Applicant': full_name,
        'Social Security Number of Applicant': get('ssn'),
        'Signature Field 10': '',
        'Date of Signing 6': get('signature_date'),

        # Page 7: Photograph and Media Release Waiver
        'Text Field 28': full_name,
        'Date Field 3': get('dob'),
        'Number Field 1': get('phone'),
        'Text Field 29': student_email,
        'Date of Signing 2': get('signature_date'),
        'Date of Signing 3': get('signature_date'),
        'Text Field 30': full_name,
        'Text Field 32': full_name,
        'Date of Signing 5': get('signature_date'),
        'Text Field 27': full_name,
        'Date of Signing 1': get('signature_date'),

        # Page 4: Enrollment Application
        'Text Field 3': get('last_name'),
        'Text Field 1': get('first_name'),
        'Text Field 4': get('middle_initial'),
        'Text Field 2': get('how_heard'),
        'Date Field 1': get('dob'),
        'Text Field 5': get('ssn'),
        'Text Field 6': get('street'),
        'Text Field 11': get('phone'),
        'Text Field 7': get('city'),
        'Text Field 8': get('state'),
        'Text Field 9': get('zip'),
        'Text Field 10': student_email,
        'Text Field 12': get('course_applied'),
        'Text Field 13': get('emergency_name'),
        'Text Field 14': get('emergency_phone'),
        'Text Field 15': get('emergency_address'),
        'Text Field 16': get('emergency_relationship'),
        'Text Field 17': get('hs_name'),
        'Text Field 18': get('hs_address'),
        'Text Field 19': get('hs_from'),
        'Text Field 20': get('hs_to'),
        'Text Field 21': get('hs_diploma'),
        'Text Field 23': get('college_name'),
        'Text Field 22': get('college_address'),
        'Text Field 24': get('college_from'),
        'Text Field 25': get('college_to'),
        'Text Field 26': get('degree'),
        'Date Field 2': get('signature_date'),
    }

    checkbox_values = {}
    if get('hs_graduated_cma') == 'Yes':
        checkbox_values['Checkbox 1'] = '/Yes'
    elif get('hs_graduated_cma') == 'No':
        checkbox_values['Checkbox 2'] = '/Yes'
    if get('college_graduated') == 'Yes':
        checkbox_values['Checkbox 6'] = '/Yes'
    elif get('college_graduated') == 'No':
        checkbox_values['Checkbox 5'] = '/Yes'

    # Note: attestation Yes/No checkboxes share field names across all 5 questions
    # in this PDF's form design, so we cannot set them independently via AcroForm.
    # We overlay X marks at known coordinates instead (see below).

    for page in writer.pages:
        writer.update_page_form_field_values(page, {**field_values, **checkbox_values}, auto_regenerate=False)

    # Overlay attestation Yes/No marks (shared field names can't represent 5 independent answers)
    att_page = writer.pages[0]
    att_ph = float(original_reader.pages[0].mediabox[3])
    att_pw = float(original_reader.pages[0].mediabox[2])
    att_overlay_buf = io.BytesIO()
    atc = rl_canvas.Canvas(att_overlay_buf, pagesize=(att_pw, att_ph))
    atc.setFont('Helvetica-Bold', 10)
    atc.setFillColor(HexColor('#000000'))
    qy_positions = [
        ('cma_age', 376),
        ('cma_education', 363),
        ('cma_experience', 345),
        ('cma_cert', 333),
        ('cma_capability', 320),
    ]
    for field_key, y_pt in qy_positions:
        ans = get(field_key)
        if ans == 'Yes':
            atc.drawString(426, y_pt, '\u2713')
        elif ans == 'No':
            atc.drawString(480, y_pt, '\u2713')
    atc.save()
    att_overlay_buf.seek(0)
    att_overlay_reader = PdfReader(att_overlay_buf)
    att_page.merge_page(att_overlay_reader.pages[0])

    # Force form field appearances to render
    try:
        writer.set_need_appearances_writer(True)
    except Exception:
        pass

    # ---- Overlay signatures (image-based, AcroForm text fields can't hold images) ----
    sig_targets = [
        (0, 'sig_cma_attestation', 321, 158, 170, 30),       # Page 1 attestation signature
        (3, 'sig_final', 126, 114, 140, 24),                  # Page 4 enrollment signature
        (5, 'sig_clinical_tasks', 129, 485, 200, 24),         # Page 6 clinical tasks
        (6, 'sig_final', 186, 141, 150, 18),                  # Page 7 media release student sig (reuse final signature)
        (15, 'sig_nar_rules', 52, 318, 200, 22),              # Page 16 NAR signature
        (17, 'sig_refund_policy', 366, 116, 110, 18),         # Page 18 refund acknowledgment
        (19, 'sig_background_check', 132, 246, 200, 26),      # Page 20 background check signature
        (21, 'sig_clinical_tasks', 129, 485, 200, 24),        # Page 22 duplicate clinical tasks ack
    ]
    for page_idx, sig_key, x, y, w, h in sig_targets:
        if page_idx >= len(writer.pages):
            continue
        if sig_key not in data or not data.get(sig_key):
            continue
        page = writer.pages[page_idx]
        ph = float(page.mediabox[3])
        pw = float(page.mediabox[2])
        overlay_buf = io.BytesIO()
        oc = rl_canvas.Canvas(overlay_buf, pagesize=(pw, ph))
        draw_sig_img(oc, sig_key, x, y, w, h)
        oc.save()
        overlay_buf.seek(0)
        overlay_reader = PdfReader(overlay_buf)
        page.merge_page(overlay_reader.pages[0])

    # ---- Affidavit page (page 2) — use real fields where possible, fallback overlay for checkboxes ----
    aff_field_values = {
        'efield68_Text1': get('alien_number'),
        'Text2': get('authorizing_document'),
        'Date5_af_date': get('signature_date'),
        'Signature Field 7': '',
        'Text7': f"{get('city')}, {get('state')}",
        'Text8': full_name,
        'Text9': get('renewal_number'),
    }

    bg_field_values = {
        'Text Field 31': full_name,
        'Date of Signing 4': get('signature_date'),
    }
    bg_checkbox_values = {}
    if get('background_check') == 'glory_conducts':
        bg_checkbox_values['Checkbox 4'] = '/Yes'
    elif get('background_check') == 'self_provide':
        bg_checkbox_values['Checkbox 3'] = '/Yes'
    writer.update_page_form_field_values(writer.pages[19], {**bg_field_values, **bg_checkbox_values}, auto_regenerate=False)

    nar_field_values = {
        'Text1': f"{get('signature_date')}   {full_name}",
        'Text4': get('course_applied'),
    }
    writer.update_page_form_field_values(writer.pages[15], nar_field_values, auto_regenerate=False)
    aph = float(original_reader.pages[1].mediabox[3])
    apw = float(original_reader.pages[1].mediabox[2])
    writer.update_page_form_field_values(writer.pages[1], aff_field_values, auto_regenerate=False)
    affidavit_page = writer.pages[1]

    aff_overlay_buf = io.BytesIO()
    aoc = rl_canvas.Canvas(aff_overlay_buf, pagesize=(apw, aph))
    aoc.setFont('Helvetica-Bold', 13)
    aoc.setFillColor(HexColor('#000000'))
    lp_value = get('lawful_presence')
    if lp_value == 'us_citizen':
        aoc.drawString(36, 636, '\u2713')
    elif lp_value == 'qualified_alien':
        aoc.drawString(38, 597, '\u2713')
    draw_sig_img(aoc, 'sig_final', 380, 412, 170, 18)
    aoc.save()
    aff_overlay_buf.seek(0)
    aff_overlay_reader = PdfReader(aff_overlay_buf)
    affidavit_page.merge_page(aff_overlay_reader.pages[0])

    final_buf = io.BytesIO()
    writer.write(final_buf)
    final_buf.seek(0)
    pdf_bytes = final_buf.read()

    email_error = None
    try:
        msg = EmailMessage(
            subject=f'New CMA Application Received - {full_name}',
            body=f"""A student has submitted their CMA application through the Glory Nursing website.

Student: {full_name}
Email: {student_email}
Phone: {get("phone")}

The completed application is attached.

Glory Nursing Online Portal""",
            from_email=None,
            to=['glorynursing@yahoo.com'],
        )
        msg.attach('CMA_Application.pdf', pdf_bytes, 'application/pdf')
        msg.send()

        EmailMessage(
            subject='Your Glory Nursing CMA Application Received',
            body=f"""Thank you for submitting your CMA application to Glory Nursing!

We have received your completed application. Our admissions team will review it and contact you within 1-2 business days.

Next step: Complete your enrollment payment at glorynursing.com

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120""",
            from_email=None,
            to=[student_email],
        ).send()
    except Exception as e:
        email_error = str(e)
        print(f"Email error: {e}")


    # Auto-create student account
    from django.contrib.auth.models import User as AuthUser
    import secrets, string
    try:
        if not AuthUser.objects.filter(email=student_email).exists():
            username = student_email.split('@')[0].lower().replace('.','_')[:30]
            base_username = username
            counter = 1
            while AuthUser.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
            alphabet = string.ascii_letters + string.digits
            temp_password = ''.join(secrets.choice(alphabet) for _ in range(10))
            new_user = AuthUser.objects.create_user(
                username=username,
                email=student_email,
                password=temp_password,
                first_name=data.get('first_name',''),
                last_name=data.get('last_name',''),
            )
            try:
                EmailMessage(
                    subject='Your Glory Nursing Account Has Been Created',
                    body=f"""Welcome to Glory Nursing Healthcare Training School!

Your application has been received and your student account has been created.

Login Details:
Website: https://glorynursingok.com/lms/login/
Username: {username}
Password: {temp_password}

Please login and complete your enrollment payment to gain access to your course.

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School""",
                    from_email=None,
                    to=[student_email],
                ).send()
            except Exception as e:
                print(f"Credentials email error: {e}")
            # Create pending enrollment based on course_applied field
            try:
                from lms.models import Course as LMSCourse2, Enrollment
                course_title = data.get('course_applied', '').strip()
                pending_c = None
                if course_title:
                    pending_c = LMSCourse2.objects.filter(title=course_title, is_published=True).first()
                if not pending_c:
                    pending_c = LMSCourse2.objects.filter(is_published=True).order_by('price').first()
                if pending_c:
                    Enrollment.objects.get_or_create(student=new_user, course=pending_c)
            except Exception as enroll_err:
                print(f"Pending enrollment error: {enroll_err}")
    except Exception as e:
        print(f"Account creation error: {e}")

    request.session['application_submitted'] = True

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="CMA_Application_{full_name.replace(" ", "_")}.pdf"'
    if email_error:
        response['X-Email-Error'] = email_error[:200]
    return response

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
    import io
    import json
    import base64
    from pypdf import PdfReader, PdfWriter
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.utils import ImageReader
    from django.http import HttpResponse, JsonResponse
    from django.core.mail import EmailMessage

    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    data = json.loads(request.body)
    annotations = data.get('annotations', {})  
    render_dpi = data.get('dpi', 120)

    pdf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            'static', 'core', 'documents', pdf_filename)

    reader = PdfReader(pdf_path)
    writer = PdfWriter()
    writer.append(reader)

    # Standard scale mapping factor between high-res display pixels and raw PDF points
    scale = 72.0 / render_dpi

    for page_str, annots in annotations.items():
        page_idx = int(page_str) - 1
        if page_idx < 0 or page_idx >= len(writer.pages):
            continue

        page_height = float(reader.pages[page_idx].mediabox[3])
        page_width = float(reader.pages[page_idx].mediabox[2])

        overlay_buf = io.BytesIO()
        c = rl_canvas.Canvas(overlay_buf, pagesize=(page_width, page_height))

        for annot in annots:
            # Map structural browser overlay data back to exact native vector points
            pdf_x = annot['x'] * scale
            pdf_y = page_height - (annot['y'] * scale)

            if annot['type'] == 'text':
                font_size = annot.get('fontSize', 12)
                color = annot.get('color', '#000000')
                
                try:
                    r = int(color[1:3], 16) / 255.0
                    g = int(color[3:5], 16) / 255.0
                    b = int(color[5:7], 16) / 255.0
                except Exception:
                    r, g, b = 0.0, 0.0, 0.0
                
                c.setFillColorRGB(r, g, b)
                c.setFont("Times-Bold", font_size)
                # Keep font text resting evenly centered on the actual structural fill line
                c.drawString(pdf_x, pdf_y, annot.get('text', ''))

            elif annot['type'] == 'sig':
                img_data = annot.get('data', '')
                if img_data and img_data.startswith('data:image'):
                    try:
                        header, b64 = img_data.split(',', 1)
                        img_bytes = base64.b64decode(b64)
                        img_buf = io.BytesIO(img_bytes)
                        img_reader = ImageReader(img_buf)
                        
                        w = annot.get('w', 180) * scale
                        h = annot.get('h', 50) * scale
                        
                        # Signatures must drop down vertically based on image rendering coordinates
                        c.drawImage(img_reader, pdf_x, pdf_y - h, width=w, height=h, mask='auto')
                    except Exception as e:
                        print(f"Signature render exception: {e}")

            elif annot['type'] == 'check':
                c.setFont("Helvetica-Bold", 14)
                c.setFillColorRGB(0, 0, 0)
                # Aligns check glyph directly inside checkbox layout grids
                c.drawString(pdf_x - 3, pdf_y - 4, '✓')

        c.save()
        overlay_buf.seek(0)
        overlay_reader = PdfReader(overlay_buf)
        writer.pages[page_idx].merge_page(overlay_reader.pages[0])

    output_buf = io.BytesIO()
    writer.write(output_buf)
    output_buf.seek(0)
    pdf_bytes = output_buf.read()

    action = data.get('action', 'download')  

    if action == 'submit':
        try:
            student_email = data.get('student_email', '')
            program = data.get('program', 'Program')
            msg = EmailMessage(
                subject=f'New {program} Application Received',
                body=f'A student has submitted their {program} application through the Glory Nursing website.\n\nStudent Email: {student_email if student_email else "Not provided"}\n\nGlory Nursing Online Portal',
                from_email=None,
                to=['glorynursing@yahoo.com'],
            )
            msg.attach(output_filename, pdf_bytes, 'application/pdf')
            msg.send()

            if student_email:
                EmailMessage(
                    subject=f'Your Glory Nursing {program} Application Received',
                    body=f'Thank you for submitting your {program} application to Glory Nursing!\n\nWe have received your completed application.\n\nGlory Nursing School',
                    from_email=None,
                    to=[student_email],
                ).send()
        except Exception as e:
            print(f"Email routing error: {e}")

        return JsonResponse({'success': True, 'message': 'Application submitted successfully!'})

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


@csrf_exempt
def upload_application_document(request):
    """AJAX endpoint — securely upload a single applicant document."""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST required'}, status=400)

    from .models import ApplicationDocument

    file_obj = request.FILES.get('file')
    doc_type = request.POST.get('document_type', 'other')
    full_name = request.POST.get('full_name', '').strip()
    email = request.POST.get('email', '').strip()
    program = request.POST.get('program', '').strip()

    if not file_obj:
        return JsonResponse({'error': 'No file provided'}, status=400)

    allowed_ext = ('.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx')
    if not file_obj.name.lower().endswith(allowed_ext):
        return JsonResponse({'error': 'File type not allowed. Use PDF, JPG, PNG, or Word.'}, status=400)

    if file_obj.size > 10 * 1024 * 1024:
        return JsonResponse({'error': 'File too large. Max 10MB.'}, status=400)

    if not request.session.session_key:
        request.session.save()

    doc = ApplicationDocument.objects.create(
        full_name=full_name,
        email=email,
        program=program,
        document_type=doc_type,
        file=file_obj,
        session_key=request.session.session_key,
    )

    # Store uploaded doc ids in session so we know what this applicant submitted
    uploaded = request.session.get('uploaded_doc_ids', [])
    uploaded.append(doc.id)
    request.session['uploaded_doc_ids'] = uploaded

    return JsonResponse({
        'success': True,
        'id': doc.id,
        'filename': file_obj.name,
        'document_type': doc.get_document_type_display(),
    })


def delete_application_document(request, doc_id):
    """Remove an uploaded document (only if it belongs to this session)."""
    from .models import ApplicationDocument
    uploaded = request.session.get('uploaded_doc_ids', [])
    if doc_id in uploaded:
        ApplicationDocument.objects.filter(id=doc_id).delete()
        uploaded.remove(doc_id)
        request.session['uploaded_doc_ids'] = uploaded
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Not found'}, status=404)
