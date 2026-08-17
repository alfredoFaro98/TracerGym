from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0024_bodymetric_note'),
    ]

    operations = [
        migrations.AddField(
            model_name='workoutsession',
            name='orario_fine',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
