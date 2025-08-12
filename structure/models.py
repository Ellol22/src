from django.db import models
from django.apps import apps



# الأقسام
class DepartmentChoices(models.TextChoices):
    AI = 'AI', 'Artificial Intelligence'
    DATA = 'DATA', 'Data Science'
    CYBER = 'CYBER', 'Cyber Security'
    AUTOTRONICS = 'AUTOTRONICS', 'Autotronics'
    MECHATRONICS = 'MECHATRONICS', 'Mechatronics'
    GARMENT_MANUFACTURING = 'GARMENT_MANUFACTURING', 'Garment Manufacturing'
    CONTROL_SYSTEMS = 'CONTROL_SYSTEMS', 'Control Systems'

# السنوات الدراسية
class AcademicYearChoices(models.TextChoices):
    FIRST = 'First', 'First Year'
    SECOND = 'Second', 'Second Year'
    THIRD = 'Third', 'Third Year'
    FOURTH = 'Fourth', 'Fourth Year'

# الترم
class SemesterChoices(models.TextChoices):
    FIRST = 'First', 'First Semester'
    SECOND = 'Second', 'Second Semester'

# حالة الطالب
class StudentStatusChoices(models.TextChoices):
    ACTIVE = 'active', 'Active'
    PASSED = 'passed', 'Passed'
    SUMMER = 'summer', 'Summer Course'
    RETAKE_YEAR = 'retake_year', 'Retake Year'



class StudentStructure(models.Model):
    def some_method(self):
        Course = apps.get_model('courses', 'Course')
    department = models.CharField(max_length=25, choices=DepartmentChoices.choices)
    year = models.CharField(max_length=6, choices=AcademicYearChoices.choices)
    semester = models.CharField(max_length=6, choices=SemesterChoices.choices)
    status = models.CharField(
        max_length=20, choices=StudentStatusChoices.choices, default=StudentStatusChoices.PASSED
    )
    
    # ⛔ ده فقط للأسامي، ومالوش علاقة بالعلاقات الحقيقية بين الكورسات
    failed_courses_names = models.JSONField(default=list, blank=True)

    # ✅ دا اللي محتاج تضيفه علشان تستخدم set() و clear()
    failed_courses = models.ManyToManyField('courses.Course', blank=True, related_name="failed_structures")

    def __str__(self):
        return f"{self.get_department_display()} - {self.get_year_display()} - {self.get_semester_display()} - {self.get_status_display()}"

    @property
    def student(self):
        return self.student_structure.first()




# موديل السمر كورس
class SummerCourseEnrollment(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} - {self.course}"


# موديل المواد اللي الطالب سقط فيها بعد السمر كورس
class FailedSummerCourseSubject(models.Model):
    student = models.ForeignKey('accounts.Student', on_delete=models.CASCADE)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE)
    year = models.CharField(max_length=6, choices=AcademicYearChoices.choices)
    semester = models.CharField(max_length=6, choices=SemesterChoices.choices)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course', 'year', 'semester')

    def __str__(self):
        return f"{self.student} - {self.course} ({self.year} - {self.semester})"


