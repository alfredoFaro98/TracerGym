import shutil
import tempfile
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
    BodyMetric, Exercise, ExerciseImage, UserProfile, WaterEntry, WaterGoal,
    WorkoutSession, WorkoutSet,
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

