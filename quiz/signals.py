from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Sum
from .models import QuizSubmission, Submission
from grades.models import GradeSheet, StudentGrade

@receiver(post_save, sender=QuizSubmission)
def update_quiz_year_work_score(sender, instance, **kwargs):
    if instance.grade is not None:
        student = instance.student
        course = instance.quiz.course
        try:
            grade_sheet = GradeSheet.objects.get(course=course)
            student_grade, created = StudentGrade.objects.get_or_create(
                grade_sheet=grade_sheet,
                student=student
            )
            # Calculate total quiz and assignment grades for the course
            quiz_grades_result = QuizSubmission.objects.filter(
                student=student,
                quiz__course=course,
                grade__isnull=False
            ).aggregate(total=Sum('grade'))['total']
            assignment_grades_result = Submission.objects.filter(
                student=student,
                assignment__course=course,
                grade__isnull=False
            ).aggregate(total=Sum('grade'))['total']
            # Handle None values
            quiz_grades = quiz_grades_result if quiz_grades_result is not None else 0
            assignment_grades = assignment_grades_result if assignment_grades_result is not None else 0
            # Assume quizzes and assignments contribute equally
            total_grades = quiz_grades + assignment_grades
            # Normalize to year_work_full_score (default 15)
            year_work_full_score = grade_sheet.year_work_full_score
            # Assuming total_grades is out of 200 (100 for quizzes + 100 for assignments)
            student_grade.year_work_score = min((total_grades / 200) * year_work_full_score, year_work_full_score)
            student_grade.save()
        except GradeSheet.DoesNotExist:
            pass  # Skip if no GradeSheet exists

@receiver(post_save, sender=Submission)
def update_assignment_year_work_score(sender, instance, **kwargs):
    if instance.grade is not None:
        student = instance.student
        course = instance.assignment.course
        try:
            grade_sheet = GradeSheet.objects.get(course=course)
            student_grade, created = StudentGrade.objects.get_or_create(
                grade_sheet=grade_sheet,
                student=student
            )
            # Calculate total quiz and assignment grades for the course
            quiz_grades_result = QuizSubmission.objects.filter(
                student=student,
                quiz__course=course,
                grade__isnull=False
            ).aggregate(total=Sum('grade'))['total']
            assignment_grades_result = Submission.objects.filter(
                student=student,
                assignment__course=course,
                grade__isnull=False
            ).aggregate(total=Sum('grade'))['total']
            # Handle None values
            quiz_grades = quiz_grades_result if quiz_grades_result is not None else 0
            assignment_grades = assignment_grades_result if assignment_grades_result is not None else 0
            # Assume quizzes and assignments contribute equally
            total_grades = quiz_grades + assignment_grades
            # Normalize to year_work_full_score (default 15)
            year_work_full_score = grade_sheet.year_work_full_score
            # Assuming total_grades is out of 200 (100 for quizzes + 100 for assignments)
            student_grade.year_work_score = min((total_grades / 200) * year_work_full_score, year_work_full_score)
            student_grade.save()
        except GradeSheet.DoesNotExist:
            pass  # Skip if no GradeSheet exists