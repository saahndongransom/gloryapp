# lms/models.py
from django.db import models
from django.contrib.auth.models import User

# --- CORE CATALOGS ---
class Course(models.Model):
    title = models.CharField(max_length=255)
    program = models.CharField(max_length=100)  # e.g., CNA, NCLEX
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    description = models.TextField(blank=True, default='')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return f"{self.program} - {self.title}"

class Module(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.program} -> {self.title}"

class Lesson(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    order = models.IntegerField(default=1)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class ContentItem(models.Model):
    TYPE_CHOICES = [
        ('pdf', 'PDF Document'),
        ('ppt', 'PowerPoint Presentation'),
        ('word', 'Word Document'),
        ('youtube', 'YouTube Embedded Video'),
        ('video', 'Direct Video File'),
        ('text', 'Text / Rich Content'),
    ]
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='contents')
    title = models.CharField(max_length=255)
    content_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    file_attachment = models.FileField(upload_to='lms_contents/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True)
    text_content = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"[{self.get_content_type_display()}] {self.title}"

# --- ADVANCED MODULE 1: TESTING ENGINE ---
class Quiz(models.Model):
    lesson = models.OneToOneField(Lesson, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=255)
    passing_score = models.IntegerField(default=70)
    time_limit = models.IntegerField(default=0, help_text="Minutes. 0 = no limit.")

    def __str__(self):
        return self.title

class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('image_choice', 'Image + Multiple Choice'),
        ('drag_drop_match', 'Drag & Drop Matching'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    text = models.TextField()
    image = models.ImageField(upload_to='quiz_images/', blank=True, null=True)

    # Standard multiple choice / image choice fields
    option_a = models.CharField(max_length=255, blank=True)
    option_b = models.CharField(max_length=255, blank=True)
    option_c = models.CharField(max_length=255, blank=True)
    option_d = models.CharField(max_length=255, blank=True)
    correct_answer = models.CharField(max_length=1, choices=[('A','A'),('B','B'),('C','C'),('D','D')], blank=True)

    # Drag & drop matching: JSON structure
    # {"pairs": [{"left": "Term A", "right": "Definition A"}, {"left": "Term B", "right": "Definition B"}]}
    match_data = models.JSONField(default=dict, blank=True)

class QuizAttempt(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    score = models.IntegerField()  # Percentage integer e.g., 85
    passed = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

# --- ADVANCED MODULE 2: REAL-TIME ANALYTICS TRACKER ---
class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'lesson')

# --- ADVANCED MODULE 3: CERTIFICATES LEDGER ---
class Certificate(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    certificate_code = models.CharField(max_length=100, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)

# --- ADVANCED MODULE 4: INTERACTIVE DISCUSSION Q&A ---
class StudentActivity(models.Model):
    """Tracks every student action for admin monitoring."""
    ACTIVITY_TYPES = [
        ('login', 'Logged In'),
        ('lesson_view', 'Viewed Lesson'),
        ('lesson_complete', 'Completed Lesson'),
        ('quiz_attempt', 'Attempted Quiz'),
        ('quiz_pass', 'Passed Quiz'),
        ('quiz_fail', 'Failed Quiz'),
        ('certificate', 'Earned Certificate'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=30, choices=ACTIVITY_TYPES)
    description = models.CharField(max_length=300)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True, blank=True)
    lesson = models.ForeignKey('Lesson', on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} — {self.activity_type}"


class Discussion(models.Model):
    lesson = models.ForeignKey('Lesson', on_delete=models.CASCADE, related_name='lesson_discussions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.user.username}: {self.message[:50]}"


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class SupportThread(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='discussions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

# --- FINANCIALS & ACCESS MAPS ---
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

class Subscription(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    tier_name = models.CharField(max_length=100, default="Premium Full Access")
    amount_paid = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, default='active')
    started_at = models.DateTimeField(auto_now_add=True)



class SupportTicket(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='tickets')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Ticket from {self.user.username} on {self.lesson.title}"

class AuditLog(models.Model):
    """Tracks admin actions for security and accountability."""
    ACTION_CHOICES = [
        ('login', 'Admin Login'),
        ('login_failed', 'Failed Login Attempt'),
        ('create', 'Created Record'),
        ('update', 'Updated Record'),
        ('delete', 'Deleted Record'),
        ('grade', 'Graded Submission'),
        ('enroll', 'Enrolled Student'),
        ('2fa_enabled', '2FA Enabled'),
        ('2fa_disabled', '2FA Disabled'),
        ('other', 'Other Action'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='audit_logs')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='other')
    target_model = models.CharField(max_length=100, blank=True)  # e.g. "Student", "Course"
    target_id = models.CharField(max_length=50, blank=True)
    target_repr = models.CharField(max_length=255, blank=True)  # human-readable description
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user} - {self.get_action_display()} - {self.target_repr} - {self.timestamp}"


class CourseReview(models.Model):
    """Student reviews/ratings for courses."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='course_reviews')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='reviews')
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])  # 1-5 stars
    comment = models.TextField(blank=True)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.rating}★"


class StudentStreak(models.Model):
    """Tracks daily login streaks for gamification."""
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name='streak')
    current_streak = models.IntegerField(default=0)
    longest_streak = models.IntegerField(default=0)
    last_active_date = models.DateField(null=True, blank=True)
    total_active_days = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.student.username} - {self.current_streak} day streak"

    def update_streak(self):
        """Call this on each login to update streak data."""
        from datetime import date, timedelta
        today = date.today()

        if self.last_active_date == today:
            return  # Already counted today

        if self.last_active_date == today - timedelta(days=1):
            # Consecutive day
            self.current_streak += 1
        elif self.last_active_date is None or self.last_active_date < today - timedelta(days=1):
            # Streak broken or first login
            self.current_streak = 1

        self.total_active_days += 1
        if self.current_streak > self.longest_streak:
            self.longest_streak = self.current_streak

        self.last_active_date = today
        self.save()


class InteractiveElement(models.Model):
    """Interactive learning elements embedded within lessons."""
    TYPE_CHOICES = [
        ('flashcards', 'Flashcard Deck'),
        ('knowledge_check', 'Quick Knowledge Check'),
        ('scenario', 'Clinical Scenario'),
        ('drag_drop', 'Drag & Drop Labeling'),
    ]

    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='interactive_elements')
    title = models.CharField(max_length=255)
    element_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    order = models.IntegerField(default=1)
    # If set, this element appears as a popup right after this content item is viewed.
    # If null, it appears inline at the end of the lesson content.
    attached_to = models.ForeignKey(
        ContentItem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='interactive_triggers',
        help_text="Show as a popup after this content item is completed. Leave blank to show at end of lesson."
    )

    # JSON field stores type-specific data structure
    # flashcards: [{"front": "...", "back": "..."}, ...]
    # knowledge_check: {"question": "...", "options": [...], "correct": 0, "explanation": "..."}
    # scenario: {"situation": "...", "choices": [{"text": "...", "outcome": "...", "is_best": true}]}
    # drag_drop: {"image_url": "...", "labels": [{"text": "...", "x": 10, "y": 20}]}
    data = models.JSONField(default=dict)

    points = models.IntegerField(default=10)  # XP awarded on completion

    def __str__(self):
        return f"[{self.get_element_type_display()}] {self.title}"


class InteractiveCompletion(models.Model):
    """Tracks student completion of interactive elements for XP/gamification."""
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='interactive_completions')
    element = models.ForeignKey(InteractiveElement, on_delete=models.CASCADE)
    completed_at = models.DateTimeField(auto_now_add=True)
    score = models.IntegerField(default=0)  # for knowledge checks / scenarios

    class Meta:
        unique_together = ('student', 'element')

    def __str__(self):
        return f"{self.student.username} - {self.element.title}"
