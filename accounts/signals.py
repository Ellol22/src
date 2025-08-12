from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from accounts.models import Student, Doctor
from courses.models import Course, StudentCourse, StudentStructure
from itertools import chain

User = get_user_model()

# ========== ✅ مزامنة الاسم ==========
@receiver(post_save, sender=User)
def sync_user_name_to_profile(sender, instance, **kwargs):
    user = instance
    if hasattr(user, 'student'):
        if user.student.name != user.first_name:
            user.student.name = user.first_name
            user.student.save(update_fields=['name'])

    elif hasattr(user, 'doctor'):
        if user.doctor.name != user.first_name:
            user.doctor.name = user.first_name
            user.doctor.save(update_fields=['name'])


@receiver(post_save, sender=Student)
def sync_student_name_to_user(sender, instance, **kwargs):
    student = instance
    if student.user and student.user.first_name != student.name:
        student.user.first_name = student.name
        student.user.save(update_fields=['first_name'])


@receiver(post_save, sender=Doctor)
def sync_doctor_name_to_user(sender, instance, **kwargs):
    doctor = instance
    if doctor.user and doctor.user.first_name != doctor.name:
        doctor.user.first_name = doctor.name
        doctor.user.save(update_fields=['first_name'])


# ========== 🧠 تذكُّر الـ structure الأديم ==========
@receiver(pre_save, sender=Student)
def remember_old_structure(sender, instance, **kwargs):
    if instance.pk:
        try:
            old_student = Student.objects.get(pk=instance.pk)
            instance._old_structure = old_student.structure
        except Student.DoesNotExist:
            instance._old_structure = None
    else:
        instance._old_structure = None


# ========== 📚 ربط الطالب بالكورسات تلقائيًا ==========
@receiver(post_save, sender=Student)
def auto_assign_courses_to_student(sender, instance, created=False, **kwargs):
    student = instance

    if not student.structure:
        return

    if not hasattr(student, '_old_structure') or student.structure != student._old_structure:
        # امسح المواد القديمة
        StudentCourse.objects.filter(student=student).delete()

        # التركيبات اللي عايز أجيبها
        valid_structures = [
            ('First', 'First'),
            ('First', 'Second'),
            ('Second', 'First'),
            ('Second', 'Second'),
            ('Third', 'First'),
            ('Third', 'Second'),
            ('Fourth', 'First'),
            ('Fourth', 'Second'),
        ]

        # استخدم filter بدل get لتجنب الخطأ
        structure_matches = list(chain.from_iterable(
            StudentStructure.objects.filter(
                year=year,
                semester=sem,
                department=student.structure.department
            )
            for year, sem in valid_structures
        ))

        # هات المواد اللي ليها نفس structure
        matched_courses = Course.objects.filter(structure__in=structure_matches)

        for course in matched_courses:
            StudentCourse.objects.create(student=student, course=course)
