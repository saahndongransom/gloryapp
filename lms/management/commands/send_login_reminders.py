from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.contrib.auth.models import User
from lms.models import StudentStreak, Enrollment
from datetime import date, timedelta


class Command(BaseCommand):
    help = 'Sends reminder emails to students who have not logged in for several days'

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7, help='Days of inactivity before sending reminder')

    def handle(self, *args, **options):
        days_threshold = options['days']
        cutoff_date = date.today() - timedelta(days=days_threshold)

        # Students with active enrollments
        students = User.objects.filter(is_staff=False, enrollment__isnull=False).distinct()

        sent_count = 0
        skipped_count = 0

        for student in students:
            streak, _ = StudentStreak.objects.get_or_create(student=student)

            # Skip if active recently
            if streak.last_active_date and streak.last_active_date >= cutoff_date:
                skipped_count += 1
                continue

            # Skip if no email
            if not student.email:
                skipped_count += 1
                continue

            # Get their enrollments for personalization
            enrollments = Enrollment.objects.filter(student=student).select_related('course')
            course_names = ', '.join([e.course.title for e in enrollments]) or 'your program'

            days_inactive = (date.today() - streak.last_active_date).days if streak.last_active_date else 'several'

            try:
                send_mail(
                    subject="We miss you at Glory Nursing! Continue your training",
                    message=f"""Hi {student.first_name or student.username},

We noticed you haven't logged into your Glory Nursing student portal in {days_inactive} days.

Your progress in {course_names} is waiting for you! Consistency is key to completing your certification on time.

Log in now to continue: http://127.0.0.1:8000/lms/login/

Need help? Contact us:
Phone: (405) 968-5004
Email: glorynursing@yahoo.com

Glory Nursing Healthcare Training School
12032 N Pennsylvania Ave, Oklahoma City, OK 73120""",
                    from_email=None,
                    recipient_list=[student.email],
                    fail_silently=False,
                )
                sent_count += 1
                self.stdout.write(f"Sent reminder to {student.username} ({student.email}) - inactive {days_inactive} days")
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Failed to send to {student.email}: {e}"))

        self.stdout.write(self.style.SUCCESS(f"\nDone! Sent {sent_count} reminders, skipped {skipped_count} active students."))
