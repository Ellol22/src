from django.contrib import admin
from .models import UploadFile

@admin.register(UploadFile)
class UploadFileAdmin(admin.ModelAdmin):
    list_display = ['id', 'file', 'get_course', 'uploaded_by', 'uploaded_at']
    search_fields = ['file', 'course__name', 'uploaded_by__username']
    list_filter = ['course', 'uploaded_at']

    def get_course(self, obj):
        return obj.course.name if obj.course else "-"
    get_course.short_description = 'Course'
