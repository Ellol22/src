import json
import logging
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate, get_user_model
from accounts.serializers import CustomTokenObtainPairSerializer
from .models import DoctorRole, Student, Doctor
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

# Set up logging
logger = logging.getLogger(__name__)

def validate_email_format(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

User = get_user_model()
import json
import traceback
import logging
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.password_validation import validate_password, ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import User, Student, Doctor, DoctorRole

logger = logging.getLogger(__name__)

@csrf_exempt
@api_view(['POST'])
def api_sign_up(request):
    try:
        try:
            logger.info("🔵 Incoming SIGNUP request data:\n%s", json.dumps(request.data, indent=2))
        except Exception:
            logger.warning("❗ Could not parse request.data as JSON:\n%s", str(request.data))

        data = request.data

        username = data.get('username')
        password = data.get('password')
        user_type = data.get('user_type')
        national_id = data.get('national_id')
        email = data.get('email')
        name = data.get('fullname')
        mobile = data.get('mobile', '')
        sec_num = data.get('sec_num', None)
        role = data.get('staff_role', 'subject_doctor')

        if not all([username, password, user_type, national_id, email, name]):
            logger.error("❌ Missing required fields")
            response_data = {
                'error': 'All required fields (username, password, userType, nationalId, email, fullname) must be provided.'
            }
            logger.info("🔴 Signup response:\n%s", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if not validate_email_format(email):
            logger.error("❌ Invalid email format: %s", email)
            response_data = {'error': 'Invalid email format.'}
            logger.info("🔴 Signup response:\n%s", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(password)
        except ValidationError as e:
            logger.error("❌ Password validation error: %s", e.messages)
            response_data = {'error': e.messages}
            logger.info("🔴 Signup response:\n%s", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            logger.error("❌ Username already exists: %s", username)
            response_data = {'error': 'Username is already taken.'}
            logger.info("🔴 Signup response:\n%s", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

        if user_type == 'student':
            try:
                student = Student.objects.get(national_id=national_id)
                if student.user:
                    logger.error("❌ Student already linked to user: %s", national_id)
                    response_data = {'error': 'This national ID is already registered with a Student account.'}
                    logger.info("🔴 Signup response:\n%s", response_data)
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
                user.is_active = False
                user.save()
                logger.info("✅ Created user for student: %s", username)

                student.user = user
                student.mobile = mobile or student.mobile
                if sec_num is not None:
                    try:
                        student.sec_num = int(sec_num)
                    except ValueError:
                        logger.error("❌ sec_num is not an integer: %s", sec_num)
                        response_data = {'error': 'sec_num must be an integer.'}
                        logger.info("🔴 Signup response:\n%s", response_data)
                        return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                student.save()
                logger.info("✅ Linked student to user: %s", national_id)

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                activation_link = f"{settings.SITE_DOMAIN}/accounts/activate/{uid}/{token}/"
                logger.info("📧 Activation link: %s", activation_link)

                send_mail(
                    subject="Activate your account ✉",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"Your account has been created.\n"
                        f"Username: {username}\n"
                        f"Password: {password}\n\n"
                        f"⚠ Please activate your account:\n{activation_link}\n\n"
                        f"Thank you."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info("📨 Activation email sent to: %s", user.email)

                response_data = {'message': 'Student account created successfully. Check your email to activate.'}
                logger.info("🟢 Signup response:\n%s", response_data)
                return Response(response_data, status=status.HTTP_201_CREATED)

            except Student.DoesNotExist:
                logger.error("❌ Student not found with national ID: %s", national_id)
                response_data = {'error': 'National ID not found in the student database.'}
                logger.info("🔴 Signup response:\n%s", response_data)
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        elif user_type == 'staff':
            try:
                doctor = Doctor.objects.get(national_id=national_id)
                if doctor.user:
                    logger.error("❌ Doctor already linked to user: %s", national_id)
                    response_data = {'error': 'This national ID is already registered with a Doctor account.'}
                    logger.info("🔴 Signup response:\n%s", response_data)
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

                if role not in dict(DoctorRole.choices):
                    logger.warning("⚠ Invalid role: %s. Defaulting to 'subject_doctor'", role)
                    role = 'subject_doctor'

                if role == DoctorRole.ADMIN_DOCTOR and (not request.user.is_authenticated or not request.user.is_superuser):
                    logger.error("❌ Unauthorized to create admin_doctor. User: %s", request.user)
                    response_data = {'error': 'Only admins can create admin doctor accounts.'}
                    logger.info("🔴 Signup response:\n%s", response_data)
                    return Response(response_data, status=status.HTTP_403_FORBIDDEN)

                user = User.objects.create_user(username=username, password=password, email=email, first_name=name)
                if role == DoctorRole.ADMIN_DOCTOR:
                    user.is_staff = True
                    user.is_superuser = True

                user.is_active = False
                user.save()
                logger.info("✅ Created user for doctor: %s", username)

                doctor.user = user
                doctor.role = role
                doctor.mobile = mobile or doctor.mobile
                doctor.save()
                logger.info("✅ Linked doctor to user: %s", national_id)

                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)
                activation_link = f"{settings.SITE_DOMAIN}/accounts/activate/{uid}/{token}/"
                logger.info("📧 Activation link: %s", activation_link)

                send_mail(
                    subject="Activate your account ✉",
                    message=(
                        f"Hello {user.username},\n\n"
                        f"Your account has been created.\n"
                        f"Username: {username}\n"
                        f"Password: {password}\n\n"
                        f"⚠ Please activate your account:\n{activation_link}\n\n"
                        f"Thank you."
                    ),
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info("📨 Activation email sent to: %s", user.email)

                response_data = {'message': 'Doctor account created successfully. Check your email to activate.'}
                logger.info("🟢 Signup response:\n%s", response_data)
                return Response(response_data, status=status.HTTP_201_CREATED)

            except Doctor.DoesNotExist:
                logger.error("❌ Doctor not found with national ID: %s", national_id)
                response_data = {'error': 'National ID not found in the doctor database.'}
                logger.info("🔴 Signup response:\n%s", response_data)
                return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        else:
            logger.error("❌ Invalid userType: %s", user_type)
            response_data = {'error': 'Invalid userType. Must be \"Student\" or \"Staff\".'}
            logger.info("🔴 Signup response:\n%s", response_data)
            return Response(response_data, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.exception("💥 Unhandled exception in signup:\n%s", traceback.format_exc())
        response_data = {'error': 'Something went wrong. Please try again later.'}
        logger.info("🔴 Signup response:\n%s", response_data)
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




# login
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)

        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        refresh_token = data.get('refresh')

        # إعداد الـ response مع البيانات
        response = Response(data, status=status.HTTP_200_OK)

        # ✅ ضيف الكوكي هنا
        response.set_cookie(
            key='refresh',
            value=refresh_token,
            httponly=True,
            secure=True,  # يستخدم secure فقط في production
            samesite='None',
            path='/',
        )

        return response



@csrf_exempt
class CustomTokenRefreshView(TokenRefreshView):
    pass  # No customization needed unless you want to add extra logic

@api_view(['GET'])
def activate_user(request, uidb64, token):
    logger.debug("Activation attempt with uid: %s and token: %s", uidb64, token)
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        logger.error("Activation error: %s", str(e))
        return Response({'error': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)

    if user and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        logger.info("User %s activated successfully", user.username)
        return Response({'message': 'Account activated successfully.'}, status=status.HTTP_200_OK)
    else:
        logger.error("Invalid or expired activation link")
        return Response({'error': 'Invalid or expired activation link.'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def api_logout(request):
    logger.debug("Logout request received")
    try:
        refresh_token = request.data.get('refresh')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
            logger.info("Refresh token blacklisted successfully")
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error("Error during logout: %s", str(e))
        return Response({'message': 'Logged out successfully.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def api_forgot_password(request):
    email = request.data.get('email')
    logger.debug("Password reset requested for email: %s", email)

    if not validate_email_format(email):
        logger.error("Invalid email format: %s", email)
        return Response({'error': 'Invalid email format.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        logger.debug("Password reset link: %s", reset_link)

        send_mail(
            subject="Reset your password",
            message=f"Hello {user.username},\nPlease use the following link to reset your password:\n{reset_link}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("Sent password reset email to %s", email)
        return Response({'message': 'Password reset link sent to your email.'}, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        logger.error("Email not found: %s", email)
        return Response({'error': 'Email not found.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def api_reset_password(request):
    uidb64 = request.data.get('uid')
    token = request.data.get('token')
    new_password = request.data.get('password')
    logger.debug("Password reset attempt with uid: %s and token: %s", uidb64, token)

    if not uidb64 or not token or not new_password:
        logger.error("Missing required fields for password reset")
        return Response({'error': 'UID, token, and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError, OverflowError) as e:
        logger.error("Reset password error: %s", str(e))
        return Response({'error': 'Invalid reset link.'}, status=status.HTTP_400_BAD_REQUEST)

    if not default_token_generator.check_token(user, token):
        logger.error("Invalid or expired reset token")
        return Response({'error': 'Invalid or expired reset token.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        validate_password(new_password)
    except ValidationError as e:
        logger.error("Password validation error: %s", e.messages)
        return Response({'error': e.messages}, status=status.HTTP_400_BAD_REQUEST)

    user.set_password(new_password)
    user.save()
    logger.info("Password reset successfully for user %s", user.username)
    return Response({'message': 'Password reset successful.'}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_type(request):
    user = request.user
    logger.debug("Get user type for user: %s", user.username)

    if hasattr(user, 'student'):
        student = user.student
        structure = getattr(student, 'structure', None)
        return Response({
            'userType': 'Student',
            'fullName': student.name,
            'nationalId': student.national_id,
            'academicYear': structure.get_year_display() if structure else None,
            'department': structure.get_department_display() if structure else None,
        })

    elif hasattr(user, 'doctor'):
        doctor = user.doctor
        structures = doctor.structures.all()
        return Response({
            'userType': 'Staff',
            'fullName': doctor.name,
            'nationalId': doctor.national_id,
            'academicYear': [s.get_year_display() for s in structures],
            'department': [s.get_department_display() for s in structures],
        })

    else:
        logger.warning("User %s has no associated student or doctor", user.username)
        return Response({'userType': 'Other'}, status=status.HTTP_400_BAD_REQUEST)

