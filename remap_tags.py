import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tracker.models import Exercise, Tag

# Helper function similar to our JS logic
def match_exercise(nome, tags, required_macro, include_keywords=None, exclude_keywords=None):
    if required_macro not in tags:
        return False
    
    nome_lower = nome.lower()
    match = True
    if include_keywords:
        match = any(k.lower() in nome_lower for k in include_keywords)
    if match and exclude_keywords:
        match = not any(k.lower() in nome_lower for k in exclude_keywords)
    return match

exercises = Exercise.objects.prefetch_related('tags').all()

new_mappings = {
    'Polpacci': lambda nome, tags: match_exercise(nome, tags, 'gambe', ['calf', 'polpacci']),
    'Quadricipiti': lambda nome, tags: match_exercise(nome, tags, 'gambe', ['squat', 'pressa', 'extension', 'affondi', 'leg extension'], ['bulgaro', 'jefferson', 'sissy', 'curl', 'stacchi']),
    'Addominali': lambda nome, tags: match_exercise(nome, tags, 'addome', [], ['obliquo', 'russian', 'side', 'twist']),
    'Obliqui': lambda nome, tags: match_exercise(nome, tags, 'addome', ['obliqu', 'russian', 'twist', 'side']),
    'Bicipiti': lambda nome, tags: match_exercise(nome, tags, 'bicipiti'),
    'Deltoide Anteriore e Laterale': lambda nome, tags: match_exercise(nome, tags, 'spalle', ['frontali', 'lento', 'press', 'laterali', 'military'], ['dietro', '90', 'inverso']),
    'Pettorali': lambda nome, tags: match_exercise(nome, tags, 'pettorali'),
    'Trapezi': lambda nome, tags: match_exercise(nome, tags, 'spalle', ['shrug', 'rematore verticale', 'tirate']),
    'Deltoide Posteriore': lambda nome, tags: match_exercise(nome, tags, 'spalle', ['90 gradi', 'inverso', 'posteriori', 'a 90']),
    'Romboidi': lambda nome, tags: match_exercise(nome, tags, 'dorsali', ['rematore', 'pulley']),
    'Gran Dorsale': lambda nome, tags: match_exercise(nome, tags, 'dorsali', ['trazioni', 'lat machine', 'pullover', 'chin up', 'dorsy', 'nautilus']),
    'Lombari': lambda nome, tags: match_exercise(nome, tags, 'dorsali', ['iperestensioni', 'goodmorning', 'stacchi']),
    'Tricipiti': lambda nome, tags: match_exercise(nome, tags, 'tricipiti'),
    'Glutei': lambda nome, tags: match_exercise(nome, tags, 'gambe', ['glute', 'ponte', 'abductor', 'adductor', 'bulgaro', 'squat'], ['front', 'jefferson']),
    'Ischio-Crurali': lambda nome, tags: match_exercise(nome, tags, 'gambe', ['curl', 'stacchi gambe tese']),
    'Cardio': lambda nome, tags: match_exercise(nome, tags, 'cardio'),
}

# Non eliminiamo i tag subito per non perdere le relazioni
# Creiamo in anticipo i nuovi tag
new_tags = {}
for t_name in list(new_mappings.keys()) + ['Altro']:
    tag_obj, _ = Tag.objects.get_or_create(nome=t_name)
    new_tags[t_name] = tag_obj

mapped_count = 0
unmapped = []

for ex in exercises:
    old_tag_names = [t.nome.lower() for t in ex.tags.all()]
    assigned_tags = []
    
    for new_tag_name, func in new_mappings.items():
        if func(ex.nome, old_tag_names):
            assigned_tags.append(new_tags[new_tag_name])
            
    if not assigned_tags:
        assigned_tags.append(new_tags['Altro'])
        unmapped.append(ex.nome)
        
    ex.tags.set(assigned_tags)
    mapped_count += 1

# Delete old tags that are not in new_tags
for tag in Tag.objects.all():
    if tag.nome not in new_tags:
        tag.delete()

print(f"Successfully mapped {mapped_count} exercises.")
print(f"Unmapped exercises (put in 'Altro'): {len(unmapped)}")
for u in unmapped:
    print(f" - {u}")
