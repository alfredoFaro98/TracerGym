from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0042_exercise_nome_it'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='lingua_esercizi',
            field=models.CharField(
                choices=[('it', 'Italiano'), ('en', 'English')],
                default='it',
                max_length=2,
            ),
        ),
    ]
