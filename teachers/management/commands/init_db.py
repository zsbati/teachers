from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Initializes the database and applies migrations'

    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing the database and applying migrations...')

        try:
            # Ensure that all migrations are created
            call_command('makemigrations')

            # Apply the migrations
            call_command('migrate')

            # Check if a superuser exists
            User = get_user_model()
            if not User.objects.filter(is_superuser=True).exists():
                self.stdout.write('No superuser found. Creating a superuser...')

                # You can customize the superuser creation logic here
                call_command('createsuperuser', interactive=True)
            else:
                self.stdout.write('A superuser already exists.')

            self.stdout.write(self.style.SUCCESS('Database initialized and migrations applied successfully!'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
