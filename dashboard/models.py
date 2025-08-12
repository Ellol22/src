import os
from django.db import models
from accounts.models import Student  # استدعي الموديل بتاع الطالب
from django.contrib.auth.models import User

def dynamic_image_upload(instance, filename):
    name, extension = os.path.splitext(filename)
    extension = extension.lstrip('.')

    if instance.student:
        return f"student-image/{instance.student.user.username}.{extension}"
    elif instance.doctor:
        return f"doctor-image/{instance.doctor.user.username}.{extension}"
    return f"others/{name}.{extension}"


from accounts.models import Student, Doctor  # ✅ استدعي Doctor

class Dash(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, null=True, blank=True)
    doctor = models.OneToOneField(Doctor, on_delete=models.CASCADE, null=True, blank=True)
    image = models.ImageField(upload_to=dynamic_image_upload, null=True, blank=True)

    
##################################################################################


class Announcement(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
    

##################################################################################
# notifications/models.py
from django.db import models
from accounts.models import Doctor, Student
from courses.models import Course

class Notifications(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name='sent_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.course.name}"
