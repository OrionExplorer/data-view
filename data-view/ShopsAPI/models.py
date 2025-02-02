from django.db import models


class BillingMixin:
    @classmethod
    def get_billing(cls):
        return cls.billing


class Shop(models.Model, BillingMixin):
    class Meta:
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'

    billing = {
        'chunk_KB': 10,
        'credits': 0.1,
        'min_chunk_KB': 10
    }

    name = models.CharField(max_length=256, verbose_name='name', blank=False, null=False)
    brand = models.CharField(max_length=256, verbose_name='name', blank=False, null=False)
    city = models.CharField(max_length=64, verbose_name='city', blank=False, null=False)
    address = models.CharField(max_length=256, verbose_name='address', blank=False, null=False)
    zip_code = models.CharField(max_length=16, verbose_name='zip code', blank=False, null=False)
    address = models.CharField(max_length=256, verbose_name='address', blank=False, null=False)

    def __str__(self):
        return f"{self.name}, {self.zip_code} {self.city}"
