from django.core.management.base import BaseCommand
from tracker.models import Tag, Exercise

# Dati completi dal CSV esercizi_superpalestra.csv
# formato: (nome, tipologia)
EXERCISES = {
    'Spalle': [
        ('Military Press', 'Esercizio con bilanciere'),
        ('Alzate laterali', 'Esercizio con manubrio'),
        ('Lento Avanti con bilanciere', 'Esercizio con bilanciere'),
        ('Lento Avanti con manubri', 'Esercizio con manubrio'),
        ('Alzate laterali ai cavi', 'Esercizio ai cavi'),
        ('Shoulder press', 'Esercizio alle macchine'),
        ('Lento Dietro con bilanciere', 'Esercizio con bilanciere'),
        ('Alzate frontali', 'Esercizio con manubrio'),
        ('Alzate frontali ai cavi', 'Esercizio alle macchine'),
        ('Alzate frontali con bilanciere', 'Esercizio con bilanciere'),
        ('Crossover ai cavi inverso', 'Esercizio ai cavi'),
        ('Alzate a 90 gradi', 'Esercizio con manubrio'),
        ('Alzate a 90 gradi ai cavi', 'Esercizio ai cavi'),
        ('Rematore verticale con bilanciere', 'Esercizio con bilanciere'),
        ('Rematore verticale con manubri', 'Esercizio con manubrio'),
        ('Shrug con bilanciere', 'Esercizio con bilanciere'),
        ('Shrug con manubri', 'Esercizio con manubrio'),
        ('Shrug al multipower', 'Esercizio alle macchine'),
        ('Alzate frontali con manubrio da seduto', 'Esercizio con manubrio'),
        ('Alzate laterali con manubrio da seduto', 'Esercizio con manubrio'),
        ('Panca piana presa inversa', 'Esercizio con bilanciere'),
        ('Arnold press', 'Esercizio con manubrio'),
        ('Alzate frontali con corda', 'Esercizio ai cavi'),
    ],
    'Dorsali': [
        ('Stacchi da terra', 'Esercizio con bilanciere'),
        ('Trazioni alla sbarra (chin up)', 'Esercizio a corpo libero'),
        ('Rematore con bilanciere', 'Esercizio con bilanciere'),
        ('Rematore con manubrio', 'Esercizio con manubrio'),
        ('Rematore ai cavi (unilaterale o bilaterale)', 'Esercizio ai cavi'),
        ('Pulldown alla lat machine', 'Esercizio alle macchine'),
        ('Pulldown alla lat machine presa inversa', 'Esercizio alle macchine'),
        ('Pulldown alla lat machine con triangolo', 'Esercizio alle macchine'),
        ('Pulldown alla lat machine con trazibar', 'Esercizio alle macchine'),
        ('Pullover con manubrio', 'Esercizio con manubrio'),
        ('Pullover ai cavi', 'Esercizio ai cavi'),
        ('Lateral Pulley (orizzontale o inclinato)', 'Esercizio alle macchine'),
        ('Lateral Pulley (orizzontale o inclinato) presa larga', 'Esercizio alle macchine'),
        ('Lateral Pulley (orizzontale o inclinato) con trazybar', 'Esercizio alle macchine'),
        ('Lateral Pulley con maniglia unilaterale', 'Esercizio alle macchine'),
        ('Lat machine con maniglia', 'Esercizio alle macchine'),
        ('Iperestensioni alla panca romana', 'Esercizi a corpo libero'),
        ('Rematore su panca inclinata con manubrio', 'Esercizio con manubrio'),
        ('Rematore su panca inclinata con bilanciere', 'Esercizio con bilanciere'),
        ('Trazioni alla sbarra presa inversa (chin up)', 'Esercizio a corpo libero'),
        ('Rematore con bilanciere presa inversa', 'Esercizio con bilanciere'),
        ('Rematore al multipower', 'Esercizio alle macchine'),
        ('Goodmorning con bilanciere', 'Esercizio con bilanciere'),
        ('Dorsy Machine', 'Esercizio alle macchine'),
        ('Nautilus Machine', 'Esercizio alle macchine'),
    ],
    'Gambe': [
        ('Squat', 'Esercizio con bilanciere'),
        ('Pressa 45 gradi', 'Esercizio alle macchine'),
        ('Pressa Orizzontale', 'Esercizio alle macchine'),
        ('Pressa Verticale', 'Esercizio alle macchine'),
        ('Leg Extension', 'Esercizio alle macchine'),
        ('Leg Curl', 'Esercizio alle macchine'),
        ('Stacchi da terra gambe tese', 'Esercizio con bilanciere'),
        ('Stacchi da terra gambe tese con manubri', 'Esercizio con manubrio'),
        ('Standing leg curl', 'Esercizio alle macchine'),
        ('Sitting leg curl', 'Esercizio alle macchine'),
        ('Affondi frontali (con manubri)', 'Esercizio a corpo libero o con manubri'),
        ('Affondi laterali (con manubri)', 'Esercizio a corpo libero o con manubri'),
        ('Affondi rumeni (al multipower)', 'Esercizio alle macchine'),
        ('Squat Bulgaro', 'Esercizio con bilanciere'),
        ('Front Squat', 'Esercizio con bilanciere'),
        ('Hack Squat', 'Esercizio alle macchine'),
        ('Slanci posteriori della gamba', 'Esercizio ai cavi'),
        ('Gluteus Machine', 'Esercizio alle macchine'),
        ('Adductor Machine', 'Esercizio alle macchine'),
        ('Abductor Machine', 'Esercizio alle macchine'),
        ('Ponte per glutei', 'Esercizio a corpo libero'),
        ('Slanci laterali della gamba', 'Esercizio ai cavi'),
        ('Calf raises in piedi', 'Esercizio alle macchine'),
        ('Calf raises seduto', 'Esercizio alle macchine'),
        ('Calf raises alla leg press', 'Esercizio alle macchine'),
        ('Calf raises alla multipower', 'Esercizio alle macchine'),
        ('Squat al multipower', 'Esercizio alle macchine'),
        ('Hack Squat con bilanciere', 'Esercizio con bilanciere'),
        ('Affondi frontali con bilanciere', 'Esercizio con bilanciere'),
        ('Affondi laterali con bilanciere', 'Esercizio con bilanciere'),
        ('Jefferson squat', 'Esercizio con bilanciere'),
        ('Stacchi da terra con trap bar', 'Esercizio con bilanciere'),
        ('Sissy Squat', 'Esercizio a corpo libero o con manubri'),
        ('Sumo Squat', 'Esercizio a corpo libero o con manubri'),
    ],
    'Pettorali': [
        ('Distensioni con bilanciere su panca inclinata', 'Esercizio con bilanciere'),
        ('Distensioni con bilanciere su panca piana', 'Esercizio con bilanciere'),
        ('Distensioni con bilanciere su panca reclinata', 'Esercizio con bilanciere'),
        ('Distensioni con manubri su panca inclinata', 'Esercizio con manubrio'),
        ('Distensioni con manubri su panca piana', 'Esercizio con manubrio'),
        ('Distensioni con manubri su panca reclinata', 'Esercizio con manubrio'),
        ('Dip alle parallele per i pettorali', 'Esercizio a corpo libero'),
        ('Chest Press', 'Esercizio alle macchine'),
        ('Chest Press Incline', 'Esercizio alle macchine'),
        ('Pectoral Machine', 'Esercizio alle macchine'),
        ('Croci con manubri su panca inclinata', 'Esercizio con manubrio'),
        ('Croci con manubri su panca piana', 'Esercizio con manubrio'),
        ('Croci con manubri su panca reclinata', 'Esercizio con manubrio'),
        ('Croci con manubri around the world', 'Esercizio con manubrio'),
        ('Piegamenti sulle braccia', 'Esercizio a corpo libero'),
        ('Croci ai cavi', 'Esercizio ai cavi'),
        ('Croci ai cavi su panca piana', 'Esercizio ai cavi'),
        ('Croci ai cavi su panca inclinata', 'Esercizio ai cavi'),
        ('Distensioni su panca inclinata alla smith machine', 'Esercizio alle macchine'),
        ('Distensioni su panca piana alla smith machine', 'Esercizio alle macchine'),
        ('Distensioni su panca reclinata alla smith machine', 'Esercizio alle macchine'),
        ('Croci ai cavi dal basso', 'Esercizio ai cavi'),
        ('Chest press per il petto basso', 'Esercizio alle macchine'),
    ],
    'Bicipiti': [
        ('Curl con bilanciere', 'Esercizio con bilanciere'),
        ('Curl con manubri', 'Esercizio con manubrio'),
        ('Curl a martello', 'Esercizio con manubrio'),
        ('Curl con bilanciere alla panca Scott', 'Esercizio con bilanciere'),
        ('Curl con manubri alla panca Scott', 'Esercizio con manubrio'),
        ('Curl con manubri su panca inclinata', 'Esercizio con manubrio'),
        ('Bicipiti alla macchina (arm curl)', 'Esercizio alle macchine'),
        ('Spider curl con bilanciere', 'Esercizio con bilanciere'),
        ('Spider curl con manubrio', 'Esercizio con manubrio'),
        ('Curl ai cavi unilaterali e bilaterali', 'Esercizio ai cavi'),
        ('Curl con bilanciere presa inversa', 'Esercizio con bilanciere'),
        ('Curl di concentrazione con manubrio', 'Esercizio con manubrio'),
        ('Curl di concentrazione ai cavi', 'Esercizio ai cavi'),
        ('Curl con corda', 'Esercizio ai cavi'),
        ('Curl a martello frontali', 'Esercizio con manubrio'),
        ('Curl ai cavi da sdraiato', 'Esercizio ai cavi'),
        ('Curl ai cavi sopra la testa', 'Esercizio ai cavi'),
        ('Curl con bilanciere alla panca Scott presa inversa', 'Esercizio con bilanciere'),
    ],
    'Tricipiti': [
        ('French Press (o skull crusher)', 'Esercizio con bilanciere'),
        ('French Press con manubri', 'Esercizio con manubrio'),
        ('Pushdown ai cavi', 'Esercizio ai cavi'),
        ('Pushdown ai cavi con corda', 'Esercizio ai cavi'),
        ('Estensioni con corda sopra la testa', 'Esercizio ai cavi'),
        ('Estensioni con manubrio sopra la testa', 'Esercizio con manubrio'),
        ('Dip alle parallele per i tricipiti', 'Esercizio a corpo libero'),
        ('Dip tra panche per i tricipiti', 'Esercizio a corpo libero'),
        ('Spinte inverse ai cavi (unilaterali o bilaterali)', 'Esercizio ai cavi'),
        ('Panca presa stretta', 'Esercizio con bilanciere'),
        ('Panca presa stretta al multipower', 'Esercizio alle macchine'),
        ('Flessioni presa stretta per i tricipiti', 'Esercizio a corpo libero'),
        ('Estensioni sopra la testa ai cavi da seduto', 'Esercizio ai cavi'),
        ('French press su panca inclinata', 'Esercizio con bilanciere'),
        ('French press verticale', 'Esercizio con bilanciere'),
        ('Macchina per i dip', 'Esercizio alle macchine'),
        ('Estensioni con manubrio busto flesso', 'Esercizio con manubrio'),
        ('Press per i tricipiti sopra la testa con manubrio', 'Esercizio con manubrio'),
    ],
    'Addome': [
        ('Crunch', 'Esercizio a corpo libero'),
        ('Plank', 'Esercizio a corpo libero'),
        ('Sit-up', 'Esercizio a corpo libero'),
        ('Leg raise', 'Esercizio a corpo libero'),
        ('Leg raise alle parallele', 'Esercizio a corpo libero'),
        ('Russian twist', 'Esercizio a corpo libero'),
        ('Cable crunch ai cavi', 'Esercizio ai cavi'),
        ('Ab wheel', 'Esercizio a corpo libero'),
        ('Crunch inverso', 'Esercizio a corpo libero'),
        ('Crunch obliquo', 'Esercizio a corpo libero'),
        ('Hollow hold', 'Esercizio a corpo libero'),
        ('Dragon flag', 'Esercizio a corpo libero'),
    ],
    'Cardio': [
        ('Tapis Roulant', 'Cardio'),
        ('Cyclette', 'Cardio'),
        ('Ellittica', 'Cardio'),
        ('Vogatore', 'Cardio'),
        ('Salto con la corda', 'Cardio'),
        ('Corsa', 'Cardio'),
        ('Camminata veloce', 'Cardio'),
        ('HIIT', 'Cardio'),
        ('Nuoto', 'Cardio'),
    ],
}


class Command(BaseCommand):
    help = 'Popola il database con il catalogo completo di esercizi dal CSV superpalestra'

    def handle(self, *args, **kwargs):
        created_tags = 0
        created_ex = 0
        updated_ex = 0

        for gruppo, esercizi in EXERCISES.items():
            tag, tag_created = Tag.objects.get_or_create(nome=gruppo)
            if tag_created:
                created_tags += 1
                self.stdout.write(self.style.SUCCESS(f'Creato gruppo: {gruppo}'))

            for nome, tipologia in esercizi:
                exercise, created = Exercise.objects.get_or_create(nome=nome)
                changed = False
                if created:
                    created_ex += 1
                    changed = True
                if not exercise.tipologia and tipologia:
                    exercise.tipologia = tipologia
                    changed = True
                    if not created:
                        updated_ex += 1
                if changed:
                    exercise.save()
                exercise.tags.add(tag)

        self.stdout.write(self.style.SUCCESS(
            f'\nCompletato: {created_tags} gruppi, {created_ex} esercizi creati, {updated_ex} aggiornati.'
        ))
