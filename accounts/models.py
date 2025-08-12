
import logging
from django.db import models
from django.contrib.auth.models import User
from structure.models import StudentStructure
from collections import defaultdict

# Set up logging
logger = logging.getLogger(__name__)

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=25)
    mobile = models.CharField(max_length=11, blank=True, null=True)
    national_id = models.CharField(max_length=14)
    student_id = models.CharField(  # ✅ ده رقم الجلوس
        max_length=10,
        unique=True,
        null=True,  # عشان الطلبة القديمة اللي لسه مالهمش رقم جلوس
        blank=True,
        db_index=True
        )
    sec_num = models.IntegerField(null=True, blank=True)
    structure = models.ForeignKey(StudentStructure, on_delete=models.SET_NULL, null=True, blank=True, related_name="student_structure")

    def __str__(self):
        return f"{self.name} ({self.student_id or self.pk})"


    def get_my_courses(self):
        from courses.models import Course
        if self.structure:
            logger.debug("Fetching courses for student: %s", self.name)
            return Course.objects.filter(
                department=self.structure.department,
                academic_year=self.structure.year,
                semester=self.structure.semester
            )
        logger.warning("No structure found for student: %s", self.name)
        return Course.objects.none()

    def get_all_department_courses_grouped(self):
        from courses.models import Course
        if not self.structure:
            logger.warning("No structure found for student: %s", self.name)
            return {}

        logger.debug("Fetching grouped courses for student: %s", self.name)
        courses = Course.objects.filter(structure__department=self.structure.department)
        grouped = defaultdict(list)

        for course in courses:
            key = f"{course.structure.year} - {course.structure.semester}"
            grouped[key].append(course)

        return dict(grouped)

    class Meta:
        indexes = [
            models.Index(fields=['national_id']),
        ]

class DoctorRole(models.TextChoices):
    SUBJECT_DOCTOR = 'subject_doctor', 'دكتور مادة'
    ADMIN_DOCTOR = 'admin_doctor', 'دكتور إداري'
    TEACHING_ASSISTANT = 'teaching_assistant', 'معيد'

class Doctor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=True, null=True)
    name = models.CharField(max_length=25)
    mobile = models.CharField(max_length=11, blank=True, null=True)
    national_id = models.CharField(max_length=14, unique=True)
    role = models.CharField(
        max_length=20,
        choices=DoctorRole.choices,
        default=DoctorRole.SUBJECT_DOCTOR
    )
    structures = models.ManyToManyField('structure.StudentStructure', blank=True, related_name="doctor_structure")

    def __str__(self):
        return f"{self.name} ({self.get_role_display()})"

    def get_my_courses(self):
        from courses.models import Course
        logger.debug("Fetching courses for doctor: %s", self.name)
        return Course.objects.filter(doctor=self)

    class Meta:
        indexes = [
            models.Index(fields=['national_id']),
        ]
