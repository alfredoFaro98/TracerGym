from django.db import migrations, models

MUSCLES = [
    'Petto', 'Dorso', 'Spalle', 'Bicipiti', 'Tricipiti',
    'Quadricipiti', 'Femorali', 'Glutei', 'Addome', 'Polpacci',
    'Trapezio', 'Lombari', 'Avambracci',
]

def add_muscles(apps, schema_editor):
    MuscleGroup = apps.get_model('tracker', 'MuscleGroup')
    for name in MUSCLES:
        MuscleGroup.objects.get_or_create(nome=name)

class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0002_workoutset_rest_time_alter_exercise_id_alter_tag_id_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='MuscleGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=50, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='workoutset',
            name='muscles',
            field=models.ManyToManyField(blank=True, related_name='sets', to='tracker.MuscleGroup'),
        ),
        migrations.RunPython(add_muscles, migrations.RunPython.noop),
    ]
