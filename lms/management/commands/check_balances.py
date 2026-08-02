from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from lms.models import Subscription
from django.core.mail import EmailMessage

class Command(BaseCommand):
    help = "Check outstanding balances and block/remind students"

    def handle(self, *args, **options):
        today = timezone.now().date()
        
        # Block access for overdue payments
        overdue = Subscription.objects.filter(
            payment_plan__in=["half", "custom"],
            payment_due_date__lt=today,
            amount_due__gt=0,
            access_blocked=False,
            status="active"
        )
        for sub in overdue:
            sub.access_blocked = True
            sub.status = "suspended"
            sub.save()
            # Email student
            try:
                EmailMessage(
                    subject="Your Glory Nursing Course Access Has Been Suspended",
                    body=f"""Dear {sub.student.get_full_name() or sub.student.username},

Your course access has been suspended due to an outstanding balance of ${sub.amount_due}.

Your payment was due on {sub.payment_due_date}.

Please complete your payment immediately to restore access:
https://glorynursingok.com/lms/pay/?name={sub.student.get_full_name()}&email={sub.student.email}&amount={sub.amount_due}

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School""",
                    from_email=None,
                    to=[sub.student.email],
                ).send()
                self.stdout.write(f"Suspended: {sub.student.email}")
            except Exception as e:
                self.stdout.write(f"Email error: {e}")

        # Send reminder 7 days before due
        reminder_date = today + timedelta(days=7)
        reminders = Subscription.objects.filter(
            payment_plan__in=["half", "custom"],
            payment_due_date=reminder_date,
            amount_due__gt=0,
            access_blocked=False,
            status="active"
        )
        for sub in reminders:
            try:
                EmailMessage(
                    subject="Reminder: Balance Due in 7 Days - Glory Nursing",
                    body=f"""Dear {sub.student.get_full_name() or sub.student.username},

This is a reminder that your outstanding balance of ${sub.amount_due} is due on {sub.payment_due_date}.

Please complete your payment to avoid course suspension:
https://glorynursingok.com/lms/pay/?name={sub.student.get_full_name()}&email={sub.student.email}&amount={sub.amount_due}

Questions? Call us at (405) 968-5004 or email glorynursing@yahoo.com

Glory Nursing Healthcare Training School""",
                    from_email=None,
                    to=[sub.student.email],
                ).send()
                self.stdout.write(f"Reminded: {sub.student.email}")
            except Exception as e:
                self.stdout.write(f"Email error: {e}")

        # Send reminder 3 days before due
        reminder_date3 = today + timedelta(days=3)
        reminders3 = Subscription.objects.filter(
            payment_plan__in=["half", "custom"],
            payment_due_date=reminder_date3,
            amount_due__gt=0,
            access_blocked=False,
            status="active"
        )
        for sub in reminders3:
            try:
                EmailMessage(
                    subject="URGENT: Balance Due in 3 Days - Glory Nursing",
                    body=f"""Dear {sub.student.get_full_name() or sub.student.username},

URGENT: Your outstanding balance of ${sub.amount_due} is due in 3 days on {sub.payment_due_date}.

Pay now to keep your course access:
https://glorynursingok.com/lms/pay/?name={sub.student.get_full_name()}&email={sub.student.email}&amount={sub.amount_due}

Glory Nursing Healthcare Training School""",
                    from_email=None,
                    to=[sub.student.email],
                ).send()
                self.stdout.write(f"Urgent reminder: {sub.student.email}")
            except Exception as e:
                self.stdout.write(f"Email error: {e}")

        self.stdout.write(self.style.SUCCESS(f"Done. Suspended: {overdue.count()}, Reminded: {reminders.count() + reminders3.count()}"))
