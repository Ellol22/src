from django.db.models.signals import post_save
from django.dispatch import receiver
from accounts.models import Student
from courses.models import Course, StudentCourse
from structure.models import StudentStatusChoices, StudentStructure

# ترتيب السنوات علشان نقدر نقارن
year_order = {
    'First': 1,
    'Second': 2,
    'Third': 3,
    'Fourth': 4,
}

semester_order = {
    'First': 1,
    'Second': 2,
}

@receiver(post_save, sender=Student)
def auto_assign_courses_to_student(sender, instance, **kwargs):
    student = instance

    if not student.structure:
        return

    structure = student.structure
    status = structure.status

    # امسح أي مواد قديمة مرتبطة بالطالب
    StudentCourse.objects.filter(student=student).delete()

    # 🧠: أولًا نرجع كل المواد من السنين اللي فاتت (أقل من السنة الحالية)
    previous_structures = []
    for year, y_val in year_order.items():
        for sem, s_val in semester_order.items():
            if y_val < year_order[structure.year]:
                previous_structures.append((year, sem))
            elif y_val == year_order[structure.year] and s_val < semester_order[structure.semester]:
                previous_structures.append((year, sem))

    past_structures = StudentStructure.objects.filter(
        department=structure.department,
        year__in=[y for y, _ in previous_structures],
        semester__in=[s for _, s in previous_structures]
    )

    courses = list(Course.objects.filter(structure__in=past_structures))

    # 🧠: بعد كدا نضيف مواد الترم الحالي بناءً على حالة الطالب
    if status == StudentStatusChoices.PASSED:
        # لو ناجح → ياخد مواد الترم الحالي بالكامل
        current_courses = Course.objects.filter(structure=structure)
        courses += list(current_courses)

    elif status in [StudentStatusChoices.SUMMER, StudentStatusChoices.RETAKE_YEAR]:
        # لو summer أو retake → ياخد المواد اللي سقط فيها فقط
        failed_course_names = structure.failed_courses_names or []
        current_failed_courses = Course.objects.filter(
            structure=structure,
            name__in=failed_course_names
        )
        courses += list(current_failed_courses)

    # أضف المواد للطالب
    for course in courses:
        StudentCourse.objects.get_or_create(student=student, course=course)
