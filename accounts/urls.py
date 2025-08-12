from django.urls import path
from .views import (
    api_sign_up,
    CustomTokenObtainPairView,
    activate_user,
    api_logout,
    api_forgot_password,
    api_reset_password,
    get_user_type,
)
from .serializers import CustomCookieTokenRefreshView

urlpatterns = [
    path('signup/', api_sign_up, name='sign_up'),
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', CustomCookieTokenRefreshView.as_view(), name='token_refresh'),
    path('activate/<str:uidb64>/<str:token>/', activate_user, name='activate'),
    path('logout/', api_logout, name='logout'),
    path('forgot-password/', api_forgot_password, name='forgot_password'),
    path('reset-password/', api_reset_password, name='reset_password'),
    path('get-user-type/', get_user_type, name='get_user_type'),
    path('user/', get_user_type, name='get_user_type'),
]
