from django.contrib import admin, messages
from .models import StudentStructure, SummerCourseEnrollment, FailedSummerCourseSubject
from grades.models import StudentGrade
from django.db.models import Q
from courses.models import Course

@admin.register(StudentStructure)
class StudentStructureAdmin(admin.ModelAdmin):
    list_display = ['get_student_username', 'department', 'year', 'semester', 'status', 'failed_courses_display']
    search_fields = ['department', 'year', 'semester', 'status']
    list_filter = ['department', 'year', 'semester', 'status']
    readonly_fields = ['failed_courses_display']
    actions = ['assign_summer_courses', 'finalize_student_status_after_summer']

    def get_student_username(self, obj):
        try:
            return obj.student.user.username
        except:
            return "-"
    get_student_username.short_description = 'Student Username'

    def failed_courses_display(self, obj):
        return ", ".join(obj.failed_courses_names or [])
    failed_courses_display.short_description = 'Failed Courses'

    def assign_summer_courses(self, request, queryset):
        count = 0
        for structure in queryset:
            grades = StudentGrade.objects.filter(
                student=structure.student,
                grade_sheet__course__in=structure.course_structure.all()
            )

            failed_courses = []
            for grade in grades:
                final_total = grade.grade_sheet.final_exam_full_score or 1  # Avoid division by zero
                final_percent = (grade.final_exam_score / final_total) * 100

                if grade.percentage < 60 or final_percent < 40:
                    failed_courses.append(grade.grade_sheet.course.id)

            if failed_courses:
                structure.status = 'SUMMER'
                structure.failed_courses.set(failed_courses)
                structure.save()

                for course_id in failed_courses:
                    SummerCourseEnrollment.objects.get_or_create(student=structure.student, course_id=course_id)

                count += 1

        self.message_user(request, f"تم إدخال {count} طالب للسمر كورس بنجاح", messages.SUCCESS)
    assign_summer_courses.short_description = "📌 تقييم الطلاب وإدخالهم السمر كورس"

    def finalize_student_status_after_summer(self, request, queryset):
        count = 0
        for structure in queryset:
            summer_courses = SummerCourseEnrollment.objects.filter(
                student=structure.student
            ).values_list('course', flat=True)

            grades = StudentGrade.objects.filter(
                student=structure.student,
                grade_sheet__course_id__in=summer_courses
            )

            failed_in_summer = []
            for grade in grades:
                final_total = grade.grade_sheet.final_exam_full_score or 1
                final_percent = (grade.final_exam_score / final_total) * 100

                if grade.percentage < 60 or final_percent < 40:
                    failed_in_summer.append(grade.grade_sheet.course.id)

            # تخزين المواد الراسبة بعد السمر
            for course_id in failed_in_summer:
                FailedSummerCourseSubject.objects.get_or_create(
                    student=structure.student,
                    course_id=course_id,
                    year=structure.year,
                    semester=structure.semester
                )

            failed_count = len(failed_in_summer)

            if failed_count >= 3:
                structure.status = 'RETAKE_YEAR'
                structure.failed_courses.set(failed_in_summer)
            elif 1 <= failed_count <= 2:
                structure.status = 'RETAKE_WITH'
                structure.failed_courses.set(failed_in_summer)
            else:
                structure.status = 'PASSED'
                structure.failed_courses.clear()

            structure.save()
            count += 1

        self.message_user(request, f"تم تقييم حالة {count} طالب بعد السمر كورس", messages.SUCCESS)
    finalize_student_status_after_summer.short_description = "✅ تقييم الطلاب بعد السمر كورس"
