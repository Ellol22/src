from django.db import models
from django.utils import timezone
from accounts.models import Student
from courses.models import Course

# جلسة المحاضرة اللي الدكتور بيسجلها
class LectureSession(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    date = models.DateField(default=timezone.now)
    is_open_for_attendance = models.BooleanField(default=False)
    qr_session_started_at = models.DateTimeField(null=True, blank=True)
    
    # ✅ الحقل الجديد
    building_code = models.CharField(max_length=5, blank=True, null=True, help_text="أدخل حرف المبنى أو رمز القاعة (مثلاً: D105 أو B)")

    def __str__(self):
        return f"{self.course.name} - {self.title} ({self.date})"


# سجل الحضور لكل طالب في كل محاضرة
class Attendance(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
    status_choices = [
        ('present', 'Present'),
        ('absent', 'Absent'),
    ]
    status = models.CharField(max_length=10, choices=status_choices, default='absent')
    failed_face_attempts = models.PositiveIntegerField(default=0)
    face_updated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.name} - {self.lecture} - {self.get_status_display()}"

# جلسة الـ QR Code الخاصة بمحاضرة معينة
class CodeSession(models.Model):
    lecture = models.ForeignKey(LectureSession, on_delete=models.CASCADE, null=True, blank=True)
    qr_code_data = models.TextField(blank=True,null=True)  # base64 image
    qr_text = models.CharField(max_length=255, blank=True, null=True)  # ✅ النص الحقيقي للكود
    created_at = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)

    def is_expired(self):
        return (timezone.now() - self.created_at).total_seconds() > 60

    def __str__(self):
        return f"{self.lecture} | QR Code | Time: {self.created_at.strftime('%H:%M:%S')}"
