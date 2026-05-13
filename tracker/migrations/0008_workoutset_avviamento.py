from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0007_workoutset_per_lato'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutset',
            name='avviamento',
            field=models.BooleanField(default=False),
        ),
    ]
