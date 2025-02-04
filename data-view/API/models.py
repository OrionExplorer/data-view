import random
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


def _InternalIdentifierGenerator(length=12):
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(length))


def GenerateAPIKey():
    PartList = []
    for index in range(4):
        PartList.append(_InternalIdentifierGenerator(6))
    return '-'.join(PartList)


class ApiKey(models.Model):
    class Meta:
        verbose_name = 'API key'
        verbose_name_plural = 'API keys'

    api_key = models.CharField(max_length=32, verbose_name='Key', blank=False, null=False, default=GenerateAPIKey())
    credits = models.DecimalField(max_digits=19, decimal_places=2, verbose_name='Credits', default=1, blank=False, null=False, validators=[MinValueValidator(1)])
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, blank=True, verbose_name=u'created')

    # Billing Configuration
    billing_credit_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.1,  # Domyślny koszt 0.1 kredytu za jednostkę
        validators=[MinValueValidator(0.01)],
        verbose_name='Credit Cost per Chunk'
    )
    billing_chunk_kb = models.PositiveIntegerField(
        default=10,  # Domyślnie 10 KB jako jednostka rozliczeniowa
        validators=[MinValueValidator(1)],
        verbose_name='Chunk Size (KB)'
    )
    billing_min_chunk_kb = models.PositiveIntegerField(
        default=10,  # Minimalny rozmiar rozliczeniowy 10 KB
        validators=[MinValueValidator(1)],
        verbose_name='Minimum Chunk Size (KB)'
    )

    def clean(self):
        ApiKeyMatch = ApiKey.objects.filter(api_key=self.api_key).exclude(id=self.id)
        if ApiKeyMatch.count() > 0:
            raise ValidationError(u'Given API key already exists!')

    def __str__(self):
        return f"{self.user} (credits: {self.credits}) [{self.api_key}]"


class ApiKeyCreditHistory(models.Model):
    class Meta:
        verbose_name = 'API key credit history item'
        verbose_name_plural = 'API key credit history list'

    api_key = models.ForeignKey(ApiKey, verbose_name='key', null=False, blank=False, on_delete=models.CASCADE)
    data_request_uri = models.CharField(max_length=1024, verbose_name='request', null=False, blank=False)
    response_size = models.IntegerField(verbose_name='response size (KB)', null=False, blank=False)
    request_chunk_size = models.IntegerField(verbose_name='request chunk size (KB)', null=False, blank=False)
    chunk_count = models.IntegerField(verbose_name='chunks for request', null=False, blank=False)
    credit_per_chunk = models.DecimalField(max_digits=19, decimal_places=2, verbose_name='credit cost per chunk', default=1, blank=False, null=False, validators=[MinValueValidator(1)])
    total_credit_cost = models.DecimalField(max_digits=19, decimal_places=2, verbose_name='total credit cost', default=1, blank=False, null=False, validators=[MinValueValidator(1)])
    credit_balance = models.DecimalField(max_digits=19, decimal_places=2, verbose_name='balance before request', default=1, blank=False, null=False, validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, blank=True, verbose_name=u'created')
    ip = models.GenericIPAddressField(protocol='both', verbose_name='IP address', null=False, blank=False)
    request_uid = models.CharField(max_length=48, verbose_name="Request UID in api.log", blank=False, null=False)

    def __str__(self):
        return f"{self.api_key.user}, credits used: {self.total_credit_cost}/{self.credit_balance} - {self.data_request_uri} - ({str(timezone.localtime(self.timestamp))[:19]})"


class ApiKeyCreditTopUp(models.Model):
    class Meta:
        verbose_name = 'API key credit top-up'
        verbose_name_plural = 'API key credit top-ups'

    api_key = models.ForeignKey(ApiKey, verbose_name=u'key', null=False, blank=False, on_delete=models.CASCADE)
    credit_top_up = models.DecimalField(max_digits=19, decimal_places=2, verbose_name='Top-up', default=1, blank=False, null=False, validators=[MinValueValidator(1)])
    timestamp = models.DateTimeField(auto_now=False, auto_now_add=True, null=True, blank=True, verbose_name=u'created')

    def save(self, *args, **kwargs):
        ApiKeyItem = ApiKey.objects.get(id=self.api_key.id)
        ApiKeyItem.credits = ApiKeyItem.credits + self.credit_top_up
        ApiKeyItem.save()
        super(ApiKeyCreditTopUp, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.api_key.user}, top-up: {self.credit_top_up} - ({str(timezone.localtime(self.timestamp))[:19]})"
