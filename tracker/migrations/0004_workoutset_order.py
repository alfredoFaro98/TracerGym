from django.db import migrations, models

def set_initial_order(apps, schema_editor):
    WorkoutSet = apps.get_model('tracker', 'WorkoutSet')
    from collections import defaultdict
    session_sets = defaultdict(list)
    for ws in WorkoutSet.objects.order_by('session_id', 'id'):
        session_sets[ws.session_id].append(ws)
    for sets in session_sets.values():
        for i, ws in enumerate(sets):
            ws.order = i
            ws.save()

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0003_musclegroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutset',
            name='order',
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.RunPython(set_initial_order, migrations.RunPython.noop),
    ]
