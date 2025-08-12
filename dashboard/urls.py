from django.urls import path
from .views import personal_info ,announcement_api
from .views import get_doctor_courses, send_notification, student_notifications

urlpatterns = [
    path('pers-info/', personal_info, name='pers-info'),
    path('announcements/', announcement_api, name='announcements'),                # بدون ID ← GET, POST
    path('announcements/<int:id>/', announcement_api, name='announcement-detail'), # مع ID ← GET (لو عايزة), PUT, DELETE
    path('notification/', send_notification, name='notification-list'),                  # GET, POST
    path('notification/<int:id>/', send_notification, name='notification-detail'),       # GET (واحدة), PUT, DELETE
    path('notification/student/', student_notifications, name='student-notifications'),
    path('staff/courses/', get_doctor_courses, name='doctor-courses'),
]
