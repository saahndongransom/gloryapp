from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

urlpatterns = [
    path('login/', views.lms_login_view, name='lms_login'),
    path('logout/', views.lms_logout_view, name='lms_logout'),
    path('2fa/setup/', views.setup_2fa, name='setup_2fa'),
    path('review/submit/', views.submit_review, name='submit_review'),
    path('interactive/<int:element_id>/complete/', views.complete_interactive, name='complete_interactive'),
    path('lesson/<int:lesson_id>/content-items/', views.lesson_content_items, name='lesson_content_items'),
    path('dashboard/', views.lms_dashboard_view, name='lms_dashboard'),
    path('classroom/<int:course_id>/', views.course_classroom, name='course_classroom'),
    path('lesson/<int:lesson_id>/', views.lesson_view, name='lesson_view'),
    path('lesson/<int:lesson_id>/complete/', views.complete_lesson, name='complete_lesson'),
    # Add this line to your urlpatterns in lms/urls.py
    path('quiz/<int:quiz_id>/', views.quiz_view, name='quiz_view'),
    # Add this line to lms/urls.py
    path('quiz/<int:quiz_id>/submit/', views.submit_quiz, name='submit_quiz'),
    path('quiz/results/<int:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('certificate/<int:cert_id>/download/', views.download_certificate, name='download_certificate'),
    path('search/', views.lms_search, name='lms_search'),
    path('pay/', views.generic_payment, name='generic_payment'),
    path('pay/success/', views.generic_payment_success, name='generic_payment_success'),
    path('enroll/<int:course_id>/', views.enroll_page, name='enroll_page'),
    path('enroll/<int:course_id>/pay/', views.process_payment, name='process_payment'),
    path('enroll/success/', views.enrollment_success, name='enrollment_success'),
    path('quiz/<int:quiz_id>/check-pass/', views.check_quiz_pass, name='check_quiz_pass'),
    path('lesson/<int:lesson_id>/discuss/', views.lesson_discussion, name='lesson_discussion'),
    path('password-reset/', auth_views.PasswordResetView.as_view(
        template_name='lms/password_reset.html',
        email_template_name='lms/password_reset_email.html',
        success_url=reverse_lazy('password_reset_done'),
    ), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='lms/password_reset_done.html',
    ), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='lms/password_reset_confirm.html',
        success_url=reverse_lazy('password_reset_complete'),
    ), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='lms/password_reset_complete.html',
    ), name='password_reset_complete'),

    path('settings/', views.account_settings, name='account_settings'),
   # path('password/', auth_views.PasswordChangeView.as_view(template_name='lms/password_change.html'), name='password_change'),
   path('password/', auth_views.PasswordChangeView.as_view(
        template_name='lms/password_change.html',
        success_url=reverse_lazy('account_settings') # Redirect back to settings after success
    ), name='password_change'),
    # Add this line to lms/urls.py inside urlpatterns:

    path('course-builder/', views.course_builder, name='course_builder'),
    # Add these lines to lms/urls.py inside urlpatterns:

    path('content/<int:content_id>/serve/', views.serve_protected_content, name='serve_content'),
    path('content/<int:content_id>/slide/<int:slide_index>/', views.serve_slide, name='serve_slide'),
    path('content/<int:content_id>/slide-count/', views.get_slide_count, name='slide_count'),

]


