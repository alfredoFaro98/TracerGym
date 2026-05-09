from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
from django.db import models
import json
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from itertools import groupby
import time
from datetime import datetime
from django.utils import timezone
from .models import WorkoutSession, WorkoutSet, Exercise, MuscleGroup

def _parse_custom_muscles(raw):
    """Splits a comma-separated string of muscle names, gets or creates each, returns list of IDs."""
    ids = []
    for name in raw.split(','):
        name = name.strip()
        if name:
            obj, _ = MuscleGroup.objects.get_or_create(nome__iexact=name, defaults={'nome': name})
            ids.append(obj.id)
    return ids

@login_required
def dashboard(request):
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

    # Prepara dati per heatmap (su tutte le sessioni filtrate per anno)
    all_sessions = WorkoutSession.objects.filter(utente=request.user, data__year=year_int)
    date_counts = {}
    for s in all_sessions:
        d_str = s.data.strftime('%Y-%m-%d')
        date_counts[d_str] = date_counts.get(d_str, 0) + 1

    heatmap_data = []
    for d_str, count in date_counts.items():
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        timestamp = int(time.mktime(dt.timetuple()))
        heatmap_data.append({'date': timestamp, 'value': count})

    # Statistiche per schermi piccoli
    total_sets = WorkoutSet.objects.filter(session__utente=request.user).count()
    now = timezone.now()
    this_month_sessions = all_sessions.filter(data__year=now.year, data__month=now.month).count()

    return render(request, 'tracker/dashboard.html', {
        'sessions': sessions,
        'total_sessions_count': all_sessions.count(),
        'total_sets': total_sets,
        'this_month_sessions': this_month_sessions,
        'heatmap_data_json': json.dumps(heatmap_data),
        'selected_year': year_int,
    })

@login_required
def create_session(request):
    # Crea la sessione immediatamente appena si clicca il link e reindirizza ai dettagli
    session = WorkoutSession.objects.create(utente=request.user)
    return redirect('session_detail', session_id=session.id)

@login_required
def session_detail(request, session_id):
    # Recupera la sessione assicurandosi che appartenga all'utente loggato
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    exercises = Exercise.objects.all()
    muscle_groups = MuscleGroup.objects.all()

    if request.method == 'POST':
        exercise_name = request.POST.get('exercise_name')
        reps = request.POST.get('reps')
        weight = request.POST.get('weight') or None
        rest_time = request.POST.get('rest_time') or None
        selected_muscles = request.POST.getlist('muscles')
        selected_muscles += _parse_custom_muscles(request.POST.get('muscles_custom', ''))

        num_sets = int(request.POST.get('num_sets') or 1)
        exercise, _ = Exercise.objects.get_or_create(nome=exercise_name.strip())
        base_order = session.sets.count()
        for i in range(max(1, min(num_sets, 20))):
            s = WorkoutSet.objects.create(
                order=base_order + i,
                session=session,
                exercise=exercise,
                reps=reps,
                weight=weight,
                rest_time=rest_time
            )
            if selected_muscles:
                s.muscles.set(selected_muscles)
        url = reverse('session_detail', kwargs={'session_id': session.id})
        return redirect(f'{url}?open={exercise.id}')

    all_sets = list(session.sets.select_related('exercise').prefetch_related('muscles').order_by('order', 'id'))
    exercise_groups = []
    for _, grp in groupby(all_sets, key=lambda s: s.exercise_id):
        grp_list = list(grp)
        exercise_groups.append({
            'exercise': grp_list[0].exercise,
            'sets': grp_list,
            'count': len(grp_list),
        })

    return render(request, 'tracker/session_detail.html', {
        'session': session,
        'exercises': exercises,
        'exercise_groups': exercise_groups,
        'muscle_groups': muscle_groups,
    })

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'tracker/register.html', {'form': form})

@login_required
def delete_set(request, set_id):
    # Recupera il set solo se la sessione appartiene all'utente loggato
    workout_set = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    session_id = workout_set.session.id
    if request.method == 'POST':
        workout_set.delete()
    return redirect('session_detail', session_id=session_id)

@login_required
def duplicate_set(request, set_id):
    original = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    if request.method == 'POST':
        # Shifta di 1 tutte le serie che vengono dopo quella originale
        original.session.sets.filter(order__gt=original.order).update(order=models.F('order') + 1)
        new_set = WorkoutSet.objects.create(
            session=original.session,
            exercise=original.exercise,
            reps=original.reps,
            weight=original.weight,
            rest_time=original.rest_time,
            order=original.order + 1,
        )
        new_set.muscles.set(original.muscles.all())
    url = reverse('session_detail', kwargs={'session_id': original.session.id})
    return redirect(f'{url}?open={original.exercise_id}')

@login_required
def edit_set(request, set_id):
    workout_set = get_object_or_404(WorkoutSet, id=set_id, session__utente=request.user)
    if request.method == 'POST':
        exercise_name = request.POST.get('exercise_name', '').strip()
        reps = request.POST.get('reps')
        weight = request.POST.get('weight') or None
        rest_time = request.POST.get('rest_time') or None
        if exercise_name:
            exercise, _ = Exercise.objects.get_or_create(nome=exercise_name)
            workout_set.exercise = exercise
        workout_set.reps = reps
        workout_set.weight = weight
        workout_set.rest_time = rest_time
        workout_set.save()
        muscles = request.POST.getlist('muscles')
        muscles += _parse_custom_muscles(request.POST.get('muscles_custom', ''))
        workout_set.muscles.set(muscles)
    url = reverse('session_detail', kwargs={'session_id': workout_set.session.id})
    return redirect(f'{url}?open={workout_set.exercise_id}')

@login_required
def duplicate_session(request, session_id):
    original = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        new_session = WorkoutSession.objects.create(utente=request.user)
        for s in original.sets.all():
            WorkoutSet.objects.create(
                session=new_session,
                exercise=s.exercise,
                reps=s.reps,
                weight=s.weight,
                rest_time=s.rest_time
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
def delete_exercise_sets(request, session_id, exercise_id):
    session = get_object_or_404(WorkoutSession, id=session_id, utente=request.user)
    if request.method == 'POST':
        session.sets.filter(exercise_id=exercise_id).delete()
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
def exercise_suggestions(request):
    q = request.GET.get('q', '').strip()
    qs = Exercise.objects.filter(workoutset__session__utente=request.user).distinct()
    if q:
        qs = qs.filter(nome__icontains=q)
    results = list(qs.order_by('nome').values_list('nome', flat=True)[:12])
    return JsonResponse({'results': results})
