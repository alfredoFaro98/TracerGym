from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0043_userprofile_lingua_esercizi'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='accent_hex',
            field=models.CharField(blank=True, default='', max_length=7),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='accent',
            field=models.CharField(
                choices=[
                    ('viola', 'Viola'),
                    ('corallo', 'Corallo'),
                    ('lime', 'Lime'),
                    ('teal', 'Teal'),
                    ('verde', 'Verde'),
                    ('custom', 'Personalizzato'),
                ],
                default='viola',
                max_length=20,
            ),
        ),
    ]
