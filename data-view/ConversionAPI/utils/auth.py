from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from API.models import ApiKey


def GetUserFromApiKey(request):
    api_key = request.headers.get('x-api-key')
    if not api_key:
        raise PermissionDenied("No API key provided")

    try:
        key = ApiKey.objects.get(api_key=api_key)
        return key.user
    except ApiKey.DoesNotExist:
        raise PermissionDenied("API key is invalid")
