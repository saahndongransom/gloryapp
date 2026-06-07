from django.contrib import admin

# Register your models here.


from django.contrib import admin
from .models import Program



from django.contrib import admin
from .models import Program, BlogPost, Event


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
