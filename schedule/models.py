from django.db import models
from accounts.models import Doctor
from courses.models import Course
from structure.models import StudentStructure  # استيراد الموديل من الابليكيشن التاني

# Lecture Type Choices
class LectureTypeChoices(models.TextChoices):
    Lecture = 'Lecture', 'Lecture'
    Section = 'Section', 'Section'

class Schedule(models.Model):
    student_structure = models.ForeignKey(StudentStructure, on_delete=models.CASCADE, related_name='schedules')
    course = models.ForeignKey(Course, on_delete=models.CASCADE,related_name="subject")  # << ربط بكورس حقيقي
    day = models.CharField(max_length=10)
    slot_number = models.PositiveIntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    section = models.CharField(max_length=10)  # e.g. "All" or "Sec 1", "Sec 2"
    instructor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True,related_name="doc")
    room = models.CharField(max_length=10)
    type = models.CharField(
        max_length=10,
        choices=LectureTypeChoices.choices,
        default=LectureTypeChoices.Lecture,
        editable=False,
        help_text="Automatically set to 'Lecture' if section is 'All'"
    )
    
    def save(self, *args, **kwargs):
        if self.section.strip().lower() == 'all':
            self.type = LectureTypeChoices.Lecture
        else:
            self.type = LectureTypeChoices.Section
        super().save(*args, **kwargs)

    
    def __str__(self):
        return f"{self.student_structure} - {self.day} Slot {self.slot_number} - {self.course} ({self.section})"
