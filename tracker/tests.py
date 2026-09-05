from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import Exercise, WorkoutSession, WorkoutSet


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
