from django import template

from tracker.models import WorkoutSession

register = template.Library()


@register.filter(name='in_list')
def in_list(value, arg):
    """True se value e' presente nella lista arg separata da virgole (usato per evidenziare la voce attiva della sidebar)."""
    if not value:
        return False
    return value in arg.split(',')


@register.filter(name='nome_lingua')
def nome_lingua(exercise, lingua):
    """Nome dell'esercizio nella lingua scelta dall'utente.

    Uso: {{ group.exercise|nome_lingua:lingua_esercizi }} — `lingua_esercizi`
    arriva dal context processor `appearance`, quindi e' gia' in ogni template.
    Su un esercizio assente (serie orfana) torna stringa vuota invece di
    esplodere, come farebbe `{{ ... .nome }}`.
    """
    if exercise is None:
        return ''
    return exercise.nome_in(lingua)


def _profile_username(context):
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if not match or match.url_name != 'user_profile':
        return None
    return match.kwargs.get('username')


@register.simple_tag(takes_context=True)
def is_own_profile(context):
    """True se la pagina corrente e' 'user_profile' per l'utente loggato (per evidenziare 'Il mio profilo' e non 'Atleti' quando si guarda il profilo di un altro)."""
    username = _profile_username(context)
    return username is not None and username == getattr(context.get('user'), 'username', None)


def _is_empty_own_session(context):
    """True se la pagina corrente e' 'session_detail' per una sessione propria senza serie/circuiti
    (cioe' appena creata da 'Nuovo Allenamento' e non ancora popolata)."""
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if not match or match.url_name != 'session_detail':
        return False
    session_id = match.kwargs.get('session_id')
    user = context.get('user')
    if not session_id or not getattr(user, 'is_authenticated', False):
        return False
    return WorkoutSession.objects.filter(
        id=session_id, utente=user, sets__isnull=True, circuits__isnull=True,
    ).exists()


@register.simple_tag(takes_context=True)
def is_new_workout_active(context):
    """True per 'Nuovo Allenamento': la pagina di creazione o una sessione propria appena creata e ancora vuota."""
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if match and match.url_name == 'create_session':
        return True
    return _is_empty_own_session(context)


@register.simple_tag(takes_context=True)
def is_dashboard_active(context):
    """True per 'Dashboard': la dashboard stessa, o una sessione propria gia' popolata (non quella appena creata)."""
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if match and match.url_name == 'dashboard':
        return True
    if match and match.url_name == 'session_detail':
        return not _is_empty_own_session(context)
    return False


@register.simple_tag(takes_context=True)
def is_athletes_active(context):
    """True per 'Atleti': lista atleti, sessione di un altro utente, o profilo di un altro utente (ma non il proprio)."""
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if match and match.url_name in ('user_list', 'session_view', 'import_session_from_user'):
        return True
    username = _profile_username(context)
    return username is not None and username != getattr(context.get('user'), 'username', None)
