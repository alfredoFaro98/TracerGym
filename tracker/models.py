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
    ORIGINE_CHOICES = [
        ('personale', 'Personale'),
        ('opengym', 'openGym'),
    ]

    # Catalogo degli esercizi
    nome = models.CharField(max_length=100)
    tipologia = models.CharField(max_length=120, blank=True, default='')
    carrucole = models.PositiveIntegerField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='exercises')

    # Muscolo target e secondari (utile per gli esercizi importati da openGym,
    # ma disponibile a chiunque voglia compilarlo anche sui propri).
    target_muscle = models.CharField(max_length=60, blank=True, default='')
    secondary_muscles = models.JSONField(blank=True, default=list)
    instructions_en = models.JSONField(blank=True, default=list)
    instructions_it = models.JSONField(blank=True, default=list)

    # Provenienza dell'esercizio (import_opengym_exercises usa external_id per
    # essere ri-eseguibile senza duplicare le righe).
    origine = models.CharField(max_length=20, choices=ORIGINE_CHOICES, default='personale')
    external_id = models.CharField(max_length=30, blank=True, null=True, unique=True)

    def __str__(self):
        return self.nome

class WorkoutSession(models.Model):
    # Singola sessione di allenamento (giornata)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='workout_sessions')
    data = models.DateField(default=timezone.now)
    note = models.TextField(blank=True, null=True)
    luogo = models.CharField(max_length=150, blank=True, default='')
    orario = models.TimeField(null=True, blank=True)
    orario_fine = models.TimeField(null=True, blank=True)
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


class IntegratoreEntry(models.Model):
    # Singola assunzione di creatina/aminoacidi/proteine in una giornata
    TIPO_CHOICES = [
        ('creatina', 'Creatina'),
        ('aminoacidi', 'Aminoacidi'),
        ('proteine', 'Proteine'),
    ]
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='integratore_entries')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES)
    quantita_g = models.PositiveIntegerField()
    data = models.DateField(default=timezone.now)
    creato_il = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-data', '-creato_il']

    def __str__(self):
        return f"{self.utente.username} - {self.get_tipo_display()} {self.quantita_g}g ({self.data})"

class BodyMetric(models.Model):
    # Misurazioni corporee dell'utente per una data giornata (una sola voce per giorno)
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='body_metrics')
    data = models.DateField(default=timezone.now)
    orario = models.TimeField(null=True, blank=True)
    peso_kg = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    altezza_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    body_fat_pct = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    vita_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    torace_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    braccia_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    cosce_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True)
    note = models.CharField(max_length=100, blank=True, default='')

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
    is_gif = models.BooleanField(default=False)

    class Meta:
        ordering = ['ordine', 'id']

    def __str__(self):
        return f"Immagine {self.id} - {self.exercise.nome}"


class SiteVisit(models.Model):
    # Una riga per giorno: numero di volte in cui dashboard o login sono state
    # caricate quel giorno (visibile solo ai superuser, in sidebar).
    data = models.DateField(default=timezone.now, unique=True)
    conteggio = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.data}: {self.conteggio} visite"


class WeekdayPlan(models.Model):
    # Cosa allena l'utente di default in un dato giorno della settimana
    # (0=Lunedì ... 6=Domenica, stessa convenzione di date.weekday()).
    # Si ripete ogni settimana finché non viene cambiato o sovrascritto
    # per una data specifica da DayPlanOverride.
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekday_plans')
    giorno_settimana = models.PositiveSmallIntegerField()
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)
    riposo = models.BooleanField(default=False)

    class Meta:
        unique_together = ('utente', 'giorno_settimana')

    def __str__(self):
        return f"{self.utente.username} - giorno {self.giorno_settimana}"


class DayPlanOverride(models.Model):
    # Eccezione per una singola data: ha priorità sul WeekdayPlan di quel
    # giorno della settimana (es. "di solito è gambe ma oggi riposo").
    utente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='day_plan_overrides')
    data = models.DateField()
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, null=True, blank=True)
    riposo = models.BooleanField(default=False)

    class Meta:
        unique_together = ('utente', 'data')

    def __str__(self):
        return f"{self.utente.username} - {self.data}"
