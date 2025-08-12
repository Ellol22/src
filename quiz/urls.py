from django.urls import path
from .views import (
    staff_courses, staff_quizzes, staff_quiz_detail,
    staff_assignments, staff_assignment_detail,
    student_courses, student_quizzes, student_quiz_detail,
    student_assignments, student_submit_assignment, student_delete_submission,
    quiz_submissions, grade_quiz_submission,
    task_submissions, grade_task_submission,
    my_quiz_submission, my_task_submission,
    create_quiz
)

urlpatterns = [
    # Staff endpoints
    path('courses/', staff_courses, name='staff-courses'), ##
    path('quizzes/instructor-quizzes/', staff_quizzes, name='staff-quizzes'), # GET ##
    path('quizzes/', create_quiz, name='staff-quiz-detail'), # POST ##
    path('quizzes/<int:quiz_id>/', staff_quiz_detail, name='staff-quiz-detail'), # PUT , GET , Delete ##

    path('tasks/instructor-tasks/', staff_assignments, name='staff-assignments'), ##
    path('tasks/<int:assignment_id>/', staff_assignment_detail, name='staff-assignment-detail'), ##

    path('quiz-submissions/quiz-submissions/<int:quiz_id>/', quiz_submissions, name='quiz-submissions'), ##
    path('quiz-submissions/<int:submission_id>/grade-quiz/', grade_quiz_submission, name='grade-quiz-submission'),

    path('submissions/task-submissions/<int:task_id>/', task_submissions, name='task-submissions'),
    path('submissions/<int:submission_id>/grade-submission/', grade_task_submission, name='grade-task-submission'),
    
    # Student endpoints
    path('courses/student-courses/', student_courses, name='student-courses'), ##
    path('quizzes/student-quizzes/', student_quizzes, name='student-quizzes'), ##
    path('quizzes/submit-quiz/<int:quiz_id>/', student_quiz_detail, name='student-quiz-detail'), ##
    path('tasks/student-tasks/', student_assignments, name='student-assignments'), ##
    path('submissions/assignments/<int:assignment_id>/submit/', student_submit_assignment, name='student-submit-assignment'),
    path('submissions/<int:submission_id>/delete/<int:task_id>/', student_delete_submission, name='student-delete-submission'),
    path('quiz-submissions/my-submission/<int:quiz_id>/', my_quiz_submission, name='my-quiz-submission'),
    path('submissions/my-submission/<int:task_id>/', my_task_submission, name='my-task-submission'),
]