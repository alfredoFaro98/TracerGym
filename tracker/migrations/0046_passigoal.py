import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0045_passigiorno'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PassiGoal',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(default=django.utils.timezone.now)),
                ('obiettivo_passi', models.PositiveIntegerField()),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='passi_goals', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-data'],
                'unique_together': {('utente', 'data')},
            },
        ),
    ]
