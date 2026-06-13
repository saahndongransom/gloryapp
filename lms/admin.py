# lms/admin.py
from django.contrib import admin
from .models import Course, Module, Lesson, Enrollment, InteractiveElement, InteractiveCompletion

# Register your main courses
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'program', 'is_published')
    search_fields = ('title',)

# Register course modules
@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'order')
    list_filter = ('course',)
    ordering = ('course', 'order')

# Register individual lessons
@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ('title', 'module', 'order')
    list_filter = ('module__course', 'module')
    ordering = ('module', 'order')

# Register student enrollments with the matching fields
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    # 'student' and 'enrolled_at' match your actual lms/models.py file fields!
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course',)
    search_fields = ('student__username', 'student__email', 'course__title')

@admin.register(InteractiveElement)
class InteractiveElementAdmin(admin.ModelAdmin):
    list_display = ('title', 'lesson', 'element_type', 'order', 'points')
    list_filter = ('element_type', 'lesson__module__course')
    search_fields = ('title',)


@admin.register(InteractiveCompletion)
class InteractiveCompletionAdmin(admin.ModelAdmin):
    list_display = ('student', 'element', 'score', 'completed_at')
    list_filter = ('element__element_type',)
