from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0022_sitevisit'),
    ]

    operations = [
        migrations.AddField(
            model_name='bodymetric',
            name='orario',
            field=models.TimeField(blank=True, null=True),
        ),
    ]
