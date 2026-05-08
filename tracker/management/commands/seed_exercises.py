from django.core.management.base import BaseCommand
from tracker.models import Tag, Exercise

class Command(BaseCommand):
    help = 'Popola il database con alcuni esercizi e tag di base'

    def handle(self, *args, **kwargs):
        # Dati base
        tags_data = ['Petto', 'Dorso', 'Gambe', 'Spalle', 'Braccia', 'Addome', 'Cardio']
        
        exercises_data = [
            {'nome': 'Panca Piana', 'tags': ['Petto', 'Braccia']},
            {'nome': 'Croci ai cavi', 'tags': ['Petto']},
            {'nome': 'Trazioni alla sbarra', 'tags': ['Dorso', 'Braccia']},
            {'nome': 'Rematore con bilanciere', 'tags': ['Dorso']},
            {'nome': 'Squat', 'tags': ['Gambe']},
            {'nome': 'Affondi', 'tags': ['Gambe']},
            {'nome': 'Leg Press', 'tags': ['Gambe']},
            {'nome': 'Lento Avanti', 'tags': ['Spalle', 'Braccia']},
            {'nome': 'Alzate Laterali', 'tags': ['Spalle']},
            {'nome': 'Curl con bilanciere', 'tags': ['Braccia']},
            {'nome': 'Pushdown tricipiti', 'tags': ['Braccia']},
            {'nome': 'Crunch', 'tags': ['Addome']},
            {'nome': 'Plank', 'tags': ['Addome']},
            {'nome': 'Tapis Roulant', 'tags': ['Cardio']},
        ]

        # Creazione Tag
        tags_dict = {}
        for tag_nome in tags_data:
            tag, created = Tag.objects.get_or_create(nome=tag_nome)
            tags_dict[tag_nome] = tag
            if created:
                self.stdout.write(self.style.SUCCESS(f'Creato tag: {tag_nome}'))

        # Creazione Esercizi
        for ex_data in exercises_data:
            exercise, created = Exercise.objects.get_or_create(nome=ex_data['nome'])
            if created:
                # Associa i tag
                for tag_nome in ex_data['tags']:
                    exercise.tags.add(tags_dict[tag_nome])
                self.stdout.write(self.style.SUCCESS(f'Creato esercizio: {exercise.nome}'))
            else:
                self.stdout.write(self.style.WARNING(f'Esercizio già esistente: {exercise.nome}'))

        self.stdout.write(self.style.SUCCESS('Popolamento iniziale completato con successo!'))
