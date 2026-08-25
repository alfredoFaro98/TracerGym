"""Importa il catalogo esercizi di openGym (1300+ esercizi, immagini + gif,
istruzioni in inglese e italiano) dentro TracerGym, fondendolo con il catalogo
esistente.

Fonte: il repo openGym clonato in locale (frontend/src/lib/exercises-data.js
+ frontend/src/instr/it.js), più le immagini/gif già scaricate in ./media/img
e ./media/gif dalla root del progetto openGym.

Rieseguibile: ogni esercizio è identificato da `external_id` (l'id numerico
di openGym), quindi rilanciare il comando aggiorna le righe esistenti invece
di duplicarle.

Uso:
    python manage.py import_opengym_exercises
    python manage.py import_opengym_exercises --opengym-path "C:\\altro\\path\\openGym"
"""
import json
import re
import shutil
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from tracker.models import Exercise, ExerciseImage, Tag

DEFAULT_OPENGYM_PATH = r"C:\Users\alfredo\Desktop\openGym-main\openGym-main"

# bodyPart (bp) -> nome del Tag esistente in TracerGym.
# 'upper arms' non è qui: viene deciso caso per caso in base al target (bicipiti/tricipiti).
BP_TO_TAG = {
    'back': 'Dorsali',
    'cardio': 'Cardio',
    'chest': 'Pettorali',
    'lower arms': 'Avambracci',
    'lower legs': 'Gambe',
    'neck': 'Collo',
    'shoulders': 'Spalle',
    'upper legs': 'Gambe',
    'waist': 'Addome',
}

# equipment (eq) -> tipologia in italiano, nello stesso stile di seed_exercises.py.
EQ_TO_TIPOLOGIA = {
    'assisted': 'Esercizio assistito',
    'band': 'Esercizio con elastico',
    'barbell': 'Esercizio con bilanciere',
    'body weight': 'Esercizio a corpo libero',
    'bosu ball': 'Esercizio con bosu',
    'cable': 'Esercizio ai cavi',
    'dumbbell': 'Esercizio con manubrio',
    'elliptical machine': 'Cardio (ellittica)',
    'ez barbell': 'Esercizio con bilanciere EZ',
    'hammer': 'Esercizio alla macchina hammer',
    'kettlebell': 'Esercizio con kettlebell',
    'leverage machine': 'Esercizio alle macchine',
    'medicine ball': 'Esercizio con palla medica',
    'olympic barbell': 'Esercizio con bilanciere olimpico',
    'resistance band': 'Esercizio con elastico',
    'roller': 'Esercizio con rullo',
    'rope': 'Esercizio con corda',
    'skierg machine': 'Cardio (skierg)',
    'sled machine': 'Esercizio con slitta',
    'smith machine': 'Esercizio alla smith machine',
    'stability ball': 'Esercizio con fitball',
    'stationary bike': 'Cardio (cyclette)',
    'stepmill machine': 'Cardio (stepmill)',
    'tire': 'Esercizio con pneumatico',
    'trap bar': 'Esercizio con trap bar',
    'upper body ergometer': 'Cardio (ergometro braccia)',
    'weighted': 'Esercizio con sovraccarico',
    'wheel roller': 'Esercizio con ruota addominale',
}

# target (tg) + secondary muscles (sm) -> italiano.
MUSCLE_IT = {
    'abductors': 'abduttori', 'abs': 'addominali', 'adductors': 'adduttori',
    'biceps': 'bicipiti', 'calves': 'polpacci',
    'cardiovascular system': 'sistema cardiovascolare', 'delts': 'deltoidi',
    'forearms': 'avambracci', 'glutes': 'glutei', 'hamstrings': 'femorali',
    'lats': 'gran dorsale', 'levator scapulae': 'elevatore della scapola',
    'pectorals': 'pettorali', 'quads': 'quadricipiti',
    'serratus anterior': 'dentato anteriore', 'spine': 'colonna vertebrale',
    'traps': 'trapezio', 'triceps': 'tricipiti', 'upper back': 'schiena alta',
    'abdominals': 'addominali', 'ankle stabilizers': 'stabilizzatori caviglia',
    'ankles': 'caviglie', 'back': 'schiena', 'brachialis': 'brachiale',
    'chest': 'petto', 'core': 'core', 'deltoids': 'deltoidi', 'feet': 'piedi',
    'grip muscles': 'muscoli della presa', 'groin': 'inguine', 'hands': 'mani',
    'hip flexors': "flessori dell'anca", 'inner thighs': 'interno coscia',
    'latissimus dorsi': 'gran dorsale', 'lower abs': 'addominali bassi',
    'lower back': 'zona lombare', 'obliques': 'obliqui',
    'quadriceps': 'quadricipiti', 'rear deltoids': 'deltoidi posteriori',
    'rhomboids': 'romboidi', 'rotator cuff': 'cuffia dei rotatori',
    'shins': 'tibie', 'shoulders': 'spalle', 'soleus': 'soleo',
    'sternocleidomastoid': 'sternocleidomastoideo', 'trapezius': 'trapezio',
    'upper chest': 'petto alto', 'wrist extensors': 'estensori del polso',
    'wrist flexors': 'flessori del polso', 'wrists': 'polsi',
}


def fix_mojibake(text):
    """instr/it.js è UTF-8 salvato due volte (es. 'perchÃ©' invece di 'perché').
    Riporta i byte alla codifica corretta; se il testo è già pulito, non tocca nulla."""
    try:
        return text.encode('latin1').decode('utf8')
    except (UnicodeDecodeError, UnicodeEncodeError):
        return text


def load_js_module(path, prefix):
    """exercises-data.js e instr/it.js sono JS ma con sintassi JSON valida
    dietro un `export const X=` / `export default `: basta togliere il prefisso
    (e le righe di commento) e fare json.loads."""
    raw = path.read_text(encoding='utf-8')
    raw = re.sub(r'^\s*//.*$', '', raw, flags=re.MULTILINE)  # via i commenti // ...
    idx = raw.index(prefix)
    raw = raw[idx + len(prefix):].strip()
    if raw.endswith(';'):
        raw = raw[:-1]
    return json.loads(raw)


class Command(BaseCommand):
    help = 'Importa/aggiorna il catalogo esercizi di openGym dentro TracerGym (fuso con quello esistente).'

    def add_arguments(self, parser):
        parser.add_argument('--opengym-path', default=DEFAULT_OPENGYM_PATH,
                             help='Cartella root del progetto openGym clonato in locale.')

    def handle(self, *args, **options):
        base = Path(options['opengym_path'])
        exdb_path = base / 'frontend' / 'src' / 'lib' / 'exercises-data.js'
        instr_it_path = base / 'frontend' / 'src' / 'instr' / 'it.js'
        gif_dir = base / 'media' / 'gif'

        for p in (exdb_path, instr_it_path, gif_dir):
            if not p.exists():
                raise CommandError(f'Non trovo {p} — controlla --opengym-path.')

        self.stdout.write('Leggo il catalogo openGym...')
        exdb = load_js_module(exdb_path, 'export const EXDB=')
        instr_it = load_js_module(instr_it_path, 'export default ')

        dest_dir = Path(settings.MEDIA_ROOT) / 'exercises'
        dest_dir.mkdir(parents=True, exist_ok=True)

        tag_cache = {}

        def get_tag(name):
            if name not in tag_cache:
                tag_cache[name], _ = Tag.objects.get_or_create(nome=name)
            return tag_cache[name]

        def tag_for(ex):
            bp = ex['bp']
            if bp == 'upper arms':
                tg = ex.get('tg', '')
                if tg == 'biceps':
                    return get_tag('Bicipiti')
                if tg == 'triceps':
                    return get_tag('Tricipiti')
                return get_tag('Braccia')
            return get_tag(BP_TO_TAG.get(bp, bp.capitalize()))

        def copy_media(filename, src_dir):
            dest = dest_dir / filename
            if not dest.exists():
                shutil.copyfile(src_dir / filename, dest)
            return f'exercises/{filename}'

        created = updated = images_copied = 0

        with transaction.atomic():
            for ex in exdb:
                ext_id = ex['id']
                nome = ex['n'][0:1].upper() + ex['n'][1:]
                tipologia = EQ_TO_TIPOLOGIA.get(ex.get('eq', ''), ex.get('eq', ''))
                target_it = MUSCLE_IT.get(ex.get('tg', ''), ex.get('tg', ''))
                secondary_it = [MUSCLE_IT.get(m, m) for m in ex.get('sm', [])]
                instr_en = ex.get('st', [])
                instr_it_list = [fix_mojibake(s) for s in instr_it.get(ext_id, [])] or instr_en

                exercise, was_created = Exercise.objects.update_or_create(
                    external_id=ext_id,
                    defaults=dict(
                        nome=nome,
                        tipologia=tipologia,
                        target_muscle=target_it,
                        secondary_muscles=secondary_it,
                        instructions_en=instr_en,
                        instructions_it=instr_it_list,
                        origine='opengym',
                    ),
                )
                exercise.tags.add(tag_for(ex))
                created += was_created
                updated += not was_created

                # TracerGym permette una sola immagine per esercizio (vedi
                # _validate_exercise_image in views.py) — usiamo la gif: è quella
                # con l'animazione, resta sempre sotto il limite di 2 MB dell'app.
                gif_name = ex.get('gif')
                if gif_name and not exercise.images.exists():
                    rel = copy_media(gif_name, gif_dir)
                    ExerciseImage.objects.create(exercise=exercise, immagine=rel, ordine=0, is_gif=True)
                    images_copied += 1

        self.stdout.write(self.style.SUCCESS(
            f'\nCompletato: {created} esercizi creati, {updated} aggiornati, '
            f'{images_copied} file immagine/gif copiati in {dest_dir}.'
        ))
