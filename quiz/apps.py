from django.apps import AppConfig

class QuizzesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quiz'

    def ready(self):
        import quiz.signals  # Import signals to register them