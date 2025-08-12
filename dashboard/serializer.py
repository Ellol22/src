from rest_framework import serializers
from accounts.models import Doctor, Student
from django.contrib.auth.models import User

# from courses.models import Course
from .models import Announcement

class StudentSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    first_name = serializers.CharField(source='user.first_name', read_only=True)
    structure = serializers.PrimaryKeyRelatedField(read_only=True)  # عشان يرجع ID مش object كامل
    image = serializers.SerializerMethodField()  # هنجيب الصورة يدويًا

    class Meta:
        model = Student
        fields = ['username', 'first_name', 'email', 'name', 'mobile', 'national_id', 'structure', 'image']

    def get_image(self, obj):
        try:
            return obj.dash.image.url if obj.dash and obj.dash.image else None
        except:
            return None

class DoctorSerializer(serializers.ModelSerializer):
    courses = serializers.SerializerMethodField()
    email = serializers.EmailField(source='user.email', read_only=True)
    departments = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = ['name', 'national_id', 'mobile', 'image', 'structures', 'email', 'courses' , 'departments']

    def get_courses(self, obj):
        return [course.name for course in obj.courses.all()]  # أو أي تمثيل للكورسات

    image = serializers.SerializerMethodField()

    def get_image(self, obj):
        try:
            return obj.dash.image.url if obj.dash and obj.dash.image else None
        except:
            return None


    def get_departments(self, obj):
        return list(set([
            structure.department.name  # أو structure.department لو عايزة ID
            for structure in obj.structures.all()
            if structure.department
        ]))



############################################################################
from rest_framework import serializers
from .models import Announcement
from accounts.models import Doctor  # أو Student أو User حسب نوع created_by

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = '__all__'  # أو عدلها إلى: ['id', 'title', 'content', 'created_at', 'created_by_name']
        extra_kwargs = {
            'created_by': {'required': False, 'write_only': True},  # لنرسله أثناء الإنشاء فقط
            'created_at': {'required': False}
        }

    def get_created_by_name(self, obj):
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None

    def to_internal_value(self, data):
        # تعديل أسماء الحقول من الفرونت
        modified_data = data.copy()

        if 'message' in modified_data:
            modified_data['content'] = modified_data.pop('message')
        if 'date' in modified_data:
            modified_data['created_at'] = modified_data.pop('date')

        return super().to_internal_value(modified_data)





##################################################################################
from rest_framework import serializers
from .models import Notifications
from courses.models import Course
from structure.models import StudentStructure

class NotificationSerializer(serializers.ModelSerializer):
    # 📥 حقل كتابة: إدخال course ID
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )

    # 📤 حقل قراءة: اسم المادة
    course = serializers.CharField(source='course.name', read_only=True)

    # 📤 حقل قراءة: اسم الدكتور بالكامل (من User المرتبط)
    sender = serializers.CharField(source='sender.user.username', read_only=True)

    class Meta:
        model = Notifications
        fields = [
            'id',
            'title',
            'message',
            'created_at',
            'course_id',  # input فقط
            'course',     # output فقط (name)
            'sender',     # output فقط
        ]





class StructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentStructure
        fields = ['department', 'year', 'semester']

class CourseSerializer(serializers.ModelSerializer):
    structure = StructureSerializer()

    class Meta:
        model = Course
        fields = ['id', 'name', 'structure']
