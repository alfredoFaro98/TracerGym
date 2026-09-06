"""Applica le traduzioni italiane dei nomi esercizi openGym.

Le traduzioni stanno in `tracker/data/nomi_esercizi_it.json`, una mappa
`external_id -> nome italiano`. L'`external_id` e' l'id openGym, stabile fra
installazioni diverse: percio' lo stesso file vale in locale e in produzione
senza dover spostare il database.

Il comando tocca solo `nome_it`, mai `nome`: se una traduzione non convince si
corregge il JSON e si rilancia, senza aver perso l'originale inglese.

Uso:
    python manage.py applica_nomi_it
    python manage.py applica_nomi_it --dry-run
"""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracker.models import Exercise

DEFAULT_PATH = Path(__file__).resolve().parents[2] / 'data' / 'nomi_esercizi_it.json'


class Command(BaseCommand):
    help = 'Scrive Exercise.nome_it dai nomi tradotti in tracker/data/nomi_esercizi_it.json.'

    def add_arguments(self, parser):
        parser.add_argument('--file', default=str(DEFAULT_PATH),
                            help='JSON con la mappa external_id -> nome italiano.')
        parser.add_argument('--dry-run', action='store_true',
                            help='Mostra cosa cambierebbe senza scrivere sul database.')

    def handle(self, *args, **options):
        percorso = Path(options['file'])
        if not percorso.exists():
            raise CommandError(f'File non trovato: {percorso}')

        with open(percorso, encoding='utf-8') as f:
            mappa = json.load(f)
        if not isinstance(mappa, dict):
            raise CommandError('Il JSON deve essere un oggetto {"external_id": "nome italiano"}.')

        esercizi = {e.external_id: e for e in Exercise.objects.filter(external_id__isnull=False)}

        da_scrivere, invariati, mancanti = [], 0, []
        for external_id, nome_it in mappa.items():
            esercizio = esercizi.get(external_id)
            if esercizio is None:
                mancanti.append(external_id)
                continue
            if esercizio.nome_it == nome_it:
                invariati += 1
                continue
            esercizio.nome_it = nome_it
            da_scrivere.append(esercizio)

        for esercizio in da_scrivere[:15]:
            self.stdout.write(f'  {esercizio.external_id}  {esercizio.nome}  ->  {esercizio.nome_it}')
        if len(da_scrivere) > 15:
            self.stdout.write(f'  ... e altri {len(da_scrivere) - 15}')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING(
                f'[dry-run] Da aggiornare: {len(da_scrivere)}. Gia\' a posto: {invariati}.'
            ))
        else:
            with transaction.atomic():
                Exercise.objects.bulk_update(da_scrivere, ['nome_it'], batch_size=500)
            self.stdout.write(self.style.SUCCESS(
                f'Aggiornati: {len(da_scrivere)}. Gia\' a posto: {invariati}.'
            ))

        # Un external_id nel JSON ma non nel database vuol dire che le due
        # installazioni hanno cataloghi diversi: va segnalato, non ignorato.
        if mancanti:
            self.stdout.write(self.style.WARNING(
                f'{len(mancanti)} external_id del JSON non esistono qui: '
                f'{", ".join(mancanti[:10])}{" ..." if len(mancanti) > 10 else ""}'
            ))
        senza_traduzione = [
            e.nome for e in esercizi.values()
            if e.origine == 'opengym' and e.external_id not in mappa
        ]
        if senza_traduzione:
            self.stdout.write(self.style.WARNING(
                f'{len(senza_traduzione)} esercizi openGym non hanno ancora una traduzione '
                f'(restano in inglese): {", ".join(senza_traduzione[:5])} ...'
            ))
