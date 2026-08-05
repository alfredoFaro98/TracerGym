from .version import get_app_version


def app_version(request):
    return {'app_version': get_app_version()}
