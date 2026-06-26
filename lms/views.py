import json
import random
import string
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Prefetch
from django.db import models
from django.http import JsonResponse
from .models import (
    Course, Module, Lesson, ContentItem, Quiz, Question, 
    QuizAttempt, LessonProgress, Certificate, SupportThread, 
    Enrollment, Subscription, Announcement, Discussion, StudentActivity, AuditLog,
    CourseReview, StudentStreak, InteractiveElement, InteractiveCompletion
)

# =========================================================================
# 1. SECURITY LIFECYCLE MANAGEMENT (AUTHENTICATION GATEWAYS)
# =========================================================================

def lms_login_view(request):
    """Secure universal entry point. Redirects active sessions automatically."""
    if request.user.is_authenticated:
        return redirect('lms_dashboard')
        
    if request.method == 'POST':
        # Step 2: verifying 2FA code (user already passed password check)
        if request.POST.get('action') == 'verify_2fa':
            from django_otp.plugins.otp_totp.models import TOTPDevice
            pending_user_id = request.session.get('pending_2fa_user_id')
            token = request.POST.get('token', '').strip()

            if not pending_user_id:
                return redirect('lms_login')

            pending_user = User.objects.filter(id=pending_user_id).first()
            device = TOTPDevice.objects.filter(user=pending_user, confirmed=True).first()

            if device and device.verify_token(token):
                login(request, pending_user)
                del request.session['pending_2fa_user_id']
                log_audit(request, pending_user, 'login', target_repr=f'{pending_user.username} logged in (2FA verified)')
                return redirect('lms_dashboard')
            else:
                log_audit(request, pending_user, 'login_failed', target_repr=f'{pending_user.username} entered invalid 2FA code')
                return render(request, 'lms/login.html', {'show_2fa': True, 'error': 'Invalid 2FA code. Please try again.'})

        # Step 1: username/password
        user_handle = request.POST.get('username', '').strip()
        pass_string = request.POST.get('password', '').strip()
        user = authenticate(request, username=user_handle, password=pass_string)
        
        if user is not None:
            # Check if user has 2FA enabled
            from django_otp.plugins.otp_totp.models import TOTPDevice
            device = TOTPDevice.objects.filter(user=user, confirmed=True).first()

            if device:
                # Require 2FA code
                request.session['pending_2fa_user_id'] = user.id
                return render(request, 'lms/login.html', {'show_2fa': True})

            login(request, user)
            if user.is_staff:
                log_audit(request, user, 'login', target_repr=f'{user.username} logged in')
            else:
                streak, _ = StudentStreak.objects.get_or_create(student=user)
                streak.update_streak()
            return redirect('lms_dashboard')
        else:
            # Log failed admin login attempts
            try:
                attempted_user = User.objects.filter(username=user_handle).first()
                if attempted_user and attempted_user.is_staff:
                    log_audit(request, attempted_user, 'login_failed', target_repr=f'Failed login attempt for {user_handle}')
            except Exception:
                pass
            return render(request, 'lms/login.html', {'error': 'Invalid authentication security credentials.'})
            
    return render(request, 'lms/login.html')


def lms_logout_view(request):
    """Terminates active user session cache arrays and clears cookies."""
    logout(request)
    return redirect('lms_login')


# =========================================================================
# 2. THE UNIFIED MASTER CONTROL CENTER (ROLE-BASED TRAFFIC COP)
# =========================================================================

@login_required(login_url='lms_login')
def lms_dashboard_view(request):
    user = request.user

    # -------------------------------------------------------------------------
    # ROUTE A: ADMINISTRATIVE OPERATOR DESK
    # -------------------------------------------------------------------------
    if user.is_staff:
        if request.method == 'POST':
            action = request.POST.get('action')

            # --- INTERACTIVE CONTENT BUILDER ---
            if action == 'add_interactive':
                lesson_id = request.POST.get('lesson_id')
                title = request.POST.get('title', '').strip()
                element_type = request.POST.get('element_type')
                points = int(request.POST.get('points', 10))
                attached_to = request.POST.get('attached_to') or None
                data_json = request.POST.get('data_json', '{}')

                try:
                    data = json.loads(data_json)
                except Exception:
                    data = {}

                lesson_obj = Lesson.objects.filter(id=lesson_id).first()
                if lesson_obj and title and element_type:
                    elem = InteractiveElement.objects.create(
                        lesson=lesson_obj,
                        title=title,
                        element_type=element_type,
                        points=points,
                        data=data,
                        attached_to_id=attached_to,
                        order=InteractiveElement.objects.filter(lesson=lesson_obj).count() + 1,
                    )
                    log_audit(request, user, 'create', target_model='InteractiveElement', target_id=elem.id, target_repr=f'Added {element_type} "{title}" to lesson {lesson_obj.title}')
                return redirect('lms_dashboard')

            elif action == 'delete_interactive':
                element_id = request.POST.get('element_id')
                elem = InteractiveElement.objects.filter(id=element_id).first()
                if elem:
                    title = elem.title
                    elem.delete()
                    log_audit(request, user, 'delete', target_model='InteractiveElement', target_id=element_id, target_repr=f'Deleted interactive element "{title}"')
                return redirect('lms_dashboard')

            # --- COURSE REVIEW MODERATION ---
            if action == 'approve_review':
                review_id = request.POST.get('review_id')
                CourseReview.objects.filter(id=review_id).update(is_approved=True)
                log_audit(request, user, 'update', target_model='CourseReview', target_id=review_id, target_repr='Approved a course review')
                return redirect('lms_dashboard')

            elif action == 'reject_review':
                review_id = request.POST.get('review_id')
                CourseReview.objects.filter(id=review_id).delete()
                log_audit(request, user, 'delete', target_model='CourseReview', target_id=review_id, target_repr='Rejected/deleted a course review')
                return redirect('lms_dashboard')

            # --- USER PROVISIONING ENGINE ---
            if action == 'create_student':
                username = request.POST.get('username', '').strip()
                email = request.POST.get('email', '').strip()
                
                if User.objects.filter(username=username).exists():
                    messages.error(request, f"Error: Username '{username}' is already taken.")
                elif User.objects.filter(email=email).exists():
                    messages.error(request, f"Error: Email '{email}' is already registered.")
                else:
                    pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                    new_user = User.objects.create_user(username=username, email=email, password=pwd)
                    new_user.is_staff = False
                    new_user.save()
                    
                    # Instantiate standardized active premium invoice records
                    Subscription.objects.create(
                        student=new_user, 
                        tier_name="Premium Access Track", 
                        amount_paid=250.00, 
                        status='active'
                    )
                    
                    try:
                        from django.core.mail import send_mail
                        send_mail(
                            subject='Your Glory Nursing LMS Login Credentials',
                            message=f"Welcome to Glory Nursing!\n\nUsername: {username}\nPassword: {pwd}\n\nLogin at: https://glorynursingok.com/lms/login/\n\nPlease change your password after first login.",
                            from_email=None,
                            recipient_list=[email],
                            fail_silently=True,
                        )
                        email_status = "Credentials sent to their email."
                    except Exception:
                        email_status = "Email could not be sent — share credentials manually."

                    messages.success(request, f"✅ Account Created! Username: {username} | Password: {pwd} | {email_status}")
                return redirect('lms_dashboard')

            # --- TESTING & ASSESSMENTS INJECTOR ---
            elif action == 'create_quiz':
                lesson_id = request.POST.get('lesson_id')
                title = request.POST.get('title')
                passing = request.POST.get('passing_score', 70)
                time_limit = request.POST.get('time_limit', 0)
                if lesson_id:
                    les = get_object_or_404(Lesson, id=lesson_id)
                    Quiz.objects.create(lesson=les, title=title, passing_score=passing, time_limit=time_limit)
                    messages.success(request, f"Assessment module '{title}' linked directly to Lesson.")
                return redirect('lms_dashboard')

            elif action == 'create_question':
                quiz_id = request.POST.get('quiz_id')
                question_type = request.POST.get('question_type', 'multiple_choice')

                if quiz_id:
                    qz = get_object_or_404(Quiz, id=quiz_id)

                    q_kwargs = {
                        'quiz': qz,
                        'text': request.POST.get('text'),
                        'question_type': question_type,
                    }

                    if question_type in ('multiple_choice', 'image_choice'):
                        q_kwargs.update({
                            'option_a': request.POST.get('option_a', ''),
                            'option_b': request.POST.get('option_b', ''),
                            'option_c': request.POST.get('option_c', ''),
                            'option_d': request.POST.get('option_d', ''),
                            'correct_answer': request.POST.get('correct_answer', 'A'),
                        })

                    if question_type == 'image_choice' and request.FILES.get('image'):
                        q_kwargs['image'] = request.FILES['image']

                    if question_type == 'drag_drop_match':
                        match_json = request.POST.get('match_data_json', '{}')
                        try:
                            q_kwargs['match_data'] = json.loads(match_json)
                        except Exception:
                            q_kwargs['match_data'] = {}

                    Question.objects.create(**q_kwargs)
                    messages.success(request, "Question added successfully.")
                return redirect('lms_dashboard')

            elif action == 'bulk_add_questions':
                quiz_id = request.POST.get('quiz_id')
                bulk_text = request.POST.get('bulk_text', '')

                if quiz_id and bulk_text.strip():
                    qz = get_object_or_404(Quiz, id=quiz_id)

                    # Split into question blocks by blank lines
                    # Normalize line endings and split on blank lines
                    import re
                    normalized = bulk_text.replace('\r\n', '\n').replace('\r', '\n')
                    blocks = [b.strip() for b in re.split(r'\n\s*\n', normalized.strip()) if b.strip()]
                    created_count = 0
                    errors = []

                    for block in blocks:
                        lines = [l.strip() for l in block.split('\n') if l.strip()]
                        q_data = {'text': '', 'option_a': '', 'option_b': '', 'option_c': '', 'option_d': '', 'correct_answer': ''}

                        for line in lines:
                            if line.upper().startswith('Q:'):
                                q_data['text'] = line[2:].strip()
                            elif line.upper().startswith('A)'):
                                q_data['option_a'] = line[2:].strip()
                            elif line.upper().startswith('B)'):
                                q_data['option_b'] = line[2:].strip()
                            elif line.upper().startswith('C)'):
                                q_data['option_c'] = line[2:].strip()
                            elif line.upper().startswith('D)'):
                                q_data['option_d'] = line[2:].strip()
                            elif line.upper().startswith('CORRECT:'):
                                ans = line.split(':', 1)[1].strip().upper()
                                q_data['correct_answer'] = ans

                        if q_data['text'] and q_data['option_a'] and q_data['option_b'] and q_data['option_c'] and q_data['option_d'] and q_data['correct_answer'] in ['A', 'B', 'C', 'D']:
                            Question.objects.create(quiz=qz, **q_data)
                            created_count += 1
                        else:
                            errors.append(q_data['text'] or block[:40])

                    if created_count:
                        messages.success(request, f"Bulk import: {created_count} question(s) added successfully.")
                    if errors:
                        messages.warning(request, f"Skipped {len(errors)} malformed question(s). Check the format and try again.")
                return redirect('lms_dashboard')

            # --- COMMUNICATIONS TICKET AUDITS ---
            elif action == 'resolve_thread':
                thread_id = request.POST.get('thread_id')
                thread = get_object_or_404(SupportThread, id=thread_id)
                thread.is_resolved = True
                thread.save()
                messages.success(request, "Interactive communication string marked resolved.")
                return redirect('lms_dashboard')

            # --- VERIFIED COMPLETION ISSUANCES ---
            elif action == 'issue_certificate':
                student_id = request.POST.get('student_id')
                course_id = request.POST.get('course_id')
                if student_id and course_id:
                    st = get_object_or_404(User, id=student_id)
                    cs = get_object_or_404(Course, id=course_id)
                    code = f"CERT-{cs.program}-" + ''.join(random.choices(string.digits, k=6))
                    Certificate.objects.get_or_create(student=st, course=cs, defaults={'certificate_code': code})
                    messages.success(request, f"Certificate hash reference {code} initialized.")
                return redirect('lms_dashboard')

            # --- DATA MEDIA PAYLOAD MANAGEMENT ---
            elif action == 'upload_content':
                lesson_id = request.POST.get('lesson_id')
                title = request.POST.get('title')
                content_type = request.POST.get('content_type')
                video_url = request.POST.get('video_url', '').strip()
                file_attachment = request.FILES.get('file_attachment')
                if lesson_id and title:
                    target_lesson = get_object_or_404(Lesson, id=lesson_id)
                    text_content = request.POST.get('text_content', '').strip()
                    content_item = ContentItem.objects.create(
                        lesson=target_lesson, title=title, content_type=content_type,
                        file_attachment=file_attachment, video_url=video_url,
                        text_content=text_content if text_content else None
                    )
                    if content_type == 'ppt' and file_attachment:
                        try:
                            slide_count = convert_ppt_to_images(content_item)
                            messages.success(request, f"'{title}' uploaded and converted to {slide_count} slides.")
                        except Exception as e:
                            messages.warning(request, f"'{title}' uploaded but slide conversion failed: {str(e)}")
                    else:
                        messages.success(request, f"'{title}' uploaded successfully.")
                return redirect('lms_dashboard')

            # --- BASE CURRICULUM STRUCTURAL DATA BLOCKS ---
            elif action == 'create_course':
                Course.objects.create(title=request.POST.get('title'), program=request.POST.get('program'))
                messages.success(request, "Base training course program deployed.")
                return redirect('lms_dashboard')
            
            elif action == 'create_module':
                cs = get_object_or_404(Course, id=request.POST.get('course_id'))
                Module.objects.create(course=cs, title=request.POST.get('title'), order=request.POST.get('order', 1))
                messages.success(request, "Learning module unit compiled to curriculum architecture.")
                return redirect('lms_dashboard')
            
            elif action == 'create_lesson':
                md = get_object_or_404(Module, id=request.POST.get('module_id'))
                Lesson.objects.create(module=md, title=request.POST.get('title'), order=request.POST.get('order', 1))
                messages.success(request, "Specific lesson milestone anchored successfully.")
                return redirect('lms_dashboard')
            
            elif action == 'create_enrollment':
                st = get_object_or_404(User, id=request.POST.get('student_id'))
                cs = get_object_or_404(Course, id=request.POST.get('course_id'))
                Enrollment.objects.get_or_create(student=st, course=cs)
                messages.success(request, f"Access portal mapped successfully for {st.username}.")
                return redirect('lms_dashboard')
            elif action == 'delete_course':
                course = get_object_or_404(Course, id=request.POST.get('course_id'))
                course.delete()
                messages.success(request, "Course deleted successfully.")
                return redirect('lms_dashboard')

            elif action == 'delete_module':
                module = get_object_or_404(Module, id=request.POST.get('module_id'))
                module.delete()
                messages.success(request, "Module deleted successfully.")
                return redirect('lms_dashboard')

            elif action == 'delete_lesson':
                lesson = get_object_or_404(Lesson, id=request.POST.get('lesson_id'))
                lesson.delete()
                messages.success(request, "Lesson deleted successfully.")
                return redirect('lms_dashboard')

            elif action == 'create_announcement':
                title = request.POST.get('title', '').strip()
                message = request.POST.get('message', '').strip()
                if title and message:
                    Announcement.objects.create(title=title, message=message, created_by=request.user)
                    messages.success(request, f"Announcement '{title}' posted.")
                return redirect('lms_dashboard')

            elif action == 'delete_announcement':
                ann = get_object_or_404(Announcement, id=request.POST.get('announcement_id'))
                ann.delete()
                messages.success(request, "Announcement deleted.")
                return redirect('lms_dashboard')

            # --- WEBSITE PROGRAMS ---
            elif action == 'save_program':
                from core.models import Program as CoreProgram
                prog_id = request.POST.get('program_id')
                title = request.POST.get('prog_title', '').strip()
                if title:
                    course_id = request.POST.get('prog_course') or None
                    course_obj = Course.objects.filter(id=course_id).first() if course_id else None
                    data = {
                        'title': title,
                        'short': request.POST.get('prog_short', ''),
                        'icon': request.POST.get('prog_icon', '🏥'),
                        'duration': request.POST.get('prog_duration', ''),
                        'hours': request.POST.get('prog_hours', ''),
                        'category': request.POST.get('prog_category', 'nursing'),
                        'description': request.POST.get('prog_description', ''),
                        'schedules': request.POST.get('prog_schedules', ''),
                        'order': int(request.POST.get('prog_order', 0)),
                        'is_active': 'prog_active' in request.POST,
                        'course': course_obj,
                    }
                    if prog_id:
                        CoreProgram.objects.filter(id=prog_id).update(**{k:v for k,v in data.items() if k != 'course'})
                        CoreProgram.objects.filter(id=prog_id).update(course=course_obj)
                        messages.success(request, f"Program '{title}' updated.")
                    else:
                        from django.utils.text import slugify
                        data['slug'] = slugify(title)
                        CoreProgram.objects.create(**data)
                        messages.success(request, f"Program '{title}' created.")
                return redirect('lms_dashboard')

            elif action == 'delete_program':
                from core.models import Program as CoreProgram
                prog = CoreProgram.objects.filter(id=request.POST.get('program_id')).first()
                if prog:
                    prog.delete()
                    messages.success(request, "Program deleted.")
                return redirect('lms_dashboard')

            # --- WEBSITE BLOG POSTS ---
            elif action == 'save_blog':
                from core.models import BlogPost
                title = request.POST.get('blog_title', '').strip()
                if title:
                    from django.utils.text import slugify
                    slug = slugify(title)
                    # Make unique slug
                    base_slug = slug
                    counter = 1
                    while BlogPost.objects.filter(slug=slug).exists():
                        slug = f"{base_slug}-{counter}"
                        counter += 1
                    BlogPost.objects.create(
                        title=title,
                        slug=slug,
                        excerpt=request.POST.get('blog_excerpt', ''),
                        content=request.POST.get('blog_content', ''),
                        image=request.FILES.get('blog_image'),
                        published_date=request.POST.get('blog_date') or None,
                        is_published='blog_published' in request.POST,
                    )
                    messages.success(request, f"Blog post '{title}' saved.")
                return redirect('lms_dashboard')

            elif action == 'delete_blog':
                from core.models import BlogPost
                post = BlogPost.objects.filter(id=request.POST.get('blog_id')).first()
                if post:
                    post.delete()
                    messages.success(request, "Blog post deleted.")
                return redirect('lms_dashboard')

            # --- WEBSITE EVENTS ---
            elif action == 'save_event':
                from core.models import Event
                title = request.POST.get('event_title', '').strip()
                if title:
                    Event.objects.create(
                        title=title,
                        description=request.POST.get('event_description', ''),
                        event_date=request.POST.get('event_date'),
                        start_time=request.POST.get('event_start'),
                        end_time=request.POST.get('event_end') or None,
                        location=request.POST.get('event_location', ''),
                        registration_open='event_registration' in request.POST,
                        is_active=True,
                    )
                    messages.success(request, f"Event '{title}' saved.")
                return redirect('lms_dashboard')

            elif action == 'delete_event':
                from core.models import Event
                event = Event.objects.filter(id=request.POST.get('event_id')).first()
                if event:
                    event.delete()
                    messages.success(request, "Event deleted.")
                return redirect('lms_dashboard')


            elif action == 'edit_content':
                ci_id = request.POST.get('content_id')
                ci = get_object_or_404(ContentItem, id=ci_id)
                ci.title = request.POST.get('title', ci.title).strip()
                if request.POST.get('video_url'):
                    ci.video_url = request.POST.get('video_url').strip()
                if request.FILES.get('file_attachment'):
                    ci.file_attachment = request.FILES['file_attachment']
                ci.save()
                messages.success(request, f"Content '{ci.title}' updated successfully!")
                return redirect('lms_dashboard')

            elif action == 'delete_content':
                ci = get_object_or_404(ContentItem, id=request.POST.get('content_id'))
                # Delete slide images if PPT
                import shutil
                slides_dir = os.path.join(settings.MEDIA_ROOT, 'slides', str(ci.id))
                if os.path.exists(slides_dir):
                    shutil.rmtree(slides_dir)
                ci.delete()
                messages.success(request, "Content item deleted.")
                return redirect('lms_dashboard')

            elif action == 'edit_course':
                course_id = request.POST.get('course_id')
                course = get_object_or_404(Course, id=course_id)
                course.title = request.POST.get('title', course.title).strip()
                course.program = request.POST.get('program', course.program).strip()
                course.price = float(request.POST.get('price', course.price) or 0)
                course.is_published = request.POST.get('is_published') == 'on'
                course.save()
                messages.success(request, f"Course '{course.title}' updated successfully!")
                return redirect('lms_dashboard')

            elif action == 'edit_module':
                module_id = request.POST.get('module_id')
                module = get_object_or_404(Module, id=module_id)
                module.title = request.POST.get('title', module.title).strip()
                module.order = int(request.POST.get('order', module.order) or module.order)
                module.save()
                messages.success(request, f"Module '{module.title}' updated successfully!")
                return redirect('lms_dashboard')

            elif action == 'edit_lesson':
                lesson_id = request.POST.get('lesson_id')
                lesson = get_object_or_404(Lesson, id=lesson_id)
                lesson.title = request.POST.get('title', lesson.title).strip()
                lesson.order = int(request.POST.get('order', lesson.order) or lesson.order)
                lesson.save()
                messages.success(request, f"Lesson '{lesson.title}' updated successfully!")
                return redirect('lms_dashboard')

            elif action == 'create_full_course':
                title = request.POST.get('title', '').strip()
                program = request.POST.get('program', '').strip()
                structure_json = request.POST.get('structure', '[]')
                if title and program:
                    price = float(request.POST.get('price', 0) or 0)
                    course = Course.objects.create(title=title, program=program, price=price, is_published=True)
                    try:
                        structure = json.loads(structure_json)
                        for mod_order, mod_data in enumerate(structure, start=1):
                            mod_title = mod_data.get('title', '').strip()
                            if not mod_title:
                                continue
                            module = Module.objects.create(course=course, title=mod_title, order=mod_order)
                            for les_order, les_data in enumerate(mod_data.get('lessons', []), start=1):
                                les_title = les_data.get('title', '').strip()
                                if not les_title:
                                    continue
                                Lesson.objects.create(module=module, title=les_title, order=les_order)
                    except (json.JSONDecodeError, KeyError):
                        pass
                    messages.success(request, f"Course '{title}' created successfully!")
                return redirect('lms_dashboard')

        # --- REVENUE & ANALYTICS METRICS AGGREGATION ---
        students_profiles = []
        raw_students = User.objects.filter(is_staff=False)
        total_lessons_count = Lesson.objects.count()

        for s in raw_students:
            completed_count = LessonProgress.objects.filter(student_id=s.id, is_completed=True).count()
            prog_ratio = int((completed_count / total_lessons_count) * 100) if total_lessons_count > 0 else 0
            last_attempt = QuizAttempt.objects.filter(student_id=s.id).order_by('-timestamp').first()
            
            students_profiles.append({
                'user_obj': s,
                'progress_percentage': prog_ratio,
                'last_score_attempt': last_attempt
            })

        revenue_query = Subscription.objects.filter(status='active').aggregate(total=Sum('amount_paid'))
        total_revenue = revenue_query['total'] if revenue_query['total'] is not None else 0.00

        context = {
            'all_students': raw_students,
            'students_profiles': students_profiles,
            'all_courses': Course.objects.all(),
            'all_modules': Module.objects.all(),
            'all_lessons': Lesson.objects.all(),
            'all_quizzes': Quiz.objects.all().select_related('lesson'),
            'open_tickets': SupportThread.objects.filter(is_resolved=False).select_related('user', 'lesson'),
            'all_certificates': Certificate.objects.all().select_related('student', 'course'),
            'all_subscriptions': Subscription.objects.all().select_related('student'),
            'total_students': raw_students.count(),
            'total_courses': Course.objects.count(),
            'total_revenue': float(total_revenue),
            'chart_data_json': json.dumps([400, 900, 1500, 2900, int(total_revenue)]),
            'all_content_items': ContentItem.objects.all().select_related('lesson__module__course'),
            'all_announcements': Announcement.objects.all(),
            'all_discussions': Discussion.objects.all().select_related('user', 'lesson__module__course').order_by('-created_at')[:50],
            'all_activities': StudentActivity.objects.all().select_related('student', 'course', 'lesson').order_by('-created_at')[:100],
            'revenue_data': get_revenue_report(),
            'audit_logs': AuditLog.objects.select_related('user').all()[:100],
            'pending_reviews': CourseReview.objects.filter(is_approved=False).select_related('student', 'course'),
            'all_courses': Course.objects.prefetch_related('modules__lessons'),
            'all_interactive_elements': InteractiveElement.objects.select_related('lesson').order_by('-id'),
            'approved_reviews': CourseReview.objects.filter(is_approved=True).select_related('student', 'course'),
            'page': 'lms_admin_dashboard',
            'all_programs': __import__('core.models', fromlist=['Program']).Program.objects.filter(is_active=True).order_by('order'),
            'all_blog_posts': __import__('core.models', fromlist=['BlogPost']).BlogPost.objects.all().order_by('-published_date'),
            'all_events': __import__('core.models', fromlist=['Event']).Event.objects.all().order_by('event_date'),
        }
        return render(request, 'lms/admin_dashboard.html', context)

    # -------------------------------------------------------------------------
    # ROUTE B: AUTHENTICATED STUDENT LEARNER RUNTIME ENVIRONMENT
    # -------------------------------------------------------------------------
    else:
        raw_enrollments = Enrollment.objects.filter(student=user).select_related('course')
        total_lessons = Lesson.objects.count()

        enrollments = []
        for enrollment in raw_enrollments:
            course_lessons = Lesson.objects.filter(module__course=enrollment.course)
            course_lesson_count = course_lessons.count()
            completed_count = LessonProgress.objects.filter(
                student=user,
                lesson__in=course_lessons,
                is_completed=True
            ).count()
            progress = int((completed_count / course_lesson_count) * 100) if course_lesson_count > 0 else 0

            # Find last lesson accessed
            last_progress = LessonProgress.objects.filter(
                student=user,
                lesson__in=course_lessons
            ).order_by('-updated_at').first()

            next_lesson = None
            if last_progress:
                next_lesson = last_progress.lesson
            else:
                first_module = enrollment.course.modules.order_by('order').first()
                if first_module:
                    next_lesson = first_module.lessons.order_by('order').first()

            enrollments.append({
                'course': enrollment.course,
                'progress_percentage': progress,
                'completed_count': completed_count,
                'total_lessons': course_lesson_count,
                'next_lesson': next_lesson,
                'module_count': enrollment.course.modules.count(),
            })

        # Real stats
        all_course_lessons = Lesson.objects.filter(module__course__enrollment__student=user)
        total_completed = LessonProgress.objects.filter(student=user, is_completed=True).count()
        total_course_lessons = all_course_lessons.count()
        overall_progress = int((total_completed / total_course_lessons) * 100) if total_course_lessons > 0 else 0

        last_quiz = QuizAttempt.objects.filter(student=user).order_by('-timestamp').first()
        avg_score = int(QuizAttempt.objects.filter(student=user).aggregate(avg=models.Avg('score'))['avg'] or 0)

        my_certificates = Certificate.objects.filter(student=user).select_related('course')

        # Real leaderboard — based on completed lessons + quiz scores
        from django.db.models import Count, Avg
        all_students = User.objects.filter(is_staff=False)
        leaderboard = []
        for s in all_students:
            lessons_done = LessonProgress.objects.filter(student=s, is_completed=True).count()
            avg_quiz = QuizAttempt.objects.filter(student=s).aggregate(avg=models.Avg('score'))['avg'] or 0
            xp = (lessons_done * 50) + int(avg_quiz * 10)
            leaderboard.append({
                'username': s.username,
                'initials': s.username[:2].upper(),
                'xp': xp,
                'is_me': s.id == user.id,
            })
        leaderboard.sort(key=lambda x: x['xp'], reverse=True)
        # Find current user rank
        my_rank = next((i+1 for i, s in enumerate(leaderboard) if s['is_me']), 0)

        # Real activity feed
        recent_lessons = LessonProgress.objects.filter(
            student=user, is_completed=True
        ).select_related('lesson__module__course').order_by('-updated_at')[:8]

        recent_quizzes = QuizAttempt.objects.filter(
            student=user
        ).select_related('quiz__lesson__module__course').order_by('-timestamp')[:5]

        # Merge and sort activity
        activity = []
        for lp in recent_lessons:
            activity.append({
                'type': 'lesson',
                'text': f'Completed <strong>{lp.lesson.title}</strong>',
                'course': lp.lesson.module.course.program,
                'time': lp.updated_at,
                'icon': '✅',
                'color': '#d1fae5',
            })
        for qa in recent_quizzes:
            activity.append({
                'type': 'quiz',
                'text': f'Scored <strong>{int(qa.score)}%</strong> on {qa.quiz.title}',
                'course': qa.quiz.lesson.module.course.program,
                'time': qa.timestamp,
                'icon': '📝',
                'color': '#e8f0fe',
            })
        activity.sort(key=lambda x: x['time'], reverse=True)
        activity = activity[:8]

        # Streak data
        streak, _ = StudentStreak.objects.get_or_create(student=user)

        # Courses eligible for review (completed but not yet reviewed)
        reviewable_courses = []
        for e in enrollments:
            if e['progress_percentage'] >= 100:
                already_reviewed = CourseReview.objects.filter(student=user, course=e['course']).exists()
                if not already_reviewed:
                    reviewable_courses.append(e['course'])

        pending_course_id = request.session.get('pending_course_id', '')
        has_paid = Subscription.objects.filter(student=user, status='active').exists()
        context = {
            'user': user,
            'enrollments': enrollments,
            'has_paid': has_paid,
            'overall_progress': overall_progress,
            'avg_score': avg_score,
            'total_completed': total_completed,
            'my_certificates': my_certificates,
            'activity': activity,
            'announcements': Announcement.objects.filter(is_active=True)[:3],
            'leaderboard': leaderboard[:10],
            'my_rank': my_rank,
            'pending_course_id': pending_course_id,
            'streak': streak,
            'reviewable_courses': reviewable_courses,
            'page': 'lms_student_dashboard'
        }
        return render(request, 'lms/dashboard.html', context)


# =========================================================================
# 3. INTERACTIVE LEARNING ENVIRONMENT CLASSROOM INTERFACES
# =========================================================================

@login_required(login_url='lms_login')
def course_classroom(request, course_id):
    enrollment = get_object_or_404(Enrollment, course_id=course_id, student=request.user)
    # Payment gate — must have active subscription
    if not request.user.is_staff:
        has_paid = Subscription.objects.filter(student=request.user, status='active').exists()
        if not has_paid:
            messages.warning(request, 'Please complete your payment to access course content.')
            return redirect('enroll_page', course_id=course_id)
    modules = Module.objects.filter(course_id=course_id).order_by('order').prefetch_related(Prefetch('lessons', queryset=Lesson.objects.order_by('order')))
    course_lessons = Lesson.objects.filter(module__course_id=course_id)
    total = course_lessons.count()
    completed = LessonProgress.objects.filter(
        student=request.user, lesson__in=course_lessons, is_completed=True
    ).count()
    progress = int((completed / total) * 100) if total > 0 else 0

    context = {
        'enrollment': enrollment,
        'course': enrollment.course,
        'modules': modules,
        'progress_percentage': progress,
        'completed': completed,
        'total': total,
        'page': 'lms_classroom'
    }
    return render(request, 'lms/classroom.html', context)

# Add this to lms/views.py
@login_required(login_url='lms_login')
def quiz_view(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    # Placeholder: replace with your actual quiz rendering logic
    return render(request, 'lms/quiz.html', {'quiz': quiz})
@login_required(login_url='lms_login')
def submit_quiz(request, quiz_id):
    if request.method == 'POST':
        quiz = get_object_or_404(Quiz, id=quiz_id)
        score = 0
        total = quiz.questions.count()
        results = []

        for question in quiz.questions.all():
            selected = request.POST.get(f'q{question.id}')

            if question.question_type == 'drag_drop_match':
                # selected is a JSON array like ["0","1","2"] - position i should equal i if correct
                correct = False
                try:
                    answer_list = json.loads(selected) if selected else []
                    pairs_count = len(question.match_data.get('pairs', []))
                    correct = (
                        len(answer_list) == pairs_count and
                        all(str(i) == str(answer_list[i]) for i in range(pairs_count))
                    )
                except Exception:
                    correct = False
            else:
                correct = selected == question.correct_answer

            if correct:
                score += 1
            results.append({
                'question': question,
                'selected': selected,
                'correct': correct,
            })

        percentage = int((score / total) * 100) if total > 0 else 0
        passed = percentage >= quiz.passing_score

        attempt = QuizAttempt.objects.create(
            student=request.user,
            quiz=quiz,
            score=percentage,
            passed=passed
        )

        # Log quiz activity
        StudentActivity.objects.create(
            student=request.user,
            activity_type='quiz_pass' if passed else 'quiz_fail',
            description=f'{"Passed" if passed else "Failed"} "{quiz.title}" with {int(percentage)}%',
            course=quiz.lesson.module.course,
            lesson=quiz.lesson
        )

        request.session[f'quiz_results_{attempt.id}'] = {
            'score': percentage,
            'passed': passed,
            'total': total,
            'correct': score,
            'results': [
                {
                    'text': r['question'].text,
                    'option_a': r['question'].option_a,
                    'option_b': r['question'].option_b,
                    'option_c': r['question'].option_c,
                    'option_d': r['question'].option_d,
                    'correct_answer': r['question'].correct_answer,
                    'selected': r['selected'],
                    'correct': r['correct'],
                }
                for r in results
            ]
        }
        return redirect('quiz_results', attempt_id=attempt.id)

    return redirect('quiz_view', quiz_id=quiz_id)


@login_required(login_url='lms_login')
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    results_data = request.session.get(f'quiz_results_{attempt_id}', None)
    context = {
        'attempt': attempt,
        'quiz': attempt.quiz,
        'results_data': results_data,
        'lesson': attempt.quiz.lesson,
    }
    return render(request, 'lms/quiz_results.html', context)


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Course, Module, Lesson, ContentItem, Quiz, QuizAttempt, LessonProgress

def lms_video_helper(url):
    """Extracts YouTube video ID and returns clean embed URL."""
    if not url: return ""
    import re
    # Extract video ID from any YouTube URL format
    patterns = [
        r'youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            video_id = match.group(1)
            return f"https://www.youtube.com/embed/{video_id}?rel=0&modestbranding=1"
    return url

@login_required(login_url='lms_login')
def lesson_view(request, lesson_id):
    # Payment gate
    if not request.user.is_staff:
        has_paid = Subscription.objects.filter(student=request.user, status='active').exists()
        if not has_paid:
            lesson = get_object_or_404(Lesson, id=lesson_id)
            course_id = lesson.module.course_id
            messages.warning(request, 'Please complete your payment to access course content.')
            return redirect('enroll_page', course_id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id)

    # Check enrollment
    course = lesson.module.course
    if not request.user.is_staff:
        enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
        if not enrolled:
            return redirect('lms_dashboard')

    # Get all lessons in order
    all_lessons = Lesson.objects.filter(
        module__course=course
    ).order_by('module__order', 'order')
    all_lessons_list = list(all_lessons)
    current_idx = next((i for i, l in enumerate(all_lessons_list) if l.id == lesson.id), 0)

    # Enforce lesson order — check previous lesson is completed
    if not request.user.is_staff and current_idx > 0:
        prev = all_lessons_list[current_idx - 1]
        prev_done = LessonProgress.objects.filter(
            student=request.user, lesson=prev, is_completed=True
        ).exists()
        if not prev_done:
            messages.warning(request, f'Please complete "{prev.title}" first.')
            return redirect('lesson_view', lesson_id=prev.id)

    content_payloads = ContentItem.objects.filter(lesson=lesson)
    for item in content_payloads:
        if item.content_type == 'youtube':
            item.video_url = lms_video_helper(item.video_url)

    # Get completed lessons for sidebar
    completed_ids = set(LessonProgress.objects.filter(
        student=request.user, is_completed=True,
        lesson__module__course=course
    ).values_list('lesson_id', flat=True))

    prev_lesson = all_lessons_list[current_idx - 1] if current_idx > 0 else None
    next_lesson = all_lessons_list[current_idx + 1] if current_idx < len(all_lessons_list) - 1 else None

    # Log lesson view activity
    if not request.user.is_staff:
        StudentActivity.objects.create(
            student=request.user,
            activity_type='lesson_view',
            description=f'Viewing: {lesson.title}',
            course=course,
            lesson=lesson
        )

    interactive_elements = InteractiveElement.objects.filter(lesson=lesson).order_by('order')
    for elem in interactive_elements:
        elem.data_json = json.dumps(elem.data)

    attached_elements = [e for e in interactive_elements if e.attached_to_id]
    standalone_elements = [e for e in interactive_elements if not e.attached_to_id]
    completed_element_ids = set()
    if not request.user.is_staff:
        completed_element_ids = set(InteractiveCompletion.objects.filter(
            student=request.user, element__lesson=lesson
        ).values_list('element_id', flat=True))

    context = {
        'lesson': lesson,
        'content_payloads': content_payloads,
        'quizzes': Quiz.objects.filter(lesson=lesson),
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
        'lesson_number': current_idx + 1,
        'total_lessons': len(all_lessons_list),
        'completed_ids': completed_ids,
        'discussions': Discussion.objects.filter(lesson=lesson, parent=None).prefetch_related('replies__user').select_related('user'),
        'interactive_elements': standalone_elements,
        'attached_elements': attached_elements,
        'completed_element_ids': completed_element_ids,
        'page': 'lms_lesson'
    }
    return render(request, 'lms/lesson.html', context)


@login_required(login_url='lms_login')
def complete_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)

    progress_obj, created = LessonProgress.objects.get_or_create(
        student=request.user,
        lesson=lesson,
        defaults={'is_completed': True}
    )
    if not created and not progress_obj.is_completed:
        progress_obj.is_completed = True
        progress_obj.save()

    # Log completion activity
    StudentActivity.objects.create(
        student=request.user,
        activity_type='lesson_complete',
        description=f'Completed: {lesson.title}',
        course=lesson.module.course,
        lesson=lesson
    )

    # Check if entire course is now complete
    course = lesson.module.course
    total = Lesson.objects.filter(module__course=course).count()
    completed = LessonProgress.objects.filter(
        student=request.user,
        lesson__module__course=course,
        is_completed=True
    ).count()

    cert_issued = False
    if total > 0 and completed >= total:
        # Auto-issue certificate
        code = f"CERT-{course.program}-" + ''.join(random.choices(string.digits, k=6))
        cert, created_cert = Certificate.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'certificate_code': code}
        )
        if created_cert:
            cert_issued = True

    return JsonResponse({
        'status': 'success',
        'cert_issued': cert_issued,
        'course_title': course.title if cert_issued else ''
    })




from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages

@login_required
def account_settings(request):
    from lms.models import LessonProgress, Enrollment, Certificate
    if request.method == 'POST':
        user = request.user
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()
        messages.success(request, "Profile updated successfully!")
        return redirect('account_settings')

    total_completed = LessonProgress.objects.filter(student=request.user, is_completed=True).count()
    total_enrolled = Enrollment.objects.filter(student=request.user).count()
    total_certs = Certificate.objects.filter(student=request.user).count()

    context = {
        'total_completed': total_completed,
        'total_enrolled': total_enrolled,
        'total_certs': total_certs,
    }
    return render(request, 'lms/settings.html', context)






# ── Add this view to lms/views.py ─────────────────────────────────────────

@login_required(login_url='lms_login')
def course_builder(request):
    """The Course Builder page — create or edit a course."""
    if not request.user.is_staff:
        return redirect('lms_dashboard')

    import json as _json
    edit_id = request.GET.get('edit')
    edit_course = None
    edit_structure = '[]'

    if edit_id:
        edit_course = get_object_or_404(Course, id=edit_id)
        structure = []
        for module in edit_course.modules.all().order_by('order'):
            lessons = [{'title': l.title} for l in module.lessons.all().order_by('order')]
            structure.append({'title': module.title, 'lessons': lessons})
        edit_structure = _json.dumps(structure)

    students_profiles = []
    for s in User.objects.filter(is_staff=False):
        students_profiles.append({'user_obj': s})

    context = {
        'students_profiles': students_profiles,
        'page': 'course_builder',
        'edit_course': edit_course,
        'edit_structure': edit_structure,
    }
    return render(request, 'lms/course_builder.html', context)

# ── Add this action inside lms_dashboard_view, inside the if user.is_staff block ──
# Find the section: # --- BASE CURRICULUM STRUCTURAL DATA BLOCKS ---
# Add this AFTER the existing create_course / create_module / create_lesson actions:





# ══════════════════════════════════════════════════════════════
# ADD TO TOP OF lms/views.py (with other imports)
# ══════════════════════════════════════════════════════════════


import os
import mimetypes
from django.http import HttpResponse, Http404, StreamingHttpResponse, JsonResponse
from django.conf import settings

@login_required(login_url='lms_login')
def serve_protected_content(request, content_id):
    content = get_object_or_404(ContentItem, id=content_id)
    if not request.user.is_staff:
        course = content.lesson.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            raise Http404
    if not content.file_attachment:
        raise Http404
    file_path = content.file_attachment.path
    if not os.path.exists(file_path):
        raise Http404
    mime_type, _ = mimetypes.guess_type(file_path)
    if not mime_type:
        mime_type = 'application/octet-stream'
    def file_iterator(path, chunk_size=8192):
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
    response = StreamingHttpResponse(file_iterator(file_path), content_type=mime_type)
    response['Content-Disposition'] = 'inline'
    response['X-Content-Type-Options'] = 'nosniff'
    response['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response['X-Frame-Options'] = 'SAMEORIGIN'
    return response


@login_required(login_url='lms_login')
def serve_slide(request, content_id, slide_index):
    content = get_object_or_404(ContentItem, id=content_id)
    if not request.user.is_staff:
        course = content.lesson.module.course
        if not Enrollment.objects.filter(student=request.user, course=course).exists():
            raise Http404
    slide_path = os.path.join(
        settings.MEDIA_ROOT, 'slides', str(content_id), f'slide_{slide_index}.png'
    )
    if not os.path.exists(slide_path):
        raise Http404
    with open(slide_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='image/png')
        response['Content-Disposition'] = 'inline'
        response['Cache-Control'] = 'private, max-age=3600'
        response['X-Frame-Options'] = 'SAMEORIGIN'
        return response


@login_required(login_url='lms_login')
def get_slide_count(request, content_id):
    content = get_object_or_404(ContentItem, id=content_id)
    slides_dir = os.path.join(settings.MEDIA_ROOT, 'slides', str(content_id))
    if not os.path.exists(slides_dir):
        return JsonResponse({'count': 0})
    count = len([f for f in os.listdir(slides_dir) if f.endswith('.png')])
    return JsonResponse({'count': count})


def convert_ppt_to_images(content_item):
    """
    Converts PPT/PPTX to PNG images using LibreOffice.
    Full fidelity — preserves backgrounds, images, fonts, colors.
    """
    import subprocess
    import shutil
    from pdf2image import convert_from_path

    file_path = content_item.file_attachment.path
    slides_dir = os.path.join(settings.MEDIA_ROOT, 'slides', str(content_item.id))
    os.makedirs(slides_dir, exist_ok=True)

    # Step 1: Convert PPT to PDF using LibreOffice
    tmp_dir = os.path.join(settings.MEDIA_ROOT, 'tmp_convert')
    os.makedirs(tmp_dir, exist_ok=True)

    result = subprocess.run([
        'soffice',
        '--headless',
        '--convert-to', 'pdf',
        '--outdir', tmp_dir,
        file_path
    ], capture_output=True, text=True, timeout=120)

    # Find the generated PDF
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    pdf_path = os.path.join(tmp_dir, base_name + '.pdf')

    if not os.path.exists(pdf_path):
        raise Exception(f"LibreOffice conversion failed: {result.stderr}")

    # Step 2: Convert PDF pages to PNG images
    images = convert_from_path(pdf_path, dpi=150, fmt='png')

    for i, img in enumerate(images):
        slide_path = os.path.join(slides_dir, f'slide_{i}.png')
        img.save(slide_path, 'PNG', quality=95)

    # Cleanup temp PDF
    os.remove(pdf_path)

    return len(images)


@login_required(login_url='lms_login')
def check_quiz_pass(request, quiz_id):
    """Check if student has passed a quiz — used by lesson completion lock."""
    passed = QuizAttempt.objects.filter(
        student=request.user, quiz_id=quiz_id, passed=True
    ).exists()
    return JsonResponse({'passed': passed})


@login_required(login_url='lms_login')
def download_certificate(request, cert_id):
    """Generates and serves a professional PDF certificate."""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape, A4
    from reportlab.lib.colors import HexColor
    from reportlab.lib.units import inch
    from django.http import HttpResponse
    import io

    cert = get_object_or_404(Certificate, id=cert_id, student=request.user)

    buffer = io.BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    # Background
    c.setFillColor(HexColor('#0f172a'))
    c.rect(0, 0, w, h, fill=1, stroke=0)

    # Gold border
    c.setStrokeColor(HexColor('#d97706'))
    c.setLineWidth(3)
    c.rect(30, 30, w-60, h-60, fill=0, stroke=1)
    c.setLineWidth(1)
    c.rect(38, 38, w-76, h-76, fill=0, stroke=1)

    # Header — Glory Nursing
    c.setFillColor(HexColor('#d97706'))
    c.setFont('Helvetica-Bold', 13)
    c.drawCentredString(w/2, h-80, 'GLORY NURSING HEALTHCARE TRAINING SCHOOL')

    c.setFillColor(HexColor('#94a3b8'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h-98, 'Oklahoma City, Oklahoma · State-Approved Vocational Institution')

    # Divider
    c.setStrokeColor(HexColor('#d97706'))
    c.setLineWidth(0.5)
    c.line(w/2-180, h-112, w/2+180, h-112)

    # Certificate of Completion
    c.setFillColor(HexColor('#ffffff'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(w/2, h-140, 'CERTIFICATE OF COMPLETION')

    # Student name
    c.setFillColor(HexColor('#f8fafc'))
    c.setFont('Helvetica-Bold', 38)
    c.drawCentredString(w/2, h-195, cert.student.get_full_name() or cert.student.username)

    # Line under name
    c.setStrokeColor(HexColor('#334155'))
    c.setLineWidth(1)
    c.line(w/2-220, h-205, w/2+220, h-205)

    # Body text
    c.setFillColor(HexColor('#94a3b8'))
    c.setFont('Helvetica', 11)
    c.drawCentredString(w/2, h-228, 'has successfully completed all requirements for the program')

    # Course name
    c.setFillColor(HexColor('#d97706'))
    c.setFont('Helvetica-Bold', 22)
    c.drawCentredString(w/2, h-262, cert.course.title.upper())

    # Program badge
    c.setFillColor(HexColor('#1e3a5f'))
    c.roundRect(w/2-40, h-292, 80, 22, 5, fill=1, stroke=0)
    c.setFillColor(HexColor('#60a5fa'))
    c.setFont('Helvetica-Bold', 10)
    c.drawCentredString(w/2, h-283, cert.course.program)

    # Date and cert ID
    from datetime import date
    c.setFillColor(HexColor('#64748b'))
    c.setFont('Helvetica', 10)
    c.drawCentredString(w/2, h-318, f'Issued: {date.today().strftime("%B %d, %Y")}  ·  Certificate ID: {cert.certificate_code}')

    # Signature lines
    sig_y = 95
    sig_gap = 160
    for label, title in [('Charles Mensah', 'Co-Founder & Director'), ('Binui Mensah', 'Co-Founder & Administrator')]:
        x = w/2 - sig_gap if label == 'Charles Mensah' else w/2 + sig_gap
        c.setStrokeColor(HexColor('#334155'))
        c.setLineWidth(0.8)
        c.line(x-70, sig_y+18, x+70, sig_y+18)
        c.setFillColor(HexColor('#f1f5f9'))
        c.setFont('Helvetica-Bold', 10)
        c.drawCentredString(x, sig_y+6, label)
        c.setFillColor(HexColor('#64748b'))
        c.setFont('Helvetica', 9)
        c.drawCentredString(x, sig_y-6, title)

    # Seal
    c.setFillColor(HexColor('#d97706'))
    c.circle(w/2, sig_y+10, 28, fill=1, stroke=0)
    c.setFillColor(HexColor('#0f172a'))
    c.circle(w/2, sig_y+10, 24, fill=1, stroke=0)
    c.setFillColor(HexColor('#d97706'))
    c.setFont('Helvetica-Bold', 7)
    c.drawCentredString(w/2, sig_y+14, 'GLORY')
    c.drawCentredString(w/2, sig_y+6, 'NURSING')
    c.setFont('Helvetica', 6)
    c.drawCentredString(w/2, sig_y-2, '✦ CERTIFIED ✦')

    c.save()
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="certificate_{cert.certificate_code}.pdf"'
    return response


@login_required(login_url='lms_login')
def lms_search(request):
    query = request.GET.get('q', '').strip()
    results = {'lessons': [], 'courses': []}

    if query:
        # Search lessons
        from django.db.models import Q
        lessons = Lesson.objects.filter(
            Q(title__icontains=query) | Q(module__title__icontains=query),
            module__course__enrollment__student=request.user
        ).select_related('module__course').distinct()[:10]

        courses = Course.objects.filter(
            Q(title__icontains=query) | Q(program__icontains=query),
            enrollment__student=request.user
        ).distinct()[:5]

        results['lessons'] = lessons
        results['courses'] = courses

    return render(request, 'lms/search_results.html', {
        'query': query,
        'results': results,
    })


@login_required(login_url='lms_login')
def lesson_discussion(request, lesson_id):
    """AJAX — post a discussion message or reply."""
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        parent_id = request.POST.get('parent_id')
        if message:
            parent = None
            if parent_id:
                try:
                    parent = Discussion.objects.get(id=parent_id)
                except Discussion.DoesNotExist:
                    pass
            Discussion.objects.create(
                lesson=lesson,
                user=request.user,
                message=message,
                parent=parent
            )
    return redirect('lesson_view', lesson_id=lesson_id)


# ══════════════════════════════════════════════════════════════
# SQUARE PAYMENT FLOW
# ══════════════════════════════════════════════════════════════

def generic_payment(request):
    """Generic payment page — collect name, email, amount, reason and process payment."""
    from dotenv import load_dotenv
    load_dotenv()
    if request.method == 'POST':
        import uuid
        nonce = request.POST.get('nonce', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        amount_str = request.POST.get('amount', '0').strip()
        reason = request.POST.get('reason', '').strip()

        if not all([nonce, first_name, email, amount_str, reason]):
            messages.error(request, 'Please fill in all required fields.')
            return redirect('generic_payment')

        try:
            amount = int(float(amount_str) * 100)
            if amount < 100:
                messages.error(request, 'Minimum payment is $1.00.')
                return redirect('generic_payment')
        except ValueError:
            messages.error(request, 'Invalid amount.')
            return redirect('generic_payment')

        try:
            from square import Square
            from square.environment import SquareEnvironment
            env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
            sq_env = SquareEnvironment.SANDBOX if env == 'sandbox' else SquareEnvironment.PRODUCTION
            client = Square(token=os.environ.get('SQUARE_ACCESS_TOKEN'), environment=sq_env)

            result = client.payments.create(
                source_id=nonce,
                idempotency_key=str(uuid.uuid4()),
                amount_money={'amount': amount, 'currency': 'USD'},
                location_id=os.environ.get('SQUARE_LOCATION_ID'),
                buyer_email_address=email,
                note=f"Payment from {first_name} {last_name} — {reason}",
            )

            payment = getattr(result, 'payment', None)
            success = (payment and hasattr(payment, 'id')) or (not (hasattr(result, 'errors') and result.errors))

            if success:
                # Send confirmation email to payer
                try:
                    from django.core.mail import EmailMessage
                    EmailMessage(
                        subject='Payment Received — Glory Nursing',
                        body=f"""Hi {first_name},

Your payment of ${float(amount_str):.2f} has been received successfully.

Payment Details:
- Name: {first_name} {last_name}
- Email: {email}
- Amount: ${float(amount_str):.2f}
- Reason: {reason}

Thank you for your payment. If you have any questions, contact us at glorynursing@yahoo.com or (405) 968-5004.

Glory Nursing Healthcare Training School""",
                        from_email=None,
                        to=[email],
                    ).send()
                    EmailMessage(
                        subject=f'New Payment Received — {first_name} {last_name}',
                        body=f"""A payment has been received through the Glory Nursing website.

Name: {first_name} {last_name}
Email: {email}
Phone: {phone}
Amount: ${float(amount_str):.2f}
Reason: {reason}

Glory Nursing Online Portal""",
                        from_email=None,
                        to=['glorynursing@yahoo.com'],
                    ).send()
                except Exception as e:
                    print(f"Email error: {e}")

                messages.success(request, f'Payment of ${float(amount_str):.2f} received successfully! A confirmation has been sent to {email}.')
                return redirect('generic_payment_success')
            else:
                errors = getattr(result, 'errors', [])
                error_msg = errors[0].detail if errors else 'Payment failed. Please try again.'
                messages.error(request, error_msg)
                return redirect('generic_payment')

        except Exception as e:
            messages.error(request, f'Payment error: {str(e)}')
            return redirect('generic_payment')

    context = {
        'square_app_id': os.environ.get('SQUARE_APP_ID', ''),
        'location_id': os.environ.get('SQUARE_LOCATION_ID', ''),
        'square_env': os.environ.get('SQUARE_ENVIRONMENT', 'sandbox'),
    }
    return render(request, 'lms/generic_payment.html', context)


def generic_payment_success(request):
    return render(request, 'lms/generic_payment_success.html')


def enroll_page(request, course_id):
    """Public enrollment page — student enters details and pays."""
    # Allow logged-in students with existing enrollment to proceed directly
    if not request.session.get('application_submitted'):
        if request.user.is_authenticated and not request.user.is_staff:
            # Check if student has a pending enrollment for this course
            if Enrollment.objects.filter(student=request.user, course_id=course_id).exists():
                pass  # Allow through
            else:
                messages.warning(request, 'Please submit your application form first.')
                return redirect('programs')
        elif not request.user.is_authenticated:
            messages.warning(request, 'Please log in to complete your enrollment.')
            return redirect('lms_login')
    from dotenv import load_dotenv
    load_dotenv()
    course = get_object_or_404(Course, id=course_id, is_published=True)
    context = {
        'course': course,
        'square_app_id': os.environ.get('SQUARE_APP_ID', ''),
        'location_id': os.environ.get('SQUARE_LOCATION_ID', ''),
        'square_env': os.environ.get('SQUARE_ENVIRONMENT', 'sandbox'),
    }
    return render(request, 'lms/enroll.html', context)


def process_payment(request, course_id):
    """Processes Square payment, creates account, enrolls student."""
    if request.method != 'POST':
        return redirect('enroll_page', course_id=course_id)

    course = get_object_or_404(Course, id=course_id)
    nonce = request.POST.get('nonce')
    first_name = request.POST.get('first_name', '').strip()
    last_name = request.POST.get('last_name', '').strip()
    email = request.POST.get('email', '').strip()
    phone = request.POST.get('phone', '').strip()

    if not all([nonce, first_name, email]):
        messages.error(request, "Please fill in all required fields.")
        return redirect('enroll_page', course_id=course_id)

    # Check if email already registered — allow if user is already logged in
    if not request.user.is_authenticated and User.objects.filter(email=email).exists():
        messages.error(request, "An account with this email already exists. Please log in.")
        return redirect('lms_login')

    try:
        from dotenv import load_dotenv
        load_dotenv()
        from square import Square
        from square.environment import SquareEnvironment

        env = os.environ.get('SQUARE_ENVIRONMENT', 'sandbox')
        sq_env = SquareEnvironment.SANDBOX if env == 'sandbox' else SquareEnvironment.PRODUCTION

        client = Square(
            token=os.environ.get('SQUARE_ACCESS_TOKEN'),
            environment=sq_env
        )
        addon_total = float(request.POST.get("addon_total", 0) or 0)
        pay_amount = float(request.POST.get("pay_amount", 0) or 0)
        payment_plan = request.POST.get("payment_plan", "full")
        # Use pay_amount if provided, otherwise fall back to full price + addon
        if pay_amount > 0:
            amount = int(pay_amount * 100)  # Convert to cents
        else:
            amount = int((float(course.price) + addon_total) * 100)

        result = client.payments.create(
            source_id=nonce,
            idempotency_key=f"{email}-{course_id}-{random.randint(10000,99999)}",
            amount_money={
                'amount': amount,
                'currency': 'USD'
            },
            location_id=os.environ.get('SQUARE_LOCATION_ID'),
            buyer_email_address=email,
            note=f"Enrollment: {course.title} - {first_name} {last_name}",
        )

        # New Square SDK returns response directly, check for payment object
        payment = getattr(result, 'payment', None)
        if payment and hasattr(payment, 'id'):
            result_success = True
        elif hasattr(result, 'errors') and result.errors:
            result_success = False
        else:
            result_success = True

        if result_success:
            # Payment successful — create student account
            username = email.split('@')[0] + str(random.randint(100, 999))
            while User.objects.filter(username=username).exists():
                username = email.split('@')[0] + str(random.randint(100, 999))

            pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            new_user = User.objects.create_user(
                username=username,
                email=email,
                password=pwd,
                first_name=first_name,
                last_name=last_name
            )

            # Enroll in course
            Enrollment.objects.create(student=new_user, course=course)

            # Create subscription record
            Subscription.objects.create(
                student=new_user,
                tier_name=course.program,
                amount_paid=course.price,
                status='active'
            )

            # Notify Glory Nursing of new enrollment
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject=f'New Enrollment: {first_name} {last_name} — {course.title}',
                    message=f"""A new student has enrolled and paid through the website.

Student Details:
Name: {first_name} {last_name}
Email: {email}
Phone: {phone}
Course: {course.title} ({course.program})
Amount Paid: ${pay_amount if pay_amount > 0 else course.price} ({payment_plan} payment plan)
Username: {username}

Login to the admin dashboard to view their enrollment:
https://glorynursingok.com/lms/dashboard/

Glory Nursing Online Portal""",
                    from_email=None,
                    recipient_list=['glorynursing@yahoo.com'],
                    fail_silently=True,
                )
            except Exception:
                pass

            # Send credentials email
            try:
                from django.core.mail import send_mail
                send_mail(
                    subject=f'Welcome to Glory Nursing — Your Login Credentials',
                    message=f"""Hi {first_name},

Welcome to Glory Nursing Healthcare Training School!

Your payment was successful. Here are your login details:

Course: {course.title}
Username: {username}
Password: {pwd}

Login at: https://glorynursingok.com/lms/login/

Please change your password after your first login.

Glory Nursing Healthcare Training School
Oklahoma City, Oklahoma""",
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=True,
                )
            except Exception:
                pass

            # Log activity
            StudentActivity.objects.create(
                student=new_user,
                activity_type='login',
                description=f'Enrolled in {course.title} via payment',
                course=course
            )

            # Store success info in session
            request.session['enrollment_success'] = {
                'name': first_name,
                'course': course.title,
                'username': username,
                'email': email,
            }
            return redirect('enrollment_success')

        else:
            errors = getattr(result, 'errors', None)
            if errors:
                error_msg = errors[0].detail if hasattr(errors[0], 'detail') else str(errors[0])
            else:
                error_msg = "Payment failed. Please try again."
            messages.error(request, f"Payment failed: {error_msg}")
            return redirect('enroll_page', course_id=course_id)

    except Exception as e:
        messages.error(request, f"Payment error: {str(e)}")
        return redirect('enroll_page', course_id=course_id)


def enrollment_success(request):
    """Success page shown after payment."""
    data = request.session.pop('enrollment_success', None)
    if not data:
        return redirect('lms_login')
    return render(request, 'lms/enrollment_success.html', {'data': data})


def get_revenue_report():
    """Generate revenue report grouped by month and by course."""
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    from datetime import datetime, timedelta

    subscriptions = Subscription.objects.all()

    # Total revenue
    total_revenue = subscriptions.aggregate(total=Sum('amount_paid'))['total'] or 0
    total_enrollments = subscriptions.count()

    # Revenue by month (last 12 months)
    monthly = (
        subscriptions
        .annotate(month=TruncMonth('started_at'))
        .values('month')
        .annotate(revenue=Sum('amount_paid'), count=Count('id'))
        .order_by('-month')[:12]
    )
    monthly_data = [
        {
            'month': m['month'].strftime('%b %Y') if m['month'] else 'Unknown',
            'revenue': float(m['revenue'] or 0),
            'count': m['count'],
        }
        for m in monthly
    ]

    # Revenue by program/course
    by_program = (
        subscriptions
        .values('tier_name')
        .annotate(revenue=Sum('amount_paid'), count=Count('id'))
        .order_by('-revenue')
    )
    program_data = [
        {
            'program': p['tier_name'],
            'revenue': float(p['revenue'] or 0),
            'count': p['count'],
        }
        for p in by_program
    ]

    # This month vs last month
    now = datetime.now()
    this_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_month_start = (this_month_start - timedelta(days=1)).replace(day=1)

    this_month_revenue = subscriptions.filter(started_at__gte=this_month_start).aggregate(t=Sum('amount_paid'))['t'] or 0
    last_month_revenue = subscriptions.filter(started_at__gte=last_month_start, started_at__lt=this_month_start).aggregate(t=Sum('amount_paid'))['t'] or 0

    return {
        'total_revenue': float(total_revenue),
        'total_enrollments': total_enrollments,
        'monthly': monthly_data,
        'by_program': program_data,
        'this_month': float(this_month_revenue),
        'last_month': float(last_month_revenue),
    }


def log_audit(request, user, action, target_model='', target_id='', target_repr='', details=''):
    """Helper to create an audit log entry."""
    try:
        ip = request.META.get('REMOTE_ADDR', None)
        AuditLog.objects.create(
            user=user,
            action=action,
            target_model=target_model,
            target_id=str(target_id),
            target_repr=target_repr,
            details=details,
            ip_address=ip,
        )
    except Exception as e:
        print(f"Audit log error: {e}")


@login_required(login_url='lms_login')
def setup_2fa(request):
    """Allow staff to enable/disable 2FA (TOTP) on their account."""
    if not request.user.is_staff:
        return redirect('lms_dashboard')

    from django_otp.plugins.otp_totp.models import TOTPDevice
    from django_otp import devices_for_user
    import qrcode
    import qrcode.image.svg
    from io import BytesIO
    import base64

    device = TOTPDevice.objects.filter(user=request.user, name='default').first()

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'enable':
            token = request.POST.get('token', '').strip()
            if device and device.verify_token(token):
                device.confirmed = True
                device.save()
                log_audit(request, request.user, '2fa_enabled', target_repr=f'{request.user.username} enabled 2FA')
                return render(request, 'lms/setup_2fa.html', {'success': '2FA enabled successfully!', 'device': device, 'confirmed': True})
            else:
                return render(request, 'lms/setup_2fa.html', {'error': 'Invalid code. Please try again.', 'device': device, 'qr_code': _get_qr(device, request.user), 'confirmed': False})

        elif action == 'disable':
            if device:
                device.delete()
                log_audit(request, request.user, '2fa_disabled', target_repr=f'{request.user.username} disabled 2FA')
            return render(request, 'lms/setup_2fa.html', {'success': '2FA disabled.', 'device': None, 'confirmed': False})

    # GET request
    if not device:
        device = TOTPDevice.objects.create(user=request.user, name='default', confirmed=False)

    if device.confirmed:
        return render(request, 'lms/setup_2fa.html', {'device': device, 'confirmed': True})

    qr_code = _get_qr(device, request.user)
    return render(request, 'lms/setup_2fa.html', {'device': device, 'qr_code': qr_code, 'confirmed': False})


def _get_qr(device, user):
    import qrcode
    from io import BytesIO
    import base64
    url = device.config_url
    img = qrcode.make(url)
    buf = BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode()


@login_required(login_url='lms_login')
def submit_review(request):
    """Student submits a course review."""
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        course = Course.objects.filter(id=course_id).first()
        if course and rating:
            CourseReview.objects.update_or_create(
                student=request.user,
                course=course,
                defaults={'rating': int(rating), 'comment': comment, 'is_approved': False}
            )
    return redirect('lms_dashboard')


@login_required(login_url='lms_login')
def complete_interactive(request, element_id):
    """Mark an interactive element as completed, award XP."""
    if request.method == 'POST':
        element = get_object_or_404(InteractiveElement, id=element_id)
        data = json.loads(request.body) if request.body else {}
        score = data.get('score', 0)

        InteractiveCompletion.objects.update_or_create(
            student=request.user,
            element=element,
            defaults={'score': score}
        )
        return JsonResponse({'status': 'success', 'points': element.points})
    return JsonResponse({'error': 'POST required'}, status=400)


@login_required(login_url='lms_login')
def lesson_content_items(request, lesson_id):
    """API: return content items for a lesson (for admin builder)."""
    items = ContentItem.objects.filter(lesson_id=lesson_id).values('id', 'title', 'content_type')
    return JsonResponse({'items': list(items)})
