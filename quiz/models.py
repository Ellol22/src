from django.db import models
from accounts.models import Doctor, Student
from courses.models import Course

class Quiz(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='quizzes')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    created_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='created_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    total_mark = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # ✅ إضافة درجة الكويز

    def __str__(self):
        return f"{self.title} - {self.course.name}"


class QuizQuestion(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    options = models.JSONField()
    correct_option = models.PositiveSmallIntegerField()

    def __str__(self):
        return f"Question: {self.text} (Quiz: {self.quiz.title})"


class QuizSubmission(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='quiz_submissions')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='submissions')
    answers = models.JSONField()
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[('not_started', 'Not Started'), ('ended', 'Ended')], default='not_started')

    class Meta:
        unique_together = ('student', 'quiz')

    def calculate_score(self):
        correct_answers = 0
        total_questions = self.quiz.questions.count()

        for q_id, selected in self.answers.items():
            try:
                question = self.quiz.questions.get(id=q_id)
                if selected == question.correct_option:
                    correct_answers += 1
            except QuizQuestion.DoesNotExist:
                continue  # لو السؤال اتحذف أو غير موجود

        if total_questions == 0:
            self.grade = 0
        else:
            self.grade = (correct_answers / total_questions) * float(self.quiz.total_mark)  # ✅ بدل 100

        self.save()


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    deadline = models.DateTimeField()
    created_by = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, related_name='created_assignments')
    total_mark = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)  # ✅ أضفنا ده هنا
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.course.name}"



class AssignmentFile(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='files')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='files', null=True, blank=True)
    file = models.FileField(upload_to='assignments/files/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File: {self.file.name} (Assignment: {self.assignment.title if self.assignment else 'Quiz'})"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    file = models.FileField(upload_to='assignments/submissions/')
    answer_html = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-submitted_at']
