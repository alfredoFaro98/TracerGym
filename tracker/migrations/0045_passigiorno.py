import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('tracker', '0044_userprofile_accent_hex'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='obiettivo_passi',
            field=models.PositiveIntegerField(default=10000),
        ),
        migrations.CreateModel(
            name='PassiGiorno',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data', models.DateField(default=django.utils.timezone.now)),
                ('passi', models.PositiveIntegerField()),
                ('nota', models.CharField(blank=True, default='', max_length=200)),
                ('creato_il', models.DateTimeField(default=django.utils.timezone.now)),
                ('utente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='passi_giorno',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'ordering': ['-data'],
                'unique_together': {('utente', 'data')},
            },
        ),
    ]
