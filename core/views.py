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

    return render(request, 'core/home.html', {
        'programs': featured_programs,
        'use_db': use_db,
        'testimonials': TESTIMONIALS,
        'latest_posts': latest_posts,
        'upcoming_events': upcoming_events,
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
    db_program = Program.objects.filter(slug=slug, is_active=True).first()
    if db_program:
        return render(request, 'core/program_detail.html', {
            'program': db_program,
            'use_db': True,
            'page': 'programs',
        })
    program = next((p for p in PROGRAMS if p['slug'] == slug), None)
    if not program:
        from django.http import Http404
        raise Http404
    return render(request, 'core/program_detail.html', {
        'program': program,
        'use_db': False,
        'page': 'programs',
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
 