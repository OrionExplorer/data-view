import json
import logging
from django.http import JsonResponse, HttpResponse
from API.models import ApiKey, ApiKeyCreditHistory, _InternalIdentifierGenerator
from API.decorators import valid_api_key
from django.apps import apps
from django.core import serializers
from django.core.paginator import Paginator
from decimal import Decimal
from django.conf import settings
from django.db import models
from django.db.models import Q


logger = logging.getLogger("django")


class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super().default(obj)


def LOG_data(request_uid="none", log_fn=logger.info, text="no content"):
    log_fn(f"[{request_uid}] {text}")


def _GetModelByName(name):
    if name is None:
        return None

    if name in settings.API_APP_BLACKLIST:
        return None

    for AppName in apps.all_models:
        AppModels = apps.all_models[AppName]
        # LOG_data(text=f"App: {AppName}, models: {AppModels}")
        if name in AppModels:
            try:
                return apps.get_model(f"{AppName}.{name}")
            except Exception:
                return None
    return None


def _GetAllModels():
    Result = []

    for AppName in apps.all_models:
        if AppName in settings.API_APP_BLACKLIST:
            continue
        AppModels = apps.all_models[AppName]
        for ModelName in AppModels:
            LOG_data(text=f"App: {AppName}, models: {ModelName}")
            try:
                AppModelItem = apps.get_model(f"{AppName}.{ModelName}")
                AppModelFieldsRaw = {field.name for field in AppModelItem._meta.get_fields()}
                AppModeFieldsList = []
                for ModelField in AppModelFieldsRaw:
                    FieldData = AppModelItem._meta.get_field(ModelField)
                    FieldConfig = {
                        'name': ModelField,
                        'type': FieldData.get_internal_type(),
                    }
                    if FieldData.get_internal_type() == "CharField":
                        FieldConfig['max_length'] = FieldData.max_length

                    AppModeFieldsList.append(FieldConfig)

                Result.append({
                    'model': ModelName,
                    'fields': AppModeFieldsList,
                    'billing': AppModelItem.get_billing()
                })
            except Exception as e:
                LOG_data(text=f"[_GetAllModels] error: {e}.", log_fn=logger.error)
    return Result


def _CalculateCreditCost(model, transfer_size_KB, billing_info=None, request_uid=None):
    ChunkSize = settings.API_CREDIT_COST['_default']['chunk_KB']
    CreditCost = settings.API_CREDIT_COST['_default']['credits']
    MinChunkSize = settings.API_CREDIT_COST['_default']['min_chunk_KB']

    if billing_info:
        ChunkSize = billing_info['chunk_KB']
        CreditCost = billing_info['credits']
        MinChunkSize = billing_info['min_chunk_KB']

    LOG_data(request_uid=request_uid, log_fn=logger.info, text="==============================================")
    LOG_data(request_uid=request_uid, log_fn=logger.info, text=f"_CalculateCreditCost({model}, {transfer_size_KB})")
    if transfer_size_KB < MinChunkSize:
        LOG_data(request_uid=request_uid, log_fn=logger.warning, text=f"  NOTICE: Size of transferred data ({transfer_size_KB} KB) is smaller than minimun chunk size ({MinChunkSize} KB)!")
        transfer_size_KB = MinChunkSize
    LOG_data(request_uid=request_uid, log_fn=logger.info, text=f"  - We charge {CreditCost} per {ChunkSize} KB")
    ChunkSizeCount = round(transfer_size_KB / ChunkSize)
    LOG_data(request_uid=request_uid, log_fn=logger.info, text=f"  - {ChunkSize} KB chunks used for this request: {ChunkSizeCount}")
    CreditToCharge = round(ChunkSizeCount * CreditCost, 2)
    LOG_data(request_uid=request_uid, log_fn=logger.info, text=f"  - Credits charged for this request: {CreditToCharge}")
    LOG_data(request_uid=request_uid, log_fn=logger.info, text="==============================================")
    return {
        'chunk_size': ChunkSize,
        'credit_per_chunk': CreditCost,
        'credit_to_charge': CreditToCharge,
        'chunk_size_count': ChunkSizeCount,
        'min_chunk_size': MinChunkSize
    }


def _AddApiKeyCreditHistory(UserApiKeyItem, data_request_uri, response_size, request_chunk_size, chunk_count, credit_per_chunk, total_credit_cost, credit_balance, ip, request_uid):
    if UserApiKeyItem and data_request_uri and response_size and request_chunk_size and chunk_count and credit_per_chunk and total_credit_cost and credit_balance and ip and request_uid:
        HistoryItem = ApiKeyCreditHistory()
        HistoryItem.api_key = UserApiKeyItem
        HistoryItem.data_request_uri = data_request_uri
        HistoryItem.response_size = response_size
        HistoryItem.request_chunk_size = request_chunk_size
        HistoryItem.chunk_count = chunk_count
        HistoryItem.credit_per_chunk = credit_per_chunk
        HistoryItem.total_credit_cost = total_credit_cost
        HistoryItem.credit_balance = credit_balance
        HistoryItem.ip = ip
        HistoryItem.request_uid = request_uid
        HistoryItem.save()


def _FetchData(RequestedModel, model, request):
    LimitData = int(request.GET.get('limit', 25))
    StartFrom = int(request.GET.get('start', 0))

    RequestUID = request.META['data-view-uid']

    LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"Requested model: {model}. Billing info: {RequestedModel.get_billing()}")
    LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"Request query: {request.META['RAW_URI']}")
    LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"  - start: {StartFrom}")
    LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"  - limit: {LimitData}")

    RequestedModelFields = {field.name for field in RequestedModel._meta.get_fields()}
    # LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"  - available fields: {RequestedModelFields}")

    AllData = []

    # Budowanie dynamicznego filtra
    QueryFilters = Q()
    HasQueryFilters = False
    for key, value in request.GET.items():
        if key in RequestedModelFields:
            HasQueryFilters = True
            field = RequestedModel._meta.get_field(key)
            if isinstance(field, models.IntegerField):
                QueryFilters &= Q(**{key: int(value)})
            elif isinstance(field, models.DateField):
                QueryFilters &= Q(**{key: value})  # Tu można dodać parsowanie dat
            else:
                QueryFilters &= Q(**{f"{key}__icontains": value})

    if HasQueryFilters is True:
        LOG_data(request_uid=RequestUID, log_fn=logger.info, text=f"  - generated filter: {QueryFilters}")
        AllData = RequestedModel.objects.filter(QueryFilters).order_by('id')[StartFrom:StartFrom + LimitData]
    else:
        LOG_data(request_uid=RequestUID, log_fn=logger.info, text="  - no filters to apply")
        AllData = RequestedModel.objects.all().order_by('id')[StartFrom:StartFrom + LimitData]

    RawData = serializers.serialize('python', AllData)

    return {
        'RawData': RawData,
        'total': AllData.count()
    }


@valid_api_key
def GetItemsTemplate(request, model):
    AllowedOutputTypes = ['json']
    if request.method == 'GET':
        RequestedModel = _GetModelByName(name=model)
        if RequestedModel:
            OutputType = request.GET.get('outputType', 'json')

            if OutputType not in AllowedOutputTypes:
                return JsonResponse(
                    {
                        "data": [],
                        "message": f"Invalid outputType: {OutputType}."
                    },
                    json_dumps_params={'indent': 2},
                    status=400,
                )

            UserIPAddress = None
            if 'HTTP_X_FORWARDED_FOR' in request.META:
                UserIPAddress = request.META['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
            else:
                UserIPAddress = request.META['REMOTE_ADDR']

            UserApiKeyItem = None
            if 'x-api-id' in request.META:
                UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

            request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

            if UserApiKeyItem is None:
                return JsonResponse(
                    {
                        "data": [],
                        "message": "Unexpected error: missing API key in internal header."
                    },
                    json_dumps_params={'indent': 2},
                    status=500,
                )

            CreditsLeft = UserApiKeyItem.credits
            BillingInfo = RequestedModel.get_billing()
            DataInfo = _FetchData(RequestedModel, model, request)

            RawData = DataInfo['RawData']

            Data = {
                'total': DataInfo['total'],
                'data': []
            }
            TransferSize = 0
            if OutputType == 'json':
                Data['data'] = [d['fields'] | dict(id=d['pk']) for d in RawData]
                JSONData = json.dumps(Data, indent=2, ensure_ascii=False, cls=DecimalEncoder)
                TransferSize = round(len(JSONData) / 1000, 1)
                CreditCalculateData = _CalculateCreditCost(model=model, transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
                CreditTransferCost = CreditCalculateData['credit_to_charge']
                LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Transfer size: {TransferSize} KB (records in response: {Data['total']})")
                LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before data transfer: {CreditsLeft}")
                PredictedBallance = round(CreditsLeft - Decimal.from_float(CreditTransferCost), 1)
                if PredictedBallance < 0.0:
                    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.error, text=f"ERROR: Request exceeds available credits. Predicted ballance is {round(PredictedBallance, 2)}!")
                    return JsonResponse(
                        {
                            "data": [],
                            "message": "Your request exceeds available credits."
                        },
                        json_dumps_params={'indent': 2},
                        status=400,
                    )
                UserApiKeyItem.credits = max(0, PredictedBallance)
                UserApiKeyItem.save()
                _AddApiKeyCreditHistory(
                    UserApiKeyItem=UserApiKeyItem,
                    data_request_uri=request.META['RAW_URI'],
                    response_size=TransferSize,
                    request_chunk_size=CreditCalculateData['chunk_size'],
                    chunk_count=CreditCalculateData['chunk_size_count'],
                    credit_per_chunk=CreditCalculateData['credit_per_chunk'],
                    total_credit_cost=CreditCalculateData['credit_to_charge'],
                    credit_balance=CreditsLeft,
                    ip=UserIPAddress,
                    request_uid=request.META['data-view-uid']
                )
                LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before after transfer: {round(UserApiKeyItem.credits, 2)}")
                return HttpResponse(JSONData, status=200, content_type='application/json')  # return JsonResponse(Data, safe=False, json_dumps_params={'indent': 2, 'ensure_ascii': False})
            else:  # TODO: for now with only supported JSON output type
                return JsonResponse(
                    {
                        "data": [],
                        "message": "Only JSON output type is supported."
                    },
                    json_dumps_params={'indent': 2},
                    status=400,
                )
        else:
            return JsonResponse(
                {
                    "data": [],
                    "message": f"Resource {model} is invalid."
                },
                json_dumps_params={'indent': 2},
                status=400,
            )
    else:
        return JsonResponse(
            {
                "data": [],
                "message": "Only GET requests are accepted."
            },
            json_dumps_params={'indent': 2},
            status=400,
        )


@valid_api_key
def GetItemsListDetails(request):
    if request.method == 'GET':
        RawData = _GetAllModels()
        return JsonResponse(
            {
                "data": RawData,
                "total": len(RawData)
            },
            json_dumps_params={'indent': 2, 'ensure_ascii': False},
            status=200,
        )
    else:
        return JsonResponse(
            {
                "data": [],
                "message": "Only GET requests are accepted."
            },
            json_dumps_params={'indent': 2},
            status=400,
        )
