from django.db import models
from django.utils.text import slugify
from django.utils import timezone


class Program(models.Model):
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
