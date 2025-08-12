from django.urls import path
from . import views

urlpatterns = [
    path('create_lecture/', views.create_lecture_api, name='create_lecture_api'),#
    # يستخدمه الدكتور: 
    # - GET: لجلب قائمة المواد المرتبطة بالدكتور عشان يختار منها لإنشاء محاضرة.
    # - POST: لإنشاء محاضرة جديدة (بتاخد course_id, lecture_date, lecture_name).
    # الربط مع Flutter: واجهة الدكتور بتعمل طلب GET لعرض المواد، وطلب POST لإنشاء المحاضرة.

    path('get_latest_code/<int:lecture_id>/', views.get_latest_code_api, name='get_latest_code_api'),
    # يستخدمه الدكتور: 
    # - GET: لجلب آخر كود 6 أرقام مولد لمحاضرة معينة (مع وقت التوليد).
    # الربط مع Flutter: واجهة الدكتور بتعمل طلب GET كل دقيقة عشان تعرض الكود الجديد للطلاب.

    path('verify_code/', views.verify_code_api, name='verify_code_api'), #
    # يستخدمه الطالب: 
    # - GET: للتحقق من الكود الـ 6 أرقام اللي الطالب دخله (بتاخد code كـ query parameter).
    # الربط مع Flutter: واجهة الطالب بترسل الكود المدخل في TextField عشان تتحقق منه.

    path('verify_location/', views.verify_location_api, name='verify_location_api'), #
    # يستخدمه الطالب: 
    # - POST: للتحقق إذا كان الطالب في الموقع الجغرافي الصحيح (بتاخد latitude, longitude, course_id, student_structure_id).
    # الربط مع Flutter: واجهة الطالب بترسل إحداثيات الموقع بعد التحقق من الكود.

    path('register_face/', views.register_face_api, name='register_face_api'),
    # يستخدمه الطالب: 
    # - POST: لتسجيل الوجه بتاع الطالب (بتاخد 3 صور للوجه لتدريب الموديل).
    # الربط مع Flutter: واجهة الطالب بترسل الصور التلاتة عشان تسجل بيانات الوجه.

    path('verify_face/', views.verify_face_api, name='verify_face_api'),
    # يستخدمه الطالب: 
    # - POST: للتحقق من وجه الطالب وتسجيل الحضور (بتاخد lecture_id وصورة الوجه).
    # الربط مع Flutter: واجهة الطالب بترسل صورة الوجه بعد التحقق من الكود والموقع.

    path('open_lectures/', views.get_open_lectures_for_student, name='get_open_lectures_for_student'),
    # يستخدمه الطالب: 
    # - GET: لجلب قائمة المحاضرات المفتوحة للحضور (اللي لسه فيها أكواد نشطة).
    # الربط مع Flutter: واجهة الطالب بتعمل طلب GET عشان تعرض المحاضرات المتاحة لتسجيل الحضور.

    path('student/', views.student_attendance_summary, name='student_attendance_summary'),
    # يستخدمه الطالب: 
    # - GET: لجلب ملخص حضور الطالب في كل المواد (عدد المحاضرات الحاضرها، النسبة، الحالة).
    # الربط مع Flutter: واجهة الطالب بتعرض الملخص ده في صفحة الحضور بتاعته.

    path('doctor/', views.doctor_attendance_overview, name='doctor_attendance_overview'),
    # يستخدمه الدكتور: 
    # - GET: لجلب نظرة عامة على حضور الطلاب في كل المحاضرات لمواد الدكتور.
    # الربط مع Flutter: واجهة الدكتور بتعرض جدول بكل الطلاب وحضورهم في المحاضرات.


    path('summary/students/', views.doctor_students_attendance_summary, name='doctor_students_attendance_summary'),


]