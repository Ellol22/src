from django.core.management.base import BaseCommand
import json
from courses.models import Course
from structure.models import DepartmentChoices, AcademicYearChoices, SemesterChoices, StudentStructure


def map_academic_year(year_key):
    return {
        'year_1': AcademicYearChoices.FIRST,
        'year_2': AcademicYearChoices.SECOND,
        'year_3': AcademicYearChoices.THIRD,
        'year_4': AcademicYearChoices.FOURTH,
    }.get(year_key)


def map_semester(term_key):
    return {
        'term_1': SemesterChoices.FIRST,
        'term_2': SemesterChoices.SECOND,
    }.get(term_key)


class Command(BaseCommand):
    help = 'Reload Industrial Control department courses from JSON (clear old and add new)'

    def handle(self, *args, **kwargs):
        json_path = 'data/control_sys_courses.json'  # تأكد من اسم الملف
        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"❌ File not found: {json_path}"))
            return

        control_courses = data.get('industrial_control', {})

        # 🗑️ حذف الكورسات القديمة للقسم
        deleted, _ = Course.objects.filter(structure__department=DepartmentChoices.CONTROL_SYSTEMS).delete()
        self.stdout.write(self.style.WARNING(f"🗑️ Deleted {deleted} old courses from Industrial Control department"))

        count = 0
        for year_key, year_data in control_courses.items():
            academic_year = map_academic_year(year_key)

            for term_key, courses in year_data.items():
                semester = map_semester(term_key)

                if not academic_year or not semester:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ Invalid academic year or semester: {year_key}, {term_key}"
                    ))
                    continue

                # 🔍 جلب StudentStructure المناسب
                try:
                    structure = StudentStructure.objects.get(
                        department=DepartmentChoices.CONTROL_SYSTEMS,
                        year=academic_year,
                        semester=semester
                    )
                except StudentStructure.DoesNotExist:
                    self.stdout.write(self.style.WARNING(
                        f"⚠️ No StudentStructure found for Control Systems, {academic_year}, {semester}"
                    ))
                    continue

                # ➕ إنشاء الكورسات
                for name in courses:
                    Course.objects.create(
                        name=name,
                        structure=structure
                    )
                    count += 1

        self.stdout.write(self.style.SUCCESS(f"✅ Successfully added {count} new courses for Industrial Control department"))
