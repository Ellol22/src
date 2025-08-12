from rest_framework.parsers import MultiPartParser
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Dash
from django.http import JsonResponse
from accounts.models import Student, Doctor  # استورد موديل Doctor
from .serializer import StudentSerializer, DoctorSerializer  # هنعمل DoctorSerializer بسيط
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from accounts.models import Student, Doctor
from dashboard.models import Dash
from dashboard.serializer import StudentSerializer, DoctorSerializer

# dashboard/views.py

@csrf_exempt
@api_view(['GET', 'POST', 'OPTIONS'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, JSONParser])
def personal_info(request):
    print("=" * 50)
    print(f"[Personal Info] Incoming {request.method} request")
    print(f"Path: {request.path}")
    print(f"User: {request.user.username} (ID: {request.user.id})")
    print(f"Body: {request.data}")
    print(f"Files: {request.FILES}")
    print("=" * 50)

    if request.method == 'OPTIONS':
        response = Response(status=204)
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response["Access-Control-Max-Age"] = "86400"
        return response

    try:
        user = request.user
        profile_type = None
        profile_instance = None

        try:
            student = Student.objects.get(user=user)
            profile_type = 'student'
            profile_instance = student
        except Student.DoesNotExist:
            pass

        if profile_instance is None:
            try:
                doctor = Doctor.objects.get(user=user)
                profile_type = 'doctor'
                profile_instance = doctor
            except Doctor.DoesNotExist:
                pass

        if profile_instance is None:
            response_data = {'error': 'Profile not found'}
            response_status = 404

        else:
            if request.method == 'GET':
                if profile_type == 'student':
                    serializer = StudentSerializer(profile_instance)
                    response_data = {
                        'photo': serializer.data.get('image'),
                        'name': serializer.data.get('name'),
                        'studentId': serializer.data.get('national_id'),
                        'department': student.structure.get_department_display() if student.structure else None,
                        'email': serializer.data.get('email'),
                        'phone': serializer.data.get('mobile'),
                    }
                else:
                    serializer = DoctorSerializer(profile_instance)
                    response_data = {
                        'photo': serializer.data.get('image'),
                        'name': serializer.data.get('name'),
                        'national_id': serializer.data.get('national_id'),
                        'departments': serializer.data.get('departments', []),
                        'email': serializer.data.get('email'),
                        'phone': serializer.data.get('mobile'),
                        'courses': serializer.data.get('courses', []),
                    }

                response_status = 200

            elif request.method == 'POST':
                dash = None
                if profile_type == 'student':
                    dash, created = Dash.objects.get_or_create(student=profile_instance)
                else:
                    dash, created = Dash.objects.get_or_create(doctor=profile_instance)

                uploaded_image = request.FILES.get('photo') or request.FILES.get('image')

                if not uploaded_image:
                    response_data = {'error': 'No image provided'}
                    response_status = 400
                else:
                    if dash.image and dash.image.name:
                        dash.image.delete(save=False)

                    dash.image = uploaded_image
                    dash.save()

                    response_data = {'message': 'Image uploaded successfully'}
                    response_status = 200


    except Exception as e:
        import traceback
        print(f"[Personal Info] Exception: {str(e)}")
        traceback.print_exc()
        response_data = {'error': 'An unexpected error occurred'}
        response_status = 500

    print("=" * 50)
    print(f"[Personal Info] Final Response ({response_status}): {response_data}")
    print("=" * 50)

    return Response(response_data, status=response_status)



#################################################################################

# dashboard/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Announcement
from .serializer import AnnouncementSerializer
from django.shortcuts import get_object_or_404
from accounts.models import DoctorRole

from django.utils import timezone
from django.contrib.auth.models import User

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def announcement_api(request ,id=None):
    print(f"📥 Incoming {request.method} Request: {request.data}")

    if request.method == 'GET':
        if id is not None:
            announcement = get_object_or_404(Announcement, id=id)
            serializer = AnnouncementSerializer(announcement)
            return Response(serializer.data)
        else:
            announcements = Announcement.objects.all().order_by('-created_at')
            serializer = AnnouncementSerializer(announcements, many=True)
            return Response(serializer.data)


    try:
        doctor = request.user.doctor
    except:
        print("🚫 Not a doctor.")
        return Response({"detail": "Only doctors can perform this action."}, status=403)

    if doctor.role == DoctorRole.TEACHING_ASSISTANT:
        print("🚫 Teaching assistant tried modifying announcement.")
        return Response({"detail": "Teaching assistants can only view announcements."}, status=403)


    if request.method == 'POST':
        # 🔒 معالجة البيانات بأمان
        if isinstance(request.data, dict):
            data = request.data.copy()
        else:
            import json
            try:
                data = json.loads(request.data)
            except json.JSONDecodeError:
                return Response({"detail": "Invalid JSON format."}, status=400)

        serializer = AnnouncementSerializer(data=data)
        if serializer.is_valid():
            # ✅ ربط الإعلان بالمستخدم اللي عامل الطلب
            serializer.save(created_by=request.user)
            print(f"✅ Created Announcement: {serializer.data}")
            return Response(serializer.data, status=201)

        print(f"❌ Invalid Data: {serializer.errors}")
        return Response(serializer.errors, status=400)

    # لو عايزة تعملي GET بعدين حطيه هنا



    elif request.method == 'PUT':
        if not id:
            return Response({"detail": "ID is required for update."}, status=400)

        announcement = get_object_or_404(Announcement, id=id, created_by=request.user)
        data = request.data.copy()

        if not data.get('created_by'):
            data['created_by'] = request.user.id
        if not data.get('created_at'):
            data['created_at'] = announcement.created_at

        serializer = AnnouncementSerializer(announcement, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            print(f"✏️ Updated Announcement: {serializer.data}")
            return Response(serializer.data)
        print(Announcement.objects.filter(id=id))  # هل الإعلان موجود؟
        print(Announcement.objects.filter(id=id, created_by=request.user))  # هل الدكتور اللي طالب التعديل هو اللي عمله؟
        print(f"❌ Update Error: {serializer.errors}")
        return Response(serializer.errors, status=400)

    elif request.method == 'DELETE':
        if not id:
            return Response({"detail": "ID is required for deletion."}, status=400)

        announcement = get_object_or_404(Announcement, id=id, created_by=request.user)
        announcement.delete()
        print(f"🗑️ Deleted Announcement ID {id}")
        return Response({'message': 'Deleted successfully.'})

    
#################################################################################
#notification
# notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .serializer import NotificationSerializer
from .models import Notifications
from accounts.models import Doctor
import json

# notifications/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import json
from .models import Notifications
from .serializer import NotificationSerializer
from accounts.models import Doctor
from courses.models import Course

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def send_notification(request, id=None):
    # Verify the user is a doctor
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'Current user is not a Doctor.'}, status=403)

    if request.method == 'GET':
        if id is not None:
            notification = get_object_or_404(Notifications, id=id, sender=doctor)
            serializer = NotificationSerializer(notification)
            return Response(serializer.data)
        else:
            notifications = Notifications.objects.filter(sender=doctor).order_by('-created_at')
            serializer = NotificationSerializer(notifications, many=True)
            return Response(serializer.data)

    if request.method == 'POST':
        data = request.data.copy() if isinstance(request.data, dict) else json.loads(request.data)
        print("🔵 Incoming Request Data (Before Cleaning):", data)

        # ✅ احذفي أي قيمة جاية في sender لو اتبعت غلط من الفرونت
        data.pop('sender', None)

        course_id = data.get('course_id')
        if not course_id:
            print("🔴 Missing course_id in request.")
            return Response({'detail': 'course_id is required.'}, status=400)

        try:
            course = Course.objects.get(id=course_id)
            if not doctor.courses.filter(id=course.id).exists():
                print(f"🔴 Doctor not authorized for course ID {course.id}")
                return Response({'detail': 'You are not authorized to send notifications for this course.'}, status=403)
        except Course.DoesNotExist:
            print(f"🔴 Course not found: {course_id}")
            return Response({'detail': 'Course not found.'}, status=400)

        serializer = NotificationSerializer(data=data)
        if serializer.is_valid():
            # ✅ ربط الدكتور كـ sender تلقائيًا
            serializer.save(sender=doctor)
            print("✅ Notification created:", serializer.data)
            return Response(serializer.data, status=201)

        print("🔴 Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=400)



    if request.method == 'PUT':
        if not id:
            return Response({'detail': 'Notification ID required in URL.'}, status=400)
        notification = get_object_or_404(Notifications, id=id, sender=doctor)
        data = request.data.copy() if isinstance(request.data, dict) else json.loads(request.data)
        data['sender'] = doctor.id

        # Validate course authorization for updates
        course_id = data.get('course', notification.course.id)
        try:
            course = Course.objects.get(id=course_id)
            if not doctor.courses.filter(id=course_id).exists():
                return Response({'detail': 'You are not authorized to send notifications for this course.'}, status=403)
        except Course.DoesNotExist:
            return Response({'detail': 'Invalid course ID.'}, status=400)

        serializer = NotificationSerializer(notification, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    if request.method == 'DELETE':
        if not id:
            return Response({'detail': 'Notification ID required in URL.'}, status=400)
        notification = get_object_or_404(Notifications, id=id, sender=doctor)
        notification.delete()
        return Response({'detail': 'Notification deleted successfully.'}, status=200)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_notifications(request):
    from accounts.models import Student
    from courses.models import StudentCourse

    try:
        student = Student.objects.get(user=request.user)
    except Student.DoesNotExist:
        return Response({'detail': 'Current user is not a student.'}, status=403)

    # ✅ جيبي المواد اللي الطالب مشترك فيها
    student_courses = StudentCourse.objects.filter(student=student).values_list('course', flat=True)

    # ✅ جيبي النوتيفيكيشنز المرتبطة بالمواد دي
    notifications = Notifications.objects.filter(course__in=student_courses).order_by('-created_at')

    serializer = NotificationSerializer(notifications, many=True)
    return Response(serializer.data)








# مثلا في courses/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from accounts.models import Doctor
from courses.models import Course
from .serializer import CourseSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_doctor_courses(request):
    try:
        doctor = Doctor.objects.get(user=request.user)
    except Doctor.DoesNotExist:
        return Response({'detail': 'أنت مش دكتور'}, status=403)

    courses = doctor.courses.all()
    serializer = CourseSerializer(courses, many=True)
    print("doc courses : ",serializer.data)
    return Response(serializer.data)



#################################################################################
