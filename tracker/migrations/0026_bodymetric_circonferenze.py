from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0025_workoutsession_orario_fine'),
    ]

    operations = [
        migrations.AddField(
            model_name='bodymetric',
            name='vita_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='bodymetric',
            name='torace_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='bodymetric',
            name='braccia_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
        migrations.AddField(
            model_name='bodymetric',
            name='cosce_cm',
            field=models.DecimalField(blank=True, decimal_places=1, max_digits=5, null=True),
        ),
    ]
