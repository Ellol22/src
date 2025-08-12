from django.core.management.base import BaseCommand
from django.core.exceptions import ObjectDoesNotExist
from structure.models import StudentStructure, DepartmentChoices, AcademicYearChoices, SemesterChoices
from schedule.models import Schedule
from courses.models import Course
from accounts.models import Doctor
from datetime import datetime
import json
import os
import difflib
import re


class Command(BaseCommand):
    help = 'Load schedule data from JSON with robust course & instructor matching'

    def clean_instructor_name(self, name):
        """Remove prefixes like Dr., Eng., etc. (English + Arabic) and normalize spacing/capitalization."""
        if not name:
            return ''
        
        # Lowercase + strip spaces
        name = name.strip().lower()

        # Remove common prefixes regardless of spaces/dots
        prefix_pattern = r'^(dr|dr\.|eng|eng\.|م\.|د\.|دكتور|مهندس|د)\s*'
        name = re.sub(prefix_pattern, '', name, flags=re.IGNORECASE).strip()

        # Remove extra dots/commas and collapse multiple spaces
        name = re.sub(r'[.,]+', ' ', name)
        name = re.sub(r'\s+', ' ', name).strip()

        # Capitalize each word, keep full name (not just first name)
        name = ' '.join(word.capitalize() for word in name.split())
        return name

    def get_instructor_instance(self, raw_name):
        """Find Doctor object by name with cleaning & closest-match fallback."""
        name = self.clean_instructor_name(raw_name)
        if not name:
            return None

        all_names = list(Doctor.objects.values_list('name', flat=True))
        
        # Use closest match with a lower cutoff for more flexible matching
        close_matches = difflib.get_close_matches(name, all_names, n=1, cutoff=0.5)
        if close_matches:
            matched_name = close_matches[0]
            self.stdout.write(self.style.WARNING(
                f"⚠️ Using closest match for instructor '{raw_name}': '{matched_name}'"
            ))
            return Doctor.objects.get(name=matched_name)
        
        self.stdout.write(self.style.ERROR(
            f"❌ Instructor '{raw_name}' not found in Doctors table."
        ))
        return None

    def normalize(self, text):
        """Normalize text for matching: lowercase, remove punctuation, collapse spaces."""
        if not text:
            return ''
        text = text.lower()
        text = re.sub(r'[^a-z0-9\u0600-\u06FF\s]', ' ', text)  # Keep Arabic letters too
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def handle(self, *args, **kwargs):
        base_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(base_dir, '..', '..', 'json', 'ai_schedule.json')

        if not os.path.exists(json_path):
            self.stdout.write(self.style.ERROR(f"❌ JSON file not found: {json_path}"))
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            json_data = json.load(f)

        year_map = {
            'year_1': AcademicYearChoices.FIRST,
            'year_2': AcademicYearChoices.SECOND,
            'year_3': AcademicYearChoices.THIRD,
            'year_4': AcademicYearChoices.FOURTH,
        }

        semester_map = {
            'term_1': SemesterChoices.FIRST,
            'term_2': SemesterChoices.SECOND,
        }

        department_map = {
            'ai_department': DepartmentChoices.AI,
            'data_department': DepartmentChoices.DATA,
            'cyber_department': DepartmentChoices.CYBER,
            'autotronics_department': DepartmentChoices.AUTOTRONICS,
            'mechatronics_department': DepartmentChoices.MECHATRONICS,
            'garment_manufacturing_department': DepartmentChoices.GARMENT_MANUFACTURING,
            'control_systems_department': DepartmentChoices.CONTROL_SYSTEMS,
        }

        total_saved = 0
        total_missing_courses = 0
        total_missing_instructors = 0

        for department_key, years_dict in json_data.items():
            department_val = department_map.get(department_key)
            if not department_val:
                self.stdout.write(self.style.WARNING(f"Unknown department key in JSON: {department_key}"))
                continue

            for year_key, terms_dict in years_dict.items():
                year_val = year_map.get(year_key)
                if not year_val:
                    self.stdout.write(self.style.WARNING(f"Unknown year key in JSON: {year_key}"))
                    continue

                for term_key, schedules_list in terms_dict.items():
                    semester_val = semester_map.get(term_key)
                    if not semester_val:
                        self.stdout.write(self.style.WARNING(f"Unknown semester key in JSON: {term_key}"))
                        continue

                    try:
                        student_structure = StudentStructure.objects.get(
                            department=department_val,
                            year=year_val,
                            semester=semester_val
                        )
                    except ObjectDoesNotExist:
                        self.stdout.write(self.style.WARNING(
                            f"StudentStructure not found for department {department_val}, year {year_val}, semester {semester_val}"
                        ))
                        continue

                    # حذف القديم قبل الإضافة
                    deleted_count, _ = Schedule.objects.filter(student_structure=student_structure).delete()
                    if deleted_count:
                        self.stdout.write(self.style.WARNING(f"🗑️ Deleted {deleted_count} old schedules for {student_structure}"))

                    # تجهيز خريطة الكورسات
                    courses_qs = Course.objects.filter(structure=student_structure)
                    course_map = {self.normalize(c.name): c for c in courses_qs}
                    course_norm_names = list(course_map.keys())

                    saved_for_structure = 0

                    for sched in schedules_list:
                        section = sched.get('section', '').strip()
                        try:
                            start_time = datetime.strptime(sched['start_time'], '%H:%M').time()
                            end_time = datetime.strptime(sched['end_time'], '%H:%M').time()
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"Invalid time format in entry: {sched}. Error: {e}"))
                            continue

                        original_name = sched.get('course', '').strip()
                        if not original_name:
                            self.stdout.write(self.style.ERROR("Course name empty in JSON entry, skipping."))
                            total_missing_courses += 1
                            continue

                        # محاولة مطابقة مباشرة
                        course_obj = Course.objects.filter(structure=student_structure, name__iexact=original_name).first()

                        if not course_obj:
                            norm_name = self.normalize(original_name)
                            if norm_name in course_map:
                                course_obj = course_map[norm_name]
                            else:
                                close = difflib.get_close_matches(norm_name, course_norm_names, n=1, cutoff=0.6)
                                if close:
                                    matched_norm = close[0]
                                    course_obj = course_map[matched_norm]
                                    self.stdout.write(self.style.WARNING(
                                        f"⚠️ Using closest match for '{original_name}': '{course_obj.name}'"
                                    ))

                        if not course_obj:
                            self.stdout.write(self.style.ERROR(
                                f"❌ Course '{original_name}' not found for {student_structure}. Skipping entry."
                            ))
                            total_missing_courses += 1
                            continue

                        instructor_instance = self.get_instructor_instance(sched.get('instructor'))
                        if not instructor_instance and sched.get('instructor'):
                            total_missing_instructors += 1

                        Schedule.objects.create(
                            student_structure=student_structure,
                            day=sched.get('day'),
                            slot_number=sched.get('slot_number'),
                            start_time=start_time,
                            end_time=end_time,
                            section=section,
                            course=course_obj,
                            instructor=instructor_instance,
                            room=sched.get('room', '')
                        )
                        saved_for_structure += 1
                        total_saved += 1

                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Loaded {saved_for_structure} schedule entries for {student_structure}"
                    ))

        self.stdout.write(self.style.SUCCESS(
            f"\n🎉 All done. Saved schedules: {total_saved}. Missing courses: {total_missing_courses}. Missing instructors: {total_missing_instructors}."
        ))
