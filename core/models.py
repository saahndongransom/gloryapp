from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class ApplicationRecord(models.Model):
    student_email = models.EmailField()
    full_name = models.CharField(max_length=200)
    program = models.CharField(max_length=100)
    pdf_file = models.FileField(upload_to='applications/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-submitted_at']

    def __str__(self):
        return f"{self.full_name} - {self.program} - {self.submitted_at.strftime('%Y-%m-%d')}"

class ClassSchedule(models.Model):
    program = models.ForeignKey('Program', on_delete=models.CASCADE, related_name='schedules_list')
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    days = models.CharField(max_length=100, help_text="e.g. Mon-Fri, Mon/Wed/Fri")
    seats_total = models.IntegerField(default=15)
    seats_filled = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['start_date']

    def __str__(self):
        return f"{self.program.short} — {self.start_date}"

    @property
    def seats_available(self):
        return self.seats_total - self.seats_filled

    @property
    def is_full(self):
        return self.seats_filled >= self.seats_total


class Program(models.Model):
    is_online = models.BooleanField(default=False, help_text="Online/Hybrid program with LMS access")
    price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, help_text="Program price (overrides course price)")
    CATEGORY_CHOICES = [
        ('nursing', 'Nursing'),
        ('allied_health', 'Allied Health'),
        ('life_support', 'Life Support'),
    ]

    title = models.CharField(max_length=200)
    short = models.CharField(max_length=20, help_text="Short name e.g. CNA, CMA")
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=10, default='🏥', help_text="Emoji icon")
    image = models.ImageField(upload_to='programs/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='nursing')
    duration = models.CharField(max_length=50, help_text="e.g. 2–4 Weeks")
    hours = models.CharField(max_length=50, help_text="e.g. 77 Clock Hours")
    description = models.TextField()
    schedules = models.TextField(help_text="One schedule per line e.g. Weekday Classes")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0, help_text="Display order")
    course = models.ForeignKey('lms.Course', null=True, blank=True, on_delete=models.SET_NULL, related_name='programs', help_text="Link to LMS course for enrollment")

    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Program'
        verbose_name_plural = 'Programs'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def get_schedules_list(self):
        return [s.strip() for s in self.schedules.splitlines() if s.strip()]


class BlogPost(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    excerpt = models.TextField(max_length=300, help_text="Short summary shown on homepage")
    content = models.TextField()
    published_date = models.DateField(default=timezone.now)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['-published_date']
        verbose_name = 'Blog Post'
        verbose_name_plural = 'Blog Posts'

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    event_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField(blank=True, null=True)
    location = models.CharField(max_length=300, blank=True)
    registration_open = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['event_date', 'start_time']
        verbose_name = 'Event'
        verbose_name_plural = 'Events'

    def __str__(self):
        return f"{self.title} – {self.event_date}"

class ApplicationDocument(models.Model):
    DOCUMENT_TYPES = [
        ('national_id', 'National ID Card'),
        ('ssn_card', 'Social Security Card'),
        ('diploma', 'High School Diploma / GED'),
        ('immunization', 'Immunization Records'),
        ('tb_test', 'TB Test Results'),
        ('background_check', 'Background Check'),
        ('other', 'Other Document'),
    ]

    full_name = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    program = models.CharField(max_length=20, blank=True, help_text="e.g. CNA, CMA")
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='applicant_documents/%Y/%m/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Application Document'
        verbose_name_plural = 'Application Documents'

    def __str__(self):
        return f"{self.full_name or 'Anonymous'} – {self.get_document_type_display()}"
