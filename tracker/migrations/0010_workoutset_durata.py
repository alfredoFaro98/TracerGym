from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0009_exerciseimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='workoutset',
            name='reps',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='workoutset',
            name='durata',
            field=models.PositiveIntegerField(blank=True, help_text='Durata in secondi', null=True),
        ),
    ]
