from django.contrib import admin
from .models import GradeSheet, StudentGrade

# عرض الدرجات داخل كل GradeSheet
class StudentGradeInline(admin.TabularInline):
    model = StudentGrade
    extra = 0
    readonly_fields = ('percentage', 'letter_grade')

@admin.register(GradeSheet)
class GradeSheetAdmin(admin.ModelAdmin):
    list_display = ('course',)
    inlines = [StudentGradeInline]
    list_filter = (
        'course__structure__year',       # السنة الدراسية
        'course__structure__department', # القسم
        'course__structure__semester',   # الترم
    )

@admin.register(StudentGrade)
class StudentGradeAdmin(admin.ModelAdmin):
    list_display = (
        'student', 
        'grade_sheet', 
        'midterm_score', 
        'section_exam_score', 
        'final_exam_score', 
        'year_work_score', 
        'total_score', 
        'percentage', 
        'letter_grade'
    )
    readonly_fields = ('percentage', 'letter_grade')
    
    list_filter = (
        'grade_sheet__course__structure__year',        # فلتر السنة الدراسية
        'grade_sheet__course__structure__department',  # فلتر القسم
        'grade_sheet__course__structure__semester',    # فلتر الترم
    )
    
    search_fields = ('student__name', 'grade_sheet__course__name')