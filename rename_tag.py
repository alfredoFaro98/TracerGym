import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tracker.models import Tag

try:
    tag = Tag.objects.get(nome='Pettorali')
    tag.nome = 'Petto'
    tag.save()
    print("Tag 'Pettorali' successfully renamed to 'Petto'.")
except Tag.DoesNotExist:
    print("Tag 'Pettorali' does not exist in the database.")
except Exception as e:
    print(f"An error occurred: {e}")
