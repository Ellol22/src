from django.contrib import admin
from django.db.models import Case, When, IntegerField
from .models import Schedule

class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('get_course_name', 'day', 'slot_number', 'section', 'type', 'get_department', 'get_year', 'get_semester')

    def get_course_name(self, obj):
        return obj.course.name
    get_course_name.short_description = 'Course'
    list_filter = ('student_structure__department', 'student_structure__year', 'student_structure__semester', 'day', 'type')
    search_fields = ('course', 'instructor', 'room', 'slot_number')

    def get_department(self, obj):
        return obj.student_structure.get_department_display()
    get_department.short_description = 'Department'

    def get_year(self, obj):
        return obj.student_structure.get_year_display()
    get_year.short_description = 'Year'

    def get_semester(self, obj):
        return obj.student_structure.get_semester_display()
    get_semester.short_description = 'Semester'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # ترتيب الأيام - لازم تكون نفس الكلمات في حقل day
        order = Case(
            When(day='Saturday', then=0),
            When(day='Sunday', then=1),
            When(day='Monday', then=2),
            When(day='Tuesday', then=3),
            When(day='Wednesday', then=4),
            When(day='Thursday', then=5),
            output_field=IntegerField(),
        )
        return qs.annotate(day_order=order).order_by('day_order', 'slot_number')

admin.site.register(Schedule, ScheduleAdmin)
