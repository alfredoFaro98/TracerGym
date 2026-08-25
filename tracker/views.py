from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string
from django.urls import reverse
from django.http import JsonResponse
from django.db import models, transaction
import json
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from django.contrib.auth.views import LoginView
from itertools import groupby
import time
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta, time as dt_time
from django.utils import timezone
from django.contrib.auth.models import User
from .models import WorkoutSession, WorkoutSet, Exercise, MuscleGroup, Tag, UserProfile, ExerciseImage, Circuit, WaterEntry, BodyMetric, WaterGoal, IntegratoreEntry, SiteVisit


REMEMBER_ME_SECONDS = 60 * 60 * 24 * 30  # 30 giorni


def _record_site_visit():
    """Incrementa il contatore di visite (dashboard/login) del giorno corrente."""
    today = timezone.now().date()
    updated = SiteVisit.objects.filter(data=today).update(conteggio=models.F('conteggio') + 1)
    if not updated:
        SiteVisit.objects.get_or_create(data=today, defaults={'conteggio': 1})


def _parse_carrucole(request):
    """Numero di carrucole per un esercizio, solo se la checkbox è flaggata."""
    if request.POST.get('has_carrucole') != 'on':
        return None
    try:
        return int(request.POST.get('carrucole', ''))
    except ValueError:
        return None


class TracerLoginView(LoginView):
    template_name = 'tracker/login.html'
    redirect_authenticated_user = True

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if response.status_code == 200:
            _record_site_visit()
        return response

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.POST.get('remember') == 'on':
            self.request.session.set_expiry(REMEMBER_ME_SECONDS)
        # Se non spuntato, non tocchiamo nulla: resta la durata di default (SESSION_COOKIE_AGE).
        return response


def _delete_blank_sessions(user):
    """Rimuove solo le sessioni create ma mai davvero usate: nessuna serie,
    nessun circuito, e nessun campo di dettaglio compilato (luogo/orario/
    durata/peso/altezza/compagni/note). Cosi' una sessione dove l'utente ha
    gia' compilato i dettagli ma non ha ancora aggiunto esercizi non sparisce
    al primo giro in dashboard."""
    WorkoutSession.objects.filter(
        utente=user,
        sets__isnull=True,
        circuits__isnull=True,
        luogo='',
        orario__isnull=True,
        durata_minuti__isnull=True,
        peso_kg__isnull=True,
        altezza_cm__isnull=True,
        compagni_allenamento='',
    ).filter(
        models.Q(note__isnull=True) | models.Q(note='')
    ).delete()


@login_required
def dashboard(request):
    _record_site_visit()
    _delete_blank_sessions(request.user)

    # Recupera tutte le sessioni dell'utente loggato con prefetch per ottimizzare le query
    sessions_query = WorkoutSession.objects.filter(utente=request.user).prefetch_related('sets__exercise').order_by('-data', '-id')
    
    # Filtro di ricerca testo
    q = request.GET.get('q', '').strip()
    if q:
        sessions_query = sessions_query.filter(
            models.Q(note__icontains=q) | 
            models.Q(sets__exercise__nome__icontains=q)
        ).distinct()
        
    # Filtro per anno (nuovo)
    year_str = request.GET.get('year')
    if year_str and year_str.isdigit():
        year_int = int(year_str)
    else:
        year_int = timezone.now().year
    # Applica filtro anno sia a sessions_query che a all_sessions
    sessions_query = sessions_query.filter(data__year=year_int)
    
    # Filtro per mese (mantieni filtraggio)
    month_filter = request.GET.get('month', '')
    if month_filter:
        try:
            year_part, month = month_filter.split('-')
            sessions_query = sessions_query.filter(data__year=year_part, data__month=month)
        except ValueError:
            pass

    # Paginazione: 15 sessioni per pagina
    paginator = Paginator(sessions_query, 15)
    page_number = request.GET.get('page')
    sessions = paginator.get_page(page_number)

    # Prepara dati per heatmap: colore in base al numero di SERIE fatte quel
    # giorno (non al numero di sessioni), sommando piu' sessioni nello stesso giorno.
    all_sessions = WorkoutSession.objects.filter(utente=request.user, data__year=year_int)
    set_counts = (
        WorkoutSet.objects.filter(session__utente=request.user, session__data__year=year_int)
        .values('session__data')
        .annotate(total=models.Count('id'))
    )
    date_counts = {}
    for row in set_counts:
        d_str = row['session__data'].strftime('%Y-%m-%d')
        date_counts[d_str] = date_counts.get(d_str, 0) + row['total']

    heatmap_data = []
    for d_str, count in date_counts.items():
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        timestamp = int(time.mktime(dt.timetuple()))
        heatmap_data.append({'date': timestamp, 'value': count})

    # Statistiche per schermi piccoli
    total_sets = WorkoutSet.objects.filter(session__utente=request.user).count()
    now = timezone.now()
    this_month_sessions = all_sessions.filter(data__year=now.year, data__month=now.month).count()

    exercises_qs = Exercise.objects.prefetch_related('tags').order_by('nome')
    exercises_data = []
    for ex in exercises_qs:
        exercises_data.append({
            'id': ex.id,
            'nome': ex.nome,
            'tipologia': ex.tipologia or '',
            'tags': [t.nome.lower() for t in ex.tags.all()],
        })
    
    last_set = (
        WorkoutSet.objects
        .filter(session__utente=request.user)
        .filter(models.Q(weight__isnull=False) | models.Q(barra_kg__isnull=False))
        .order_by('-session__data', '-id')
        .select_related('exercise')
        .first()
    )
    default_exercise = last_set.exercise.nome if last_set else ''

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    today = timezone.now().date()
    water_entries_today = WaterEntry.objects.filter(utente=request.user, data=today).order_by('-creato_il')
    water_today_ml = sum(e.quantita_ml for e in water_entries_today)
    today_goal_override = WaterGoal.objects.filter(utente=request.user, data=today).first()
    water_goal_ml = today_goal_override.obiettivo_ml if today_goal_override else profile.obiettivo_acqua_ml

    return render(request, 'tracker/dashboard.html', {
        'sessions': sessions,
        'total_sessions_count': all_sessions.count(),
        'total_sets': total_sets,
        'this_month_sessions': this_month_sessions,
        'heatmap_data_json': json.dumps(heatmap_data),
        'selected_year': year_int,
        'exercises_json': json.dumps(exercises_data),
        'default_exercise': default_exercise,
        'water_entries_today': water_entries_today,
        'water_today_ml': water_today_ml,
        'water_goal_ml': water_goal_ml,
        'water_today_l': water_today_ml / 1000,
        'water_goal_l': water_goal_ml / 1000,
        'water_progress_pct': min(100, round(water_today_ml / water_goal_ml * 100)) if water_goal_ml else 0,
    })

@login_required
def weekly_sessions_data(request):
    monday_str = request.GET.get('monday', '')
    today = timezone.now().date()

    try:
        monday = date.fromisoformat(monday_str) if monday_str else today - timedelta(days=today.weekday())
    except ValueError:
        monday = today - timedelta(days=today.weekday())

    monday -= timedelta(days=monday.weekday())
    sunday = monday + timedelta(days=6)

    sessions = (
        WorkoutSession.objects
        .filter(utente=request.user, data__gte=monday, data__lte=sunday)
        .prefetch_related('sets__exercise', 'circuits__sets__exercise')
        .order_by('data', 'id')
    )

    def _ws_entry(ws):
        entry = {}
        if ws.reps: entry['reps'] = ws.reps
        if ws.weight is not None: entry['weight'] = float(ws.weight)
        if ws.durata: entry['durata'] = ws.durata
        if ws.a_cedimento: entry['a_cedimento'] = True
        if ws.barra_kg is not None: entry['barra_kg'] = float(ws.barra_kg)
        if ws.per_lato: entry['per_lato'] = True
        if ws.rest_time: entry['rest_time'] = ws.rest_time
        return entry

    days = []
    for i in range(7):
        day_date = monday + timedelta(days=i)
        day_sessions = [s for s in sessions if s.data == day_date]
        sessions_data = []
        for s in day_sessions:
            exercises = {}
            order_list = []
            for ws in s.sets.all().order_by('order', 'id'):
                if ws.circuit_id is not None:
                    continue
                ex = ws.exercise.nome
                if ex not in exercises:
                    exercises[ex] = []
                    order_list.append(ex)
                exercises[ex].append(_ws_entry(ws))
            circuit_list = []
            for c in s.circuits.all().order_by('order', 'id'):
                c_exercises = {}
                c_order_list = []
                for ws in c.sets.all().order_by('order', 'id'):
                    ex = ws.exercise.nome
                    if ex not in c_exercises:
                        c_exercises[ex] = []
                        c_order_list.append(ex)
                    c_exercises[ex].append(_ws_entry(ws))
                circuit_list.append({
                    'nome': c.nome,
                    'rounds': c.rounds,
                    'rest_tra_round': c.rest_tra_round,
                    'exercises': [{'nome': k, 'sets': c_exercises[k]} for k in c_order_list],
                })
            sessions_data.append({
                'id': s.id,
                'note': s.note or '',
                'exercises': [{'nome': k, 'sets': exercises[k]} for k in order_list],
                'circuits': circuit_list,
            })
        days.append({'date': day_date.strftime('%Y-%m-%d'), 'sessions': sessions_data})

    return JsonResponse({'monday': monday.strftime('%Y-%m-%d'), 'sunday': sunday.strftime('%Y-%m-%d'), 'days': days})


@login_required
def create_session(request):
    _delete_blank_sessions(request.user)
    session = WorkoutSession.objects.create(utente=request.user)
    return redirect('session_detail', session_id=session.id)

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)

    if request.method == 'POST':
        exercise_name = (request.POST.get('exercise_name') or '').strip()
        reps = request.POST.get('reps') or None
        durata = request.POST.get('durata') or None
        weight = request.POST.get('weight') or None
        rest_time = request.POST.get('rest_time') or None
        per_lato = request.POST.get('per_lato') == 'on'
        avviamento = request.POST.get('avviamento') == 'on'
        a_cedimento = request.POST.get('a_cedimento') == 'on'
        richiamo = request.POST.get('richiamo') == 'on'
        barra_kg = request.POST.get('barra_kg') or None
        circuit_id = request.POST.get('circuit_id') or None
        add_default_warmup = request.POST.get('aggiungi_avviamento_default') == 'on'

        exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
        if not exercise:
            return render(request, 'tracker/session_detail.html', {
                **_build_session_context(session),
                'error_exercise': f'"{exercise_name}" non è nella lista degli esercizi. Seleziona un esercizio dalla lista.',
            })

        circuit = None
        if circuit_id:
            circuit = Circuit.objects.filter(id=circuit_id, session=session).first()

        num_sets = 1 if circuit else int(request.POST.get('num_sets') or 1)

        # Serie di avviamento automatica: una sola, inserita subito prima delle serie
        # di lavoro appena aggiunte. Peso e ripetizioni sono quelli dei campi dedicati
        # (proposti dal JS a meta' peso / stesse ripetizioni, ma modificabili a mano);
        # se il peso manca o non e' valido, ricalcoliamo noi la meta' come rete di
        # sicurezza. Il peso non e' mai negativo.
        warmup_weight = None
        if add_default_warmup:
            warmup_override = request.POST.get('avviamento_default_peso')
            if warmup_override:
                try:
                    warmup_weight = max(Decimal('0'), Decimal(warmup_override))
                except InvalidOperation:
                    warmup_weight = None
            if warmup_weight is None and weight:
                try:
                    warmup_weight = max(Decimal('0'), Decimal(weight) / 2)
                except InvalidOperation:
                    warmup_weight = None
        warmup_reps = request.POST.get('avviamento_default_reps') or reps
        warmup_rest_raw = request.POST.get('avviamento_default_rest')
        try:
            warmup_rest = int(warmup_rest_raw) if warmup_rest_raw else 40
        except ValueError:
            warmup_rest = 40
        extra_warmup = 1 if warmup_weight is not None else 0

        # Inserisce le nuove serie subito dopo le serie esistenti dello stesso esercizio
        # (nello stesso ambito: circuito o lista normale), cosi' restano contigue e non
        # si spezzano in piu' gruppi separati quando si aggiunge di nuovo lo stesso esercizio.
        if circuit:
            scope_qs = circuit.sets.all()
            existing_ex_sets = list(circuit.sets.filter(exercise=exercise).order_by('order', 'id'))
        else:
            scope_qs = session.sets.filter(circuit__isnull=True)
            existing_ex_sets = list(scope_qs.filter(exercise=exercise).order_by('order', 'id'))

        total_new = num_sets + extra_warmup
        if existing_ex_sets:
            insert_after = existing_ex_sets[-1].order
            scope_qs.filter(order__gt=insert_after).update(order=models.F('order') + total_new)
            base_order = insert_after + 1
        else:
            max_order = scope_qs.aggregate(models.Max('order'))['order__max']
            base_order = (max_order + 1) if max_order is not None else session.sets.count()

        if warmup_weight is not None:
            WorkoutSet.objects.create(
                order=base_order,
                session=session,
                exercise=exercise,
                reps=warmup_reps,
                durata=durata,
                weight=warmup_weight,
                rest_time=warmup_rest,
                per_lato=per_lato,
                avviamento=True,
                a_cedimento=False,
                richiamo=False,
                barra_kg=barra_kg,
                circuit=circuit,
            )
        base_order += extra_warmup

        for i in range(max(1, min(num_sets, 20))):
            WorkoutSet.objects.create(
                order=base_order + i,
                session=session,
                exercise=exercise,
                reps=reps,
                durata=durata,
                weight=weight,
                rest_time=rest_time,
                per_lato=per_lato,
                avviamento=avviamento,
                a_cedimento=a_cedimento,
                richiamo=richiamo,
                barra_kg=barra_kg,
                circuit=circuit,
            )
        url = reverse('session_detail', kwargs={'session_id': session.id})
        if circuit:
            return redirect(f'{url}?opencircuit={circuit.id}')
        return redirect(f'{url}?open={exercise.id}')

    return render(request, 'tracker/session_detail.html', _build_session_context(session))


def _format_rest_duration(total_seconds):
    total_seconds = int(total_seconds or 0)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}h {minutes}m {seconds}s"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def _build_session_context(session):
    normal_sets = list(session.sets.filter(circuit__isnull=True).select_related('exercise').order_by('order', 'id'))
    exercise_groups = []
    total_rest_seconds = sum(s.rest_time or 0 for s in normal_sets)
    for _, grp in groupby(normal_sets, key=lambda s: s.exercise_id):
        grp_list = list(grp)
        exercise_groups.append({'exercise': grp_list[0].exercise, 'sets': grp_list, 'count': len(grp_list)})

    circuits_qs = session.circuits.prefetch_related('sets__exercise').order_by('order', 'id')
    circuit_items = []
    for circuit in circuits_qs:
        c_sets = list(circuit.sets.select_related('exercise').order_by('order', 'id'))
        total_rest_seconds += sum(s.rest_time or 0 for s in c_sets)
        if circuit.rest_tra_round and circuit.rounds > 1:
            total_rest_seconds += circuit.rest_tra_round * (circuit.rounds - 1)
        c_groups = []
        for _, grp in groupby(c_sets, key=lambda s: s.exercise_id):
            grp_list = list(grp)
            c_groups.append({'exercise': grp_list[0].exercise, 'sets': grp_list})
        circuit_items.append({'circuit': circuit, 'exercise_groups': c_groups})

    return {
        'session': session,
        'exercise_groups': exercise_groups,
        'circuit_items': circuit_items,
        'total_rest_label': _format_rest_duration(total_rest_seconds),
        'tags': Tag.objects.all().order_by('nome'),
    }

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            UserProfile.objects.create(user=user)
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def create_circuit(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        rounds = int(request.POST.get('rounds') or 3)
        rest_tra_round = request.POST.get('rest_tra_round') or None
        order = session.circuits.count()
        circuit = Circuit.objects.create(
            session=session, nome=nome, rounds=rounds,
            rest_tra_round=rest_tra_round, order=order,
        )
        url = reverse('session_detail', kwargs={'session_id': session_id})
        return redirect(f'{url}?opencircuit={circuit.id}')
    return redirect('session_detail', session_id=session_id)


@login_required
def import_circuit(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        source = (
            Circuit.objects
            .filter(id=request.POST.get('circuit_id'), session__utente=request.user)
            .prefetch_related('sets__exercise')
            .first()
        )
        if source:
            order = session.circuits.count()
            new_circuit = Circuit.objects.create(
                session=session, nome=source.nome, rounds=source.rounds,
                rest_tra_round=source.rest_tra_round, order=order,
            )
            base_order = session.sets.count()
            for i, s in enumerate(source.sets.order_by('order', 'id')):
                WorkoutSet.objects.create(
                    session=session, exercise=s.exercise, circuit=new_circuit,
                    reps=s.reps, durata=s.durata, weight=s.weight,
                    rest_time=s.rest_time, per_lato=s.per_lato,
                    avviamento=s.avviamento, a_cedimento=s.a_cedimento,
                    richiamo=s.richiamo, barra_kg=s.barra_kg,
                    order=base_order + i,
                )
            url = reverse('session_detail', kwargs={'session_id': session_id})
            return redirect(f'{url}?opencircuit={new_circuit.id}')
    return redirect('session_detail', session_id=session_id)


@login_required
def circuit_suggestions(request):
    q = request.GET.get('q', '').strip()
    circuits_qs = (
        Circuit.objects
        .filter(session__utente=request.user)
        .select_related('session')
        .prefetch_related('sets__exercise')
        .order_by('-session__data', '-id')
    )
    if q:
        circuits_qs = circuits_qs.filter(
            models.Q(nome__icontains=q) | models.Q(sets__exercise__nome__icontains=q)
        ).distinct()

    results = []
    for c in circuits_qs[:20]:
        exercise_names = []
        seen = set()
        for s in c.sets.all():
            if s.exercise_id not in seen:
                seen.add(s.exercise_id)
                exercise_names.append(s.exercise.nome)
        label = f"{c.session.data.strftime('%d/%m/%Y')} — {c.nome or 'Circuito'} ({c.rounds} round, {len(exercise_names)} esercizi)"
        results.append({'id': c.id, 'label': label, 'exercises': ', '.join(exercise_names[:4])})
    return JsonResponse({'results': results})


@login_required
def edit_circuit(request, circuit_id):
    circuit = get_object_or_404(Circuit, id=circuit_id, session__utente=request.user)
    if request.method == 'POST':
        circuit.nome = request.POST.get('nome', '').strip()
        circuit.rounds = int(request.POST.get('rounds') or circuit.rounds)
        circuit.rest_tra_round = request.POST.get('rest_tra_round') or None
        circuit.save()
    url = reverse('session_detail', kwargs={'session_id': circuit.session_id})
    return redirect(f'{url}?opencircuit={circuit.id}')


@login_required
def delete_circuit(request, circuit_id):
    circuit = get_object_or_404(Circuit, id=circuit_id, session__utente=request.user)
    session_id = circuit.session_id
    if request.method == 'POST':
        circuit.sets.all().delete()
        circuit.delete()
    return redirect('session_detail', session_id=session_id)


def _render_set_row(request, workout_set):
    return render_to_string('tracker/partials/set_row.html', {
        'set': workout_set,
        'group_n': workout_set.exercise_id,
        'in_circuit': bool(workout_set.circuit_id),
    }, request=request)


@login_required
def delete_set(request, set_id):
    # Recupera il set solo se la sessione appartiene all'utente loggato
    workout_set = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    if request.method == 'POST':
        workout_set.delete()
    return JsonResponse({'ok': True})


@login_required
def duplicate_set(request, set_id):
    original = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    new_set = original
    if request.method == 'POST':
        if original.circuit_id:
            scope_qs = original.circuit.sets.all()
        else:
            scope_qs = original.session.sets.filter(circuit__isnull=True)
        scope_qs.filter(order__gt=original.order).update(order=models.F('order') + 1)
        new_set = WorkoutSet.objects.create(
            session=original.session,
            exercise=original.exercise,
            reps=original.reps,
            durata=original.durata,
            weight=original.weight,
            rest_time=original.rest_time,
            per_lato=original.per_lato,
            avviamento=original.avviamento,
            a_cedimento=original.a_cedimento,
            richiamo=original.richiamo,
            barra_kg=original.barra_kg,
            order=original.order + 1,
            circuit=original.circuit,
        )
        new_set.muscles.set(original.muscles.all())
    return JsonResponse({'ok': True, 'html': _render_set_row(request, new_set)})


@login_required
def edit_set(request, set_id):
    workout_set = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    if request.method == 'POST':
        exercise_name = request.POST.get('exercise_name', '').strip()
        weight = request.POST.get('weight') or None
        rest_time = request.POST.get('rest_time') or None
        if exercise_name:
            exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
            if exercise:
                workout_set.exercise = exercise
        workout_set.reps = request.POST.get('reps') or None
        workout_set.durata = request.POST.get('durata') or None
        workout_set.weight = weight
        workout_set.rest_time = rest_time
        workout_set.per_lato = request.POST.get('per_lato') == 'on'
        workout_set.avviamento = request.POST.get('avviamento') == 'on'
        workout_set.a_cedimento = request.POST.get('a_cedimento') == 'on'
        workout_set.richiamo = request.POST.get('richiamo') == 'on'
        workout_set.barra_kg = request.POST.get('barra_kg') or None
        workout_set.save()
    return JsonResponse({'ok': True, 'html': _render_set_row(request, workout_set)})

@login_required
def duplicate_session(request, session_id):
    original = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        new_session = WorkoutSession.objects.create(
            utente=request.user,
            note=original.note,
            luogo=original.luogo,
            orario=original.orario,
            orario_fine=original.orario_fine,
            durata_minuti=original.durata_minuti,
            peso_kg=original.peso_kg,
            altezza_cm=original.altezza_cm,
            compagni_allenamento=original.compagni_allenamento,
        )
        for s in original.sets.filter(circuit__isnull=True).order_by('order', 'id'):
            WorkoutSet.objects.create(
                session=new_session, exercise=s.exercise,
                reps=s.reps, durata=s.durata, weight=s.weight,
                rest_time=s.rest_time, per_lato=s.per_lato,
                avviamento=s.avviamento, a_cedimento=s.a_cedimento,
                richiamo=s.richiamo,
                barra_kg=s.barra_kg, order=s.order,
            )
        for c in original.circuits.order_by('order', 'id'):
            new_circuit = Circuit.objects.create(
                session=new_session, nome=c.nome,
                rounds=c.rounds, rest_tra_round=c.rest_tra_round, order=c.order,
            )
            for s in c.sets.order_by('order', 'id'):
                WorkoutSet.objects.create(
                    session=new_session, exercise=s.exercise,
                    reps=s.reps, durata=s.durata, weight=s.weight,
                    rest_time=s.rest_time, per_lato=s.per_lato,
                    avviamento=s.avviamento, a_cedimento=s.a_cedimento,
                    richiamo=s.richiamo,
                    barra_kg=s.barra_kg, order=s.order, circuit=new_circuit,
                )
        return redirect('session_detail', session_id=new_session.id)
    return redirect('session_detail', session_id=session_id)

@login_required
def edit_session_date(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        new_date = request.POST.get('data')
        if new_date:
            session.data = new_date

        session.luogo = (request.POST.get('luogo') or '').strip()

        orario_str = request.POST.get('orario')
        if orario_str:
            try:
                hh, mm = orario_str.split(':')
                session.orario = dt_time(int(hh), int(mm))
            except (ValueError, AttributeError):
                pass
        else:
            session.orario = None

        orario_fine_str = request.POST.get('orario_fine')
        if orario_fine_str:
            try:
                hh, mm = orario_fine_str.split(':')
                session.orario_fine = dt_time(int(hh), int(mm))
            except (ValueError, AttributeError):
                pass
        else:
            session.orario_fine = None

        durata_str = request.POST.get('durata_minuti')
        session.durata_minuti = int(durata_str) if durata_str and durata_str.isdigit() else None

        peso_str = request.POST.get('peso_kg')
        if peso_str:
            try:
                session.peso_kg = float(peso_str)
            except ValueError:
                pass
        else:
            session.peso_kg = None

        altezza_str = request.POST.get('altezza_cm')
        if altezza_str:
            try:
                session.altezza_cm = float(altezza_str)
            except ValueError:
                pass
        else:
            session.altezza_cm = None

        session.compagni_allenamento = (request.POST.get('compagni_allenamento') or '').strip()

        session.save()
    return redirect('session_detail', session_id=session_id)

@login_required
def delete_session(request, session_id):
    # Recupera la sessione assicurandosi che appartenga all'utente loggato
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        session.delete()
    return redirect('dashboard')

@login_required
def clear_session(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        with transaction.atomic():
            session.sets.all().delete()
            session.circuits.all().delete()
    return redirect('session_detail', session_id=session_id)

@login_required
def delete_exercise_sets(request, session_id, exercise_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        session.sets.filter(exercise_id=exercise_id).delete()
    return redirect('session_detail', session_id=session_id)

@login_required
def bulk_delete_sets(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        set_ids = request.POST.getlist('set_ids')
        session.sets.filter(id__in=set_ids).delete()
    return redirect('session_detail', session_id=session_id)

@login_required
def reorder_exercises(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    data = json.loads(request.body)
    exercise_ids = data.get('exercise_ids', [])
    order_counter = 0
    for exercise_id in exercise_ids:
        for ws in session.sets.filter(exercise_id=exercise_id).order_by('order', 'id'):
            ws.order = order_counter
            ws.save(update_fields=['order'])
            order_counter += 1
    return JsonResponse({'ok': True})


@login_required
def reorder_circuit_exercises(request, circuit_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    circuit = get_object_or_404(Circuit, id=circuit_id, session__utente=request.user)
    data = json.loads(request.body)
    exercise_ids = data.get('exercise_ids', [])
    order_counter = 0
    for exercise_id in exercise_ids:
        for ws in circuit.sets.filter(exercise_id=exercise_id).order_by('order', 'id'):
            ws.order = order_counter
            ws.save(update_fields=['order'])
            order_counter += 1
    return JsonResponse({'ok': True})


def _reorder_sets_within(queryset, set_ids):
    sets = {ws.id: ws for ws in queryset.filter(id__in=set_ids)}
    slots = sorted(ws.order for ws in sets.values())
    for order_value, set_id in zip(slots, set_ids):
        ws = sets.get(int(set_id))
        if ws:
            ws.order = order_value
            ws.save(update_fields=['order'])


@login_required
def reorder_sets(request, session_id, exercise_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    data = json.loads(request.body)
    set_ids = data.get('set_ids', [])
    _reorder_sets_within(session.sets.filter(exercise_id=exercise_id, circuit__isnull=True), set_ids)
    return JsonResponse({'ok': True})


@login_required
def reorder_circuit_exercise_sets(request, circuit_id, exercise_id):
    if request.method != 'POST':
        return JsonResponse({'ok': False}, status=405)
    circuit = get_object_or_404(Circuit, id=circuit_id, session__utente=request.user)
    data = json.loads(request.body)
    set_ids = data.get('set_ids', [])
    _reorder_sets_within(circuit.sets.filter(exercise_id=exercise_id), set_ids)
    return JsonResponse({'ok': True})

def _export_set_dict(s):
    return {
        'exercise': s.exercise.nome,
        'reps': s.reps,
        'weight': float(s.weight) if s.weight is not None else None,
        'rest_time': s.rest_time,
        'per_lato': s.per_lato,
        'avviamento': s.avviamento,
        'a_cedimento': s.a_cedimento,
        'richiamo': s.richiamo,
        'barra_kg': float(s.barra_kg) if s.barra_kg is not None else None,
        'durata': s.durata,
        'order': s.order,
    }


def _export_session_dict(session):
    sets = [_export_set_dict(s) for s in session.sets.filter(circuit__isnull=True).order_by('order', 'id')]
    circuits = []
    for c in session.circuits.order_by('order', 'id'):
        circuits.append({
            'nome': c.nome,
            'rounds': c.rounds,
            'rest_tra_round': c.rest_tra_round,
            'order': c.order,
            'sets': [_export_set_dict(s) for s in c.sets.order_by('order', 'id')],
        })
    return {
        'data': session.data.strftime('%Y-%m-%d'),
        'note': session.note or '',
        'luogo': session.luogo or '',
        'orario': session.orario.strftime('%H:%M') if session.orario else None,
        'orario_fine': session.orario_fine.strftime('%H:%M') if session.orario_fine else None,
        'durata_minuti': session.durata_minuti,
        'peso_kg': float(session.peso_kg) if session.peso_kg is not None else None,
        'altezza_cm': float(session.altezza_cm) if session.altezza_cm is not None else None,
        'compagni_allenamento': session.compagni_allenamento or '',
        'sets': sets,
        'circuits': circuits,
    }


@login_required
def export_sessions(request):
    sessions = WorkoutSession.objects.filter(
        utente=request.user
    ).prefetch_related('sets__exercise', 'circuits__sets__exercise').order_by('data')

    data = [_export_session_dict(session) for session in sessions]

    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    filename = f"workout_backup_{timezone.now().strftime('%Y%m%d')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def _import_set_kwargs(s):
    return dict(
        reps=int(s.get('reps') or 0),
        weight=s.get('weight'),
        rest_time=s.get('rest_time'),
        per_lato=bool(s.get('per_lato', False)),
        avviamento=bool(s.get('avviamento', False)),
        a_cedimento=bool(s.get('a_cedimento', False)),
        richiamo=bool(s.get('richiamo', False)),
        barra_kg=s.get('barra_kg'),
        durata=s.get('durata'),
    )


def _get_or_create_exercise(name):
    exercise = Exercise.objects.filter(nome__iexact=name).first()
    if not exercise:
        exercise = Exercise.objects.create(nome=name)
    return exercise


@login_required
def import_sessions(request):
    if request.method == 'POST':
        backup_file = request.FILES.get('backup_file')
        if not backup_file:
            return render(request, 'tracker/import.html', {'error': 'Nessun file selezionato.'})

        try:
            data = json.loads(backup_file.read().decode('utf-8'))
            if not isinstance(data, list):
                raise ValueError
        except (json.JSONDecodeError, UnicodeDecodeError, ValueError):
            return render(request, 'tracker/import.html', {
                'error': 'File non valido. Usa un backup JSON esportato da questa app.'
            })

        imported = 0
        skipped = 0
        for item in data:
            try:
                session_date = datetime.strptime(item['data'], '%Y-%m-%d').date()
                note = item.get('note') or None

                orario = None
                orario_str = item.get('orario')
                if orario_str:
                    orario = dt_time.fromisoformat(orario_str)

                orario_fine = None
                orario_fine_str = item.get('orario_fine')
                if orario_fine_str:
                    orario_fine = dt_time.fromisoformat(orario_fine_str)

                session = WorkoutSession.objects.create(
                    utente=request.user, data=session_date, note=note,
                    luogo=item.get('luogo') or '',
                    orario=orario,
                    orario_fine=orario_fine,
                    durata_minuti=item.get('durata_minuti'),
                    peso_kg=item.get('peso_kg'),
                    altezza_cm=item.get('altezza_cm'),
                    compagni_allenamento=item.get('compagni_allenamento') or '',
                )
                for i, s in enumerate(item.get('sets', [])):
                    exercise_name = (s.get('exercise') or '').strip()
                    if not exercise_name:
                        continue
                    WorkoutSet.objects.create(
                        session=session,
                        exercise=_get_or_create_exercise(exercise_name),
                        order=s.get('order', i),
                        **_import_set_kwargs(s),
                    )
                for ci, c in enumerate(item.get('circuits', [])):
                    circuit = Circuit.objects.create(
                        session=session,
                        nome=c.get('nome') or '',
                        rounds=c.get('rounds') or 3,
                        rest_tra_round=c.get('rest_tra_round'),
                        order=c.get('order', ci),
                    )
                    for j, s in enumerate(c.get('sets', [])):
                        exercise_name = (s.get('exercise') or '').strip()
                        if not exercise_name:
                            continue
                        WorkoutSet.objects.create(
                            session=session,
                            exercise=_get_or_create_exercise(exercise_name),
                            circuit=circuit,
                            order=s.get('order', j),
                            **_import_set_kwargs(s),
                        )
                imported += 1
            except Exception:
                skipped += 1

        return render(request, 'tracker/import.html', {
            'success': f'{imported} sessioni importate con successo.',
            'skipped': skipped or None,
        })

    return render(request, 'tracker/import.html', {})


@login_required
def export_session(request, session_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    data = [_export_session_dict(session)]
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="sessione_{session.data.strftime("%Y%m%d")}.json"'
    return response


@login_required
def exercises_list(request):
    tags = Tag.objects.all().order_by('nome')
    selected_tag = request.GET.get('tag', '')
    error = request.GET.get('error', '')
    total_count = Exercise.objects.count()

    if selected_tag:
        exercises = Exercise.objects.filter(tags__nome=selected_tag).prefetch_related('tags', 'images').order_by('nome')
        tag_groups = None
    else:
        exercises = None
        # Un'unica query per tutti gli esercizi (con i loro tag/immagini prefetchati),
        # poi raggruppati in Python: evita una query separata per ogni tag.
        all_exercises = list(Exercise.objects.prefetch_related('tags', 'images').order_by('nome'))
        by_tag = {}
        untagged = []
        for ex in all_exercises:
            ex_tags = list(ex.tags.all())
            if not ex_tags:
                untagged.append(ex)
            for tag in ex_tags:
                by_tag.setdefault(tag.id, []).append(ex)

        tag_groups = []
        for tag in tags:
            tag_exercises = by_tag.get(tag.id, [])
            if tag_exercises:
                tag_groups.append({'tag': tag, 'exercises': tag_exercises})
        if untagged:
            tag_groups.append({'tag': None, 'exercises': untagged})

    return render(request, 'tracker/exercises.html', {
        'tags': tags,
        'exercises': exercises,
        'tag_groups': tag_groups,
        'selected_tag': selected_tag,
        'error': error,
        'total_count': total_count,
    })


@login_required
def add_exercise(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    next_url = request.POST.get('next', reverse('exercises_list'))
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipologia = request.POST.get('tipologia', '').strip()
        tag_ids = request.POST.getlist('tags')
        if nome:
            if Exercise.objects.filter(nome__iexact=nome).exists():
                from urllib.parse import urlencode
                error_msg = f'Esiste già un esercizio chiamato "{nome}".'
                separator = '&' if '?' in next_url else '?'
                return redirect(f'{next_url}{separator}{urlencode({"error": error_msg})}')
            exercise = Exercise.objects.create(nome=nome, tipologia=tipologia, carrucole=_parse_carrucole(request))
            if tag_ids:
                exercise.tags.set(tag_ids)
    return redirect(next_url)


@login_required
def add_exercise_ajax(request):
    """Crea un esercizio via fetch (usato dal modale "+" nella pagina sessione),
    senza ricaricare la pagina e senza perdere quanto gia' compilato nel form."""
    if not request.user.is_superuser:
        return JsonResponse({'error': 'Non autorizzato.'}, status=403)
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non valido.'}, status=405)

    nome = request.POST.get('nome', '').strip()
    tipologia = request.POST.get('tipologia', '').strip()
    tag_ids = request.POST.getlist('tags')

    if not nome:
        return JsonResponse({'error': 'Il nome è obbligatorio.'}, status=400)
    if Exercise.objects.filter(nome__iexact=nome).exists():
        return JsonResponse({'error': f'Esiste già un esercizio chiamato "{nome}".'}, status=409)

    exercise = Exercise.objects.create(nome=nome, tipologia=tipologia, carrucole=_parse_carrucole(request))
    if tag_ids:
        exercise.tags.set(tag_ids)
    return JsonResponse({'id': exercise.id, 'nome': exercise.nome})


@login_required
def edit_exercise_admin(request, exercise_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipologia = request.POST.get('tipologia', '').strip()
        tag_ids = request.POST.getlist('tags')
        if nome:
            exercise.nome = nome
        exercise.tipologia = tipologia
        exercise.carrucole = _parse_carrucole(request)
        exercise.save()
        exercise.tags.set(tag_ids)
    tag = request.POST.get('tag', '')
    return redirect(f"{reverse('exercises_list')}{'?tag=' + tag if tag else ''}")


@login_required
def add_exercise_image(request, exercise_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == 'POST' and request.FILES.get('immagine'):
        img = request.FILES['immagine']
        ordine = exercise.images.count()
        ExerciseImage.objects.create(exercise=exercise, immagine=img, ordine=ordine)
    return redirect(request.POST.get('next', reverse('exercises_list')))


@login_required
def delete_exercise_image(request, image_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    img = get_object_or_404(ExerciseImage, id=image_id)
    next_url = request.POST.get('next', reverse('exercises_list'))
    if request.method == 'POST':
        img.immagine.delete(save=False)
        img.delete()
    return redirect(next_url)


@login_required
def delete_exercise_admin(request, exercise_id):
    if not request.user.is_superuser:
        return redirect('dashboard')
    exercise = get_object_or_404(Exercise, id=exercise_id)
    if request.method == 'POST':
        sets_count = WorkoutSet.objects.filter(exercise=exercise).count()
        if sets_count > 0:
            from urllib.parse import urlencode
            msg = f'"{exercise.nome}" è usato in {sets_count} serie e non può essere eliminato.'
            return redirect(f"{reverse('exercises_list')}?{urlencode({'error': msg, 'tag': request.POST.get('tag', '')})}")
        exercise.delete()
    tag = request.POST.get('tag', '')
    return redirect(f"{reverse('exercises_list')}{'?tag=' + tag if tag else ''}")


@login_required
def export_exercises_json(request):
    if not request.user.is_superuser:
        return redirect('dashboard')
    exercises = Exercise.objects.prefetch_related('tags').order_by('nome')
    data = [
        {
            'nome': ex.nome,
            'tipologia': ex.tipologia or '',
            'tags': [t.nome for t in ex.tags.all()],
        }
        for ex in exercises
    ]
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="esercizi_{timezone.now().strftime("%Y%m%d")}.json"'
    return response


@login_required
def exercise_weight_history(request):
    exercise_name = request.GET.get('exercise', '').strip()
    if not exercise_name:
        return JsonResponse({'series': []})
    exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
    if not exercise:
        return JsonResponse({'series': []})

    rows = (
        WorkoutSet.objects
        .filter(session__utente=request.user, exercise=exercise)
        .filter(models.Q(weight__isnull=False) | models.Q(barra_kg__isnull=False))
        .values('session__data', 'session__luogo', 'weight', 'barra_kg', 'per_lato')
        .order_by('session__data')
    )

    # Una linea per ogni palestra (session.luogo) diversa; le sessioni senza
    # luogo indicato finiscono tutte in un'unica linea "Senza palestra".
    day_max = {}
    for r in rows:
        weight = float(r['weight'] or 0)
        barra = float(r['barra_kg'] or 0)
        # "Per lato" raddoppia solo il peso caricato, la sbarra e' un pezzo
        # solo e va contata una volta sola indipendentemente dal lato.
        total = (weight * 2 if r['per_lato'] else weight) + barra
        luogo = (r['session__luogo'] or '').strip()
        d = r['session__data'].strftime('%Y-%m-%d')
        key = (luogo, d)
        if key not in day_max or total > day_max[key]:
            day_max[key] = total

    by_luogo = {}
    for (luogo, d), w in day_max.items():
        by_luogo.setdefault(luogo, []).append({'date': d, 'weight': w})

    series = []
    unnamed_points = by_luogo.pop('', None)
    for luogo in sorted(by_luogo):
        series.append({'name': luogo, 'points': sorted(by_luogo[luogo], key=lambda p: p['date'])})
    if unnamed_points:
        name = 'Senza palestra' if series else ''
        series.append({'name': name, 'points': sorted(unnamed_points, key=lambda p: p['date'])})

    return JsonResponse({'series': series, 'exercise': exercise.nome})


@login_required
def exercise_suggestions(request):
    from django.db.models import Case, When, IntegerField
    q = request.GET.get('q', '').strip()
    user_ids = set(Exercise.objects.filter(
        workoutset__session__utente=request.user
    ).values_list('id', flat=True))

    qs = Exercise.objects.all()
    if q:
        qs = qs.filter(nome__icontains=q)
    qs = qs.annotate(
        priority=Case(
            When(id__in=user_ids, then=0),
            default=1,
            output_field=IntegerField(),
        )
    ).order_by('priority', 'nome')[:20]
    results = list(qs.values_list('nome', flat=True))
    return JsonResponse({'results': results})


@login_required
def user_list(request):
    users_data = []
    if request.user.is_superuser:
        # Il superuser vede tutti gli utenti registrati, anche quelli senza
        # ancora un UserProfile (es. creati da Django Admin invece che dalla
        # pagina di registrazione) e anche se privati.
        profiles_by_user_id = {p.user_id: p for p in UserProfile.objects.all()}
        for u in User.objects.order_by('username'):
            profile = profiles_by_user_id.get(u.id)
            session_count = WorkoutSession.objects.filter(utente=u).count()
            users_data.append({
                'user': u,
                'is_public': profile.is_public if profile else False,
                'session_count': session_count,
            })
    else:
        profiles = UserProfile.objects.filter(is_public=True).select_related('user').order_by('user__username')
        for profile in profiles:
            session_count = WorkoutSession.objects.filter(utente=profile.user).count()
            users_data.append({
                'user': profile.user,
                'is_public': profile.is_public,
                'session_count': session_count,
            })

    return render(request, 'tracker/user_list.html', {'users_data': users_data})


@login_required
def user_profile(request, username):
    target_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    is_own = request.user == target_user
    can_view = is_own or request.user.is_superuser or profile.is_public
    if not can_view:
        return render(request, 'tracker/user_profile.html', {
            'target_user': target_user,
            'private': True,
        })

    sessions = WorkoutSession.objects.filter(utente=target_user).prefetch_related('sets__exercise').order_by('-data', '-id')
    total_sets = WorkoutSet.objects.filter(session__utente=target_user).count()

    top_exercises = (
        Exercise.objects.filter(workoutset__session__utente=target_user)
        .annotate(count=models.Count('workoutset'))
        .order_by('-count')[:5]
    )

    year_str = request.GET.get('year')
    if year_str and year_str.isdigit():
        year_int = int(year_str)
    else:
        year_int = timezone.now().year

    year_sessions = sessions.filter(data__year=year_int)
    date_counts = {}
    for s in year_sessions:
        d_str = s.data.strftime('%Y-%m-%d')
        date_counts[d_str] = date_counts.get(d_str, 0) + 1
    heatmap_data = []
    for d_str, count in date_counts.items():
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        heatmap_data.append({'date': int(time.mktime(dt.timetuple())), 'value': count})

    return render(request, 'tracker/user_profile.html', {
        'target_user': target_user,
        'profile': profile,
        'is_own': is_own,
        'private': False,
        'sessions': sessions[:20],
        'total_sessions': sessions.count(),
        'total_sets': total_sets,
        'top_exercises': top_exercises,
        'heatmap_data_json': json.dumps(heatmap_data),
        'selected_year': year_int,
    })


@login_required
def session_view(request, username, session_id):
    target_user = get_object_or_404(User, username=username)
    profile, _ = UserProfile.objects.get_or_create(user=target_user)

    is_own = request.user == target_user
    can_view = is_own or request.user.is_superuser or profile.is_public
    if not can_view:
        return redirect('user_profile', username=username)

    session = get_object_or_404(WorkoutSession, id=session_id, utente=target_user)
    all_sets = list(session.sets.select_related('exercise').prefetch_related('muscles').order_by('order', 'id'))
    exercise_groups = []
    for _, grp in groupby(all_sets, key=lambda s: s.exercise_id):
        grp_list = list(grp)
        exercise_groups.append({
            'exercise': grp_list[0].exercise,
            'sets': grp_list,
            'count': len(grp_list),
        })

    return render(request, 'tracker/session_view.html', {
        'target_user': target_user,
        'session': session,
        'exercise_groups': exercise_groups,
        'is_own': is_own,
    })


@login_required
def import_session_from_user(request, username, session_id):
    if request.method != 'POST':
        return redirect('session_view', username=username, session_id=session_id)

    target_user = get_object_or_404(User, username=username)

    if request.user == target_user:
        return redirect('session_view', username=username, session_id=session_id)

    profile, _ = UserProfile.objects.get_or_create(user=target_user)
    can_view = request.user.is_superuser or profile.is_public
    if not can_view:
        return redirect('user_profile', username=username)

    original = get_object_or_404(WorkoutSession, id=session_id, utente=target_user)

    try:
        weight_pct = float(request.POST.get('weight_pct', 100))
    except (ValueError, TypeError):
        weight_pct = 100.0
    weight_pct = max(20.0, min(200.0, weight_pct))
    multiplier = weight_pct / 100

    data_str = request.POST.get('data')
    try:
        new_data = date.fromisoformat(data_str) if data_str else original.data
    except ValueError:
        new_data = original.data

    def scaled_weight(weight):
        if weight is None:
            return None
        adjusted = round(float(weight) * multiplier * 2) / 2  # arrotonda al mezzo kg più vicino
        return max(0.0, adjusted)

    new_session = WorkoutSession.objects.create(
        utente=request.user,
        data=new_data,
        note=original.note,
    )
    for s in original.sets.filter(circuit__isnull=True).order_by('order', 'id'):
        WorkoutSet.objects.create(
            session=new_session, exercise=s.exercise,
            reps=s.reps, durata=s.durata, weight=scaled_weight(s.weight),
            rest_time=s.rest_time, per_lato=s.per_lato,
            avviamento=s.avviamento, a_cedimento=s.a_cedimento, richiamo=s.richiamo,
            barra_kg=s.barra_kg, order=s.order,
        )
    for c in original.circuits.order_by('order', 'id'):
        new_circuit = Circuit.objects.create(
            session=new_session, nome=c.nome, rounds=c.rounds,
            rest_tra_round=c.rest_tra_round, order=c.order,
        )
        for s in c.sets.order_by('order', 'id'):
            WorkoutSet.objects.create(
                session=new_session, exercise=s.exercise,
                reps=s.reps, durata=s.durata, weight=scaled_weight(s.weight),
                rest_time=s.rest_time, per_lato=s.per_lato,
                avviamento=s.avviamento, a_cedimento=s.a_cedimento, richiamo=s.richiamo,
                barra_kg=s.barra_kg, order=s.order, circuit=new_circuit,
            )

    return redirect('session_detail', session_id=new_session.id)


@login_required
def toggle_profile_visibility(request):
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.is_public = not profile.is_public
        profile.save()
    return redirect('user_profile', username=request.user.username)


def _combine_water_datetime(entry_data, ora_str):
    ora = timezone.now().time()
    if ora_str:
        try:
            hh, mm = ora_str.split(':')
            ora = dt_time(int(hh), int(mm))
        except (ValueError, AttributeError):
            pass
    naive = datetime.combine(entry_data, ora)
    return timezone.make_aware(naive) if timezone.is_naive(naive) else naive


@login_required
def add_water_entry(request):
    if request.method == 'POST':
        quantita_ml = request.POST.get('quantita_ml')
        if quantita_ml and quantita_ml.isdigit() and int(quantita_ml) > 0:
            entry_data = timezone.now().date()
            data_str = request.POST.get('data')
            if data_str:
                try:
                    entry_data = date.fromisoformat(data_str)
                except ValueError:
                    pass
            creato_il = _combine_water_datetime(entry_data, request.POST.get('ora'))
            WaterEntry.objects.create(utente=request.user, quantita_ml=int(quantita_ml), data=entry_data, creato_il=creato_il)
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
def add_water_entry_ajax(request):
    """Usata dal widget acqua in Dashboard: aggiunge una bevuta di oggi senza
    ricaricare la pagina, restituendo i nuovi totali per aggiornare la UI."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Metodo non valido.'}, status=405)

    quantita_ml = request.POST.get('quantita_ml')
    if not (quantita_ml and quantita_ml.isdigit() and int(quantita_ml) > 0):
        return JsonResponse({'error': 'Quantità non valida.'}, status=400)

    today = timezone.now().date()
    creato_il = _combine_water_datetime(today, request.POST.get('ora'))
    entry = WaterEntry.objects.create(utente=request.user, quantita_ml=int(quantita_ml), data=today, creato_il=creato_il)

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    today_goal_override = WaterGoal.objects.filter(utente=request.user, data=today).first()
    goal_ml = today_goal_override.obiettivo_ml if today_goal_override else profile.obiettivo_acqua_ml

    total_ml = WaterEntry.objects.filter(utente=request.user, data=today).aggregate(total=models.Sum('quantita_ml'))['total'] or 0

    return JsonResponse({
        'ok': True,
        'entry': {'id': entry.id, 'quantita_ml': entry.quantita_ml, 'ora': entry.creato_il.strftime('%H:%M')},
        'total_ml': total_ml,
        'total_l': round(total_ml / 1000, 2),
        'goal_ml': goal_ml,
        'progress_pct': min(100, round(total_ml / goal_ml * 100)) if goal_ml else 0,
    })


@login_required
def delete_water_entry(request, entry_id):
    entry = get_object_or_404(WaterEntry, id=entry_id, utente=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
def edit_water_entry(request, entry_id):
    entry = get_object_or_404(WaterEntry, id=entry_id, utente=request.user)
    if request.method == 'POST':
        quantita_ml = request.POST.get('quantita_ml')
        data_str = request.POST.get('data')
        ora_str = request.POST.get('ora')
        if quantita_ml and quantita_ml.isdigit() and int(quantita_ml) > 0:
            entry.quantita_ml = int(quantita_ml)
        if data_str:
            try:
                entry.data = date.fromisoformat(data_str)
            except ValueError:
                pass
        if ora_str:
            entry.creato_il = _combine_water_datetime(entry.data, ora_str)
        elif data_str:
            # Se cambia solo la data, mantiene l'orario originale
            entry.creato_il = _combine_water_datetime(entry.data, entry.creato_il.strftime('%H:%M'))
        entry.save()
    return redirect(request.POST.get('next') or 'dashboard')


def _water_goals_map(utente, year=None):
    qs = WaterGoal.objects.filter(utente=utente)
    if year:
        qs = qs.filter(data__year=year)
    return {g.data: g.obiettivo_ml for g in qs}


@login_required
def water_history(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    default_goal_ml = profile.obiettivo_acqua_ml

    entries = WaterEntry.objects.filter(utente=request.user).order_by('-data', '-creato_il')
    goals_by_date = _water_goals_map(request.user)

    days = []
    for day, grp in groupby(entries, key=lambda e: e.data):
        day_entries = list(grp)
        total_ml = sum(e.quantita_ml for e in day_entries)
        goal_ml = goals_by_date.get(day, default_goal_ml)
        days.append({
            'data': day,
            'entries': day_entries,
            'total_ml': total_ml,
            'total_l': total_ml / 1000,
            'goal_ml': goal_ml,
            'goal_l': goal_ml / 1000,
            'reached': total_ml >= goal_ml,
        })

    paginator = Paginator(days, 14)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    year_str = request.GET.get('year')
    if year_str and year_str.isdigit():
        year_int = int(year_str)
    else:
        year_int = timezone.now().year

    year_totals = {}
    for e in WaterEntry.objects.filter(utente=request.user, data__year=year_int):
        year_totals[e.data] = year_totals.get(e.data, 0) + e.quantita_ml
    year_goals = _water_goals_map(request.user, year=year_int)
    heatmap_data = []
    for d, total_ml in year_totals.items():
        goal_ml = year_goals.get(d, default_goal_ml)
        timestamp = int(time.mktime(datetime(d.year, d.month, d.day).timetuple()))
        heatmap_data.append({'date': timestamp, 'value': total_ml, 'goal': goal_ml})

    return render(request, 'tracker/water_history.html', {
        'days': page,
        'water_goal_ml': default_goal_ml,
        'heatmap_data_json': json.dumps(heatmap_data),
        'selected_year': year_int,
    })


@login_required
def set_water_goal(request):
    if request.method == 'POST':
        obiettivo_ml = request.POST.get('obiettivo_ml')
        if obiettivo_ml and obiettivo_ml.isdigit() and int(obiettivo_ml) > 0:
            profile, _ = UserProfile.objects.get_or_create(user=request.user)
            profile.obiettivo_acqua_ml = int(obiettivo_ml)
            profile.save()
    return redirect(request.POST.get('next') or 'dashboard')


@login_required
def set_day_water_goal(request):
    if request.method == 'POST':
        obiettivo_ml = request.POST.get('obiettivo_ml')
        data_str = request.POST.get('data')
        if obiettivo_ml and obiettivo_ml.isdigit() and int(obiettivo_ml) > 0 and data_str:
            try:
                data = date.fromisoformat(data_str)
            except ValueError:
                data = None
            if data:
                WaterGoal.objects.update_or_create(
                    utente=request.user, data=data,
                    defaults={'obiettivo_ml': int(obiettivo_ml)},
                )
    return redirect(request.POST.get('next') or 'water_history')


@login_required
def integratori(request):
    entries = IntegratoreEntry.objects.filter(utente=request.user).order_by('-data', '-creato_il')

    filter_data_str = request.GET.get('data', '').strip()
    filter_date = None
    if filter_data_str:
        try:
            filter_date = date.fromisoformat(filter_data_str)
        except ValueError:
            filter_date = None
    if filter_date:
        entries = entries.filter(data=filter_date)

    days = []
    for day, grp in groupby(entries, key=lambda e: e.data):
        day_entries = list(grp)
        totals = {tipo: 0 for tipo, _ in IntegratoreEntry.TIPO_CHOICES}
        for e in day_entries:
            totals[e.tipo] += e.quantita_g
        days.append({
            'data': day,
            'entries': day_entries,
            'totals': totals,
        })

    paginator = Paginator(days, 14)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    year_str = request.GET.get('year')
    if year_str and year_str.isdigit():
        year_int = int(year_str)
    else:
        year_int = timezone.now().year

    year_totals = {}
    for e in IntegratoreEntry.objects.filter(utente=request.user, data__year=year_int):
        day_totals = year_totals.setdefault(e.data, {tipo: 0 for tipo, _ in IntegratoreEntry.TIPO_CHOICES})
        day_totals[e.tipo] += e.quantita_g

    heatmap_data = []
    for d, totals in year_totals.items():
        tipi_assunti = sum(1 for v in totals.values() if v > 0)
        timestamp = int(time.mktime(datetime(d.year, d.month, d.day).timetuple()))
        heatmap_data.append({
            'date': timestamp,
            'value': tipi_assunti,
            'creatina': totals['creatina'],
            'aminoacidi': totals['aminoacidi'],
            'proteine': totals['proteine'],
        })

    return render(request, 'tracker/integratori.html', {
        'days': page,
        'tipo_choices': IntegratoreEntry.TIPO_CHOICES,
        'selected_year': year_int,
        'heatmap_data_json': json.dumps(heatmap_data),
        'filter_active': filter_date is not None,
        'filter_date_str': filter_date.isoformat() if filter_date else '',
    })


@login_required
def add_integratore_entry(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        quantita_g = request.POST.get('quantita_g')
        if tipo in dict(IntegratoreEntry.TIPO_CHOICES) and quantita_g and quantita_g.isdigit() and int(quantita_g) > 0:
            entry_data = timezone.now().date()
            data_str = request.POST.get('data')
            if data_str:
                try:
                    entry_data = date.fromisoformat(data_str)
                except ValueError:
                    pass
            creato_il = _combine_water_datetime(entry_data, request.POST.get('ora'))
            IntegratoreEntry.objects.create(utente=request.user, tipo=tipo, quantita_g=int(quantita_g), data=entry_data, creato_il=creato_il)
    return redirect(request.POST.get('next') or 'integratori')


@login_required
def add_integratore_range(request):
    """Inserimento multiplo: stessa quantita' dello stesso integratore per
    ogni giorno di un intervallo (es. creatina 5g/die dal 1 al 30 del mese)."""
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        quantita_g = request.POST.get('quantita_g')
        data_inizio_str = request.POST.get('data_inizio')
        data_fine_str = request.POST.get('data_fine')
        ora_str = request.POST.get('ora')

        if (tipo in dict(IntegratoreEntry.TIPO_CHOICES)
                and quantita_g and quantita_g.isdigit() and int(quantita_g) > 0
                and data_inizio_str and data_fine_str):
            try:
                data_inizio = date.fromisoformat(data_inizio_str)
                data_fine = date.fromisoformat(data_fine_str)
            except ValueError:
                data_inizio = data_fine = None

            if data_inizio and data_fine and data_inizio <= data_fine and (data_fine - data_inizio).days < 366:
                nuove = []
                giorno = data_inizio
                while giorno <= data_fine:
                    nuove.append(IntegratoreEntry(
                        utente=request.user,
                        tipo=tipo,
                        quantita_g=int(quantita_g),
                        data=giorno,
                        creato_il=_combine_water_datetime(giorno, ora_str),
                    ))
                    giorno += timedelta(days=1)
                IntegratoreEntry.objects.bulk_create(nuove)
    return redirect(request.POST.get('next') or 'integratori')


@login_required
def delete_integratore_entry(request, entry_id):
    entry = get_object_or_404(IntegratoreEntry, id=entry_id, utente=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect(request.POST.get('next') or 'integratori')


@login_required
def edit_integratore_entry(request, entry_id):
    entry = get_object_or_404(IntegratoreEntry, id=entry_id, utente=request.user)
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        quantita_g = request.POST.get('quantita_g')
        data_str = request.POST.get('data')
        ora_str = request.POST.get('ora')
        if tipo in dict(IntegratoreEntry.TIPO_CHOICES):
            entry.tipo = tipo
        if quantita_g and quantita_g.isdigit() and int(quantita_g) > 0:
            entry.quantita_g = int(quantita_g)
        if data_str:
            try:
                entry.data = date.fromisoformat(data_str)
            except ValueError:
                pass
        if ora_str:
            entry.creato_il = _combine_water_datetime(entry.data, ora_str)
        elif data_str:
            entry.creato_il = _combine_water_datetime(entry.data, entry.creato_il.strftime('%H:%M'))
        entry.save()
    return redirect(request.POST.get('next') or 'integratori')


@login_required
def guida(request):
    return render(request, 'tracker/guida.html')


@login_required
def body_map(request):
    exercises_qs = Exercise.objects.prefetch_related('tags').order_by('nome')
    exercises_data = [
        {
            'id': ex.id,
            'nome': ex.nome,
            'tipologia': ex.tipologia or '',
            'tags': [t.nome.lower() for t in ex.tags.all()],
        }
        for ex in exercises_qs
    ]
    return render(request, 'tracker/body_map.html', {
        'exercises_json': json.dumps(exercises_data),
    })


@login_required
def misurazioni(request):
    entries_qs = BodyMetric.objects.filter(utente=request.user).order_by('-data')
    paginator = Paginator(entries_qs, 20)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    chart_entries = BodyMetric.objects.filter(utente=request.user).order_by('data')
    chart_data = {
        'peso': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.peso_kg)} for e in chart_entries if e.peso_kg is not None],
        'altezza': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.altezza_cm)} for e in chart_entries if e.altezza_cm is not None],
        'body_fat': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.body_fat_pct)} for e in chart_entries if e.body_fat_pct is not None],
        'vita': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.vita_cm)} for e in chart_entries if e.vita_cm is not None],
        'torace': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.torace_cm)} for e in chart_entries if e.torace_cm is not None],
        'braccia': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.braccia_cm)} for e in chart_entries if e.braccia_cm is not None],
        'cosce': [{'date': e.data.strftime('%d/%m/%Y'), 'value': float(e.cosce_cm)} for e in chart_entries if e.cosce_cm is not None],
    }

    return render(request, 'tracker/misurazioni.html', {
        'entries': page,
        'chart_data_json': json.dumps(chart_data),
    })


@login_required
def save_misurazione(request):
    if request.method == 'POST':
        data_str = request.POST.get('data')
        try:
            entry_data = date.fromisoformat(data_str) if data_str else timezone.now().date()
        except ValueError:
            entry_data = timezone.now().date()

        entry, _ = BodyMetric.objects.get_or_create(utente=request.user, data=entry_data)

        # Un campo lasciato vuoto non tocca il valore gia' salvato per quel giorno
        # (evita che il form rapido "+", sempre vuoto, azzeri dati inseriti in precedenza).
        for field in ('peso_kg', 'altezza_cm', 'body_fat_pct', 'vita_cm', 'torace_cm', 'braccia_cm', 'cosce_cm'):
            val = request.POST.get(field)
            if val:
                try:
                    setattr(entry, field, float(val))
                except ValueError:
                    pass

        note_val = request.POST.get('note')
        if note_val:
            entry.note = note_val.strip()[:100]

        if request.POST.get('clear_ora') == '1':
            entry.orario = None
        else:
            ora_str = request.POST.get('ora')
            if ora_str:
                try:
                    entry.orario = dt_time.fromisoformat(ora_str)
                except ValueError:
                    pass

        entry.save()
    return redirect(request.POST.get('next') or 'misurazioni')


@login_required
def delete_misurazione(request, entry_id):
    entry = get_object_or_404(BodyMetric, id=entry_id, utente=request.user)
    if request.method == 'POST':
        entry.delete()
    return redirect(request.POST.get('next') or 'misurazioni')
