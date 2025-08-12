import json
import os
from django.core.management.base import BaseCommand
from chatbot.models import Intent  # صححت هنا

class Command(BaseCommand):
    help = "Load intents from JSON file into the database"

    def handle(self, *args, **kwargs):
        file_path = os.path.join('chatbot', 'json', 'intents.json')
        with open(file_path, encoding='utf-8') as f:
            data = json.load(f)

        for item in data.get('intents', []):
            tag = item.get('tag')
            patterns = item.get('questions', [])
            responses = item.get('responses', [])

            intent, created = Intent.objects.update_or_create(
                tag=tag,
                defaults={'patterns': patterns, 'responses': responses}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f"Created intent: {tag}"))
            else:
                self.stdout.write(self.style.SUCCESS(f"Updated intent: {tag}"))
