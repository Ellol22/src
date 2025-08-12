from django.urls import path
from grades import views

urlpatterns = [
    path('student/', views.my_grades, name='my_grades'),
    path('doctor_courses/', views.doctor_courses, name='doctor_courses'),
    path('doctor/<int:course_id>/', views.manage_course_grades, name='doctor_grades'),
    path("top-students/", views.top_students_by_section_year, name="top-students"),
    path("doctor-statistics/", views.doctor_courses_statistics, name="doctor-statistics"),
    path('doctor/<int:course_id>/upload/', views.import_grades_api, name='import_grades_api'),
]