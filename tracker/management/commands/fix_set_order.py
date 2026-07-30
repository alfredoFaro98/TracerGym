from django.core.management.base import BaseCommand
from django.db import transaction

from tracker.models import WorkoutSession, Circuit


def _renumber(queryset):
    """Ricompatta 'order' cosi' che ogni esercizio resti un blocco contiguo,
    preservando l'ordine di prima apparizione degli esercizi e l'ordine
    relativo delle serie all'interno di ciascun esercizio."""
    sets = list(queryset.order_by('order', 'id'))

    seen_order = []
    by_exercise = {}
    for s in sets:
        if s.exercise_id not in by_exercise:
            by_exercise[s.exercise_id] = []
            seen_order.append(s.exercise_id)
        by_exercise[s.exercise_id].append(s)

    counter = 0
    changed = 0
    for exercise_id in seen_order:
        for s in by_exercise[exercise_id]:
            if s.order != counter:
                s.order = counter
                s.save(update_fields=['order'])
                changed += 1
            counter += 1
    return changed


class Command(BaseCommand):
    help = (
        "Ricompatta i valori di 'order' delle serie in modo che ogni esercizio "
        "resti un blocco contiguo. Corregge le sessioni gia' rovinate dal bug "
        "che spezzava lo stesso esercizio in piu' gruppi separati quando gli "
        "si aggiungevano nuove serie in momenti diversi."
    )

    def handle(self, *args, **options):
        total_changed = 0
        with transaction.atomic():
            for session in WorkoutSession.objects.all():
                total_changed += _renumber(session.sets.filter(circuit__isnull=True))
            for circuit in Circuit.objects.all():
                total_changed += _renumber(circuit.sets.all())
        self.stdout.write(self.style.SUCCESS(f'Sistemate {total_changed} serie.'))
