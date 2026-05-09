from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0004_workoutset_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='exercise',
            name='tipologia',
            field=models.CharField(blank=True, default='', max_length=120),
        ),
    ]
