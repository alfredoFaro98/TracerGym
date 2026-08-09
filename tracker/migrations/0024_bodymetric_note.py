from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0023_bodymetric_orario'),
    ]

    operations = [
        migrations.AddField(
            model_name='bodymetric',
            name='note',
            field=models.CharField(blank=True, default='', max_length=100),
        ),
    ]
