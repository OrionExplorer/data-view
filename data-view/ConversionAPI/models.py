from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from .utils.email_to_pdf import _InternalIdentifierGenerator


class BillingMixin:
    @classmethod
    def get_billing(cls):
        return cls.billing


class ConvertedEmail(models.Model, BillingMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file_path = models.CharField(max_length=255, verbose_name="File path")
    file_size = models.PositiveIntegerField(default=0, verbose_name="File size")
    created = models.DateTimeField(auto_now_add=True)
    download_token = models.CharField(max_length=32, verbose_name="Download token", default=_InternalIdentifierGenerator)

    billing = {
        'chunk_KB': 5,
        'credits': 0.5,
        'min_chunk_KB': 5
    }

    def __str__(self):
        return f"Email for {self.user.username} at {str(timezone.localtime(self.created))[:19]}"


class DownloadLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    file = models.ForeignKey(ConvertedEmail, on_delete=models.CASCADE)
    downloaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Downloaded at")
    ip_address = models.GenericIPAddressField(verbose_name="IP address", null=True, blank=True)

    def __str__(self):
        return f"Download by {self.user.username} on {self.downloaded_at}"


class SystemSetting(models.Model):
    SETTING_TYPE_CHOICES = [
        ('boolean', 'Boolean'),
        ('integer', 'Integer'),
    ]

    key = models.CharField(max_length=100, unique=True)
    setting_type = models.CharField(max_length=10, verbose_name='Setting type', choices=SETTING_TYPE_CHOICES, default='boolean')
    boolean_value = models.BooleanField(default=False, verbose_name='Boolean value')
    integer_value = models.PositiveIntegerField(null=True, verbose_name='Integer value', blank=True)

    def __str__(self):
        return f"{self.key}: {self.get_value()}"

    def get_value(self):
        if self.setting_type == 'boolean':
            return self.boolean_value
        elif self.setting_type == 'integer':
            return self.integer_value
        return None
