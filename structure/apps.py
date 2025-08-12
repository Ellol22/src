# structure/apps.py

from django.apps import AppConfig

class StructureConfig(AppConfig):
    name = 'structure'

    def ready(self):
        pass
