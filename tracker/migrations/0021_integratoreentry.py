import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0020_watergoal'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='IntegratoreEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('tipo', models.CharField(choices=[('creatina', 'Creatina'), ('aminoacidi', 'Aminoacidi'), ('proteine', 'Proteine')], max_length=20)),
                ('quantita_g', models.PositiveIntegerField()),
                ('data', models.DateField(default=django.utils.timezone.now)),
                ('creato_il', models.DateTimeField(default=django.utils.timezone.now)),
                ('utente', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='integratore_entries', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-data', '-creato_il'],
            },
        ),
    ]
