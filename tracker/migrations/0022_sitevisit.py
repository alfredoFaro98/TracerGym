import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0021_integratoreentry'),
    ]

    operations = [
        migrations.CreateModel(
            name='SiteVisit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(default=django.utils.timezone.now, unique=True)),
                ('conteggio', models.PositiveIntegerField(default=0)),
            ],
            options={
                'ordering': ['-data'],
            },
        ),
    ]
