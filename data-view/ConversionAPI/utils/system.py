from ConversionAPI.models import SystemSetting

def get_system_setting(key, default=None):
    try:
        setting = SystemSetting.objects.get(key=key)
        return setting.get_value()
    except SystemSetting.DoesNotExist:
        return default
