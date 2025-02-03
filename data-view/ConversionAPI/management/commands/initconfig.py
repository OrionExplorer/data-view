from django.core.management.base import BaseCommand
from ConversionAPI.models import SystemSetting
from ConversionAPI.utils.system import get_system_setting


class Command(BaseCommand):
    help = "Initialize default system values"

    def handle(self, *args, **options):
        CHECK_MAGIC_NUMBER = get_system_setting('CHECK_MAGIC_NUMBER', -1)
        MAX_FILE_SIZE = get_system_setting('MAX_FILE_SIZE', -1)

        self.stdout.write(
            self.style.SUCCESS("Checking default system values...")
        )

        if CHECK_MAGIC_NUMBER == -1:
            self.stdout.write(
                self.style.SUCCESS("Creating default setting for \"CHECK_MAGIC_NUMBER\"...")
            )
            SystemSetting.objects.create(key='CHECK_MAGIC_NUMBER', setting_type='boolean', boolean_value=True)
            self.stdout.write(
                self.style.SUCCESS("Creating default setting for \"CHECK_MAGIC_NUMBER\"...done.")
            )

        if MAX_FILE_SIZE == -1:
            self.stdout.write(
                self.style.SUCCESS("Creating default setting for \"MAX_FILE_SIZE\"...")
            )
            SystemSetting.objects.create(key='MAX_FILE_SIZE', setting_type='integer', integer_value=50)
            self.stdout.write(
                self.style.SUCCESS("Creating default setting for \"MAX_FILE_SIZE\"...done.")
            )

        self.stdout.write(
            self.style.SUCCESS("Checking default system values...done.")
        )
