from django.contrib import admin
from django.utils.html import format_html
from .models import Program, BlogPost, Event


@admin.register(ApplicationRecord)
class ApplicationRecordAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'student_email', 'program', 'submitted_at', 'download_pdf')
    list_filter = ('program',)
    search_fields = ('full_name', 'student_email')
    ordering = ('-submitted_at',)

    def download_pdf(self, obj):
        if obj.pdf_file:
            return format_html('<a href="/media/{}" target="_blank" class="button">⬇ Download PDF</a>', obj.pdf_file)
        return 'No PDF'
    download_pdf.short_description = 'PDF'

@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ['short', 'title', 'category', 'duration', 'hours', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'short', 'description']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Basic Info', {'fields': ('title', 'short', 'slug', 'icon', 'image', 'category')}),
        ('Details',    {'fields': ('duration', 'hours', 'description', 'schedules')}),
        ('Enrollment', {'fields': ('course',), 'description': 'Link this program to an LMS course so students can enroll and pay directly.'}),
        ('Display',    {'fields': ('order', 'is_active')}),
    )


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ['title', 'published_date', 'is_published']
    list_editable = ['is_published']
    list_filter = ['is_published', 'published_date']
    search_fields = ['title', 'excerpt', 'content']
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        ('Post Info', {'fields': ('title', 'slug', 'image', 'published_date', 'is_published')}),
        ('Content',   {'fields': ('excerpt', 'content')}),
    )


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_date', 'start_time', 'end_time', 'registration_open', 'is_active']
    list_editable = ['registration_open', 'is_active']
    list_filter = ['is_active', 'registration_open', 'event_date']
    search_fields = ['title', 'description', 'location']
    fieldsets = (
        ('Event Info', {'fields': ('title', 'event_date', 'start_time', 'end_time', 'location')}),
        ('Details',    {'fields': ('description', 'registration_open', 'is_active')}),
    )