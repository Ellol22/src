from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import Quiz, Assignment, QuizSubmission, Submission, AssignmentFile
from .serializers import AssignmentFileSerializer, QuizSerializer, AssignmentSerializer, QuizSubmissionSerializer, SubmissionSerializer
from accounts.models import Doctor, Student
from courses.models import Course, StudentCourse
import decimal
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from courses.models import Course
from .models import Assignment  # حسب اسم الابليكيشن عندك
from .models import Quiz           # حسب اسم الابليكيشن عندك
import json
from rest_framework.parsers import MultiPartParser, FormParser
from django.db.models import Avg, Sum
from grades.models import GradeSheet, StudentGrade
from datetime import datetime
from django.utils.dateparse import parse_datetime
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db import connection
import json
import logging
from .models import Quiz, QuizSubmission
from courses.models import Course
from django.http import QueryDict


def is_doctor(user):
    return hasattr(user, 'doctor')

def is_student(user):
    return hasattr(user, 'student')

def is_enrolled_in_course(user, course):
    if not is_student(user):
        return False
    return course.stucourses.filter(student=user.student).exists()

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def staff_courses(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    courses = Course.objects.filter(doctor=request.user.doctor)
    response_data = {
        'courses': [
            {'id': c.id, 'code': c.id, 'name': c.name}
            for c in courses
        ]
    }
    print("✅ Response Data:", response_data)
    return Response(response_data)



@api_view(['GET'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def staff_quizzes(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    elif request.method == 'GET':
        quizzes = Quiz.objects.filter(course__doctor=request.user.doctor)
        serializer = QuizSerializer(quizzes, many=True)
        response_data = serializer.data
        print("📤 GET Response Data:", json.dumps(response_data, indent=4, ensure_ascii=False))
        return Response(response_data)


# ------------------ POST only (Create) ------------------
import json
from rest_framework.decorators import api_view, permission_classes, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status



@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def create_quiz(request):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if 'multipart/form-data' not in request.content_type and request.content_type != 'application/json':
        return Response({"detail": "Content-Type must be application/json or multipart/form-data"}, status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    print("📥 Incoming Request Data:", request.data)

    # ✅ تحويل QueryDict إلى dict عادي
    if isinstance(request.data, QueryDict):
        data = request.data.dict()
    else:
        data = request.data.copy()

    # تحويل course_id إلى course
    data['course'] = data.pop('course_id', None)

    # تعيين الوقت الحالي كبداية
    data['start_time'] = timezone.now()

    # تحديد وقت النهاية
    data['end_time'] = data.get('end_time') or data.pop('deadline', None)

    # ✅ التأكد من الأسئلة وتحويلها من JSON
    if 'questions' in data and isinstance(data['questions'], str):
        try:
            data['questions'] = json.loads(data['questions'])
        except json.JSONDecodeError:
            return Response({'questions': 'Invalid JSON format.'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ التأكد من total_mark
    if 'total_mark' not in data:
        return Response({'total_mark': 'This field is required.'}, status=status.HTTP_400_BAD_REQUEST)

    # ✅ حفظ الكويز
    quiz_serializer = QuizSerializer(data=data, context={'request': request})
    if quiz_serializer.is_valid():
        quiz = quiz_serializer.save()
        response_data = quiz_serializer.data

        # ✅ حفظ ملف PDF لو موجود
        if 'pdf_file' in request.FILES:
            file_data = {'file': request.FILES['pdf_file']}
            file_serializer = AssignmentFileSerializer(data=file_data)
            if file_serializer.is_valid():
                upload_file = file_serializer.save(quiz=quiz, assignment=None)
                response_data['files'] = [{'id': upload_file.id, 'file_url': upload_file.file.url}]
            else:
                return Response(file_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response(response_data, status=status.HTTP_201_CREATED)

    print("❌ Serializer Errors:", quiz_serializer.errors)
    return Response(quiz_serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def staff_quiz_detail(request, quiz_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        if quiz.course.doctor != request.user.doctor:
            return Response({"detail": "You are not authorized to access this quiz."}, status=status.HTTP_403_FORBIDDEN)
    except Quiz.DoesNotExist:
        return Response({"detail": f"Quiz with id={quiz_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = QuizSerializer(quiz)
        return Response(serializer.data)

    elif request.method == 'PUT':
        print("🔁 Request Method:", request.method)
        print("📥 Raw Request Data:", request.data)

        raw_data = request.data
        data = {}

        # حل مشكلة course_id
        course_id = raw_data.get('course_id')
        if course_id:
            data['course'] = course_id if isinstance(course_id, str) else course_id[0]

        # ✅ أضف total_mark هنا
        for key in ['title', 'description', 'end_time', 'start_time', 'total_mark']:
            val = raw_data.get(key)
            if val:
                data[key] = val if isinstance(val, str) else val[0]

        # حل مشكلة questions (تحويل string → list)
        if 'questions' in raw_data:
            try:
                questions_str = raw_data.get('questions')
                if isinstance(questions_str, list):
                    questions_str = questions_str[0]
                data['questions'] = json.loads(questions_str)
            except json.JSONDecodeError:
                print("❌ JSON Decode Error in 'questions'")
                return Response({'questions': ['Invalid JSON format.']}, status=400)

        # حفظ الـ quiz بعد التعديل
        serializer = QuizSerializer(quiz, data=data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print("✅ Serializer Valid. Saved Data:", serializer.data)
            return Response(serializer.data)

        print("❌ Serializer Errors:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




    elif request.method == 'DELETE':
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)





@api_view(['GET', 'POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def staff_assignments(request):
    print("== Incoming Request ==")
    print(f"Method: {request.method}")
    print(f"User: {request.user}")
    print(f"Content-Type: {request.content_type}")
    print(f"Data: {request.data}")
    print(f"FILES: {request.FILES}")

    if not is_doctor(request.user):
        print("== Access Denied: User is not a doctor ==")
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        assignments = Assignment.objects.filter(course__doctor=request.user.doctor)
        serializer = AssignmentSerializer(assignments, many=True)
        print("== GET Response ==")
        print(serializer.data)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = AssignmentSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            assignment = serializer.save()
            print("== POST Response ==")
            print(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            print("== Validation Errors ==")
            print(serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def staff_assignment_detail(request, assignment_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=assignment_id)
        if assignment.course.doctor != request.user.doctor:
            return Response({"detail": "You are not authorized to access this assignment."}, status=status.HTTP_403_FORBIDDEN)
    except Assignment.DoesNotExist:
        print(f"❌ Assignment with id={assignment_id} not found.")
        return Response({"detail": f"Assignment with id={assignment_id} not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = AssignmentSerializer(assignment)
        print("📤 GET Response Data:", json.dumps(serializer.data, indent=4, ensure_ascii=False, default=str))
        return Response(serializer.data)

    elif request.method == 'PUT':
        serializer = AssignmentSerializer(assignment, data=request.data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            print("✅ Assignment updated successfully")
            print("📤 Outgoing Response:", json.dumps(serializer.data, indent=4, ensure_ascii=False, default=str))
            return Response(serializer.data)
        else:
            print("❌ Validation Errors:", json.dumps(serializer.errors, indent=4, ensure_ascii=False))
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        assignment.delete()
        print("🗑️ Assignment deleted successfully.")
        return Response(status=status.HTTP_204_NO_CONTENT)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_courses(request):
    if not is_student(request.user):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    student = request.user.student
    current_structure = student.structure

    if not current_structure:
        return Response({"detail": "Student has no current structure assigned."}, status=status.HTTP_404_NOT_FOUND)

    # الفلترة على المواد اللي في الاستراكتشر الحالي
    courses = Course.objects.filter(structure=current_structure)

    # فلترة المواد اللي ليها أي tasks أو quizzes أو assignments
    courses = courses.filter(
        Q(quizzes__isnull=False) |
        Q(assignments__isnull=False)
    ).distinct()


    response_data = [
        {
            "id": course.id,
            "code": course.id,
            "name": course.name
        } for course in courses
    ]

    print("📤 Outgoing Response Data:", json.dumps(response_data, indent=4, ensure_ascii=False))
    return Response(response_data)






logger = logging.getLogger(__name__)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_quizzes(request):
    student = getattr(request.user, 'student', None)
    if not student:
        return Response({'detail': 'Only students can access this endpoint.'}, status=403)

    student_courses = StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)

    # فلترة الكويزات: اللي تبع كورسات الطالب واللي وقتها لسه ما انتهاش
    now = timezone.now()
    quizzes = Quiz.objects.filter(
        course_id__in=student_courses,
        end_time__gt=now  # بس اللي لسه وقتها ما خلصش
    ).order_by('-start_time')

    serializer = QuizSerializer(quizzes, many=True, context={'request': request})
    return Response(serializer.data)




@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def student_quiz_detail(request, quiz_id):
    if not is_student(request.user):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        if not is_enrolled_in_course(request.user, quiz.course):
            return Response({"detail": "You are not authorized for this quiz."}, status=status.HTTP_403_FORBIDDEN)
    except Quiz.DoesNotExist:
        return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

    now = timezone.now()
    if not (quiz.start_time <= now <= quiz.end_time):
        return Response({"detail": "Quiz not available right now."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        serializer = QuizSerializer(quiz, context={'request': request})
        return Response(serializer.data)

    elif request.method == 'POST':
        if QuizSubmission.objects.filter(quiz=quiz, student=request.user.student).exists():
            return Response({"detail": "You have already submitted this quiz."}, status=status.HTTP_400_BAD_REQUEST)

        answers = request.data.get("answers")
        if not isinstance(answers, dict):
            return Response({"detail": "Answers must be a dictionary of question_id to selected_option_index."},
                            status=status.HTTP_400_BAD_REQUEST)

        if len(answers) != quiz.questions.count():
            return Response({"detail": "Incomplete answers. All questions must be answered."},
                            status=status.HTTP_400_BAD_REQUEST)

        submission = QuizSubmission.objects.create(
            student=request.user.student,
            quiz=quiz,
            answers=answers,
            status='ended'
        )

        submission.calculate_score()

        # ✅ ربط درجة الكويز بأعمال السنة في StudentGrade
        try:
            grade_sheet = GradeSheet.objects.get(course=quiz.course)
            student_grade, created = StudentGrade.objects.get_or_create(
                grade_sheet=grade_sheet,
                student=request.user.student
            )
            student_grade.year_work_score = submission.grade
            student_grade.save()
        except GradeSheet.DoesNotExist:
            pass

        serializer = QuizSubmissionSerializer(submission)
        return Response({
            "detail": "Quiz submitted successfully.",
            "submission": serializer.data
        }, status=status.HTTP_201_CREATED)






@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_assignments(request):
    if not is_student(request.user):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    student = request.user.student
    now = timezone.now()

    # Get IDs of student’s courses
    student_courses_ids = StudentCourse.objects.filter(student=student).values_list('course_id', flat=True)

    # Get only assignments that:
    # - are in the student's courses
    # - are assigned to the student
    # - AND the deadline has not passed
    assignments = Assignment.objects.filter(
        course_id__in=student_courses_ids,
        deadline__gt=now
    )


    assignment_data = []
    for assignment in assignments:
        file_obj = assignment.files.first()
        file_url = request.build_absolute_uri(file_obj.file.url) if file_obj else None

        assignment_data.append({
            "id": assignment.id,
            "title": assignment.title,
            "description": assignment.description,
            "course": {
                "id": assignment.course.id,
                "code": assignment.course.id,
                "name": assignment.course.name
            },
            "deadline": assignment.deadline,
            "pdf_file": file_url
        })

    print("📤 Outgoing Response Data:", json.dumps(assignment_data, indent=4, ensure_ascii=False, default=str))
    return Response(assignment_data)



@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
@permission_classes([IsAuthenticated])
def student_submit_assignment(request, assignment_id):
    if not is_student(request.user):
        return Response({"detail": "Only students can submit assignments."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=assignment_id)

        # 🔥 تحقق هل الطالب مسجل في الكورس فعلاً
        is_enrolled = StudentCourse.objects.filter(
            student=request.user.student,
            course=assignment.course
        ).exists()

        if not is_enrolled:
            return Response({"detail": "You are not authorized for this assignment."}, status=status.HTTP_403_FORBIDDEN)

        if timezone.now() > assignment.deadline:
            return Response({"detail": "Deadline has passed."}, status=status.HTTP_403_FORBIDDEN)

        pdf_file = request.FILES.get('pdf_file')
        answer_html = request.data.get('answer_html', '')
        if not pdf_file:
            return Response({"detail": "PDF file is required."}, status=status.HTTP_400_BAD_REQUEST)

        submission = Submission.objects.create(
            assignment=assignment,
            student=request.user.student,
            file=pdf_file,
            answer_html=answer_html
        )
        serializer = SubmissionSerializer(submission)
        return Response({
            "detail": "Assignment submitted successfully.",
            "submission": serializer.data
        }, status=status.HTTP_201_CREATED)

    except Assignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def student_delete_submission(request, submission_id):
    if not is_student(request.user):
        return Response({"detail": "Only students can delete submissions."}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = Submission.objects.get(id=submission_id, student=request.user.student)
        if timezone.now() > submission.assignment.deadline:
            return Response({"detail": "Deadline has passed."}, status=status.HTTP_403_FORBIDDEN)

        submission.file.delete()
        submission.delete()
        return Response({"detail": "Submission deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    except Submission.DoesNotExist:
        return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_submissions(request, quiz_id):
    if not is_doctor(request.user):
        return Response({"detail": "الطريقه دي للدكاتره بس."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        if quiz.course.doctor != request.user.doctor:
            return Response({"detail": "مش مسموحلك تشوف الكويز ده."}, status=status.HTTP_403_FORBIDDEN)
    except Quiz.DoesNotExist:
        return Response({"detail": "الكويز مش موجود."}, status=status.HTTP_404_NOT_FOUND)

    submissions = QuizSubmission.objects.filter(quiz=quiz)

    # استخدم جدول StudentCourse علشان تجيب الطلبة
    total_students = StudentCourse.objects.filter(course=quiz.course).count()
    submitted = submissions.count()
    not_submitted = total_students - submitted

    avg_grade_result = submissions.aggregate(avg_grade=Avg('grade'))['avg_grade']
    average_grade = avg_grade_result if avg_grade_result is not None else 0

    serializer = QuizSubmissionSerializer(submissions, many=True)

    return Response({
        "submissions": serializer.data,
        "stats": {
            "total_students": total_students,
            "submitted": submitted,
            "not_submitted": not_submitted,
            "average_grade": round(average_grade, 2)
        }
    })




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grade_quiz_submission(request, submission_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = QuizSubmission.objects.get(id=submission_id)
        if submission.quiz.course.doctor != request.user.doctor:
            return Response({"detail": "You are not authorized to grade this submission."}, status=status.HTTP_403_FORBIDDEN)
    except QuizSubmission.DoesNotExist:
        return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)

    grade = request.data.get('grade')
    feedback = request.data.get('feedback', '')
    if grade is None or not isinstance(grade, (int, float)) or grade < 0 or grade > 100:
        return Response({"detail": "Valid grade (0-100) is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if new grade exceeds year_work_full_score
    try:
        grade_sheet = GradeSheet.objects.get(course=submission.quiz.course)
        student_grade = StudentGrade.objects.get(grade_sheet=grade_sheet, student=submission.student)
        quiz_grades_result = QuizSubmission.objects.filter(
            student=submission.student,
            quiz__course=submission.quiz.course,
            grade__isnull=False
        ).exclude(id=submission.id).aggregate(total=Sum('grade'))['total']
        assignment_grades_result = Submission.objects.filter(
            student=submission.student,
            assignment__course=submission.quiz.course,
            grade__isnull=False
        ).aggregate(total=Sum('grade'))['total']
        quiz_grades = quiz_grades_result if quiz_grades_result is not None else 0
        assignment_grades = assignment_grades_result if assignment_grades_result is not None else 0
        total_grades = quiz_grades + assignment_grades + grade
        new_year_work_score = (total_grades / 200) * grade_sheet.year_work_full_score
        if new_year_work_score > grade_sheet.year_work_full_score:
            return Response({"detail": f"Grade would exceed year work score limit ({grade_sheet.year_work_full_score})."}, status=status.HTTP_400_BAD_REQUEST)
    except (GradeSheet.DoesNotExist, StudentGrade.DoesNotExist):
        pass  # Allow grading if GradeSheet or StudentGrade doesn't exist yet

    submission.grade = grade
    submission.feedback = feedback
    submission.save()  # This will trigger the signal to update year_work_score
    serializer = QuizSubmissionSerializer(submission)
    return Response({"detail": "Submission graded successfully.", "submission": serializer.data})




def decimal_default(obj):
    if isinstance(obj, decimal.Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def task_submissions(request, task_id):
    # ✅ اطبع بيانات الريكوست
    print("\n🔵 Request Method:", request.method)
    print("🔵 Request Path:", request.get_full_path())
    print("🔵 Request Headers:", dict(request.headers))
    if request.method == "POST":
        try:
            print("🔵 Request Body:", json.loads(request.body))
        except:
            print("🔵 Request Body: [غير قابل للتحويل لـ JSON]")

    # ✅ تحقق من صلاحيات الدكتور
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=task_id)
        if assignment.course.doctor != request.user.doctor:
            return Response({"detail": "You are not authorized to access this assignment."}, status=status.HTTP_403_FORBIDDEN)
    except Assignment.DoesNotExist:
        return Response({"detail": "Assignment not found."}, status=status.HTTP_404_NOT_FOUND)

    # ✅ إحضار التسليمات والإحصائيات
    submissions = Submission.objects.filter(assignment=assignment)
    total_students = StudentCourse.objects.filter(course=assignment.course).count()
    submitted = submissions.count()
    not_submitted = total_students - submitted

    avg_grade_result = submissions.aggregate(avg_grade=Avg('grade'))['avg_grade']
    average_grade = avg_grade_result if avg_grade_result is not None else 0

    serializer = SubmissionSerializer(submissions, many=True)

    # ✅ تحضير الريسبونس وطباعته
    response_data = {
        "submissions": serializer.data,
        "stats": {
            "total_students": total_students,
            "submitted": submitted,
            "not_submitted": not_submitted,
            "average_grade": round(average_grade, 2)
        }
    }

    try:
        print("🟢 Response Data:", json.dumps(response_data, indent=2, ensure_ascii=False, default=decimal_default))
    except Exception as e:
        print("🔴 Error printing response data:", str(e))

    return Response(response_data)




@api_view(['POST'])
@permission_classes([IsAuthenticated])
def grade_task_submission(request, submission_id):
    if not is_doctor(request.user):
        return Response({"detail": "Only doctors can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        submission = Submission.objects.get(id=submission_id)
        if submission.assignment.course.doctor != request.user.doctor:
            return Response({"detail": "You are not authorized to grade this submission."}, status=status.HTTP_403_FORBIDDEN)
    except Submission.DoesNotExist:
        return Response({"detail": "Submission not found."}, status=status.HTTP_404_NOT_FOUND)

    grade = request.data.get('grade')
    feedback = request.data.get('feedback', '')
    if grade is None or not isinstance(grade, (int, float)) or grade < 0 or grade > 100:
        return Response({"detail": "Valid grade (0-100) is required."}, status=status.HTTP_400_BAD_REQUEST)

    # Check if new grade exceeds year_work_full_score
    try:
        grade_sheet = GradeSheet.objects.get(course=submission.assignment.course)
        student_grade = StudentGrade.objects.get(grade_sheet=grade_sheet, student=submission.student)
        quiz_grades_result = QuizSubmission.objects.filter(
            student=submission.student,
            quiz__course=submission.assignment.course,
            grade__isnull=False
        ).aggregate(total=Sum('grade'))['total']
        assignment_grades_result = Submission.objects.filter(
            student=submission.student,
            assignment__course=submission.assignment.course,
            grade__isnull=False
        ).exclude(id=submission.id).aggregate(total=Sum('grade'))['total']
        quiz_grades = quiz_grades_result if quiz_grades_result is not None else 0
        assignment_grades = assignment_grades_result if assignment_grades_result is not None else 0
        total_grades = quiz_grades + assignment_grades + grade
        new_year_work_score = (total_grades / 200) * grade_sheet.year_work_full_score
        if new_year_work_score > grade_sheet.year_work_full_score:
            return Response({"detail": f"Grade would exceed year work score limit ({grade_sheet.year_work_full_score})."}, status=status.HTTP_400_BAD_REQUEST)
    except (GradeSheet.DoesNotExist, StudentGrade):
        pass  # Allow grading if GradeSheet or StudentGrade doesn't exist yet

    submission.grade = grade
    submission.feedback = feedback
    submission.save()  # This will trigger the signal to update year_work_score
    serializer = SubmissionSerializer(submission)
    return Response({"detail": "Submission graded successfully.", "submission": serializer.data})




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_quiz_submission(request, quiz_id):
    if not is_student(request.user):
        return Response({"detail": "Only students can access this endpoint."}, status=status.HTTP_403_FORBIDDEN)

    try:
        quiz = Quiz.objects.get(id=quiz_id)
        
        # لو الطالب مش مسجل في الكورس
        if not is_enrolled_in_course(request.user, quiz.course):
            return Response({"detail": "You are not authorized for this quiz."}, status=status.HTTP_403_FORBIDDEN)

    except Quiz.DoesNotExist:
        return Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        submission = QuizSubmission.objects.get(quiz=quiz, student=request.user.student)
        serializer = QuizSubmissionSerializer(submission)
        return Response(serializer.data)
    except QuizSubmission.DoesNotExist:
        return Response({"status": "No submission"})

    




def format_file_size(size_in_bytes):
    if size_in_bytes < 1024:
        return f"{size_in_bytes} B"
    elif size_in_bytes < 1024 * 1024:
        return f"{round(size_in_bytes / 1024)} KB"
    else:
        return f"{round(size_in_bytes / (1024 * 1024), 2)} MB"




@api_view(['GET'])
@permission_classes([IsAuthenticated])
def my_task_submission(request, task_id):
    if not is_student(request.user):
        data = {"detail": "Only students can access this endpoint."}
        print("📤 Response:", data)
        return Response(data, status=status.HTTP_403_FORBIDDEN)

    try:
        assignment = Assignment.objects.get(id=task_id)
        if not is_enrolled_in_course(request.user, assignment.course):
            data = {"detail": "You are not authorized for this assignment."}
            print("📤 Response:", data)
            return Response(data, status=status.HTTP_403_FORBIDDEN)
    except Assignment.DoesNotExist:
        data = {"detail": "Assignment not found."}
        print("📤 Response:", data)
        return Response(data, status=status.HTTP_404_NOT_FOUND)

    # 🧠 Get the assignment file (if exists)
    file_obj = assignment.files.first()
    if file_obj:
        file_url = request.build_absolute_uri(file_obj.file.url)
        file_size = format_file_size(file_obj.file.size)
    else:
        file_url = None
        file_size = None

    # 🧾 Build assignment info
    assignment_data = {
        "id": assignment.id,
        "title": assignment.title,
        "description": assignment.description,
        "course": {
            "id": assignment.course.id,
            "code": assignment.course.id,
            "name": assignment.course.name
        },
        "deadline": assignment.deadline,
        "pdf_file": file_url,
        "pdf_file_size": file_size,  # 🟢 الحجم الإضافي اللي طلبته
    }

    try:
        submission = Submission.objects.get(assignment=assignment, student=request.user.student)
        submission_data = SubmissionSerializer(submission).data
        response = {
            "assignment": assignment_data,
            "submission": submission_data
        }
    except Submission.DoesNotExist:
        response = {
            "assignment": assignment_data,
            "submission": None
        }

    print("📤 Final Response:", json.dumps(response, indent=4, ensure_ascii=False, default=str))
    return Response(response)