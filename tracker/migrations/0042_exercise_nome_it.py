from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0041_workoutset_zavorra_kg'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='nome_it',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
    ]
