# students/serializers.py
from rest_framework import serializers

class AttendanceSummarySerializer(serializers.Serializer):
    course = serializers.CharField()
    department = serializers.CharField()
    year = serializers.CharField()
    semester = serializers.CharField()
    attended_lectures = serializers.IntegerField()
    total_lectures = serializers.IntegerField()
    percentage = serializers.FloatField()
    status = serializers.CharField()

