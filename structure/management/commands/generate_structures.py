from django.core.management.base import BaseCommand
from structure.models import StudentStructure, DepartmentChoices, AcademicYearChoices, SemesterChoices

class Command(BaseCommand):
    help = "Generate StudentStructure records for all departments, years, and semesters."

    def handle(self, *args, **kwargs):
        count = 0
        for dept in DepartmentChoices.values:
            for year in [AcademicYearChoices.FIRST, AcademicYearChoices.SECOND, AcademicYearChoices.THIRD, AcademicYearChoices.FOURTH]:
                for semester in [SemesterChoices.FIRST, SemesterChoices.SECOND]:
                    obj, created = StudentStructure.objects.get_or_create(
                        department=dept,
                        year=year,
                        semester=semester
                    )
                    if created:
                        count += 1
                        self.stdout.write(self.style.SUCCESS(
                            f"✅ Created: {dept} - {year} - {semester}"
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f"⚠️ Already exists: {dept} - {year} - {semester}"
                        ))

        self.stdout.write(self.style.SUCCESS(f"\n🎯 Done! Created {count} new structures."))