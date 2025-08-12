from django.contrib import admin
from .models import Quiz, QuizQuestion, QuizSubmission, Assignment, AssignmentFile, Submission

class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 1
    fields = ('text', 'options', 'correct_option')
    readonly_fields = ('options',)

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'start_time', 'end_time', 'created_by', 'created_at')
    list_filter = ('course', 'created_by', 'start_time')
    search_fields = ('title', 'course__name')
    inlines = [QuizQuestionInline]
    raw_id_fields = ('course', 'created_by')
    date_hierarchy = 'start_time'

@admin.register(QuizQuestion)
class QuizQuestionAdmin(admin.ModelAdmin):
    list_display = ('text_preview', 'quiz', 'correct_option')
    search_fields = ('text', 'quiz__title')
    list_filter = ('quiz',)
    raw_id_fields = ('quiz',)

    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = 'Question Text'

@admin.register(QuizSubmission)
class QuizSubmissionAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'grade', 'status', 'submitted_at', 'feedback_preview')
    list_filter = ('quiz', 'status')
    search_fields = ('student__user__username', 'quiz__title')
    raw_id_fields = ('student', 'quiz')
    readonly_fields = ('answers', 'submitted_at')
    date_hierarchy = 'submitted_at'

    def feedback_preview(self, obj):
        return obj.feedback[:50] + '...' if obj.feedback and len(obj.feedback) > 50 else obj.feedback
    feedback_preview.short_description = 'Feedback'

class AssignmentFileInline(admin.TabularInline):
    model = AssignmentFile
    extra = 1
    fields = ('file', 'uploaded_at')
    readonly_fields = ('uploaded_at',)

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'deadline', 'created_by', 'created_at')
    list_filter = ('course', 'created_by', 'deadline')
    search_fields = ('title', 'course__name')
    inlines = [AssignmentFileInline]
    raw_id_fields = ('course', 'created_by')  # ✅ شيلنا assigned_to
    date_hierarchy = 'deadline'

@admin.register(AssignmentFile)
class AssignmentFileAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'quiz', 'file', 'uploaded_at')
    list_filter = ('assignment', 'quiz')
    search_fields = ('assignment__title', 'quiz__title')
    raw_id_fields = ('assignment', 'quiz')
    readonly_fields = ('uploaded_at',)

@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'student', 'grade', 'submitted_at', 'feedback_preview')
    list_filter = ('assignment',)
    search_fields = ('assignment__title', 'student__user__username')
    raw_id_fields = ('assignment', 'student')
    readonly_fields = ('submitted_at', 'answer_html')
    date_hierarchy = 'submitted_at'

    def feedback_preview(self, obj):
        return obj.feedback[:50] + '...' if obj.feedback and len(obj.feedback) > 50 else obj.feedback
    feedback_preview.short_description = 'Feedback'
