from django.db import models
from django.contrib.auth.models import User
from courses.models import Course  # لو الكورسيس في نفس الابلكيشن، أو عدل المسار حسب مكانه
from django.utils.timezone import now

def upload_to_course_folder(instance, filename):
    # ناخد اسم الكورس ونشيله من أي مسافات / أحرف غريبة
    course_name = instance.course.name.replace(' ', '_') if instance.course else 'unknown_course'
    return f'materials/{course_name}/{filename}'


class UploadFile(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='uploaded_files',blank=True,null=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.FileField(upload_to=upload_to_course_folder)
    uploaded_at = models.DateTimeField(auto_now_add=True)  # تاريخ الرفع تلقائي

    def __str__(self):
        return f"{self.file.name} ({self.course.name})"
