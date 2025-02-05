from django.core.management.base import BaseCommand
from API.models import ApiKey
from API.models import GenerateAPIKey
from ConversionAPI.utils.system import get_system_setting
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = "Initialize test data"

    def handle(self, *args, **options):
        print("Creating test user...")
        UserItem = User.objects.create(email="testuser@data-view.eu", username="test", password="test")
        print("Creating test user...done.")
        print("Generating new API key for user test...")
        NormalAPIKey = ApiKey.objects.create(api_key="ghijkl-654321-ghijkl-654321", credits=100.0, user=UserItem)
        print(f"Generated API key for user test: {NormalAPIKey}.")
        print("Generating weak API key for user test...")
        WeakAPIKey = ApiKey.objects.create(api_key="abcdef-123456-abcdef-123456", credits=0.0, user=UserItem)
        print(f"Generated weak API key for user test: {WeakAPIKey}.")

