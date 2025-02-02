from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Initialize admin account"

    def handle(self, *args, **options):
        if User.objects.count() == 0:
            username = "admin"
            email = "root@localhost"
            password = "admin"
            self.stdout.write(
                self.style.SUCCESS(f"Creating account for {username} ({email})...")
            )
            admin = User.objects.create_superuser(email=email, username=username, password=password)
            admin.is_active = True
            admin.is_admin = True
            admin.save()
            self.stdout.write(
                self.style.SUCCESS("Finished.")
            )
        else:
            print('Admin account can only be initialized if no other exists!')
