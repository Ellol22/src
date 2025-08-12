from rest_framework import serializers
from .models import Quiz, QuizQuestion, Assignment, AssignmentFile, QuizSubmission, Submission
from courses.models import Course
from accounts.models import Student
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, localtime
import pytz

# ----------------------------
# Quiz Question Serializer
# ----------------------------
class QuizQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizQuestion
        fields = ['id', 'text', 'options', 'correct_option']

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        request = self.context.get('request')
        if request and hasattr(request.user, 'student'):
            rep.pop('correct_option', None)
        return rep

    def validate_options(self, value):
        if not isinstance(value, list) or len(value) != 4:
            raise serializers.ValidationError("Exactly 4 options are required.")
        if not all(isinstance(opt, str) and opt.strip() for opt in value):
            raise serializers.ValidationError("All options must be non-empty strings.")
        return value

    def validate_correct_option(self, value):
        if value not in [0, 1, 2, 3]:
            raise serializers.ValidationError("Correct option must be between 0 and 3.")
        return value


# ----------------------------
# Quiz Serializer
# ----------------------------
class QuizSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True)
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())
    start_time = serializers.DateTimeField(required=False)
    end_time = serializers.DateTimeField()
    files = serializers.SerializerMethodField()
    student_status = serializers.SerializerMethodField()
    student_grade = serializers.SerializerMethodField()

    total_mark = serializers.DecimalField(max_digits=5, decimal_places=2)

    class Meta:
        model = Quiz
        fields = [
            'id', 'course', 'title', 'description', 'start_time', 'end_time',
            'questions', 'created_at', 'updated_at', 'files',
            'student_status', 'student_grade', 'total_mark'
        ]

    def get_files(self, obj):
        return [{'id': f.id, 'file_url': f.file.url} for f in obj.files.all()]

    def get_student_status(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'student'):
            submission = QuizSubmission.objects.filter(student=request.user.student, quiz=obj).first()
            if submission:
                return submission.status
            else:
                if timezone.now() > obj.end_time:
                    return 'ended'
                return 'not_started'
        return None

    def get_student_grade(self, obj):
        request = self.context.get('request')
        if request and hasattr(request.user, 'student'):
            submission = QuizSubmission.objects.filter(student=request.user.student, quiz=obj).first()
            if submission and submission.grade is not None:
                return submission.grade
        return None

    def validate(self, data):
        start_time = data.get('start_time') or (self.instance and self.instance.start_time)
        end_time = data.get('end_time')

        if start_time and end_time:
            if end_time <= start_time:
                raise serializers.ValidationError("End time must be after start time.")

            egypt_now = localtime(now(), timezone=pytz.timezone("Africa/Cairo"))
            if self.instance is None and end_time <= egypt_now:
                raise serializers.ValidationError("End time must be in the future.")

        if not self.instance and not data.get('questions'):
            raise serializers.ValidationError("At least one question is required.")

        return data

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        start_time = ret.get('start_time')
        end_time = ret.get('end_time')
        start = parse_datetime(start_time) if start_time else None
        end = parse_datetime(end_time) if end_time else None
        ret['duration'] = (end - start).total_seconds() / 60 if start and end else None
        return ret

    def create(self, validated_data):
        questions_data = validated_data.pop('questions')
        course = validated_data.pop('course')
        user = self.context['request'].user

        if not hasattr(user, 'doctor'):
            raise serializers.ValidationError("Only doctors can create quizzes.")

        if 'start_time' not in validated_data:
            validated_data['start_time'] = timezone.now()

        quiz = Quiz.objects.create(course=course, created_by=user.doctor, **validated_data)

        for question_data in questions_data:
            QuizQuestion.objects.create(quiz=quiz, **question_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop('questions', None)
        course = validated_data.pop('course', None)

        if course:
            instance.course = course

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if questions_data is not None:
            instance.questions.all().delete()
            for question_data in questions_data:
                QuizQuestion.objects.create(quiz=instance, **question_data)

        return instance


# ----------------------------
# Assignment File Serializer
# ----------------------------
class AssignmentFileSerializer(serializers.ModelSerializer):
    file = serializers.FileField()

    class Meta:
        model = AssignmentFile
        fields = ['id', 'file', 'uploaded_at']

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret['file_url'] = instance.file.url
        return ret


# ----------------------------
# Assignment Serializer
# ----------------------------
class AssignmentSerializer(serializers.ModelSerializer):
    files = AssignmentFileSerializer(many=True, read_only=True)

    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source='course',
        write_only=True
    )
    course_name = serializers.CharField(source='course.name', read_only=True)

    pdf_file = serializers.ListField(
        child=serializers.FileField(),
        write_only=True,
        required=False,
        source='uploaded_files'
    )

    class Meta:
        model = Assignment
        fields = [
            'id', 'course_id', 'course_name', 'title', 'description',
            'deadline', 'files', 'pdf_file',
            'total_mark',  # ✅ أضفنا الحقل هنا
            'created_at', 'updated_at'
        ]


    def validate(self, data):
        deadline = data.get('deadline')
        if deadline and deadline <= timezone.now():
            raise serializers.ValidationError("Deadline must be in the future.")
        return data

    def create(self, validated_data):
        files_data = self.context['request'].FILES.getlist('pdf_file')
        validated_data.pop('uploaded_files', None)

        course = validated_data.pop('course')

        if not hasattr(self.context['request'].user, 'doctor'):
            raise serializers.ValidationError("Only doctors can create assignments.")

        assignment = Assignment.objects.create(
            course=course,
            created_by=self.context['request'].user.doctor,
            **validated_data
        )

        for file in files_data:
            AssignmentFile.objects.create(assignment=assignment, file=file)

        return assignment

    def update(self, instance, validated_data):
        files_data = self.context['request'].FILES.getlist('uploaded_files')
        course = validated_data.pop('course', None)

        if course:
            instance.course = course

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if files_data:
            instance.files.all().delete()
            for file in files_data:
                AssignmentFile.objects.create(assignment=instance, file=file)

        return instance


# ----------------------------
# Quiz Submission Serializer
# ----------------------------
class QuizSubmissionSerializer(serializers.ModelSerializer):
    student = serializers.PrimaryKeyRelatedField(read_only=True)
    student_name = serializers.CharField(source='student.name', read_only=True)  # ✅ اسم الطالب من Student مباشرة
    student_code = serializers.CharField(source='student.student_id', read_only=True)  # ✅ كود الطالب
    quiz = serializers.PrimaryKeyRelatedField(read_only=True)
    total_mark = serializers.SerializerMethodField()

    class Meta:
        model = QuizSubmission
        fields = [
            'id',
            'student',
            'student_name',
            'student_code',         # ✅ أضفنا كود الطالب هنا
            'quiz',
            'answers',
            'submitted_at',
            'grade',
            'total_mark',
            'feedback',
            'status'
        ]

    def get_total_mark(self, obj):
        return obj.quiz.total_mark if obj.quiz else None





# ----------------------------
# Assignment Submission Serializer
# ----------------------------
class SubmissionSerializer(serializers.ModelSerializer):
    student = serializers.CharField(source='student.name', read_only=True)
    assignment = serializers.PrimaryKeyRelatedField(read_only=True)
    size = serializers.SerializerMethodField()
    total_mark = serializers.SerializerMethodField()  # ✅

    class Meta:
        model = Submission
        fields = ['id', 'student', 'assignment', 'file', 'size', 'answer_html', 'submitted_at', 'grade', 'feedback', 'total_mark']  # ✅

    def get_size(self, obj):
        if obj.file and hasattr(obj.file, 'size'):
            size_in_bytes = obj.file.size
            if size_in_bytes < 1024:
                return f"{size_in_bytes} B"
            elif size_in_bytes < 1024 * 1024:
                return f"{round(size_in_bytes / 1024)} KB"
            else:
                return f"{round(size_in_bytes / (1024 * 1024), 2)} MB"
        return None
    
    def get_total_mark(self, obj):
            return obj.assignment.total_mark if obj.assignment else None  # ✅