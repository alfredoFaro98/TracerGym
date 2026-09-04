from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0040_fibre'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutset',
            name='zavorra_kg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True),
        ),
    ]
