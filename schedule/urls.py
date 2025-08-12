from django.urls import path
from .views import student_schedule, doctor_schedule

urlpatterns = [
    path('student/', student_schedule, name='student-schedule'),
    path('doctor/', doctor_schedule, name='doctor-schedule'),
]