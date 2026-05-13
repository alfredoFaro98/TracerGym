from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class MuscleGroup(models.Model):
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Tag(models.Model):
    # Categoria dell'esercizio (es. Petto, Dorso, Cardio)
    nome = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.nome

class Exercise(models.Model):
    # Catalogo degli esercizi
    nome = models.CharField(max_length=100)
    tipologia = models.CharField(max_length=120, blank=True, default='')
    tags = models.ManyToManyField(Tag, related_name='exercises')

    def __str__(self):
        return self.nome

class WorkoutSession(models.Model):
    # Singola sessione di allenamento (giornata)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    data = models.DateField(default=timezone.now)
    note = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Sessione di {self.utente.username} del {self.data}"

    class Meta:
        ordering = ['-data'] # Ordina dalla più recente alla più vecchia

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"Profilo di {self.user.username}"

class WorkoutSet(models.Model):
    # Singola serie di un esercizio all'interno di una sessione
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField()
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    per_lato = models.BooleanField(default=False)
    rest_time = models.PositiveIntegerField(null=True, blank=True, help_text="Recupero in secondi")
    muscles = models.ManyToManyField(MuscleGroup, blank=True, related_name='sets')

    def __str__(self):
        return f"{self.exercise.nome} - {self.reps} reps"
