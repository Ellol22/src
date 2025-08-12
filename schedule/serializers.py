from rest_framework import serializers
from .models import Schedule

class ScheduleSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    instructor_name = serializers.SerializerMethodField()
    department = serializers.CharField(source='student_structure.department', read_only=True)
    year = serializers.CharField(source='student_structure.year', read_only=True)

    class Meta:
        model = Schedule
        fields = [
                    'id',
                    'day', 'slot_number', 'start_time', 'end_time', 'section',
                    'room', 'type', 'course_name', 'instructor_name',
                    'department', 'year'
                ]
    def get_instructor_name(self, obj):
        if obj.instructor:
            prefix = ''
            if obj.instructor.role == 'teaching_assistant':
                prefix = 'Eng. '
            else:
                prefix = 'Dr. '
            return f"{prefix}{obj.instructor.name}"
        return None
