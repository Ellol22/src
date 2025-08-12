import os
import random
import json
import pickle
import threading
import time
import numpy as np
from datetime import datetime, timedelta, date
from io import BytesIO
from PIL import Image
import face_recognition
import qrcode
import base64
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from accounts.models import Doctor, Student
from courses.models import Course, StudentCourse
from schedule.models import Schedule
from attendance.models import Attendance, LectureSession, CodeSession
from rest_framework_simplejwt.authentication import JWTAuthentication

jwt_authenticator = JWTAuthentication()

#########################
# Helper Functions
#########################

def check_student_enrollment(student, lecture):
    """تحقق إذا كان الطالب مسجل في المادة الخاصة بالمحاضرة"""
    course = lecture.course
    return StudentCourse.objects.filter(student=student, course=course).exists()

def get_authenticated_student(request):
    """استخرج الطالب من التوكن"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise Exception('Authorization header missing or invalid')

    token = auth_header.split(' ')[1]
    validated_token = jwt_authenticator.get_validated_token(token)
    user = jwt_authenticator.get_user(validated_token)

    if not hasattr(user, 'student'):
        raise Exception('Only students can perform this action')

    return user.student

def get_face_encoding_from_image_file(image_file):
    """استخراج face encoding من صورة"""
    img = Image.open(image_file)
    img = img.convert('RGB')
    img_array = np.array(img)
    face_locations = face_recognition.face_locations(img_array)
    if not face_locations:
        return None
    encoding = face_recognition.face_encodings(img_array, face_locations)[0]
    return encoding

def generate_qr_code(lecture_id, code):
    """توليد QR Code وإرجاعه كـ base64 string"""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_data = f"lecture_id:{lecture_id},code:{code}"  # بيانات الـ QR Code
    qr.add_data(qr_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    # تحويل الصورة إلى base64
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return img_str

def rotate_code(lecture, course):
    """تحديث QR Code كل دقيقة لمدة 15 دقيقة"""
    for _ in range(15):
        # ❌ اجعل الأكواد القديمة غير مفعلة
        CodeSession.objects.filter(lecture=lecture, is_active=True).update(is_active=False)

        # ✅ إنشاء كود جديد
        new_code = str(random.randint(100000, 999999))  # كود 6 أرقام
        qr_code_data = generate_qr_code(lecture.id, new_code)

        # ✅ حفظ الكود الجديد كـ QR + نص
        CodeSession.objects.create(
            lecture=lecture,
            qr_code_data=qr_code_data,
            qr_text=new_code,
            is_active=True
        )

        # ⏳ انتظر دقيقة
        time.sleep(60)

    # 🚫 بعد 15 دقيقة نغلق الحضور
    lecture.is_open_for_attendance = False
    lecture.save()

#########################
# API Endpoints
#########################

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_lecture_api(request):
    """إنشاء محاضرة جديدة مع بدء جلسة الـ QR Code تلقائيًا"""
    try:
        print("🔵 Incoming Request:")
        print("  • User:", request.user.username)
        print("  • Method:", request.method)
        print("  • Data:", request.data)

        try:
            doctor = Doctor.objects.get(user=request.user)
            print("✅ Doctor found:", doctor.user.username)
        except Doctor.DoesNotExist:
            return Response({'error': 'Only doctors can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            courses = Course.objects.filter(doctor=doctor)
            courses_data = [
                {
                    'id': course.id,
                    'name': course.name,
                    'department': course.structure.get_department_display(),
                    'year': course.structure.get_year_display(),
                    'semester': course.structure.get_semester_display()
                }
                for course in courses
            ]
            print("✅ GET Response:", courses_data)
            return Response({'status': 'success', 'courses': courses_data}, status=status.HTTP_200_OK)

        # [POST] إنشاء محاضرة
        data = request.data
        course_id = data.get('course_id')
        lecture_date_str = data.get('lecture_date')
        lecture_name = data.get('lecture_name')

        print("🟡 Creating lecture with:")
        print("  • course_id:", course_id)
        print("  • lecture_name:", lecture_name)
        print("  • lecture_date:", lecture_date_str)

        if not all([course_id, lecture_name]):
            return Response({'error': 'Missing required fields: course_id, lecture_name'}, status=status.HTTP_400_BAD_REQUEST)

        course = Course.objects.filter(id=course_id, doctor=doctor).first()
        if not course:
            return Response({'error': 'Course not found or not assigned to you.'}, status=status.HTTP_404_NOT_FOUND)

        if lecture_date_str:
            try:
                lecture_date = datetime.strptime(lecture_date_str, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Invalid lecture_date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            lecture_date = timezone.now().date()

        lecture = LectureSession.objects.create(
            course=course,
            date=lecture_date,
            title=lecture_name,
            is_open_for_attendance=False
        )

        print("✅ Lecture created successfully:", lecture.id)

        # ✅ Start QR code session directly after lecture creation
        lecture.is_open_for_attendance = True
        lecture.qr_session_started_at = timezone.now()
        lecture.save()

        # ✅ Start rotating the QR code
        threading.Thread(target=rotate_code, args=(lecture, course), daemon=True).start()

        return Response({'status': 'success', 'lecture_id': lecture.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print("❌ Internal Server Error:", str(e))
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_latest_code_api(request, lecture_id):
    """جلب آخر QR Code لمحاضرة معينة"""
    try:
        # تحقق أن المستخدم دكتور
        try:
            doctor = Doctor.objects.get(user=request.user)
        except Doctor.DoesNotExist:
            return Response({'error': 'Only doctors can access this endpoint.'}, status=status.HTTP_403_FORBIDDEN)

        lecture = LectureSession.objects.filter(id=lecture_id, course__doctor=doctor).first()
        if not lecture:
            return Response({'error': 'Lecture not found or not assigned to you.'}, status=status.HTTP_404_NOT_FOUND)

        code_session = CodeSession.objects.filter(
            lecture_id=lecture_id,
            is_active=True
        ).order_by('-created_at').first()

        if not code_session or code_session.is_expired():
            return Response({
                'qr_code': None,
                'message': 'No active QR code available or code expired'
            }, status=status.HTTP_200_OK)

        return Response({
            'qr_code': code_session.qr_code_data,
            'created_at': code_session.created_at.strftime('%H:%M:%S'),
            'status': 'success'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    

from datetime import timedelta
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from .models import CodeSession

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_code_api(request):
    try:
        print(f"🔵 Request Method: {request.method}")
        print(f"🔵 Request Path: {request.get_full_path()}")
        print(f"🔵 Request Headers: {dict(request.headers)}")
        print(f"🔵 Request Data: {request.data}")

        qr_data = request.data.get('qr_data')
        if not qr_data:
            print("🔴 Missing QR data")
            return Response({'status': 'error', 'message': 'Invalid QR data'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            lecture_id, code = qr_data.replace('lecture_id:', '').split(',code:')
        except ValueError:
            print("🔴 Invalid QR format")
            return Response({'status': 'error', 'message': 'Invalid QR data format'}, status=status.HTTP_400_BAD_REQUEST)

        # ✅ تحقق من وجود الكود ضمن نص QR المحفوظ
        code_session = CodeSession.objects.filter(
            lecture_id=lecture_id,
            is_active=True,
            qr_text=qr_data,
            created_at__gte=timezone.now() - timedelta(minutes=1)
        ).first()


        if not code_session:
            print(f"🔴 QR not found or expired: {qr_data}")
            return Response({'status': 'error', 'message': 'Invalid or expired QR code'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'status': 'success',
            'message': 'QR code is valid',
            'course_name': code_session.lecture.course.name,
            'lecture_date': code_session.lecture.date.strftime("%Y-%m-%d"),
            'lecture_id': code_session.lecture.id
        }, status=status.HTTP_200_OK)

    except Exception as e:
        print("❌ Internal Server Error:", e)
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    



# باقي الـ endpoints (verify_location_api, register_face_api, verify_face_api, get_open_lectures_for_student, student_attendance_summary, doctor_attendance_overview)
# لم يتم تعديلها لأنها لا تتعلق مباشرة بالـ QR Code
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_location_api(request):
    """التحقق من الموقع الجغرافي"""
    try:
        data = request.data
        print("📥 Request data:", data)

        lat = float(data.get('latitude'))
        lon = float(data.get('longitude'))
        lecture_id = data.get('lecture_id')

        if not all([lat, lon, lecture_id]):
            response = {'error': 'Missing parameters'}
            print("❌ Response:", response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        lecture = LectureSession.objects.select_related('course').filter(id=lecture_id).first()

        if not lecture:
            response = {'error': 'Lecture not found'}
            print("❌ Response:", response)
            return Response(response, status=status.HTTP_404_NOT_FOUND)

        # ✅ استخدم الكود اللي دخله الدكتور بنفسه
        building_code_raw = lecture.building_code or ''
        building_code = building_code_raw[0].upper() if building_code_raw else ''

        BUILDING_ZONES = {
            'A': [(30.1000, 31.2980), (30.1000, 31.2990), (30.1010, 31.2990), (30.1010, 31.2980)],
            'G': [(30.1020, 31.2950), (30.1020, 31.2960), (30.1030, 31.2960), (30.1030, 31.2950)],
            'C': [(30.1040, 31.2970), (30.1040, 31.2980), (30.1050, 31.2980), (30.1050, 31.2970)],
            'D': [(30.1060, 31.2990), (30.1060, 31.3000), (30.1070, 31.3000), (30.1070, 31.2990)],
            'F': [(30.1080, 31.3010), (30.1080, 31.3020), (30.1090, 31.3020), (30.1090, 31.3010)],
        }

        if building_code not in BUILDING_ZONES:
            response = {'error': f'Unknown building zone for code: {building_code_raw}'}
            print("❌ Response:", response)
            return Response(response, status=status.HTTP_400_BAD_REQUEST)

        def is_point_in_polygon(lat, lon, polygon):
            x = lon
            y = lat
            inside = False
            n = len(polygon)
            p1x, p1y = polygon[0][1], polygon[0][0]
            for i in range(n + 1):
                p2x, p2y = polygon[i % n][1], polygon[i % n][0]
                if min(p1y, p2y) < y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        xinters = (y - p1y) * (p2x - p1x) / ((p2y - p1y) + 1e-10) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
                p1x, p1y = p2x, p2y
            return inside

        polygon = BUILDING_ZONES[building_code]
        inside = is_point_in_polygon(lat, lon, polygon)

        response = {
            'status': 'success',
            'inside': inside,
            'building': building_code,
            'course': str(lecture.course),
            'message': f"User is {'inside' if inside else 'outside'} building {building_code}"
        }
        print("📤 Response:", response)
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        response = {'error': str(e)}
        print("❌ Internal Error:", response)
        return Response(response, status=status.HTTP_400_BAD_REQUEST)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_face_api(request):
    """تسجيل الوجه للطالب (3 صور)"""
    try:
        student = get_authenticated_student(request)
        student_id = student.id
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    images = [request.FILES.get(f'image{i}') for i in range(1, 4)]
    if any(img is None for img in images):
        return Response({'error': 'Three images (image1, image2, image3) are required'}, status=status.HTTP_400_BAD_REQUEST)

    encodings = []
    for img in images:
        encoding = get_face_encoding_from_image_file(img)
        if encoding is None:
            return Response({'error': 'No face detected in one of the images'}, status=status.HTTP_400_BAD_REQUEST)
        encodings.append(encoding)

    DATA_FOLDER = os.path.join(settings.BASE_DIR, 'students_data')
    os.makedirs(DATA_FOLDER, exist_ok=True)
    file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
    with open(file_path, 'wb') as f:
        pickle.dump(encodings, f)

    # تحديث الحضور السابق الذي لم يتم تحديث الوجه فيه
    attendances = Attendance.objects.filter(student=student, face_updated=False)
    for attendance in attendances:
        attendance.face_updated = True
        attendance.failed_face_attempts = 0
        attendance.save()

    return Response({'status': 'success', 'message': 'Face registered successfully'}, status=status.HTTP_200_OK)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def verify_face_api(request):
    """التحقق من الوجه وإعتماد الحضور"""
    try:
        student = get_authenticated_student(request)
        student_id = student.id
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

    lecture_id = request.data.get('lecture_id')
    if not lecture_id:
        return Response({'error': 'lecture_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        lecture = LectureSession.objects.get(id=lecture_id)
    except LectureSession.DoesNotExist:
        return Response({'error': 'Lecture not found.'}, status=status.HTTP_404_NOT_FOUND)

    # تحقق من وجود كود فعال
    code_session_exists = CodeSession.objects.filter(
        lecture=lecture,
        is_active=True,
        created_at__gte=timezone.now() - timedelta(minutes=15)
    ).exists()

    if not code_session_exists:
        return Response({'error': 'Attendance for this lecture is currently closed (no active code).'}, status=status.HTTP_403_FORBIDDEN)

    if not check_student_enrollment(student, lecture):
        return Response({'error': 'You are not enrolled in this course. Cannot mark attendance.'}, status=status.HTTP_403_FORBIDDEN)

    image = request.FILES.get('image')
    if image is None:
        return Response({'error': 'image is required'}, status=status.HTTP_400_BAD_REQUEST)

    input_encoding = get_face_encoding_from_image_file(image)
    if input_encoding is None:
        return Response({'error': 'No face detected in the provided image'}, status=status.HTTP_400_BAD_REQUEST)

    DATA_FOLDER = os.path.join(settings.BASE_DIR, 'students_data')
    file_path = os.path.join(DATA_FOLDER, f"{student_id}.pkl")
    if not os.path.exists(file_path):
        return Response({'error': 'No face data registered. Please register your face first.'}, status=status.HTTP_400_BAD_REQUEST)

    with open(file_path, 'rb') as f:
        known_encodings = pickle.load(f)

    matches = face_recognition.compare_faces(known_encodings, input_encoding)
    if not any(matches):
        attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
        attendance.failed_face_attempts += 1
        if attendance.failed_face_attempts >= 3:
            attendance.face_updated = False
        attendance.save()
        return Response({'error': 'Face does not match registered data. Please try again.'}, status=status.HTTP_401_UNAUTHORIZED)

    # تسجيل الحضور
    attendance, created = Attendance.objects.get_or_create(student=student, lecture=lecture)
    attendance.is_present = True
    attendance.face_updated = True
    attendance.failed_face_attempts = 0
    attendance.status = 'present'
    attendance.save()

    return Response({'status': 'success', 'message': 'Attendance marked successfully.'}, status=status.HTTP_200_OK)

from structure.models import StudentStructure
import traceback

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_open_lectures_for_student(request):
    """جلب المحاضرات المفتوحة للطالب"""
    try:
        if not hasattr(request.user, 'student'):
            response_data = {
                'status': 'error',
                'message': 'الحساب الحالي ليس طالبًا'
            }
            print("📤 Response to frontend:", response_data)
            return Response(response_data, status=status.HTTP_403_FORBIDDEN)

        student = request.user.student

        student_structure = student.structure
        if not student_structure:
            response_data = {
                'status': 'error',
                'message': 'الطالب غير مرتبط بأي هيكل دراسي'
            }
            print("📤 Response to frontend:", response_data)
            return Response(response_data, status=status.HTTP_404_NOT_FOUND)

        enrolled_courses_ids = StudentCourse.objects.filter(
            student=student
        ).values_list('course_id', flat=True)

        fifteen_minutes_ago = timezone.now() - timedelta(minutes=15)

        active_code_sessions = CodeSession.objects.filter(
            is_active=True,
            created_at__gte=fifteen_minutes_ago,
            lecture__course_id__in=enrolled_courses_ids
        ).select_related('lecture', 'lecture__course')

        open_lectures = []
        for session in active_code_sessions:
            lecture = session.lecture
            course = lecture.course

            today_weekday = timezone.localtime().strftime('%A')
            schedule = Schedule.objects.filter(
                course=course,
                day=today_weekday,
                student_structure=student_structure
            ).first()

            open_lectures.append({
                'lecture_id': lecture.id,
                'lecture_date': lecture.date.strftime("%Y-%m-%d"),
                'course_name': course.name,
                'room': lecture.building_code or "",  # ✅ هنا التعديل
            })


        response_data = {
            'status': 'success',
            'open_lectures': open_lectures
        }
        print("📤 Response to frontend:", response_data)
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        print("\n🔴 حصل خطأ أثناء تنفيذ دالة get_open_lectures_for_student:\n")
        print(traceback.format_exc())
        response_data = {
            'status': 'error',
            'message': str(e)
        }
        print("📤 Error Response to frontend:", response_data)
        return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_attendance_summary(request):
    """ملخص حضور الطالب"""
    try:
        user = request.user
        if not hasattr(user, 'student'):
            return Response({"detail": "User is not a student."}, status=status.HTTP_403_FORBIDDEN)

        student = user.student
        student_courses = StudentCourse.objects.filter(student=student)

        data = []
        for enrollment in student_courses:
            course = enrollment.course
            lectures = LectureSession.objects.filter(course=course)
            total_lectures = lectures.count()
            
            attended_count = Attendance.objects.filter(
                student=student,
                lecture__in=lectures,
                status='present'
            ).count()

            percentage = (
                (attended_count / total_lectures) * 100 if total_lectures > 0 else 0
            )
            attendance_status = "regular" if percentage >= 75 else "at risk"

            data.append({
                "course": course.name,
                "department": course.structure.get_department_display() if course.structure else "",
                "year": course.structure.get_year_display() if course.structure else "",
                "semester": course.structure.get_semester_display() if course.structure else "",
                "attended_lectures": attended_count,
                "total_lectures": total_lectures,
                "percentage": round(percentage, 2),
                "status": attendance_status
            })

        return Response(data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def doctor_attendance_overview(request):
    """GET: نظرة عامة على حضور الطلاب لكل محاضرة
       POST: تعديل الحضور لطالب في محاضرة"""
    try:
        try:
            doctor = request.user.doctor
        except:
            return Response({"error": "You are not assigned as a doctor."}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'GET':
            courses = Course.objects.filter(doctor=doctor)
            result = []

            for course in courses:
                course_data = {
                    "course_id": course.id,
                    "course_name": course.name,
                    "structure": str(course.structure),
                    "lectures": []
                }

                lectures = LectureSession.objects.filter(course=course).order_by('date')

                for lecture in lectures:
                    lecture_data = {
                        "lecture_id": lecture.id,
                        "lecture_title": lecture.title,
                        "date": lecture.date,
                        "students": []
                    }

                    student_courses = StudentCourse.objects.filter(course=course).select_related("student")

                    for sc in student_courses:
                        attendance = Attendance.objects.filter(student=sc.student, lecture=lecture).first()
                        lecture_data["students"].append({
                            "student_id": sc.student.id,
                            "student_name": sc.student.name,
                            "status": attendance.status if attendance else "absent"
                        })

                    course_data["lectures"].append(lecture_data)

                result.append(course_data)

            return Response(result, status=status.HTTP_200_OK)

        elif request.method == 'POST':
            lecture_id = request.data.get("lecture_id")
            student_id = request.data.get("student_id")
            new_status = request.data.get("status")

            if not lecture_id or not student_id or not new_status:
                return Response({"detail": "Missing fields: lecture_id, student_id, or status."}, status=status.HTTP_400_BAD_REQUEST)

            try:
                lecture = LectureSession.objects.get(id=lecture_id)
            except LectureSession.DoesNotExist:
                return Response({"detail": "Lecture not found."}, status=status.HTTP_404_NOT_FOUND)

            if lecture.course.doctor != doctor:
                return Response({"detail": "You do not have permission to modify this lecture."}, status=status.HTTP_403_FORBIDDEN)

            try:
                student = Student.objects.get(id=student_id)
            except Student.DoesNotExist:
                return Response({"detail": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

            attendance, created = Attendance.objects.get_or_create(
                student=student,
                lecture=lecture,
                defaults={'status': new_status}
            )
            if not created:
                attendance.status = new_status
                attendance.save()

            return Response({
                "message": "Attendance updated successfully.",
                "lecture_id": lecture.id,
                "student_id": student.id,
                "status": attendance.status
            }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_students_attendance_summary(request):
    """نسبة الحضور لكل طالب في كورسات الدكتور"""
    try:
        try:
            doctor = request.user.doctor
        except:
            return Response({"detail": "User is not a doctor."}, status=status.HTTP_403_FORBIDDEN)

        courses = Course.objects.filter(doctor=doctor)
        result = []

        for course in courses:
            lectures = LectureSession.objects.filter(course=course)
            total_lectures = lectures.count()

            # هات الطلاب المسجلين في الكورس
            student_courses = StudentCourse.objects.filter(course=course).select_related('student')

            students_data = []
            for sc in student_courses:
                student = sc.student
                attended_count = Attendance.objects.filter(
                    student=student,
                    lecture__in=lectures,
                    status='present'
                ).count()

                percentage = (attended_count / total_lectures) * 100 if total_lectures > 0 else 0
                attendance_status = "regular" if percentage >= 75 else "at risk"

                students_data.append({
                    "student_id": student.id,
                    "student_name": student.name,
                    "attendance_percentage": round(percentage, 2),
                    "attended_lectures": attended_count,
                    "total_lectures": total_lectures,
                    "status": attendance_status
                })

            result.append({
                "course_id": course.id,
                "course_name": course.name,
                "structure": str(course.structure),
                "students": students_data
            })

        return Response(result, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
