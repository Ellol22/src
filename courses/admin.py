from django.contrib import admin, messages
from .models import Course, StudentCourse, CourseSectionAssistant
from structure.models import StudentStructure
from django.db.models import Count, Q

class CourseSectionAssistantInline(admin.TabularInline):
    model = CourseSectionAssistant
    extra = 1
    verbose_name = "معيد للقسم"
    verbose_name_plural = "المعيدين المرتبطين بالأقسام"

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'structure', 'doctor')
    list_filter = ('structure__department', 'structure__year', 'structure__semester')
    search_fields = ('name',)
    ordering = ('structure__department', 'structure__year', 'structure__semester')
    inlines = [CourseSectionAssistantInline]

    fieldsets = (
        ('معلومات المادة', {
            'fields': ('name', 'structure', 'doctor')
        }),
    )

@admin.register(StudentCourse)
class StudentCourseAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'status')
    search_fields = ('student__user__name', 'course__name')
    list_filter = ('course__structure__department', 'course__structure__year', 'course__structure__semester')
    actions = ['evaluate_students_before_summer', 'evaluate_students_after_summer']

    @admin.action(description='تقييم الطلاب قبل السمر كورس')
    def evaluate_students_before_summer(self, request, queryset):
        # هنجيب كل الطلبة في السيستم
        students = StudentStructure.objects.all()
        updated = 0

        for student_structure in students:
            student = student_structure.student
            failed_courses = StudentCourse.objects.filter(
                student=student,
                status='FAILED'
            )
            if failed_courses.exists():
                student_structure.status = 'SUMMER'
            else:
                student_structure.status = 'PASS'
            student_structure.save()
            updated += 1

        self.message_user(request, f"تم تقييم حالة {updated} طالب قبل السمر كورس.", level=messages.SUCCESS)

    @admin.action(description='تقييم الطلاب بعد السمر كورس')
    def evaluate_students_after_summer(self, request, queryset):
        students = StudentStructure.objects.filter(status='SUMMER')
        updated = 0

        for student_structure in students:
            student = student_structure.student
            failed_courses = StudentCourse.objects.filter(
                student=student,
                status='FAILED'
            ).count()

            if failed_courses >= 3:
                student_structure.status = 'RETAKE_YEAR'
            elif 1 <= failed_courses <= 2:
                student_structure.status = 'RETAKE_WITH_COURSES'
            else:
                student_structure.status = 'PASS'

            student_structure.save()
            updated += 1

        self.message_user(request, f"تم تقييم حالة {updated} طالب بعد السمر كورس.", level=messages.SUCCESS)
