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
    luogo = models.CharField(max_length=150, blank=True, default='')
    orario = models.TimeField(null=True, blank=True)
    durata_minuti = models.PositiveIntegerField(null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altezza_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    compagni_allenamento = models.CharField(max_length=255, blank=True, default='')

    def __str__(self):
        return f"Sessione di {self.utente.username} del {self.data}"

    class Meta:
        ordering = ['-data'] # Ordina dalla più recente alla più vecchia

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_public = models.BooleanField(default=False)
    obiettivo_acqua_ml = models.PositiveIntegerField(default=2000)

    def __str__(self):
        return f"Profilo di {self.user.username}"


class WaterGoal(models.Model):
    # Obiettivo acqua specifico per una giornata (override rispetto al default su UserProfile)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_goals')
    data = models.DateField(default=timezone.now)
    obiettivo_ml = models.PositiveIntegerField()

    class Meta:
        ordering = ['-data']
        unique_together = ('utente', 'data')

    def __str__(self):
        return f"{self.utente.username} - {self.data} - {self.obiettivo_ml}ml"


class WaterEntry(models.Model):
    # Singola aggiunta di acqua bevuta in una giornata
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='water_entries')
    data = models.DateField(default=timezone.now)
    quantita_ml = models.PositiveIntegerField()
    creato_il = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-data', '-creato_il']

    def __str__(self):
        return f"{self.utente.username} - {self.quantita_ml}ml ({self.data})"

class BodyMetric(models.Model):
    # Misurazioni corporee dell'utente per una data giornata (una sola voce per giorno)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_metrics')
    data = models.DateField(default=timezone.now)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altezza_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)

    class Meta:
        ordering = ['-data']
        unique_together = ('utente', 'data')

    def __str__(self):
        return f"{self.utente.username} - {self.data}"


class Circuit(models.Model):
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='circuits')
    nome = models.CharField(max_length=100, blank=True, default='')
    rounds = models.PositiveIntegerField(default=3)
    rest_tra_round = models.PositiveIntegerField(null=True, blank=True)
    order = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Circuito {self.id} - {self.session}"


class WorkoutSet(models.Model):
    # Singola serie di un esercizio all'interno di una sessione
    session = models.ForeignKey(WorkoutSession, on_delete=models.CASCADE, related_name='sets')
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    reps = models.PositiveIntegerField(null=True, blank=True)
    durata = models.PositiveIntegerField(null=True, blank=True, help_text="Durata in secondi")
    weight = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    per_lato = models.BooleanField(default=False)
    avviamento = models.BooleanField(default=False)
    a_cedimento = models.BooleanField(default=False)
    richiamo = models.BooleanField(default=False)
    barra_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    circuit = models.ForeignKey('Circuit', on_delete=models.SET_NULL, null=True, blank=True, related_name='sets')
    rest_time = models.PositiveIntegerField(null=True, blank=True, help_text="Recupero in secondi")
    muscles = models.ManyToManyField(MuscleGroup, blank=True, related_name='sets')

    def __str__(self):
        return f"{self.exercise.nome} - {self.reps} reps"

class ExerciseImage(models.Model):
    exercise = models.ForeignKey(Exercise, on_delete=models.CASCADE, related_name='images')
    immagine = models.ImageField(upload_to='exercises/')
    ordine = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['ordine', 'id']

    def __str__(self):
        return f"Immagine {self.id} - {self.exercise.nome}"
