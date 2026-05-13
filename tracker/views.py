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
from django.contrib.auth.models import User
from .models import WorkoutSession, WorkoutSet, Exercise, MuscleGroup, Tag, UserProfile, ExerciseImage


@login_required
def dashboard(request):
    WorkoutSession.objects.filter(utente=request.user, sets__isnull=True).delete()

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

    exercises_qs = Exercise.objects.prefetch_related('tags').order_by('nome')
    exercises_data = []
    for ex in exercises_qs:
        exercises_data.append({
            'id': ex.id,
            'nome': ex.nome,
            'tipologia': ex.tipologia or '',
            'tags': [t.nome.lower() for t in ex.tags.all()],
        })
    
    return render(request, 'tracker/dashboard.html', {
        'sessions': sessions,
        'total_sessions_count': all_sessions.count(),
        'total_sets': total_sets,
        'this_month_sessions': this_month_sessions,
        'heatmap_data_json': json.dumps(heatmap_data),
        'selected_year': year_int,
        'exercises_json': json.dumps(exercises_data),
    })

@login_required
def create_session(request):
    WorkoutSession.objects.filter(utente=request.user, sets__isnull=True).delete()
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
        num_sets = int(request.POST.get('num_sets') or 1)

        exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
        if not exercise:
            all_sets = list(session.sets.select_related('exercise').order_by('order', 'id'))
            exercise_groups = []
            for _, grp in groupby(all_sets, key=lambda s: s.exercise_id):
                grp_list = list(grp)
                exercise_groups.append({'exercise': grp_list[0].exercise, 'sets': grp_list, 'count': len(grp_list)})
            return render(request, 'tracker/session_detail.html', {
                'session': session,
                'exercise_groups': exercise_groups,
                'error_exercise': f'"{exercise_name}" non è nella lista degli esercizi. Seleziona un esercizio dalla lista.',
            })

        base_order = session.sets.count()
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
            )
        url = reverse('session_detail', kwargs={'session_id': session.id})
        return redirect(f'{url}?open={exercise.id}')

    all_sets = list(session.sets.select_related('exercise').order_by('order', 'id'))
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
        'exercise_groups': exercise_groups,
    })

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
            durata=original.durata,
            weight=original.weight,
            rest_time=original.rest_time,
            per_lato=original.per_lato,
            avviamento=original.avviamento,
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
            exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
            if exercise:
                workout_set.exercise = exercise
        workout_set.reps = request.POST.get('reps') or None
        workout_set.durata = request.POST.get('durata') or None
        workout_set.weight = weight
        workout_set.rest_time = rest_time
        workout_set.per_lato = request.POST.get('per_lato') == 'on'
        workout_set.avviamento = request.POST.get('avviamento') == 'on'
        workout_set.save()
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
                durata=s.durata,
                weight=s.weight,
                rest_time=s.rest_time,
                per_lato=s.per_lato,
                avviamento=s.avviamento,
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
def export_sessions(request):
    sessions = WorkoutSession.objects.filter(
        utente=request.user
    ).prefetch_related('sets__exercise').order_by('data')

    data = []
    for session in sessions:
        sets = []
        for s in session.sets.all().order_by('order', 'id'):
            sets.append({
                'exercise': s.exercise.nome,
                'reps': s.reps,
                'weight': float(s.weight) if s.weight is not None else None,
                'rest_time': s.rest_time,
                'per_lato': s.per_lato,
                'avviamento': s.avviamento,
                'durata': s.durata,
                'order': s.order,
            })
        data.append({
            'data': session.data.strftime('%Y-%m-%d'),
            'note': session.note or '',
            'sets': sets,
        })

    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False, 'indent': 2})
    filename = f"workout_backup_{timezone.now().strftime('%Y%m%d')}.json"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


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
                date = datetime.strptime(item['data'], '%Y-%m-%d').date()
                note = item.get('note') or None
                session = WorkoutSession.objects.create(
                    utente=request.user, data=date, note=note,
                )
                for i, s in enumerate(item.get('sets', [])):
                    exercise_name = (s.get('exercise') or '').strip()
                    if not exercise_name:
                        continue
                    exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
                    if not exercise:
                        exercise = Exercise.objects.create(nome=exercise_name)
                    WorkoutSet.objects.create(
                        session=session,
                        exercise=exercise,
                        reps=int(s.get('reps') or 0),
                        weight=s.get('weight'),
                        rest_time=s.get('rest_time'),
                        per_lato=bool(s.get('per_lato', False)),
                        avviamento=bool(s.get('avviamento', False)),
                        durata=s.get('durata'),
                        order=s.get('order', i),
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
    sets = []
    for s in session.sets.all().order_by('order', 'id'):
        sets.append({
            'exercise': s.exercise.nome,
            'reps': s.reps,
            'weight': float(s.weight) if s.weight is not None else None,
            'rest_time': s.rest_time,
            'per_lato': s.per_lato,
            'avviamento': s.avviamento,
            'order': s.order,
        })
    data = [{'data': session.data.strftime('%Y-%m-%d'), 'note': session.note or '', 'sets': sets}]
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
        tag_groups = []
        for tag in tags:
            tag_exercises = list(Exercise.objects.filter(tags=tag).prefetch_related('tags', 'images').order_by('nome'))
            if tag_exercises:
                tag_groups.append({'tag': tag, 'exercises': tag_exercises})
        untagged = list(Exercise.objects.filter(tags__isnull=True).prefetch_related('tags', 'images').order_by('nome'))
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
    if request.method == 'POST':
        nome = request.POST.get('nome', '').strip()
        tipologia = request.POST.get('tipologia', '').strip()
        tag_ids = request.POST.getlist('tags')
        if nome:
            exercise, _ = Exercise.objects.get_or_create(nome=nome)
            if tipologia:
                exercise.tipologia = tipologia
                exercise.save()
            if tag_ids:
                exercise.tags.set(tag_ids)
    next_url = request.POST.get('next', reverse('exercises_list'))
    return redirect(next_url)


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
        return JsonResponse({'points': []})
    exercise = Exercise.objects.filter(nome__iexact=exercise_name).first()
    if not exercise:
        return JsonResponse({'points': []})
    rows = (
        WorkoutSet.objects
        .filter(session__utente=request.user, exercise=exercise, weight__isnull=False)
        .values('session__data')
        .annotate(max_weight=models.Max('weight'))
        .order_by('session__data')
    )
    points = [
        {'date': r['session__data'].strftime('%Y-%m-%d'), 'weight': float(r['max_weight'])}
        for r in rows
    ]
    return JsonResponse({'points': points, 'exercise': exercise.nome})


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
    if request.user.is_superuser:
        profiles = UserProfile.objects.select_related('user').order_by('user__username')
    else:
        profiles = UserProfile.objects.filter(is_public=True).select_related('user').order_by('user__username')

    users_data = []
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

    date_counts = {}
    for s in sessions:
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
        load_pct = float(request.POST.get('load_pct', 0))
        load_pct = max(-90.0, min(200.0, load_pct))
    except (ValueError, TypeError):
        load_pct = 0.0

    new_session = WorkoutSession.objects.create(
        utente=request.user,
        data=original.data,
        note=original.note,
    )
    for s in original.sets.all().order_by('order', 'id'):
        if s.weight is not None and load_pct != 0.0:
            adjusted = float(s.weight) * (1 + load_pct / 100)
            adjusted = round(adjusted * 2) / 2  # arrotonda al mezzo kg più vicino
            new_weight = max(0.0, adjusted)
        else:
            new_weight = s.weight
        WorkoutSet.objects.create(
            session=new_session,
            exercise=s.exercise,
            reps=s.reps,
            weight=new_weight,
            rest_time=s.rest_time,
            per_lato=s.per_lato,
            avviamento=s.avviamento,
            durata=s.durata,
            order=s.order,
        )

    return redirect('session_detail', session_id=new_session.id)


@login_required
def toggle_profile_visibility(request):
    if request.method == 'POST':
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.is_public = not profile.is_public
        profile.save()
    return redirect('user_profile', username=request.user.username)


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
