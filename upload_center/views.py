import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from courses.models import Course, StudentCourse
from courses.serializers import CourseSerializer  # لازم يكون موجود
from .models import UploadFile
from .serializers import UploadFileSerializer
from accounts.models import Doctor, Student

# 1️⃣ دكتور يجيب مواده (الكورسات اللي هو مسؤول عنها)
@permission_classes([IsAuthenticated])
@api_view(['GET'])
def doctor_courses_view(request):
    try:
        doctor = request.user.doctor
    except Doctor.DoesNotExist:
        return Response({"detail": "User is not a doctor."}, status=status.HTTP_403_FORBIDDEN)

    courses = Course.objects.filter(doctor=doctor)
    serializer = CourseSerializer(courses, many=True)
    print(serializer.data)
    return Response(serializer.data)


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .models import UploadFile
from courses.models import Course
from .serializers import UploadFileSerializer

@api_view(['GET', 'POST', 'DELETE'])
@permission_classes([IsAuthenticated])
def teacher_upload_file_view(request):
    print("📥 Request Method:", request.method)
    print("📥 Request Data:", request.data)
    print("📥 Request Query Params:", request.query_params)

    try:
        doctor = request.user.doctor
        # print("✅ Authenticated doctor:", doctor)
    except Exception as e:
        # print("❌ Doctor authentication failed:", str(e))
        return Response({"detail": "User is not a doctor."}, status=status.HTTP_403_FORBIDDEN)

    # 📥 جلب ملفات مادة
    if request.method == 'GET':
        course_id = request.query_params.get('course_id')
        if not course_id:
            # print("❌ No course_id provided in GET request")
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
            # print("✅ Course found:", course)
        except Course.DoesNotExist:
            # print("❌ Course not found for ID:", course_id)
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        if course.doctor != doctor:
            # print("❌ Doctor not authorized to view files for course:", course.name)
            return Response({"detail": "You are not allowed to view files for this course."}, status=status.HTTP_403_FORBIDDEN)

        files = UploadFile.objects.filter(course=course).order_by('-uploaded_at')
        data = [
            {
                'id': file.id,
                'file_url': file.file.url,
                'uploaded_at': file.uploaded_at,
                'uploaded_by': file.uploaded_by.username,
            }
            for file in files
        ]
        print("✅ Returning files list:", data)
        return Response(data, status=status.HTTP_200_OK)

    # 📤 رفع ملف
    elif request.method == 'POST':
        course_id = request.data.get('course')
        if not course_id:
            # print("❌ No course ID in POST data")
            return Response({"detail": "Course ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            course = Course.objects.get(id=course_id)
            # print("✅ Course found for upload:", course)
        except Course.DoesNotExist:
            # print("❌ Course not found:", course_id)
            return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

        if course.doctor != doctor:
            # print("❌ Doctor not allowed to upload to course:", course.name)
            return Response({"detail": "You are not allowed to upload to this course."}, status=status.HTTP_403_FORBIDDEN)

        serializer = UploadFileSerializer(data=request.data)
        if serializer.is_valid():
            upload_file = serializer.save(uploaded_by=request.user, course=course)
            response_data = {
                'id': upload_file.id,
                'course': {
                    'id': upload_file.course.id,
                    'name': upload_file.course.name
                },
                'file_url': upload_file.file.url,
                'uploaded_at': upload_file.uploaded_at
            }
            # print("✅ File uploaded successfully:", response_data)
            return Response(response_data, status=status.HTTP_201_CREATED)

        # print("❌ Serializer errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # ❌ حذف ملف
    elif request.method == 'DELETE':
        file_id = request.query_params.get('file_id')
    if not file_id:
        return Response({"detail": "File ID is required to delete."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        file = UploadFile.objects.get(id=file_id)
    except UploadFile.DoesNotExist:
        return Response({"detail": "File not found."}, status=status.HTTP_404_NOT_FOUND)

    if file.course.doctor != doctor:
        return Response({"detail": "You are not allowed to delete this file."}, status=status.HTTP_403_FORBIDDEN)

    file.delete()
    return Response({"detail": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)


# 3️⃣ طالب يجيب الكورسات (المواد) اللي مسجل فيها
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses_view(request):

    user = request.user

    # تأكد إنه طالب
    if not hasattr(user, 'student'):
        return Response({"detail": "User is not a student."}, status=403)

    student = user.student
    student_courses = StudentCourse.objects.filter(student=student)

    data = {}

    for enrollment in student_courses:
        course = enrollment.course

        year = str(course.structure.get_year_display() if course.structure else "")
        semester = str(course.structure.get_semester_display() if course.structure else "")
        subject = course.name

        key = (year, semester, subject, course.id)  # ✅ خلي الـ key يشمل course.id

        if key not in data:
            data[key] = []

        files = UploadFile.objects.filter(course=course)

        for file in files:
            if file.file and file.file.storage.exists(file.file.name):
                size_kb = str(file.file.size // 1024) + ' KB'
            else:
                print(f"⚠️ Missing file on disk: {file.file.name}")  # ده هيطبع في الترمنال
                size_kb = 'N/A'

            data[key].append({
                "id": file.id,
                "name": file.file.name.split('/')[-1],
                "type": "lecture",  # لو عندك نوع حطه هنا
                "size": size_kb,
                "date": file.uploaded_at.strftime("%Y-%m-%d"),
            })

    # تحويل الـ dict للشكل اللي الفيو مستنيه
    response_data = {}

    for (year, semester, subject, course_id), files in data.items():
        year_entry = next((item for item in response_data.values() if item['year'] == year), None)

        if not year_entry:
            year_entry = {
                "year": year,
                "semesters": {},
            }
            response_data[year] = year_entry

        semester_entry = year_entry["semesters"].get(semester)

        if not semester_entry:
            semester_entry = {
                "semester": semester,
                "subjects": {},
            }
            year_entry["semesters"][semester] = semester_entry

        subject_entry = semester_entry["subjects"].get(subject)

        if not subject_entry:
            subject_entry = {
                "subject": subject,
                "course_id": course_id,  # ✅ أضفناها هنا
                "files": [],
            }
            semester_entry["subjects"][subject] = subject_entry

        subject_entry["files"].extend(files)

    # تحويل الدكتشنري النهائي لقائمة
    final_response = []

    for year_data in response_data.values():
        semesters_list = []

        for semester_data in year_data["semesters"].values():
            subjects_list = []

            for subject_data in semester_data["subjects"].values():
                subjects_list.append(subject_data)

            semester_data_out = {
                "semester": semester_data["semester"],
                "subjects": subjects_list,
            }
            semesters_list.append(semester_data_out)

        year_data_out = {
            "year": year_data["year"],
            "semesters": semesters_list,
        }

        final_response.append(year_data_out)

    # Debug print in terminal
    print("==== Outgoing Response ====")
    print(json.dumps(final_response, indent=4))
    print("==========================")

    return Response(final_response)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_files_view(request):
    print("🔵 [student_files_view] START request")

    try:
        student = request.user.student
        # print(f"✅ Got student: {student.id} - {student.user.username}")
    except Student.DoesNotExist:
        # print("❌ User is not a student.")
        return Response({"detail": "User is not a student."}, status=status.HTTP_403_FORBIDDEN)

    course_id = request.query_params.get('course_id')
    # print(f"📌 course_id param received: {course_id}")

    if not course_id:
        # print("❌ Missing course_id parameter.")
        return Response({"detail": "course_id parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    # تحقق أن الطالب مسجل في الكورس
    from courses.models import StudentCourse
    is_enrolled = StudentCourse.objects.filter(student=student, course_id=course_id).exists()
    # print(f"📚 Is student enrolled in course {course_id}? {'YES' if is_enrolled else 'NO'}")

    if not is_enrolled:
        # print("❌ Student is not enrolled in the course.")
        return Response({"detail": "You are not enrolled in this course."}, status=status.HTTP_403_FORBIDDEN)

    # جلب ملفات الرفع الخاصة بالكورس
    files = UploadFile.objects.filter(course_id=course_id)
    # print(f"📂 Found {files.count()} files for course_id {course_id}")

    files_serializer = UploadFileSerializer(files, many=True)

    # جلب بيانات الكورس للرد
    try:
        course = Course.objects.get(id=course_id)
        # print(f"✅ Course found: {course.id} - {course.name}")
    except Course.DoesNotExist:
        # print("❌ Course not found in DB.")
        return Response({"detail": "Course not found."}, status=status.HTTP_404_NOT_FOUND)

    # print("🟢 Preparing final response...")
    response = Response({
        'course': {
            'id': course.id,
            'name': course.name
        },
        'files': files_serializer.data
    })

    print("✅ [student_files_view] END request - returning response.")
    return response
