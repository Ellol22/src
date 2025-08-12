from django.contrib import admin
from .models import Dash, Announcement, Notifications
from accounts.models import Doctor, Student  # عشان تظهر أسماء المستخدمين

@admin.register(Dash)
class DashAdmin(admin.ModelAdmin):
    list_display = ['id', 'get_student_username', 'get_doctor_username', 'image']
    list_filter = ['student', 'doctor']
    
    def get_student_username(self, obj):
        return obj.student.user.username if obj.student else "-"
    get_student_username.short_description = 'Student Username'

    def get_doctor_username(self, obj):
        return obj.doctor.user.username if obj.doctor else "-"
    get_doctor_username.short_description = 'Doctor Username'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'created_by', 'created_at']
    search_fields = ['title', 'content']
    list_filter = ['created_at']


@admin.register(Notifications)
class NotificationsAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'course', 'sender', 'created_at']
    search_fields = ['title', 'message']
    list_filter = ['course', 'created_at']
