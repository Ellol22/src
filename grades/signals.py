from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from courses.models import StudentCourse, Course
from grades.models import GradeSheet, StudentGrade
from accounts.models import Student


def refresh_student_grades(student):
    # امسح كل درجات الطالب
    StudentGrade.objects.filter(student=student).delete()

    # رجع المواد الحالية اللي الطالب فيها
    student_courses = StudentCourse.objects.filter(student=student)

    for student_course in student_courses:
        course = student_course.course

        # أنشئ GradeSheet لو مش موجود
        grade_sheet, _ = GradeSheet.objects.get_or_create(course=course)

        # أضف الطالب إلى StudentGrade
        StudentGrade.objects.create(
            grade_sheet=grade_sheet,
            student=student,
            total_score=0  # أو أي قيمة افتراضية
        )


@receiver(post_save, sender=StudentCourse)
def on_student_course_saved(sender, instance, **kwargs):
    refresh_student_grades(instance.student)


@receiver(post_delete, sender=StudentCourse)
def on_student_course_deleted(sender, instance, **kwargs):
    refresh_student_grades(instance.student)


@receiver(post_save, sender=Course)
def sync_doctor_to_gradesheet(sender, instance, **kwargs):
    course = instance
    doctor = course.doctor

    grade_sheet, _ = GradeSheet.objects.get_or_create(course=course)

    if grade_sheet.doctor != doctor:
        grade_sheet.doctor = doctor
        grade_sheet.save()
