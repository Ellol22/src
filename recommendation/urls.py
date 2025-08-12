from django.urls import path
from .views import recommend_department

urlpatterns = [
    path('', recommend_department, name='recommendation_api'),
]
