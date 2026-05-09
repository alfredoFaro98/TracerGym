from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Imposta un utente esistente come superutente'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username da promuovere a superutente')

    def handle(self, *args, **options):
        username = options['username']
        try:
            user = User.objects.get(username=username)
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'"{username}" è ora superutente.'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Utente "{username}" non trovato.'))
