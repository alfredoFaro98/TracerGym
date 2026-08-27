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
        return {'theme': profile.tema, 'accent': profile.accent}
    return {'theme': 'scuro_classico', 'accent': 'viola'}
