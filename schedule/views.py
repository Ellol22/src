from rest_framework.decorators import api_view, permission_classes
from django.db.models import Case, When, Value, IntegerField
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Schedule , Doctor
from structure.models import StudentStructure
from .serializers import ScheduleSerializer
from accounts.models import Student
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Q
from .models import Schedule
from accounts.models import Student
from .serializers import ScheduleSerializer

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_schedule(request):
    print("✅ Request received at student_schedule")
    print("🔐 Authenticated user:", request.user)

    try:
        student = Student.objects.get(user=request.user)
        print("🎓 Student found:", student)
        print("📊 Student structure:", student.structure)

        structure = student.structure

        if not structure:
            print("⚠️ الطالب غير مرتبط ببنية دراسية")
            return Response({'error': 'الطالب غير مرتبط ببنية دراسية'}, status=400)

        student_section = f"Sec {student.sec_num}"
        print("🧩 Student section:", student_section)

        schedules = Schedule.objects.filter(
            student_structure=structure
        ).filter(
            Q(section="All") | Q(section=student_section)
        )
        print("📅 Schedules found:", schedules.count())

        serializer = ScheduleSerializer(schedules, many=True)
        print("✅ Serialized data ready to return")

        return Response(serializer.data)

    except Student.DoesNotExist:
        print("❌ Student.DoesNotExist")
        return Response({'error': 'الطالب غير موجود'}, status=404)

    except Exception as e:
        print("💥 Exception occurred:", str(e))
        return Response({'error': str(e)}, status=500)


##################################################################################
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def doctor_schedule(request):
    print("✅ Request received at doctor_schedule")
    print("🔐 Authenticated user (doctor):", request.user)

    try:
        doctor = Doctor.objects.get(user=request.user)
        print("🩺 Doctor found:", doctor)

        day_order = Case(
            When(day='Saturday', then=Value(1)),
            When(day='Sunday', then=Value(2)),
            When(day='Monday', then=Value(3)),
            When(day='Tuesday', then=Value(4)),
            When(day='Wednesday', then=Value(5)),
            When(day='Thursday', then=Value(6)),
            When(day='Friday', then=Value(7)),
            output_field=IntegerField(),
        )

        schedules = Schedule.objects.filter(instructor=doctor).order_by(day_order, 'slot_number')
        print("📅 Schedules found:", schedules.count())

        serializer = ScheduleSerializer(schedules, many=True)
        print("✅ Serialized data ready to return")
        print("📤 Response data:", serializer.data)  # ✅ دي السطر اللي هيطبع الريسبونس كامل

        return Response(serializer.data)

    except Doctor.DoesNotExist:
        print("❌ Doctor.DoesNotExist")
        return Response({'error': 'Doctor not found for this user.'}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print("💥 Exception occurred:", str(e))
        return Response({'error': str(e)}, status=500)
