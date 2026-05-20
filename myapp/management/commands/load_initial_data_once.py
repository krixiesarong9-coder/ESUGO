from django.core.management import BaseCommand, call_command

from myapp.models import StoreSettings


class Command(BaseCommand):
    help = "Load the bundled initial data fixture when the Render database is missing store data."

    def handle(self, *args, **options):
        if StoreSettings.objects.exists():
            self.stdout.write(self.style.WARNING("Initial data skipped: database already has stores."))
            return

        call_command("flush", interactive=False, verbosity=0)
        call_command("loaddata", "fixtures/initial_data.json")
        self.stdout.write(self.style.SUCCESS("Initial data loaded from fixtures/initial_data.json."))
