# في accounts/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from accounts.models import Student
from courses.serializers import CourseSerializer

class DepartmentCoursesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            student = Student.objects.get(user=request.user)
        except Student.DoesNotExist:
            return Response({'error': 'Student not found.'}, status=404)

        grouped = student.get_all_department_courses_grouped()

        response_data = []
        for key, course_list in grouped.items():
            serializer = CourseSerializer(course_list, many=True)
            response_data.append({
                'year_semester': key,
                'courses': serializer.data
            })
        # print("\n regulations : \n",response_data)
        return Response(response_data)
