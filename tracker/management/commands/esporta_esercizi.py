"""Esporta il catalogo esercizi in JSON, per confrontare due installazioni.

Serve a verificare che il catalogo openGym su PythonAnywhere sia lo stesso che
abbiamo in locale prima di applicare le traduzioni: gli esercizi importati sono
identificati da `external_id`, quindi basta confrontare quella colonna.

Uso (nella console PythonAnywhere, dentro la cartella del progetto):
    python manage.py esporta_esercizi --out esercizi_pa.json
"""
import json

from django.core.management.base import BaseCommand

from tracker.models import Exercise


class Command(BaseCommand):
    help = 'Esporta il catalogo esercizi (id, external_id, nome, origine) in JSON.'

    def add_arguments(self, parser):
        parser.add_argument('--out', default='esercizi.json',
                            help='File JSON da scrivere (default: esercizi.json)')

    def handle(self, *args, **options):
        righe = list(
            Exercise.objects
            .order_by('origine', 'external_id', 'nome')
            .values('id', 'external_id', 'nome', 'nome_it', 'origine')
        )
        with open(options['out'], 'w', encoding='utf-8') as f:
            json.dump(righe, f, ensure_ascii=False, indent=1)

        opengym = sum(1 for r in righe if r['origine'] == 'opengym')
        tradotti = sum(1 for r in righe if r['nome_it'])
        self.stdout.write(self.style.SUCCESS(
            f"Scritto {options['out']}: {len(righe)} esercizi "
            f"({opengym} openGym, {len(righe) - opengym} personali, {tradotti} gia' tradotti)."
        ))
