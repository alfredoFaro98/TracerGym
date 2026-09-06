from django.db.models import Sum

from .version import get_app_version


def app_version(request):
    return {'app_version': get_app_version()}


def site_visits(request):
    if not getattr(getattr(request, 'user', None), 'is_superuser', False):
        return {}
    from .models import SiteVisit
    total = SiteVisit.objects.aggregate(total=Sum('conteggio'))['total'] or 0
    return {'site_visits_total': total}


def appearance(request):
    if getattr(getattr(request, 'user', None), 'is_authenticated', False):
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        # I cinque preset hanno la scala gia' scritta in style.css; solo per il
        # colore personalizzato serve derivarla e stamparla in pagina.
        css = ''
        if profile.accent == 'custom' and profile.accent_hex:
            from .accent import css_accent
            css = css_accent(profile.accent_hex)
        return {
            'accent': profile.accent,
            'accent_css': css,
            'accent_hex': profile.accent_hex,
            'lingua_esercizi': profile.lingua_esercizi,
        }
    # Chi non ha fatto login (login, registrazione, profili pubblici) vede i
    # default: non c'e' un profilo da cui leggere la preferenza.
    return {'accent': 'viola', 'accent_css': '', 'accent_hex': '', 'lingua_esercizi': 'it'}
