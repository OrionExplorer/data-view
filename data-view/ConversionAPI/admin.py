from django.contrib import admin
from .models import ConvertedEmail
from .models import DownloadLog
from .models import SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ('key', 'setting_type', 'boolean_value', 'integer_value')
    list_editable = ('boolean_value', 'integer_value')


@admin.register(ConvertedEmail)
class ConvertedEmailAdmin(admin.ModelAdmin):
    list_display = ('user', 'file_path', 'download_token', 'created')


@admin.register(DownloadLog)
class DownloadLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'file', 'downloaded_at', 'ip_address')
    list_filter = ('downloaded_at', 'user')
    search_fields = ('user__username', 'file__file_path')
