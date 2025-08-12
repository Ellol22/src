# upload_center/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('doctor/subjects/', views.doctor_courses_view, name='teacher_subjects'),
    path('doctor/files/', views.teacher_upload_file_view, name='teacher_upload_file'),
    path('student/subjects/', views.student_courses_view, name='student_subjects'),
    path('student/files/', views.student_files_view, name='student_files'),
]