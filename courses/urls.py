from django.urls import path
from .views import DepartmentCoursesView

urlpatterns = [
    path('regulations', DepartmentCoursesView.as_view(), name='department-courses'),
]
