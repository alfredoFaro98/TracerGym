from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tracker', '0008_workoutset_avviamento'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExerciseImage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('immagine', models.ImageField(upload_to='exercises/')),
                ('ordine', models.PositiveIntegerField(default=0)),
                ('exercise', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='tracker.exercise')),
            ],
            options={
                'ordering': ['ordine', 'id'],
            },
        ),
    ]
