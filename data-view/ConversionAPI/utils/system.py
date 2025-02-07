import socket
import random
from ConversionAPI.models import SystemSetting


LIBREOFFICE_SERVICE_NAME = "libreoffice"


def get_system_setting(key, default=None):
    try:
        setting = SystemSetting.objects.get(key=key)
        return setting.get_value()
    except SystemSetting.DoesNotExist:
        return default


def GetLibreOfficeInstance():
    """Wyszukuje dostępne instancje libreoffice w sieci Dockera."""
    try:
        instances = list(set(
            addr[-1][0] for addr in socket.getaddrinfo(LIBREOFFICE_SERVICE_NAME, 5000)
        ))
        return instances
    except socket.gaierror:
        return []

def GetRandomLibreOfficeInstance():
    """Zwraca losowy backend LibreOffice z dostępnych instancji."""
    instances = GetLibreOfficeInstance()
    if not instances:
        raise RuntimeError("No libreoffice instances found")
    return f"http://{random.choice(instances)}:5000"


def GetLibreOffice(retries=3, delay=2):
    """Wykonuje ponowną próbę pobrania serwera LibreOffice w razie niepowodzenia."""
    for _ in range(retries):
        try:
            return GetRandomLibreOfficeInstance()
        except RuntimeError:
            time.sleep(delay)
    raise RuntimeError("No libreoffice instances available after retries")
