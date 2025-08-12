# serializers.py

from rest_framework import serializers
from .models import GradeSheet, StudentGrade


# serializers.py

class StudentGradeSerializer(serializers.ModelSerializer):
    # بيانات المادة
    subjectName = serializers.CharField(source='grade_sheet.course.name', read_only=True)
    department = serializers.CharField(source='grade_sheet.course.structure.get_department_display', read_only=True)
    year = serializers.CharField(source='grade_sheet.course.structure.get_year_display', read_only=True)
    semester = serializers.CharField(source='grade_sheet.course.structure.get_semester_display', read_only=True)

    # بيانات الطالب
    student_name = serializers.SerializerMethodField()
    student_id = serializers.SerializerMethodField()  # ← رقم الجلوس الجديد

    # درجات محسوبة (غير قابلة للتعديل)
    progress = serializers.SerializerMethodField()
    midterm_score_max = serializers.SerializerMethodField()
    section_exam_score_max = serializers.SerializerMethodField()
    year_work_score_max = serializers.SerializerMethodField()
    final_exam_score_max = serializers.SerializerMethodField()
    total_score_max = serializers.SerializerMethodField()

    class Meta:
        model = StudentGrade
        fields = [
            'student_name',
            'student_id',  # ← أضف هنا
            'subjectName',
            'department',
            'year',
            'semester',
            'midterm_score',
            'midterm_score_max',
            'section_exam_score',
            'section_exam_score_max',
            'year_work_score',
            'year_work_score_max',
            'final_exam_score',
            'final_exam_score_max',
            'total_score',
            'total_score_max',
            'letter_grade',
            'percentage',
            'is_passed',
            'progress',
        ]
        read_only_fields = [
            'student_name',
            'student_id',  # ← أضف هنا كمان
            'subjectName',
            'department',
            'year',
            'semester',
            'midterm_score_max',
            'section_exam_score_max',
            'year_work_score_max',
            'final_exam_score_max',
            'total_score',
            'total_score_max',
            'letter_grade',
            'percentage',
            'is_passed',
            'progress',
        ]

    def get_student_name(self, obj):
        return obj.student.user.get_full_name() if obj.student and obj.student.user else ""

    def get_student_id(self, obj):
        return obj.student.student_id if obj.student else None

    def get_progress(self, obj):
        return int(obj.percentage) if obj.percentage is not None else 0

    def get_midterm_score_max(self, obj):
        return obj.grade_sheet.midterm_full_score

    def get_section_exam_score_max(self, obj):
        return obj.grade_sheet.section_exam_full_score

    def get_year_work_score_max(self, obj):
        return obj.grade_sheet.year_work_full_score

    def get_final_exam_score_max(self, obj):
        return obj.grade_sheet.final_exam_full_score

    def get_total_score_max(self, obj):
        return obj.grade_sheet.full_score
