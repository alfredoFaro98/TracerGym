import json
import os
import re
import shutil
import subprocess
import tempfile
from datetime import time as dt_time, timedelta
from decimal import Decimal
from io import BytesIO

from PIL import Image

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .accent import normalizza_hex, scala_accent
from .models import (
    BodyMetric, Exercise, ExerciseImage, MacroDayStatus, MacroEntry, MacroGoal,
    PassiGiorno, PassiGoal, SleepEntry, UserProfile, WaterEntry, WaterGoal, WorkoutSession,
    WorkoutSet,
)


class ApplicaATutteTest(TestCase):
    """Propagazione di una modifica alle altre serie dello stesso esercizio.

    Il punto delicato e' che la propagazione deve toccare SOLO i campi
    davvero cambiati: una piramidale (12x60, 10x65, 8x70, 6x75) esiste
    proprio perche' reps e peso cambiano di serie in serie, e correggere il
    recupero non deve appiattirla.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.altro = Exercise.objects.create(nome='Panca Inclinata')
        self.esercizio = Exercise.objects.create(nome='Panca Piana')
        self.sessione = WorkoutSession.objects.create(utente=self.user)
        self.serie = [
            WorkoutSet.objects.create(
                session=self.sessione, exercise=self.esercizio,
                reps=reps, weight=Decimal(peso), rest_time=90, order=i,
            )
            for i, (reps, peso) in enumerate([(12, '60'), (10, '65'), (8, '70'), (6, '75')])
        ]
        self.client.force_login(self.user)

    def _post(self, serie, **extra):
        campi = {
            'exercise_name': serie.exercise.nome,
            'reps': str(serie.reps or ''),
            'weight': str(serie.weight or ''),
            'rest_time': str(serie.rest_time or ''),
            'durata': '', 'barra_kg': '', 'zavorra_kg': '', 'carrucole': '',
        }
        campi.update(extra)
        return self.client.post(reverse('edit_set', args=[serie.id]), campi)

    def _ricarica(self):
        for s in self.serie:
            s.refresh_from_db()

    def test_propaga_solo_il_campo_cambiato(self):
        risposta = self._post(self.serie[0], rest_time='120', applica_a_tutte='on')
        self._ricarica()

        self.assertEqual([s.rest_time for s in self.serie], [120] * 4)
        # La piramidale resta intatta: e' la garanzia che serve davvero.
        self.assertEqual([s.reps for s in self.serie], [12, 10, 8, 6])
        self.assertEqual(
            [s.weight for s in self.serie],
            [Decimal('60'), Decimal('65'), Decimal('70'), Decimal('75')],
        )
        # Le righe aggiornate tornano al frontend per essere riscritte.
        self.assertEqual(
            sorted(risposta.json()['rows'].keys()),
            sorted(str(s.id) for s in self.serie[1:]),
        )

    def test_senza_spunta_non_propaga(self):
        risposta = self._post(self.serie[0], rest_time='45')
        self._ricarica()

        self.assertEqual([s.rest_time for s in self.serie], [45, 90, 90, 90])
        self.assertNotIn('rows', risposta.json())

    def test_un_campo_riscritto_uguale_non_viene_propagato(self):
        """Il confronto avviene sui valori riletti dal database.

        Senza la rilettura, il '60' che arriva dal POST verrebbe confrontato
        con Decimal('60.00') e risulterebbe cambiato, propagando un peso che
        l'utente non ha toccato.
        """
        self._post(self.serie[0], weight='60', rest_time='120', applica_a_tutte='on')
        self._ricarica()

        self.assertEqual([s.rest_time for s in self.serie], [120] * 4)
        self.assertEqual(
            [s.weight for s in self.serie],
            [Decimal('60'), Decimal('65'), Decimal('70'), Decimal('75')],
        )

    def test_il_peso_si_propaga_se_lo_cambi(self):
        self._post(self.serie[0], weight='80', applica_a_tutte='on')
        self._ricarica()

        self.assertEqual([s.weight for s in self.serie], [Decimal('80')] * 4)

    def test_cambiare_esercizio_trova_le_sorelle_con_quello_vecchio(self):
        risposta = self._post(
            self.serie[0], exercise_name='Panca Inclinata', applica_a_tutte='on',
        )
        self._ricarica()

        self.assertEqual([s.exercise_id for s in self.serie], [self.altro.id] * 4)
        # Le righe cambiano gruppo: la pagina va ricaricata, non rattoppata.
        self.assertIs(risposta.json().get('reload'), True)
        self.assertEqual([s.reps for s in self.serie], [12, 10, 8, 6])

    def test_le_serie_di_un_altro_esercizio_non_vengono_toccate(self):
        estranea = WorkoutSet.objects.create(
            session=self.sessione, exercise=self.altro, reps=5, rest_time=30, order=9,
        )
        self._post(self.serie[0], rest_time='120', applica_a_tutte='on')
        estranea.refresh_from_db()

        self.assertEqual(estranea.rest_time, 30)

    def test_le_serie_di_un_altra_sessione_non_vengono_toccate(self):
        altra_sessione = WorkoutSession.objects.create(utente=self.user)
        estranea = WorkoutSet.objects.create(
            session=altra_sessione, exercise=self.esercizio, reps=5, rest_time=30,
        )
        self._post(self.serie[0], rest_time='120', applica_a_tutte='on')
        estranea.refresh_from_db()

        self.assertEqual(estranea.rest_time, 30)


class LinguaEserciziTest(TestCase):
    """Scelta della lingua con cui mostrare i nomi degli esercizi.

    Il punto delicato non e' quale nome compare a schermo, ma che i form
    continuino a trovare l'esercizio giusto: le serie si salvano cercando
    l'esercizio per nome, quindi con l'italiano attivo arriva il `nome_it` e
    una ricerca sul solo `nome` inglese creerebbe un doppione del catalogo.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        # Esercizio openGym: nome inglese piu' traduzione.
        self.tradotto = Exercise.objects.create(
            nome='Assisted pull-up', nome_it='Trazioni assistite',
            origine='opengym', external_id='0017',
        )
        # Esercizio personale: un nome solo, gia' italiano.
        self.personale = Exercise.objects.create(nome='Panca Piana')
        self.sessione = WorkoutSession.objects.create(utente=self.user)
        self.client.force_login(self.user)

    def _imposta_lingua(self, lingua):
        return self.client.post(reverse('set_lingua_esercizi'), {'lingua_esercizi': lingua})

    def test_default_italiano(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.assertEqual(profile.lingua_esercizi, 'it')

    def test_il_catalogo_segue_la_lingua_scelta(self):
        self._imposta_lingua('it')
        risposta = self.client.get(reverse('exercises_list'))
        self.assertContains(risposta, 'Trazioni assistite')

        self._imposta_lingua('en')
        risposta = self.client.get(reverse('exercises_list'))
        self.assertContains(risposta, 'Assisted pull-up')

    def test_lingua_non_valida_non_cambia_nulla(self):
        self._imposta_lingua('de')
        # La view non salva (e non crea nemmeno il profilo): resta il default.
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.assertEqual(profile.lingua_esercizi, 'it')

    def test_l_esercizio_personale_resta_uguale_nelle_due_lingue(self):
        # Senza `nome_it` si ricade sull'originale: non deve sparire in inglese.
        for lingua in ('it', 'en'):
            self._imposta_lingua(lingua)
            risposta = self.client.get(reverse('exercises_list'))
            self.assertContains(risposta, 'Panca Piana')

    def test_aggiungere_una_serie_col_nome_italiano_non_duplica_l_esercizio(self):
        self._imposta_lingua('it')
        prima = Exercise.objects.count()

        self.client.post(reverse('session_detail', args=[self.sessione.id]), {
            'exercise_name': 'Trazioni assistite',
            'reps': '8', 'weight': '', 'rest_time': '', 'durata': '',
            'barra_kg': '', 'zavorra_kg': '', 'carrucole': '', 'num_sets': '1',
        })

        self.assertEqual(Exercise.objects.count(), prima)
        serie = WorkoutSet.objects.get(session=self.sessione)
        self.assertEqual(serie.exercise, self.tradotto)

    def test_il_nome_inglese_funziona_anche_con_l_italiano_attivo(self):
        self._imposta_lingua('it')
        self.client.post(reverse('session_detail', args=[self.sessione.id]), {
            'exercise_name': 'Assisted pull-up',
            'reps': '8', 'weight': '', 'rest_time': '', 'durata': '',
            'barra_kg': '', 'zavorra_kg': '', 'carrucole': '', 'num_sets': '1',
        })

        serie = WorkoutSet.objects.get(session=self.sessione)
        self.assertEqual(serie.exercise, self.tradotto)

    def test_i_suggerimenti_cercano_in_entrambe_le_lingue(self):
        self._imposta_lingua('it')
        url = reverse('exercise_suggestions')

        # Digitando l'inglese si trova comunque, ma la risposta mostra l'italiano.
        risposta = self.client.get(url, {'q': 'pull-up'})
        nomi = [r['nome'] for r in risposta.json()['results']]
        self.assertIn('Trazioni assistite', nomi)

        risposta = self.client.get(url, {'q': 'trazioni'})
        nomi = [r['nome'] for r in risposta.json()['results']]
        self.assertIn('Trazioni assistite', nomi)

    def test_il_catalogo_non_stampa_tag_di_template(self):
        # Un commento {# #} su piu' righe Django non lo riconosce e lo manda a
        # schermo tal quale, una volta per esercizio: era gia' successo.
        # Si controlla anche da superuser perche' pezzi di pagina esistono solo
        # per lui: da utente normale non verrebbero nemmeno renderizzati.
        admin = User.objects.create_superuser(username='admin', password='x')
        for utente in (self.user, admin):
            self.client.force_login(utente)
            corpo = self.client.get(reverse('exercises_list')).content.decode()
            for residuo in ('{#', '#}', '{%'):
                self.assertNotIn(residuo, corpo, f'residuo {residuo} da {utente.username}')

    def test_il_catalogo_e_ordinato_sul_nome_mostrato(self):
        # In italiano "Trazioni assistite" viene dopo "Panca Piana"; in inglese
        # "Assisted pull-up" viene prima. Se l'ordinamento restasse su `nome`
        # la lista italiana sembrerebbe in ordine casuale.
        self._imposta_lingua('it')
        risposta = self.client.get(reverse('exercises_list'))
        nomi = [e.nome_visuale for e in risposta.context['exercises']]
        self.assertEqual(nomi, ['Panca Piana', 'Trazioni assistite'])

        self._imposta_lingua('en')
        risposta = self.client.get(reverse('exercises_list'))
        nomi = [e.nome_visuale for e in risposta.context['exercises']]
        self.assertEqual(nomi, ['Assisted pull-up', 'Panca Piana'])


class FiltroSenzaImmagineTest(TestCase):
    """Filtro del catalogo per le schede a cui manca ancora la gif.

    E' uno strumento di manutenzione del catalogo, quindi deve comparire solo
    a chi il catalogo lo cura: a un utente normale non serve e non deve
    nemmeno arrivare nella pagina.
    """

    def setUp(self):
        self.admin = User.objects.create_superuser(username='capo', password='x')
        self.utente = User.objects.create_user(username='atleta', password='x')
        self.senza = Exercise.objects.create(nome='Senza Gif')
        self.con = Exercise.objects.create(nome='Con Gif')
        # Si assegna il percorso invece di caricare un file: al template serve
        # solo `.url`, e un upload vero lascerebbe file veri in media/ ad ogni
        # giro di test.
        ExerciseImage.objects.create(exercise=self.con, immagine='exercises/finta.gif')

    def test_il_filtro_c_e_solo_per_il_superuser(self):
        self.client.force_login(self.admin)
        self.assertContains(self.client.get(reverse('exercises_list')), 'Senza immagine')

        self.client.force_login(self.utente)
        self.assertNotContains(self.client.get(reverse('exercises_list')), 'Senza immagine')

    def test_solo_le_schede_senza_immagine_sono_marcate(self):
        # Il filtro lato client lavora sulla classe no-media: se il template
        # smettesse di metterla, il filtro non troverebbe piu' niente.
        self.client.force_login(self.admin)
        corpo = self.client.get(reverse('exercises_list')).content.decode()

        senza_card = corpo.split('Senza Gif')[0].rsplit('<div class="ex-card', 1)[-1]
        con_card = corpo.split('Con Gif')[0].rsplit('<div class="ex-card', 1)[-1]
        self.assertIn('no-media', senza_card)
        self.assertNotIn('no-media', con_card)


class AcquaAjaxTest(TestCase):
    """Eliminazione bevuta e obiettivo acqua dal widget in dashboard.

    Sono i due endpoint che prima ricaricavano tutta la pagina: quello che va
    verificato non e' solo che scrivano sul database, ma che rimandino
    indietro i totali giusti -- il JS non ricalcola niente, riscrive le
    etichette con quello che riceve, quindi un payload sbagliato si vede
    subito a schermo.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='bevitore', password='x')
        self.profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.profile.obiettivo_acqua_ml = 2000
        self.profile.save()
        self.oggi = timezone.localdate()
        self.client.force_login(self.user)

    def _bevuta(self, ml):
        return WaterEntry.objects.create(utente=self.user, quantita_ml=ml, data=self.oggi)

    def test_elimina_bevuta_torna_i_totali_aggiornati(self):
        rimane = self._bevuta(500)
        va_via = self._bevuta(300)

        r = self.client.post(reverse('delete_water_entry_ajax', args=[va_via.id]))

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertEqual(dati['total_ml'], 500)
        self.assertEqual(dati['progress_pct'], 25)
        self.assertEqual(list(WaterEntry.objects.filter(utente=self.user)), [rimane])

    def test_non_si_elimina_la_bevuta_di_un_altro(self):
        altro = User.objects.create_user(username='estraneo', password='x')
        sua = WaterEntry.objects.create(utente=altro, quantita_ml=500, data=self.oggi)

        r = self.client.post(reverse('delete_water_entry_ajax', args=[sua.id]))

        self.assertEqual(r.status_code, 404)
        self.assertTrue(WaterEntry.objects.filter(id=sua.id).exists())

    def test_obiettivo_salvato_e_percentuale_ricalcolata(self):
        self._bevuta(1000)

        r = self.client.post(reverse('set_water_goal_ajax'), {'obiettivo_ml': '4000'})

        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertEqual(dati['goal_ml'], 4000)
        self.assertEqual(dati['progress_pct'], 25)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.obiettivo_acqua_ml, 4000)

    def test_obiettivo_del_giorno_batte_quello_di_profilo(self):
        # Se oggi ha gia' un obiettivo suo (impostato dallo storico), cambiare
        # quello di profilo non deve far cambiare il numero mostrato: il
        # payload deve tornare l'obiettivo davvero in vigore, non l'ultimo
        # digitato, altrimenti il widget mostrerebbe un valore che sparisce al
        # primo refresh.
        WaterGoal.objects.create(utente=self.user, data=self.oggi, obiettivo_ml=1500)
        self._bevuta(750)

        dati = self.client.post(reverse('set_water_goal_ajax'), {'obiettivo_ml': '4000'}).json()

        self.assertEqual(dati['goal_ml'], 1500)
        self.assertEqual(dati['progress_pct'], 50)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.obiettivo_acqua_ml, 4000)

    def test_obiettivo_non_valido_rifiutato(self):
        r = self.client.post(reverse('set_water_goal_ajax'), {'obiettivo_ml': '0'})

        self.assertEqual(r.status_code, 400)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.obiettivo_acqua_ml, 2000)

    def test_get_non_modifica_niente(self):
        entry = self._bevuta(500)

        self.assertEqual(self.client.get(reverse('delete_water_entry_ajax', args=[entry.id])).status_code, 405)
        self.assertEqual(self.client.get(reverse('set_water_goal_ajax')).status_code, 405)
        self.assertTrue(WaterEntry.objects.filter(id=entry.id).exists())

    def test_la_dashboard_punta_agli_endpoint_ajax(self):
        # Se un {% url %} del widget tornasse alle vecchie viste che
        # rispondono con un redirect, il JS riceverebbe HTML al posto del JSON
        # e la pagina si ricaricherebbe di nuovo: qui si accorge subito.
        self._bevuta(250)
        corpo = self.client.get(reverse('dashboard')).content.decode()

        self.assertIn('data-ajax-water-del', corpo)
        self.assertIn('data-ajax-water-goal', corpo)
        self.assertIn(reverse('set_water_goal_ajax'), corpo)
        self.assertNotIn(reverse('set_water_goal') + '"', corpo)


class AccentPersonalizzatoTest(TestCase):
    """Accent scelto a mano: derivazione della scala e salvataggio.

    Il punto delicato e' che da un colore solo devono uscire dodici variabili
    usabili: se i toni del testo seguissero alla lettera un colore scuro,
    diventerebbero illeggibili sul fondo scuro dell'app.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.client.force_login(self.user)

    def test_la_scala_riproduce_i_preset_tarati_a_mano(self):
        # Se la formula si allontana da questi, i colori personalizzati
        # smettono di somigliare al resto dell'app.
        scala = scala_accent('#2dd4bf')  # teal
        self.assertEqual(scala['acc'], '#2dd4bf')
        self.assertEqual(scala['acc-2'], '#3ad7c3')
        self.assertEqual(scala['acc-3'], '#4ae0cd')
        self.assertEqual(scala['acc-4'], '#4ce8d5')

    def test_un_colore_scuro_non_produce_testo_illeggibile(self):
        # --acc-soft e --acc-4 finiscono su testo e icone: partendo da un
        # colore quasi nero devono comunque restare chiari.
        scala = scala_accent('#1a1005')
        for variabile in ('acc-4', 'acc-5', 'acc-soft'):
            valore = scala[variabile]
            luminosita = max(int(valore[i:i + 2], 16) for i in (1, 3, 5))
            self.assertGreater(luminosita, 120, f'{variabile}={valore} troppo scuro')

    def test_il_colore_scelto_resta_intatto(self):
        # I riempimenti seguono la scelta: --acc non va "corretto".
        self.assertEqual(scala_accent('#876a50')['acc'], '#876a50')

    def test_formati_accettati(self):
        self.assertEqual(normalizza_hex('#ABC'), '#aabbcc')
        self.assertEqual(normalizza_hex('876A50'), '#876a50')
        self.assertEqual(normalizza_hex('  #876a50  '), '#876a50')
        for storto in ('', None, 'rosso', '#12345', 'zzzzzz', '#876a50; evil'):
            self.assertIsNone(normalizza_hex(storto), storto)

    def test_salvataggio_e_uso_in_pagina(self):
        self.client.post(reverse('set_accent'), {'accent': 'custom', 'accent_hex': '#876A50'})
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.accent, 'custom')
        self.assertEqual(profile.accent_hex, '#876a50')

        corpo = self.client.get(reverse('impostazioni')).content.decode()
        self.assertIn('data-accent="custom"', corpo)
        self.assertIn('--acc: #876a50;', corpo)

    def test_un_colore_storto_non_spegne_l_accent_di_prima(self):
        self.client.post(reverse('set_accent'), {'accent': 'custom', 'accent_hex': '#876A50'})
        self.client.post(reverse('set_accent'), {'accent': 'custom', 'accent_hex': 'non-un-colore'})

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.accent_hex, '#876a50')

    def test_tornare_a_un_preset_conserva_il_colore_scelto(self):
        self.client.post(reverse('set_accent'), {'accent': 'custom', 'accent_hex': '#876A50'})
        self.client.post(reverse('set_accent'), {'accent': 'teal'})

        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.accent, 'teal')
        self.assertEqual(profile.accent_hex, '#876a50')
        # E la pagina torna a usare la scala del preset, non quella derivata.
        self.assertNotIn('--acc: #876a50;', self.client.get(reverse('impostazioni')).content.decode())

@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='tracer-test-media-'))
class CatalogoImmaginiAjaxTest(TestCase):
    """Caricamento ed eliminazione immagine dal modale del catalogo.

    Il payload conta quanto la scrittura su disco: da `images` il JS ridisegna
    la galleria e la miniatura, e da li' decide anche la classe `no-media`, che
    e' quella su cui gira il filtro "senza immagine". Se la lista tornasse
    sbagliata, l'esercizio appena sistemato resterebbe fra quelli da sistemare.
    """

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.admin = User.objects.create_superuser(username='capo2', password='x')
        self.esercizio = Exercise.objects.create(nome='Panca Piana')
        self.client.force_login(self.admin)

    def _png(self, nome='prova.png'):
        buf = BytesIO()
        Image.new('RGB', (10, 10), '#123456').save(buf, 'PNG')
        return SimpleUploadedFile(nome, buf.getvalue(), content_type='image/png')

    def _carica(self, **extra):
        return self.client.post(
            reverse('add_exercise_image_ajax', args=[self.esercizio.id]),
            {'immagine': self._png(), **extra},
        )

    def test_caricamento_torna_la_lista_aggiornata(self):
        r = self._carica()

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertEqual(dati['exercise_id'], self.esercizio.id)
        self.assertEqual(len(dati['images']), 1)
        self.assertEqual(dati['images'][0]['id'], self.esercizio.images.get().id)
        self.assertTrue(dati['images'][0]['url'])
        self.assertTrue(dati['total_media'])

    def test_la_seconda_immagine_e_rifiutata(self):
        self._carica()

        r = self._carica()

        self.assertEqual(r.status_code, 400)
        self.assertIn('una sola immagine', r.json()['error'])
        self.assertEqual(self.esercizio.images.count(), 1)

    def test_senza_file_non_crea_niente(self):
        r = self.client.post(reverse('add_exercise_image_ajax', args=[self.esercizio.id]))

        self.assertEqual(r.status_code, 400)
        self.assertEqual(self.esercizio.images.count(), 0)

    def test_eliminazione_svuota_la_lista(self):
        self._carica()
        img = self.esercizio.images.get()

        r = self.client.post(reverse('delete_exercise_image_ajax', args=[img.id]))

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        # exercise_id serve al JS per ritrovare la card da aggiornare: senza,
        # dopo un'eliminazione la miniatura resterebbe quella vecchia.
        self.assertEqual(dati['exercise_id'], self.esercizio.id)
        self.assertEqual(dati['images'], [])
        self.assertEqual(self.esercizio.images.count(), 0)

    def test_di_piu_immagini_ne_toglie_solo_una(self):
        # Oggi il limite e' un'immagine per esercizio, ma i dati vecchi ne
        # hanno anche due: eliminarne una non deve azzerare la galleria.
        prima = ExerciseImage.objects.create(exercise=self.esercizio, immagine=self._png('a.png'), ordine=0)
        ExerciseImage.objects.create(exercise=self.esercizio, immagine=self._png('b.png'), ordine=1)

        dati = self.client.post(reverse('delete_exercise_image_ajax', args=[prima.id])).json()

        self.assertEqual(len(dati['images']), 1)

    def test_un_utente_normale_non_tocca_le_immagini(self):
        img = ExerciseImage.objects.create(exercise=self.esercizio, immagine=self._png(), ordine=0)
        self.client.force_login(User.objects.create_user(username='atleta2', password='x'))

        self.assertEqual(self._carica().status_code, 403)
        self.assertEqual(
            self.client.post(reverse('delete_exercise_image_ajax', args=[img.id])).status_code, 403)
        self.assertEqual(self.esercizio.images.count(), 1)

    def test_get_non_modifica_niente(self):
        img = ExerciseImage.objects.create(exercise=self.esercizio, immagine=self._png(), ordine=0)

        self.assertEqual(
            self.client.get(reverse('add_exercise_image_ajax', args=[self.esercizio.id])).status_code, 405)
        self.assertEqual(
            self.client.get(reverse('delete_exercise_image_ajax', args=[img.id])).status_code, 405)
        self.assertEqual(self.esercizio.images.count(), 1)

    def test_la_card_porta_le_immagini_e_gli_endpoint_ajax(self):
        # data-images sulla card e' la fonte di verita' del JS, e gli endpoint
        # devono essere quelli che rispondono JSON: se tornassero i vecchi, il
        # modale riceverebbe HTML e la pagina si ricaricherebbe di nuovo.
        ExerciseImage.objects.create(exercise=self.esercizio, immagine=self._png(), ordine=0)
        corpo = self.client.get(reverse('exercises_list')).content.decode()

        self.assertIn('data-images=', corpo)
        # gli URL nel JS sono template con lo 0 al posto dell'id
        self.assertIn(reverse('add_exercise_image_ajax', args=[0]), corpo)
        self.assertIn(reverse('delete_exercise_image_ajax', args=[0]), corpo)

class MisurazioniAjaxTest(TestCase):
    """Salvataggio ed eliminazione dalla pagina Misurazioni senza reload.

    Due cose vanno tenute d'occhio piu' delle altre: `created`, perche' il
    salvataggio e' un get_or_create sulla data e il JS ci decide se inserire
    una riga o sostituirne una; e le serie del grafico, che guardano tutte le
    misurazioni e non solo la pagina visibile.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='misurato', password='x')
        self.client.force_login(self.user)
        self.oggi = timezone.localdate()

    def _salva(self, **campi):
        return self.client.post(reverse('save_misurazione_ajax'), campi)

    def test_salvataggio_nuovo_giorno(self):
        r = self._salva(data=self.oggi.isoformat(), peso_kg='78.5', ora='07:30')

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertTrue(dati['created'])
        self.assertEqual(dati['data'], self.oggi.isoformat())
        self.assertIn('metric-row-%d' % dati['entry_id'], dati['html'])
        self.assertEqual(dati['chart']['peso'], [{'date': self.oggi.strftime('%d/%m/%Y'), 'value': 78.5}])

    def test_stesso_giorno_aggiorna_la_riga_che_c_e_gia(self):
        primo = self._salva(data=self.oggi.isoformat(), peso_kg='78.5').json()

        secondo = self._salva(data=self.oggi.isoformat(), vita_cm='82').json()

        # created False e stesso id: il JS deve sostituire la riga, non
        # aggiungerne una seconda per lo stesso giorno.
        self.assertFalse(secondo['created'])
        self.assertEqual(secondo['entry_id'], primo['entry_id'])
        self.assertEqual(BodyMetric.objects.filter(utente=self.user).count(), 1)
        entry = BodyMetric.objects.get(utente=self.user)
        # il peso non era nel secondo invio: non deve essere stato azzerato
        self.assertEqual(float(entry.peso_kg), 78.5)
        self.assertEqual(float(entry.vita_cm), 82)

    def test_rimuovi_orario(self):
        self._salva(data=self.oggi.isoformat(), ora='07:30')

        self._salva(data=self.oggi.isoformat(), ora='07:30', clear_ora='1')

        self.assertIsNone(BodyMetric.objects.get(utente=self.user).orario)

    def test_eliminazione_svuota_anche_il_grafico(self):
        entry_id = self._salva(data=self.oggi.isoformat(), peso_kg='78.5').json()['entry_id']

        r = self.client.post(reverse('delete_misurazione_ajax', args=[entry_id]))

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertEqual(dati['chart']['peso'], [])
        self.assertFalse(BodyMetric.objects.filter(id=entry_id).exists())

    def test_non_si_elimina_la_misurazione_di_un_altro(self):
        altro = User.objects.create_user(username='estraneo3', password='x')
        sua = BodyMetric.objects.create(utente=altro, data=self.oggi, peso_kg=80)

        r = self.client.post(reverse('delete_misurazione_ajax', args=[sua.id]))

        self.assertEqual(r.status_code, 404)
        self.assertTrue(BodyMetric.objects.filter(id=sua.id).exists())

    def test_get_non_modifica_niente(self):
        entry = BodyMetric.objects.create(utente=self.user, data=self.oggi, peso_kg=80)

        self.assertEqual(self.client.get(reverse('save_misurazione_ajax')).status_code, 405)
        self.assertEqual(
            self.client.get(reverse('delete_misurazione_ajax', args=[entry.id])).status_code, 405)
        self.assertTrue(BodyMetric.objects.filter(id=entry.id).exists())

    def test_la_pagina_usa_il_partial_e_gli_endpoint_ajax(self):
        entry = BodyMetric.objects.create(utente=self.user, data=self.oggi, peso_kg=80)
        corpo = self.client.get(reverse('misurazioni')).content.decode()

        # data-data e' quello che il JS legge per infilare una riga nuova al
        # posto giusto nell'elenco ordinato per data.
        self.assertIn('data-data="%s"' % self.oggi.isoformat(), corpo)
        self.assertIn('id="metric-row-%d"' % entry.id, corpo)
        self.assertIn(reverse('save_misurazione_ajax'), corpo)
        self.assertIn(reverse('delete_misurazione_ajax', args=[entry.id]), corpo)



class PassiGiornoTest(TestCase):
    """Passi giornalieri nella pagina Attivita'.

    Il punto delicato e' l'inserimento settimanale: (utente, data) e' unico,
    quindi ricompilare una settimana gia' inserita deve correggere i valori
    invece di far fallire il salvataggio.

    La pagina e' riservata agli admin, quindi l'utente di prova e' un
    superuser: con un utente normale ogni rotta risponde con un redirect.
    """

    def setUp(self):
        self.user = User.objects.create_superuser(username='tester', password='x')
        self.client.force_login(self.user)
        self.oggi = timezone.localdate()
        # La griglia si compila sulla settimana scorsa, non su quella in corso:
        # i giorni futuri vengono scartati di proposito, quindi di lunedi' la
        # settimana corrente avrebbe avuto sei caselle su sette non salvabili.
        self.lunedi = self.oggi - timedelta(days=self.oggi.weekday() + 7)

    def _post_settimana(self, valori):
        """valori: dizionario indice-giorno (0=lunedi) -> stringa passi."""
        campi = {}
        for i in range(7):
            campi[f'data_{i}'] = (self.lunedi + timedelta(days=i)).isoformat()
            campi[f'passi_{i}'] = valori.get(i, '')
        return self.client.post(reverse('salva_passi_settimana'), campi)

    def test_la_pagina_si_apre(self):
        self.assertEqual(self.client.get(reverse('attivita')).status_code, 200)

    def test_salva_un_giorno_solo(self):
        self.client.post(reverse('salva_passi'), {
            'data': self.oggi.isoformat(), 'passi': '8500',
        })
        self.assertEqual(PassiGiorno.objects.get(utente=self.user, data=self.oggi).passi, 8500)

    def test_reinserire_lo_stesso_giorno_corregge_invece_di_duplicare(self):
        for valore in ('8500', '9200'):
            self.client.post(reverse('salva_passi'), {'data': self.oggi.isoformat(), 'passi': valore})

        voci = PassiGiorno.objects.filter(utente=self.user, data=self.oggi)
        self.assertEqual(voci.count(), 1)
        self.assertEqual(voci.first().passi, 9200)

    def test_svuotare_il_campo_cancella_il_giorno(self):
        self.client.post(reverse('salva_passi'), {'data': self.oggi.isoformat(), 'passi': '8500'})
        self.client.post(reverse('salva_passi'), {'data': self.oggi.isoformat(), 'passi': ''})

        self.assertFalse(PassiGiorno.objects.filter(utente=self.user, data=self.oggi).exists())

    def test_la_griglia_settimanale_salva_piu_giorni_insieme(self):
        self._post_settimana({0: '7000', 1: '9000', 2: '11000'})

        passi = {p.data: p.passi for p in PassiGiorno.objects.filter(utente=self.user)}
        self.assertEqual(passi.get(self.lunedi), 7000)
        self.assertEqual(passi.get(self.lunedi + timedelta(days=1)), 9000)
        self.assertEqual(passi.get(self.lunedi + timedelta(days=2)), 11000)
        # Le caselle lasciate vuote non creano voci a zero.
        self.assertEqual(len(passi), 3)

    def test_ricompilare_la_settimana_non_esplode_e_corregge(self):
        self._post_settimana({0: '7000'})
        self._post_settimana({0: '7500', 1: '8000'})

        passi = {p.data: p.passi for p in PassiGiorno.objects.filter(utente=self.user)}
        self.assertEqual(passi.get(self.lunedi), 7500)
        self.assertEqual(passi.get(self.lunedi + timedelta(days=1)), 8000)

    def test_i_giorni_futuri_vengono_ignorati(self):
        domani = self.oggi + timedelta(days=1)
        self.client.post(reverse('salva_passi_settimana'), {
            'data_0': domani.isoformat(), 'passi_0': '99999',
        })
        self.assertFalse(PassiGiorno.objects.filter(utente=self.user, data=domani).exists())

    def test_un_valore_non_numerico_non_scrive_niente(self):
        self.client.post(reverse('salva_passi'), {'data': self.oggi.isoformat(), 'passi': 'tanti'})
        self.assertFalse(PassiGiorno.objects.filter(utente=self.user).exists())

    def test_obiettivo_modificabile(self):
        self.client.post(reverse('set_obiettivo_passi'), {'obiettivo_passi': '12000'})
        self.assertEqual(UserProfile.objects.get(user=self.user).obiettivo_passi, 12000)

    def test_obiettivo_non_valido_lascia_il_precedente(self):
        self.client.post(reverse('set_obiettivo_passi'), {'obiettivo_passi': '0'})
        profile, _ = UserProfile.objects.get_or_create(user=self.user)
        self.assertEqual(profile.obiettivo_passi, 10000)

    def test_non_si_toccano_i_passi_di_un_altro(self):
        altro = User.objects.create_user(username='altro', password='x')
        voce = PassiGiorno.objects.create(utente=altro, data=self.oggi, passi=5000)

        self.client.post(reverse('elimina_passi', args=[voce.id]))

        self.assertTrue(PassiGiorno.objects.filter(id=voce.id).exists())

    def test_un_utente_normale_non_entra_nella_pagina(self):
        self.client.force_login(User.objects.create_user(username='atleta', password='x'))
        self.assertRedirects(self.client.get(reverse('attivita')), reverse('dashboard'))

    def test_un_utente_normale_non_salva_i_passi(self):
        self.client.force_login(User.objects.create_user(username='atleta', password='x'))

        self.client.post(reverse('salva_passi'), {'data': self.oggi.isoformat(), 'passi': '8500'})
        self.client.post(reverse('salva_passi_settimana'), {
            'data_0': self.oggi.isoformat(), 'passi_0': '8500',
        })
        self.client.post(reverse('set_obiettivo_passi'), {'obiettivo_passi': '12000'})

        self.assertFalse(PassiGiorno.objects.exists())
        self.assertFalse(UserProfile.objects.filter(obiettivo_passi=12000).exists())


class GiornoDatiTest(TestCase):
    """Dati del modale che si apre da una cella della heatmap.

    La casella in alto conta le sessioni del giorno invece di sommarne la
    durata: la durata di ciascuna sta gia' nella riga che la descrive, il
    totale non lo leggeva nessuno.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='tester', password='x')
        self.client.force_login(self.user)
        self.oggi = timezone.localdate()

    def _dati(self, giorno=None):
        risposta = self.client.get(reverse('giorno_dati'), {
            'data': (giorno or self.oggi).isoformat(),
        })
        self.assertEqual(risposta.status_code, 200)
        return risposta.json()

    def test_un_giorno_vuoto_non_ha_sessioni(self):
        self.assertEqual(self._dati()['sessioni'], [])

    def test_le_sessioni_del_giorno_arrivano_tutte(self):
        for _ in range(3):
            WorkoutSession.objects.create(utente=self.user, data=self.oggi)
        WorkoutSession.objects.create(utente=self.user, data=self.oggi - timedelta(days=1))

        self.assertEqual(len(self._dati()['sessioni']), 3)

    def test_non_si_contano_le_sessioni_di_un_altro(self):
        altro = User.objects.create_user(username='altro', password='x')
        WorkoutSession.objects.create(utente=altro, data=self.oggi)

        self.assertEqual(self._dati()['sessioni'], [])


class SonnoAjaxTest(TestCase):
    """Azioni della pagina Sonno senza reload.

    Qui il server non rimanda indietro la sola riga toccata ma tutto quello
    che quella riga cambia -- elenco, calendario, stats e grafico -- perche'
    modificare una notte puo' spostarla di posto, di pagina e di mese. I test
    guardano proprio quello: che la risposta descriva la pagina come sara',
    non solo il record salvato.
    """

    def setUp(self):
        self.user = User.objects.create_user(username='dormiente', password='x')
        self.client.force_login(self.user)
        self.oggi = timezone.localdate()

    def _notte(self, giorno=None, **campi):
        campi.setdefault('ora_letto', dt_time(23, 0))
        campi.setdefault('ora_sveglia', dt_time(7, 0))
        return SleepEntry.objects.create(utente=self.user, data=giorno or self.oggi, **campi)

    def _salva(self, entry_id=None, **campi):
        url = reverse('edit_sleep_entry_ajax', args=[entry_id]) if entry_id else reverse('save_sleep_entry_ajax')
        return self.client.post(url, campi)

    def test_una_notte_nuova_torna_dentro_elenco_stats_e_grafico(self):
        r = self._salva(data=self.oggi.isoformat(), ora_letto='22:30', ora_sveglia='06:30', qualita='ottima')

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertTrue(dati['ok'])
        self.assertEqual(SleepEntry.objects.get(id=dati['entry_id']).qualita, 'ottima')
        self.assertIn('Ottima', dati['lista'])
        self.assertEqual(dati['stats']['avg_hours'], '8h 00m')
        self.assertEqual(dati['chart'], [{'date': self.oggi.strftime('%d/%m'), 'value': 8.0}])

    def test_senza_orari_non_nasce_nessuna_notte(self):
        r = self._salva(data=self.oggi.isoformat(), ora_letto='', ora_sveglia='')

        dati = r.json()
        self.assertFalse(dati['ok'])
        self.assertTrue(dati['error'])
        self.assertFalse(SleepEntry.objects.exists())

    def test_la_modifica_puo_spostare_la_notte_di_giorno(self):
        notte = self._notte(qualita='buona')
        ieri = self.oggi - timedelta(days=1)

        r = self._salva(notte.id, data=ieri.isoformat(), ora_letto='00:30', ora_sveglia='08:00', qualita='scarsa')

        notte.refresh_from_db()
        self.assertEqual(notte.data, ieri)
        self.assertEqual(notte.qualita, 'scarsa')
        self.assertIn('Scarsa', r.json()['lista'])

    def test_su_una_notte_gia_salvata_un_campo_vuoto_non_azzera_l_orario(self):
        notte = self._notte()

        self._salva(notte.id, data=self.oggi.isoformat(), ora_letto='', ora_sveglia='', qualita='media')

        notte.refresh_from_db()
        self.assertEqual(notte.ora_letto, dt_time(23, 0))
        self.assertEqual(notte.qualita, 'media')

    def test_eliminazione_svuota_anche_stats_e_grafico(self):
        notte = self._notte()

        r = self.client.post(reverse('delete_sleep_entry_ajax', args=[notte.id]))

        self.assertEqual(r.status_code, 200)
        dati = r.json()
        self.assertEqual(dati['chart'], [])
        self.assertIsNone(dati['stats']['avg_hours'])
        self.assertIn('Ancora nessuna notte registrata', dati['lista'])
        self.assertFalse(SleepEntry.objects.filter(id=notte.id).exists())

    def test_non_si_tocca_la_notte_di_un_altro(self):
        altro = User.objects.create_user(username='estraneo_sonno', password='x')
        sua = SleepEntry.objects.create(utente=altro, data=self.oggi, ora_letto=dt_time(23, 0), ora_sveglia=dt_time(7, 0))

        self.assertEqual(self._salva(sua.id, qualita='scarsa').status_code, 404)
        self.assertEqual(self.client.post(reverse('delete_sleep_entry_ajax', args=[sua.id])).status_code, 404)
        sua.refresh_from_db()
        self.assertEqual(sua.qualita, 'buona')

    def test_get_non_modifica_niente(self):
        notte = self._notte()

        self.assertEqual(self.client.get(reverse('save_sleep_entry_ajax')).status_code, 405)
        self.assertEqual(self.client.get(reverse('delete_sleep_entry_ajax', args=[notte.id])).status_code, 405)
        self.assertTrue(SleepEntry.objects.filter(id=notte.id).exists())

    def test_cambio_mese_del_calendario(self):
        mese_scorso = (self.oggi.replace(day=1) - timedelta(days=1)).strftime('%Y-%m')

        dati = self.client.get(reverse('sonno_vista_ajax'), {'month': mese_scorso}).json()

        self.assertEqual(dati['month'], mese_scorso)
        self.assertIn('Qualità del sonno', dati['calendario'])

    def test_cambio_pagina_dello_storico(self):
        for i in range(21):
            self._notte(self.oggi - timedelta(days=i))

        dati = self.client.get(reverse('sonno_vista_ajax'), {'page': '2'}).json()

        self.assertEqual(dati['page'], '2')
        # La 21esima notte e' la piu' vecchia: l'elenco e' per data decrescente.
        self.assertIn((self.oggi - timedelta(days=20)).strftime('%d'), dati['lista'])

    def test_una_pagina_che_non_esiste_piu_ricade_sull_ultima(self):
        self._notte()

        dati = self.client.get(reverse('sonno_vista_ajax'), {'page': '7'}).json()

        # Il JS si riallinea su quello che il server ha davvero servito.
        self.assertEqual(dati['page'], '1')

    def test_la_pagina_usa_i_partial_e_gli_endpoint_ajax(self):
        notte = self._notte()
        corpo = self.client.get(reverse('sonno')).content.decode()

        self.assertIn('id="sleep-storico"', corpo)
        self.assertIn('id="sleep-calendario"', corpo)
        self.assertIn(reverse('save_sleep_entry_ajax'), corpo)
        self.assertIn(reverse('edit_sleep_entry_ajax', args=[notte.id]), corpo)
        self.assertIn(reverse('delete_sleep_entry_ajax', args=[notte.id]), corpo)


class AlimentazioneAjaxTest(TestCase):
    """La pagina alimentazione non si ricarica piu' a ogni modifica.

    Ogni operazione risponde con i due blocchi che cambiano gia' resi in HTML
    (riepilogo di oggi e storico) piu' i dati del grafico: il JS li incolla e
    basta, non ricalcola niente. Quindi quello da verificare non e' solo che
    il database venga scritto, ma che il payload sia completo e che la pagina
    servita corrisponda a quella che l'utente stava guardando.
    """

    AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

    def setUp(self):
        self.user = User.objects.create_user(username='mangiatore', password='x')
        self.oggi = timezone.localdate()
        self.client.force_login(self.user)

    def _voce(self, **kw):
        kw.setdefault('kcal', 500)
        kw.setdefault('data', self.oggi)
        return MacroEntry.objects.create(utente=self.user, **kw)

    def _tag_form(self, corpo, action):
        """Il tag <form> di quell'action, per guardarne gli attributi."""
        m = re.search(r'<form[^>]*action="%s"[^>]*>' % re.escape(action), corpo)
        self.assertIsNotNone(m, 'nessun form verso %s' % action)
        return m.group(0)

    def _stato(self, r):
        """Controlla che la risposta sia uno stato completo e lo restituisce."""
        self.assertEqual(r.status_code, 200, r.content[:400])
        dati = r.json()
        self.assertTrue(dati['ok'], dati)
        for chiave in ('today_html', 'days_html', 'chart_data', 'default_goals', 'page'):
            self.assertIn(chiave, dati)
        return dati

    def test_la_pagina_usa_i_partial_e_i_form_ajax(self):
        """I due blocchi sostituibili ci sono e ogni form e' marcato.

        Basta un data-macro-ajax dimenticato perche' quel form torni a
        ricaricare la pagina: da fuori sembra tutto a posto, quindi la
        marcatura la controlliamo qui una per una.
        """
        for i in range(20):
            self._voce(data=self.oggi - timedelta(days=i), nota='Pranzo')

        corpo = self.client.get(reverse('macro')).content.decode()

        self.assertIn('id="macro-today-slot"', corpo)
        self.assertIn('id="macro-days-slot"', corpo)
        voce = MacroEntry.objects.first()
        for azione, args in (
            ('add_macro_entry', []), ('set_macro_goal', []),
            ('set_macro_day_status', []), ('set_day_macro_goal', []),
            ('edit_macro_entry', [voce.id]), ('delete_macro_entry', [voce.id]),
            ('duplicate_macro_entry', [voce.id]),
        ):
            self.assertIn('data-macro-ajax', self._tag_form(corpo, reverse(azione, args=args)),
                          "form %s non marcato per AJAX" % azione)
        # Anche il cambio pagina dello storico passa dal fetch.
        self.assertIn('data-macro-page="2"', corpo)

    def test_aggiunta_torna_lo_stato_aggiornato(self):
        dati = self._stato(self.client.post(reverse('add_macro_entry'), {
            'kcal': '700', 'proteine_g': '40.5', 'data': self.oggi.isoformat(),
            'ora': '13:30', 'nota': 'Pranzo', 'spazzatura': 'on',
        }, **self.AJAX))

        voce = MacroEntry.objects.get()
        self.assertEqual(voce.kcal, 700)
        self.assertTrue(voce.e_spazzatura)
        # Il giorno toccato serve al JS per aprirlo dopo l'aggiornamento.
        self.assertEqual(dati['day'], self.oggi.isoformat())
        self.assertIn('700', dati['today_html'])
        self.assertIn('Pranzo', dati['days_html'])

    def test_kcal_mancanti_non_scrivono_niente(self):
        r = self.client.post(reverse('add_macro_entry'), {'kcal': ''}, **self.AJAX)

        self.assertEqual(r.status_code, 400)
        self.assertFalse(r.json()['ok'])
        self.assertEqual(MacroEntry.objects.count(), 0)

    def test_senza_javascript_si_torna_al_redirect_di_sempre(self):
        r = self.client.post(reverse('add_macro_entry'), {'kcal': '300'})

        self.assertRedirects(r, reverse('macro'))
        self.assertEqual(MacroEntry.objects.count(), 1)

    def test_modifica_puo_spostare_la_voce_di_giorno(self):
        voce = self._voce()
        ieri = self.oggi - timedelta(days=1)

        dati = self._stato(self.client.post(reverse('edit_macro_entry', args=[voce.id]), {
            'kcal': '800', 'data': ieri.isoformat(), 'ora': '09:15', 'nota': 'Colazione',
        }, **self.AJAX))

        voce.refresh_from_db()
        self.assertEqual(voce.kcal, 800)
        self.assertEqual(voce.data, ieri)
        self.assertEqual(timezone.localtime(voce.creato_il).strftime('%H:%M'), '09:15')
        # Il giorno da aprire e' quello di arrivo, non quello di partenza.
        self.assertEqual(dati['day'], ieri.isoformat())

    def test_eliminazione_singola(self):
        voce = self._voce()

        dati = self._stato(
            self.client.post(reverse('delete_macro_entry', args=[voce.id]), {}, **self.AJAX))

        self.assertEqual(dati['day'], self.oggi.isoformat())
        self.assertEqual(MacroEntry.objects.count(), 0)

    def test_eliminazione_in_blocco(self):
        ids = [self._voce().id for _ in range(3)]
        rimane = MacroEntry.objects.create(utente=self.user, kcal=200, data=self.oggi)

        self._stato(self.client.post(
            reverse('bulk_delete_macro_entries'), {'entry_ids': ids}, **self.AJAX))

        self.assertEqual(list(MacroEntry.objects.filter(utente=self.user)), [rimane])

    def test_importazione_su_un_altro_giorno(self):
        voce = self._voce(nota='Cena', proteine_g=Decimal('20'))
        domani = self.oggi + timedelta(days=1)

        dati = self._stato(self.client.post(
            reverse('duplicate_macro_entry', args=[voce.id]),
            {'data': domani.isoformat()}, **self.AJAX))

        self.assertEqual(dati['day'], domani.isoformat())
        self.assertEqual(MacroEntry.objects.filter(data=domani, nota='Cena').count(), 1)

    def test_obiettivo_di_default(self):
        dati = self._stato(self.client.post(reverse('set_macro_goal'), {
            'obiettivo_kcal': '2500', 'obiettivo_proteine_g': '180',
        }, **self.AJAX))

        # Torna indietro perche' il JS deve riscrivere i campi del form:
        # riaprendolo mostrerebbe altrimenti i valori vecchi.
        self.assertEqual(dati['default_goals']['kcal'], 2500)
        self.assertEqual(UserProfile.objects.get(user=self.user).obiettivo_kcal, 2500)

    def test_obiettivo_di_un_singolo_giorno(self):
        dati = self._stato(self.client.post(reverse('set_day_macro_goal'), {
            'data': self.oggi.isoformat(), 'kcal': '1800', 'proteine_g': '150',
        }, **self.AJAX))

        self.assertEqual(dati['day'], self.oggi.isoformat())
        self.assertEqual(MacroGoal.objects.get(data=self.oggi).kcal, 1800)

    def test_obiettivo_del_giorno_senza_kcal_non_passa(self):
        r = self.client.post(reverse('set_day_macro_goal'),
                             {'data': self.oggi.isoformat(), 'kcal': '0'}, **self.AJAX)

        self.assertEqual(r.status_code, 400)
        self.assertEqual(MacroGoal.objects.count(), 0)

    def test_stato_del_giorno_si_imposta_e_si_toglie(self):
        self._stato(self.client.post(reverse('set_macro_day_status'), {
            'data': self.oggi.isoformat(), 'stato': 'non_tracciato',
        }, **self.AJAX))
        self.assertEqual(MacroDayStatus.objects.get(data=self.oggi).stato, 'non_tracciato')

        self._stato(self.client.post(reverse('set_macro_day_status'), {
            'data': self.oggi.isoformat(), 'stato': '',
        }, **self.AJAX))
        self.assertEqual(MacroDayStatus.objects.count(), 0)

    def test_data_non_valida_non_passa(self):
        r = self.client.post(reverse('set_macro_day_status'),
                             {'data': 'non-una-data', 'stato': 'parziale'}, **self.AJAX)

        self.assertEqual(r.status_code, 400)

    def test_i_giorni_non_tracciati_restano_fuori_dall_andamento(self):
        self._voce(data=self.oggi - timedelta(days=1))
        self._voce(data=self.oggi)
        MacroDayStatus.objects.create(utente=self.user, data=self.oggi, stato='non_tracciato')

        dati = self._stato(self.client.get(reverse('macro'), **self.AJAX))

        giorni = [p['date'] for p in dati['chart_data']['kcal']]
        self.assertNotIn(self.oggi.strftime('%d/%m/%Y'), giorni)

    def test_lo_storico_resta_sulla_pagina_che_si_stava_guardando(self):
        for i in range(20):
            self._voce(data=self.oggi - timedelta(days=i))
        vecchia = MacroEntry.objects.order_by('data').first()

        dati = self._stato(self.client.post(
            reverse('delete_macro_entry', args=[vecchia.id]), {'page': '2'}, **self.AJAX))

        self.assertEqual(dati['page'], 2)

    def test_un_giorno_svuotato_non_e_su_un_altra_pagina(self):
        """Sparire perche' non ha piu' voci non e' come essere altrove.

        Il toast dice "giorno su un'altra pagina" solo se quel giorno esiste
        ancora davvero: su un giorno svuotato sarebbe una bugia, e manderebbe
        l'utente a cercarlo dove non c'e'.
        """
        sola = self._voce()

        dati = self._stato(self.client.post(
            reverse('delete_macro_entry', args=[sola.id]), {}, **self.AJAX))

        self.assertFalse(dati['day_altrove'])

    def test_un_giorno_fuori_pagina_viene_segnalato(self):
        for i in range(20):
            self._voce(data=self.oggi - timedelta(days=i))
        # La ventesima giornata indietro sta in seconda pagina (14 per pagina),
        # ma la richiesta arriva dalla prima.
        lontana = self.oggi - timedelta(days=19)

        dati = self._stato(self.client.post(reverse('set_macro_day_status'), {
            'data': lontana.isoformat(), 'stato': 'parziale', 'page': '1',
        }, **self.AJAX))

        self.assertTrue(dati['day_altrove'])

    def test_eliminazione_in_blocco_ignora_gli_id_non_numerici(self):
        """Un id non numerico farebbe saltare la query con un ValueError."""
        resta = self._voce()

        self._stato(self.client.post(reverse('bulk_delete_macro_entries'),
                                     {'entry_ids': ['abc', '']}, **self.AJAX))

        self.assertEqual(list(MacroEntry.objects.filter(utente=self.user)), [resta])

    def test_il_javascript_della_pagina_e_sintatticamente_valido(self):
        """Un apice fuori posto spegne tutta la pagina, in silenzio.

        Il browser scarta l'intero blocco <script> e da quel momento non
        funziona piu' niente: ne' i pulsanti, ne' i form, ne' il grafico. Gli
        altri test qui sopra passerebbero lo stesso, perche' guardano solo le
        risposte del server -- questo e' l'unico che se ne accorge.
        """
        node = shutil.which('node')
        if not node:
            self.skipTest('node non disponibile')

        self._voce()
        corpo = self.client.get(reverse('macro')).content.decode()
        blocchi = re.findall(r'<script(?![^>]*src=)[^>]*>(.*?)</script>', corpo, re.S)
        self.assertTrue(blocchi, 'nessuno script in pagina: estrazione da rivedere')

        cartella = tempfile.mkdtemp()
        try:
            for i, js in enumerate(blocchi):
                percorso = os.path.join(cartella, 'blocco%d.js' % i)
                with open(percorso, 'w', encoding='utf-8') as f:
                    f.write(js)
                esito = subprocess.run([node, '--check', percorso],
                                       capture_output=True, text=True)
                self.assertEqual(esito.returncode, 0,
                                 'script non valido:' + chr(10) + esito.stderr)
        finally:
            shutil.rmtree(cartella, ignore_errors=True)

    def test_non_si_tocca_la_voce_di_un_altro(self):
        altro = User.objects.create_user(username='estraneo', password='x')
        sua = MacroEntry.objects.create(utente=altro, kcal=100, data=self.oggi)

        r = self.client.post(reverse('delete_macro_entry', args=[sua.id]), {}, **self.AJAX)

        self.assertEqual(r.status_code, 404)
        self.assertTrue(MacroEntry.objects.filter(id=sua.id).exists())


class GraficiResponsiveTest(TestCase):
    """I grafici devono tornare grandi quando la finestra torna grande.

    Chart.js prende le misure dal contenitore del canvas. Se il canvas porta
    un max-height e il contenitore non ha un'altezza sua, l'altezza del
    contenitore finisce per dipendere dal canvas: da quel momento il grafico
    si rimpicciolisce e non torna piu' su. Lo si vede uscendo dalla modalita'
    telefono di F12, dove resta un francobollo in un riquadro largo.

    Sono controlli sul sorgente dei template e non sulla pagina resa: quello
    che conta e' la forma del markup, e cosi' valgono anche per i grafici che
    verranno aggiunti dopo, senza doverli elencare qui.
    """

    CARTELLA = os.path.join(os.path.dirname(__file__), 'templates')

    def _grafici(self):
        """(percorso, testo) di ogni template che disegna un grafico."""
        trovati = []
        for radice, _, files in os.walk(self.CARTELLA):
            for nome in sorted(files):
                if not nome.endswith('.html'):
                    continue
                percorso = os.path.join(radice, nome)
                with open(percorso, encoding='utf-8') as f:
                    testo = f.read()
                if 'new Chart(' in testo:
                    trovati.append((percorso, testo))
        return trovati

    def _contenitore_del_canvas(self, testo, inizio):
        """Il <div> che avvolge il canvas che comincia a quell'indice."""
        prima = testo[:inizio]
        apertura = prima.rfind('<div')
        if apertura == -1:
            return ''
        return testo[apertura:testo.find('>', apertura) + 1]

    def test_i_template_con_grafici_si_trovano(self):
        """Se la ricerca non trova niente i controlli qui sotto passano a vuoto."""
        self.assertTrue(self._grafici(), 'nessun template con grafici: ricerca da rivedere')

    def test_nessun_canvas_con_max_height(self):
        for percorso, testo in self._grafici():
            for tag in re.findall(r'<canvas[^>]*>', testo):
                self.assertNotIn(
                    'max-height', tag,
                    'max-height sul canvas in %s: taglia l altezza che Chart.js '
                    'ha calcolato, e il grafico non torna piu grande' % percorso)

    def test_ogni_grafico_rinuncia_alle_proporzioni_fisse(self):
        for percorso, testo in self._grafici():
            self.assertIn(
                'maintainAspectRatio: false', testo,
                'in %s manca maintainAspectRatio: false, quindi Chart.js '
                'calcola l altezza dalla larghezza invece di riempire il '
                'contenitore' % percorso)

    def test_ogni_canvas_sta_in_un_contenitore_con_altezza_propria(self):
        for percorso, testo in self._grafici():
            for m in re.finditer(r'<canvas[^>]*>', testo):
                tag = self._contenitore_del_canvas(testo, m.start())
                self.assertIn(
                    'position: relative', tag,
                    'il contenitore del canvas in %s non e position: relative '
                    '(%s)' % (percorso, tag[:120]))
                self.assertRegex(
                    tag, r'height:\s*\d',
                    'il contenitore del canvas in %s non ha un altezza propria '
                    '(%s)' % (percorso, tag[:120]))


class ImportDaAtletaTest(TestCase):
    """Pannello "importa sessione" del modale del giorno.

    Il caso piu' comune e' rifare un proprio allenamento di qualche settimana
    fa, che prima non si poteva: la ricerca escludeva se stessi e l'import
    rispondeva "Non puoi importare una tua sessione". Restava solo uscire dal
    modale e andare a cercarsela.
    """

    AJAX = {'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'}

    def setUp(self):
        self.io = User.objects.create_user(username='aaa_io', password='x')
        # Il nome viene dopo il mio in alfabeto: serve a distinguere
        # "e' in cima perche' sono io" da "e' in cima per il nome".
        self.pubblico = User.objects.create_user(username='zzz_pubblico', password='x')
        self.privato = User.objects.create_user(username='zzz_privato', password='x')
        for u, pubblico in ((self.io, False), (self.pubblico, True), (self.privato, False)):
            p, _ = UserProfile.objects.get_or_create(user=u)
            p.is_public = pubblico
            p.save()
        self.oggi = timezone.localdate()
        self.client.force_login(self.io)

    def _sessione(self, utente, peso=100):
        s = WorkoutSession.objects.create(
            utente=utente, data=self.oggi - timedelta(days=30), nome='Petto')
        es, _ = Exercise.objects.get_or_create(nome='Panca piana')
        WorkoutSet.objects.create(session=s, exercise=es, reps=8, weight=peso, order=1)
        return s

    def _cerca(self, q=''):
        r = self.client.get(reverse('atleti_cerca'), {'q': q}, **self.AJAX)
        self.assertEqual(r.status_code, 200)
        return r.json()['atleti']

    # --- chi si vede nella ricerca ---
    def test_mi_vedo_fra_gli_atleti(self):
        atleti = self._cerca()
        self.assertIn('aaa_io', [a['username'] for a in atleti])

    def test_sono_il_primo_della_lista(self):
        """Anche quando l'alfabeto direbbe altro: la propria e' la voce cercata."""
        mio = User.objects.create_user(username='zzz_ultimo', password='x')
        p, _ = UserProfile.objects.get_or_create(user=mio)
        p.is_public = False
        p.save()
        self.client.force_login(mio)

        atleti = self._cerca()

        self.assertEqual(atleti[0]['username'], 'zzz_ultimo')
        self.assertTrue(atleti[0]['io'])
        self.assertFalse(atleti[1]['io'])

    def test_mi_vedo_anche_col_profilo_privato(self):
        """is_public dice cosa vedono gli altri di me, non cosa vedo io."""
        self.assertFalse(UserProfile.objects.get(user=self.io).is_public)
        self.assertIn('aaa_io', [a['username'] for a in self._cerca()])

    def test_gli_altri_privati_restano_nascosti(self):
        nomi = [a['username'] for a in self._cerca()]
        self.assertIn('zzz_pubblico', nomi)
        self.assertNotIn('zzz_privato', nomi)

    def test_il_superuser_vede_tutti_se_compreso(self):
        capo = User.objects.create_superuser(username='capo', password='x')
        self.client.force_login(capo)
        nomi = [a['username'] for a in self._cerca()]
        for atteso in ('capo', 'aaa_io', 'zzz_pubblico', 'zzz_privato'):
            self.assertIn(atteso, nomi)

    def test_la_ricerca_per_nome_trova_anche_me(self):
        self.assertEqual([a['username'] for a in self._cerca('aaa')], ['aaa_io'])

    def test_il_conteggio_sessioni_e_il_mio(self):
        self._sessione(self.io)
        self._sessione(self.io)
        mio = [a for a in self._cerca() if a['io']][0]
        self.assertEqual(mio['n_sessioni'], 2)

    # --- sfogliare le proprie sessioni ---
    def test_posso_sfogliare_le_mie_sessioni(self):
        sess = self._sessione(self.io)
        r = self.client.get(reverse('atleta_sessioni', args=['aaa_io']), **self.AJAX)
        self.assertEqual(r.status_code, 200)
        self.assertTrue(any(s['id'] == sess.id for s in r.json()['sessioni']))

    def test_le_sessioni_di_un_privato_restano_chiuse(self):
        self._sessione(self.privato)
        r = self.client.get(reverse('atleta_sessioni', args=['zzz_privato']), **self.AJAX)
        self.assertEqual(r.status_code, 404)

    # --- importare ---
    def test_importo_una_mia_sessione_sul_giorno_scelto(self):
        sess = self._sessione(self.io, peso=100)

        r = self.client.post(
            reverse('import_session_from_user', args=['aaa_io', sess.id]),
            {'data': self.oggi.isoformat(), 'weight_pct': '90'}, **self.AJAX)

        self.assertEqual(r.status_code, 200, r.content[:300])
        dati = r.json()
        self.assertTrue(dati['ok'])
        nuova = WorkoutSession.objects.get(id=dati['session_id'])
        self.assertEqual(nuova.utente, self.io)
        self.assertEqual(nuova.data, self.oggi)
        self.assertEqual(float(nuova.sets.get().weight), 90.0)
        # L'originale resta dov'era.
        sess.refresh_from_db()
        self.assertEqual(sess.data, self.oggi - timedelta(days=30))

    def test_importare_da_se_non_tocca_l_originale(self):
        sess = self._sessione(self.io)
        self.client.post(reverse('import_session_from_user', args=['aaa_io', sess.id]),
                         {'data': self.oggi.isoformat()}, **self.AJAX)
        self.assertEqual(WorkoutSession.objects.filter(utente=self.io).count(), 2)

    def test_non_importo_la_sessione_di_un_privato(self):
        sess = self._sessione(self.privato)
        r = self.client.post(
            reverse('import_session_from_user', args=['zzz_privato', sess.id]),
            {'data': self.oggi.isoformat()}, **self.AJAX)
        self.assertEqual(r.status_code, 400)
        self.assertEqual(WorkoutSession.objects.filter(utente=self.io).count(), 0)

    def test_importo_da_un_atleta_pubblico(self):
        sess = self._sessione(self.pubblico)
        r = self.client.post(
            reverse('import_session_from_user', args=['zzz_pubblico', sess.id]),
            {'data': self.oggi.isoformat()}, **self.AJAX)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(WorkoutSession.objects.filter(utente=self.io).count(), 1)

    def test_lo_username_e_unico(self):
        """Le rotte dell'import indirizzano l'atleta per username.

        Regge perche' il campo e' unico a livello di database: due utenti con
        lo stesso nome non possono esistere, quindi non c'e' modo di importare
        dalla persona sbagliata.
        """
        self.assertTrue(User._meta.get_field('username').unique)
        with self.assertRaises(Exception):
            User.objects.create_user(username='aaa_io', password='x')


class PassiGoalTest(TestCase):
    """Obiettivo passi di una giornata specifica.

    Senza l'override l'obiettivo era un solo numero globale e retroattivo:
    alzarlo ricoloriva la heatmap all'indietro, e un giorno chiuso sopra
    l'asticella di allora diventava "sotto obiettivo" a posteriori.
    """

    def setUp(self):
        self.user = User.objects.create_superuser(username='tester', password='x')
        self.client.force_login(self.user)
        self.oggi = timezone.localdate()
        self.ieri = self.oggi - timedelta(days=1)

    def _salva(self, giorno, valore):
        return self.client.post(reverse('set_obiettivo_giorno_passi'), {
            'data': giorno.isoformat(), 'obiettivo_passi': valore,
        })

    def _obiettivi_heatmap(self):
        """Gli obiettivi che la pagina passa alla heatmap, uno per data."""
        ctx = self.client.get(reverse('attivita')).context
        return [v['goal'] for v in json.loads(ctx['heatmap_data_json'])]

    def test_senza_override_vale_il_default_del_profilo(self):
        PassiGiorno.objects.create(utente=self.user, data=self.oggi, passi=9000)
        self.assertEqual(self._obiettivi_heatmap(), [10000])

    def test_un_giorno_puo_avere_il_suo_obiettivo(self):
        self._salva(self.oggi, '6000')
        self.assertEqual(
            PassiGoal.objects.get(utente=self.user, data=self.oggi).obiettivo_passi, 6000)

    def test_la_heatmap_riceve_un_obiettivo_diverso_per_giorno(self):
        PassiGiorno.objects.create(utente=self.user, data=self.oggi, passi=9000)
        PassiGiorno.objects.create(utente=self.user, data=self.ieri, passi=9000)
        self._salva(self.ieri, '6000')

        self.assertEqual(sorted(self._obiettivi_heatmap()), [6000, 10000])

    def test_alzare_il_default_non_tocca_i_giorni_con_obiettivo_proprio(self):
        PassiGiorno.objects.create(utente=self.user, data=self.ieri, passi=8500)
        self._salva(self.ieri, '8000')

        self.client.post(reverse('set_obiettivo_passi'), {'obiettivo_passi': '15000'})

        ctx = self.client.get(reverse('attivita')).context
        # Ieri resta un giorno centrato: l'asticella di allora era 8.000.
        self.assertEqual(ctx['giorni_sopra_obiettivo'], 1)

    def test_riscrivere_lo_stesso_giorno_corregge_invece_di_duplicare(self):
        self._salva(self.oggi, '6000')
        self._salva(self.oggi, '7000')

        voci = PassiGoal.objects.filter(utente=self.user, data=self.oggi)
        self.assertEqual(voci.count(), 1)
        self.assertEqual(voci.first().obiettivo_passi, 7000)

    def test_campo_vuoto_rimuove_override_e_si_torna_al_default(self):
        self._salva(self.oggi, '6000')
        self._salva(self.oggi, '')

        self.assertFalse(PassiGoal.objects.filter(utente=self.user).exists())

    def test_percentuale_di_oggi_usa_l_obiettivo_di_oggi(self):
        PassiGiorno.objects.create(utente=self.user, data=self.oggi, passi=6000)
        self._salva(self.oggi, '6000')

        self.assertEqual(self.client.get(reverse('attivita')).context['percentuale_oggi'], 100)

    def test_una_data_o_un_valore_non_validi_non_scrivono_niente(self):
        self.client.post(reverse('set_obiettivo_giorno_passi'),
                         {'data': 'non-una-data', 'obiettivo_passi': '6000'})
        self._salva(self.oggi, 'tanti')
        self._salva(self.oggi, '0')

        self.assertFalse(PassiGoal.objects.exists())

    def test_un_utente_normale_non_imposta_obiettivi(self):
        self.client.force_login(User.objects.create_user(username='atleta', password='x'))
        self._salva(self.oggi, '6000')

        self.assertFalse(PassiGoal.objects.exists())
