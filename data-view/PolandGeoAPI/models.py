from django.db import models


class BillingMixin:
    @classmethod
    def get_billing(cls):
        return cls.billing


class LocationPoland(models.Model, BillingMixin):
    class Meta:
        verbose_name = 'Location - Poland'
        verbose_name_plural = 'Locations - Poland'

    billing = {
        'chunk_KB': 10,
        'credits': 0.1,
        'min_chunk_KB': 10
    }

    voivodeship = models.CharField(max_length=64, verbose_name='voivodeship', blank=False, null=False)
    county = models.CharField(max_length=96, verbose_name='county', blank=False, null=False)
    municipality = models.CharField(max_length=256, verbose_name='municipality', blank=False, null=False)
    street = models.CharField(max_length=256, verbose_name='street', blank=False, null=False)
    building_number = models.CharField(max_length=20, verbose_name='building number', blank=False, null=False)
    zip_code = models.CharField(max_length=16, verbose_name='zip code', blank=False, null=False)
    city = models.CharField(max_length=256, verbose_name='city', blank=False, null=False)

    def __str__(self):
        return f"{self.city}, {self.zip_code} {self.voivodeship}"
