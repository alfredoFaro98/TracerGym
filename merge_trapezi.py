import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tracker.models import Tag, Exercise

try:
    tag_trapezi, _ = Tag.objects.get_or_create(nome='Trapezi')
    try:
        tag_trapezio_sup = Tag.objects.get(nome='Trapezio sup.')
        # Trova gli esercizi e aggiorna il tag
        exercises_to_update = Exercise.objects.filter(tags=tag_trapezio_sup)
        count = 0
        for ex in exercises_to_update:
            ex.tags.remove(tag_trapezio_sup)
            ex.tags.add(tag_trapezi)
            count += 1
        
        # Elimina il vecchio tag
        tag_trapezio_sup.delete()
        print(f"Merged {count} exercises from 'Trapezio sup.' to 'Trapezi'. Tag 'Trapezio sup.' deleted.")
    except Tag.DoesNotExist:
        print("Tag 'Trapezio sup.' does not exist in the database.")

except Exception as e:
    print(f"An error occurred: {e}")
