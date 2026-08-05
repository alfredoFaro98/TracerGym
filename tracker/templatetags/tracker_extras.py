from django import template

register = template.Library()


@register.filter(name='in_list')
def in_list(value, arg):
    """True se value e' presente nella lista arg separata da virgole (usato per evidenziare la voce attiva della sidebar)."""
    if not value:
        return False
    return value in arg.split(',')


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


@register.simple_tag(takes_context=True)
def is_athletes_active(context):
    """True per 'Atleti': lista atleti, sessione di un altro utente, o profilo di un altro utente (ma non il proprio)."""
    request = context.get('request')
    match = getattr(request, 'resolver_match', None)
    if match and match.url_name in ('user_list', 'session_view', 'import_session_from_user'):
        return True
    username = _profile_username(context)
    return username is not None and username != getattr(context.get('user'), 'username', None)
