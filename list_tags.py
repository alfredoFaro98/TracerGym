import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tracker.models import Tag

print([t.nome for t in Tag.objects.all()])
