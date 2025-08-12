import logging
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Student, Doctor
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

# Set up logging
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name']

class StudentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Student
        fields = ['id', 'user', 'name', 'mobile', 'national_id', 'sec_num']

class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ['id', 'user', 'name', 'mobile', 'national_id', 'role']

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        logger.debug("Generated token for user: %s", user.username)
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        logger.debug("Validating token for user: %s", user.username)

        if hasattr(user, 'student'):
            student = user.student
            structure = getattr(student, 'structure', None)
            data['userType'] = 'Student'
            data['fullName'] = student.name
            data['nationalId'] = student.national_id
            data['academicYear'] = structure.get_year_display() if structure else None
            data['department'] = structure.get_department_display() if structure else None
            logger.info("Token validated for student: %s", user.username)

        elif hasattr(user, 'doctor'):
            doctor = user.doctor
            data['userType'] = 'Staff'
            data['fullName'] = doctor.name
            data['nationalId'] = doctor.national_id
            structures = doctor.structures.all()
            data['academicYear'] = [s.get_year_display() for s in structures]
            data['department'] = [s.get_department_display() for s in structures]
            logger.info("Token validated for doctor: %s", user.username)

        else:
            data['userType'] = 'Other'
            logger.warning("User %s has no associated student or doctor", user.username)

        return data


from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed

class CustomCookieTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        print("COOKIES:", request.COOKIES)  # ← هل في فعلاً refresh؟
        refresh_token = request.COOKIES.get('refresh')
        if not refresh_token:
            raise AuthenticationFailed('No refresh token provided in cookies.')

        serializer = self.get_serializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception:
            raise AuthenticationFailed('Invalid or expired refresh token.')

        access_token = serializer.validated_data.get('access')
        return Response({'access': access_token}, status=status.HTTP_200_OK)
