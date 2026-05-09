from django.conf import settings
from django.template.loader import render_to_string
from django.http import HttpResponse


class MaintenanceModeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False):
            if request.user.is_authenticated and request.user.is_superuser:
                return self.get_response(request)
            html = render_to_string('maintenance.html')
            return HttpResponse(html, status=503)
        return self.get_response(request)
