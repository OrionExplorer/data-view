from django.db import models


class BillingMixin:
    @classmethod
    def get_billing(cls):
        return cls.billing


class Technician(models.Model, BillingMixin):
    class Meta:
        verbose_name = 'Technician'
        verbose_name_plural = 'Technicians'

    billing = {
        'chunk_KB': 10,
        'credits': 0.1,
        'min_chunk_KB': 10
    }

    name = models.CharField(max_length=256, verbose_name='name', blank=False, null=False)
    tags = models.CharField(max_length=1024, verbose_name='tags', blank=True, null=True)
    contact_person = models.CharField(max_length=256, verbose_name='contact person', blank=True, null=True)
    city = models.CharField(max_length=64, verbose_name='city', blank=False, null=False)
    zip_code = models.CharField(max_length=16, verbose_name='zip code', blank=False, null=False)
    address = models.CharField(max_length=256, verbose_name='address', blank=False, null=False)
    phone = models.CharField(max_length=32, verbose_name='phone', blank=False, null=False)
    email = models.CharField(max_length=256, verbose_name='e-mail', blank=True, null=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='latitude')
    longitude = models.DecimalField(max_digits=9, decimal_places=6, verbose_name='longitude')

    def __str__(self):
        return f"{self.name}, {self.zip_code} {self.city}"
