from django.contrib import admin
from API.models import ApiKey, ApiKeyCreditHistory, ApiKeyCreditTopUp

admin.site.register(ApiKey)
admin.site.register(ApiKeyCreditHistory)
admin.site.register(ApiKeyCreditTopUp)
