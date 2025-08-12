from django.contrib import admin
from .models import LectureSession, Attendance, CodeSession  # ✅ ضيف CodeSession هنا

@admin.register(LectureSession)
class LectureSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'title', 'date', 'is_open_for_attendance', 'building_code')
    list_filter = ('course', 'date', 'is_open_for_attendance', 'building_code')
    search_fields = ('course__name', 'title', 'building_code')
    ordering = ('-date',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'lecture', 'status', 'failed_face_attempts', 'face_updated')
    list_filter = ('status', 'lecture__course', 'face_updated')
    search_fields = ('student__name', 'lecture__title', 'lecture__course__name')
    ordering = ('-lecture__date', 'student__name')

# ✅ رجّع تسجيل CodeSession
@admin.register(CodeSession)
class CodeSessionAdmin(admin.ModelAdmin):
    list_display = ('lecture', 'created_at', 'is_active', 'expired_status')
    list_filter = ('is_active', 'lecture__course')
    search_fields = ('lecture__title', 'lecture__course__name')
    ordering = ('-created_at',)

    def expired_status(self, obj):
        return obj.is_expired()
    expired_status.boolean = True
    expired_status.short_description = 'Expired?'
