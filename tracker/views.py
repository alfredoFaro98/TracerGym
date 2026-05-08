from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from itertools import groupby
import json
import time
from datetime import datetime
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
    # Recupera tutte le sessioni dell'utente loggato
    sessions = WorkoutSession.objects.filter(utente=request.user)
    
    # Prepara dati per heatmap
    date_counts = {}
    for s in sessions:
        d_str = s.data.strftime('%Y-%m-%d')
        date_counts[d_str] = date_counts.get(d_str, 0) + 1
        
    heatmap_data = []
    for d_str, count in date_counts.items():
        dt = datetime.strptime(d_str, '%Y-%m-%d')
        timestamp = int(time.mktime(dt.timetuple()))
        heatmap_data.append({'date': timestamp, 'value': count})

    return render(request, 'tracker/dashboard.html', {
        'sessions': sessions,
        'heatmap_data_json': json.dumps(heatmap_data)
    })

@login_required
def create_session(request):
    if request.method == 'POST':
        # Crea una nuova sessione per l'utente loggato
        session = WorkoutSession.objects.create(utente=request.user)
        # Reindirizza al dettaglio della sessione appena creata
        return redirect('session_detail', session_id=session.id)
    
    return render(request, 'tracker/create_session.html')

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
        for _ in range(max(1, min(num_sets, 20))):
            s = WorkoutSet.objects.create(
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

    all_sets = list(session.sets.select_related('exercise').prefetch_related('muscles').order_by('id'))
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
        new_set = WorkoutSet.objects.create(
            session=original.session,
            exercise=original.exercise,
            reps=original.reps,
            weight=original.weight,
            rest_time=original.rest_time
        )
        new_set.muscles.set(original.muscles.all())
    return redirect('session_detail', session_id=original.session.id)

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
