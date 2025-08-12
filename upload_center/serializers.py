from rest_framework import serializers
from courses.models import Course
from .models import UploadFile
from courses.serializers import CourseSerializer  # لو حابب تبعته مع الرد

# students/serializers.py (ضيفه هنا مثلا)

class StudentSubjectFilesSerializer(serializers.Serializer):
    year = serializers.CharField()
    semester = serializers.CharField()
    subject = serializers.CharField()
    files = serializers.ListField(child=serializers.DictField())

class UploadFileSerializer(serializers.ModelSerializer):
    # لو حابب ترجع بيانات الكورس مع كل ملف مرفوع
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    # لو عايز ترجع بيانات الكورس كاملة بدل الايدي فقط:
    # course = CourseSerializer(read_only=True)

    class Meta:
        model = UploadFile
        fields = ['id', 'course', 'uploaded_by', 'file', 'uploaded_at']
        read_only_fields = ['uploaded_by', 'uploaded_at']

# مفيش داعي لـ SubjectSerializer لو مش هتستخدم السبجكت خالص في الفيوز
