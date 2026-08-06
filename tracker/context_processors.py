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
