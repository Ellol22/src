# chat/models.py
from django.db import models

class Intent(models.Model):
    tag = models.CharField(max_length=100, unique=True)
    patterns = models.JSONField()  # قائمة الجمل أو الأسئلة
    responses = models.JSONField()  # قائمة الردود

    def __str__(self):
        return self.tag
