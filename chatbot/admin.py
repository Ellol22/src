# chat/admin.py
from django.contrib import admin
from .models import Intent

@admin.register(Intent)
class IntentAdmin(admin.ModelAdmin):
    list_display = ('tag',)
