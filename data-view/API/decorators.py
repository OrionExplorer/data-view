from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session
from API.models import ApiKey


def _GetUserFromSession(SessionKey):
    SessionItem = Session.objects.filter(session_key=SessionKey).last()
    if SessionItem:
        SessionData = SessionItem.get_decoded()
        return User.objects.get(id=SessionData['_auth_user_id'])

    return None


def valid_session(func):
    def decorated(request, *args, **kwargs):
        if 'session' in request.headers:
            if _GetUserFromSession(request.headers['session']):
                return func(request, *args, **kwargs)

        return JsonResponse(
            {"message": "Access denied"},
            status=401,
        )
    return decorated


def valid_api_key(func):
    def decorated(request, *args, **kwargs):
        if 'x-api-key' in request.headers:
            UserApiKey = ApiKey.objects.filter(api_key=request.headers['x-api-key']).last()
            if UserApiKey is not None:
                CreditsLeft = UserApiKey.credits
                if CreditsLeft > 0:
                    request.META['x-api-id'] = UserApiKey.id
                    return func(request, *args, **kwargs)
                else:
                    return JsonResponse(
                        {"message": "API key is valid, but out of credits."},
                        status=402,
                    )
            else:
                return JsonResponse(
                    {"message": f"Invalid API key: {request.headers['x-api-key']}"},
                    status=403,
                )
        return JsonResponse(
            {"message": f"Access denied {request.headers}"},
            status=403,
        )
    return decorated
