import os
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from ConversionAPI.utils.auth import GetUserFromApiKey
from ConversionAPI.models import ConvertedEmail
from ConversionAPI.models import DownloadLog
from ConversionAPI.utils.email_to_pdf import ConvertEmailToPDF
from ConversionAPI.utils.email_to_pdf import _InternalIdentifierGenerator
from ConversionAPI.utils.attachment_to_pdf import ConvertAttachmentToPDF
from API.decorators import valid_api_key
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from API.views import _CalculateCreditCost
from API.views import LOG_data
from API.views import _AddApiKeyCreditHistory
from API.models import ApiKey
from decimal import Decimal
from email import message_from_binary_file
from email.message import EmailMessage
from io import BytesIO
import base64


logger = logging.getLogger("django")


def _ValidateQueryParams(request, ViewName):
    if 'remove' in request.GET:  # Jeśli użytkownik podał parametr remove...
        ResponseMode = request.GET.get('mode', 'file_id')
        if request.GET.get('remove') == "true":  # ...i oznaczył, że chce usunąć plik po wykonanej operacji...
            if ResponseMode == 'file_id' and '/download/' not in ViewName:  # ...ale operacja to nie pobranie, ale wgranie pliku w trybie "file_id"
                return JsonResponse({'error': 'Parameter \"field_id\" is forbidden for uploads with \"remove=true\" mode.'}, status=400)

            elif ResponseMode == 'file_id' and '/download/' in ViewName:  # ..ale operacja to pobranie w trybie "file_id"
                return JsonResponse({'error': 'Parameter \"field_id\" is forbidden for this endpoint.'}, status=400)
    return True


def _GenerateContentResponse(request, UserApiKeyItem, PDFPath, SourceFileSize, OutputFileSize, ViewName):
    ResponseMode = request.GET.get('mode', 'file_id')

    ViewName = f"{ViewName}?mode={ResponseMode}"

    UserItem = UserApiKeyItem.user

    DownloadToken = _InternalIdentifierGenerator(32)

    QueryString = "&".join(f"{key}={value}" for key, value in request.GET.items())

    DoRemoveFile = False
    ForceRemoveFile = False
    if 'remove' in request.GET:  # Jeśli użytkownik podał parametr remove...
        if request.GET.get('remove') == "true":  # ...i oznaczył, że chce usunąć plik po wykonanej operacji...
            if ResponseMode == 'file_id' and '/download/' not in ViewName:  # ...ale operacja to nie pobranie, ale wgranie pliku w trybie "file_id"
                return JsonResponse({'error': 'Parameter \"field_id\" is forbidden for uploads with \"remove=true\" mode.'}, status=400)

            elif ResponseMode == 'file_id' and '/download/' in ViewName:  # ..ale operacja to pobranie w trybie "file_id"
                return JsonResponse({'error': 'Parameter \"field_id\" is forbidden for this endpoint.'}, status=400)

            elif ResponseMode != 'file_id' and '/download/' not in ViewName:  # ...ale operacja to nie pobranie, ale wgranie pliku w trybie innym niż "file_id"
                DoRemoveFile = True

            elif ResponseMode != 'file_id' and '/download/' in ViewName:  # ...ale operacja to pobranie w trybie innym niż "file_id":
                DoRemoveFile = True
            else:
                DataDump = f"""
                \r  - request.META = {request.META}
                \r  - view = {ViewName}
                \r  - query = {QueryString}
                \r  - API key = {UserApiKeyItem.api_key}
                \r  - PDFPath = {PDFPath}
                \r  - SourceFileSize = {SourceFileSize}
                \r  - OutputFileSize = {OutputFileSize}
                """
                LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Unhandled exception: '{DataDump}'.")

        else:  # ...i oznaczył, że nie chce usunąć pliku po wykonanej operacji...
            DoRemoveFile = False
    else:  # Jeśli użytkownik nie podał parametru remove...
        if '/download/' in ViewName:  # ...ale operacja to pobranie
            DoRemoveFile = False
        elif '/download/' not in ViewName:  # ...ale operacja to wgranie pliku
            if ResponseMode == 'file_id':  # ...i to wgranie pliku w trybie "file_id"
                DoRemoveFile = False
            else:  # ...i to wgranie pliku w trybie innym niż "file_id"
                DoRemoveFile = True

    CreditsLeft = UserApiKeyItem.credits
    BillingInfo = {
        'chunk_KB': UserApiKeyItem.billing_chunk_kb,
        'credits': UserApiKeyItem.billing_credit_cost,
        'min_chunk_KB': UserApiKeyItem.billing_min_chunk_kb
    }

    EncodedPDF = None

    TransferSize = len(DownloadToken)

    # Obliczenie rzeczywistego rozmiaru przesyłanych danych
    if ResponseMode == 'inline_pdf':
        TransferSize = OutputFileSize  # os.path.getsize(PDFPath)
    elif ResponseMode == 'base64_pdf':
        with open(PDFPath, 'rb') as PDFFile:
            EncodedPDF = base64.b64encode(PDFFile.read()).decode('utf-8')
            TransferSize = len(EncodedPDF)
    else:
        TransferSize = len(DownloadToken)

    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Response mode is '{ResponseMode}'.")
    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"  - source size is {round(SourceFileSize / 1000, 1)} KB.")

    TransferSize = round(TransferSize / 1000, 1)

    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"  - PDF size is {round(OutputFileSize / 1000, 1)} KB.")

    if ResponseMode == 'file_id':
        TransferSize = round(SourceFileSize / 1000, 1)
        # LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"  - PDF size in {ResponseMode} mode is {TransferSize} KB.")
    else:
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"  - PDF size in {ResponseMode} mode is {TransferSize} KB.")

    CreditCalculateData = _CalculateCreditCost(model='ConvertedEmail', transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
    CreditTransferCost = CreditCalculateData['credit_to_charge']

    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before data transfer: {CreditsLeft}")
    PredictedBallance = round(CreditsLeft - CreditTransferCost, 1)
    if PredictedBallance < 0.0:
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.error, text=f"ERROR: Request exceeds available credits. Predicted ballance is {round(PredictedBallance, 2)}!")
        return JsonResponse(
            {
                "error": "Insufficient credits. Please top up your account.",
                "available_credits": float(CreditsLeft),
                "required_credits": float(CreditTransferCost)
            },
            json_dumps_params={'indent': 2},
            status=402,
        )
    UserApiKeyItem.credits = max(0, PredictedBallance)
    UserApiKeyItem.save()
    UserIPAddress = None

    if 'HTTP_X_FORWARDED_FOR' in request.META:
        UserIPAddress = request.META['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    else:
        UserIPAddress = request.META['REMOTE_ADDR']

    _AddApiKeyCreditHistory(
        UserApiKeyItem=UserApiKeyItem,
        # data_request_uri=ViewName,
        data_request_uri=f"{ViewName}/ [{QueryString}] <{os.path.basename(PDFPath)}>",
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

    SavePDFPath = PDFPath
    if DoRemoveFile is True:
        SavePDFPath = f"{SavePDFPath} (removed)"
        

    # Zapis pliku z powiązaniem do użytkownika i tokena
    ConvertedEmailItem = ConvertedEmail.objects.create(
        user=UserItem,
        file_path=SavePDFPath,
        file_size=OutputFileSize,
        download_token=DownloadToken
    )

    PreparedResponse = JsonResponse({"file_id": DownloadToken})

    if ResponseMode == 'inline_pdf':
        PreparedResponse = FileResponse(open(PDFPath, 'rb'), content_type='application/pdf')
    elif ResponseMode == 'base64_pdf':
        PreparedResponse = JsonResponse({"pdf_base64": EncodedPDF})
    else:
        PreparedResponse = JsonResponse({"file_id": DownloadToken})

    # Jeśli przekonwertowany plik ma być od razu zwrócony w odpowiedzi (mode == inline_pdf, mode == base64_pdf),
    # to usuwamy go z serwera.
    # W przypadku mode == file_id plik musi być zachowany do późniejszego pobrania na żądanie.
    # Dopiero wtedy można użyć parametru "remove", aby usunąć plik po pobraniu
    if ResponseMode != 'file_id':
        DownloadLog.objects.create(user=UserItem, file=ConvertedEmailItem, ip_address=UserIPAddress)
        if DoRemoveFile is True:
            if os.path.exists(PDFPath):  # Nie przechowujemy pliku
                os.remove(PDFPath)

    return PreparedResponse


@csrf_exempt
@valid_api_key
def EmailToPDFView(request):
    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

    QueryParamsValidInfo = _ValidateQueryParams(request, '/api/v1/email-to-pdf/')
    if QueryParamsValidInfo is not True:
        return QueryParamsValidInfo

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    if request.method == 'POST':

        SourceFileSize = 0

        if request.content_type.startswith('multipart/form-data'):
            SourceFileSize = int(request.headers['Content-Length'])
            file = request.FILES['file']
            PDFPath, PDFFileSize = ConvertEmailToPDF(file)
        elif request.content_type == 'application/json':
            data = json.loads(request.body)
            sender = data.get('sender')
            recipient = data.get('recipient')
            subject = data.get('subject', 'No Subject')
            body = data.get('body')
            SourceFileSize = len(body)
            # attachments = data.get('attachments', [])

            if not sender or not recipient or not body:
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            # Tworzenie wiadomości e-mail w formacie EML (tymczasowy plik)
            msg = EmailMessage()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.set_content(body)

            # Przetwarzanie załączników
            # for attachment in attachments:
            #     filename = attachment.get('filename')
            #     content = attachment.get('content')
            #     if filename and content:
            #         file_data = base64.b64decode(content)
            #         msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=filename)

            # Konwersja do PDF
            eml_file = BytesIO(msg.as_bytes())
            PDFPath, PDFFileSize = ConvertEmailToPDF(eml_file)

        if PDFPath is None or PDFFileSize is None:
            return JsonResponse({"error": "Conversion failed."}, status=400)

        return _GenerateContentResponse(request, UserApiKeyItem, PDFPath, SourceFileSize, PDFFileSize, '/api/v1/email-to-pdf/')

    return JsonResponse({"error": "No email received."}, status=400)


@csrf_exempt
@valid_api_key
def AttachmentToPDFView(request):
    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

    QueryParamsValidInfo = _ValidateQueryParams(request, '/api/v1/attachment-to-pdf/')
    if QueryParamsValidInfo is not True:
        return QueryParamsValidInfo

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    if request.method == 'POST':

        SourceFileSize = 0

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            filename = data.get('filename')
            content = data.get('content')
            SourceFileSize = len(content)
            ConversionData = ConvertAttachmentToPDF(content=content, filename=filename, api_key=UserApiKeyItem.api_key)
        else:
            SourceFileSize = int(request.headers['Content-Length'])
            file = request.FILES['file']
            ConversionData = ConvertAttachmentToPDF(file=file, api_key=UserApiKeyItem.api_key)

        if ConversionData['status'] != 200:
            return JsonResponse({'error': ConversionData['data']['error']}, status=ConversionData['status'])
        else:
            PDFPath = ConversionData['data']['pdf_path']
            PDFFileSize = ConversionData['data']['file_size']

            return _GenerateContentResponse(request, UserApiKeyItem, PDFPath, SourceFileSize, PDFFileSize, '/api/v1/attachment-to-pdf/')

    return JsonResponse({"error": "No attachment files received."}, status=400)


@csrf_exempt
@valid_api_key
def DownloadPDFView(request, download_token):

    UserApiKeyItem = None
    UserItem = None
    ResponseMode = request.GET.get('mode', 'inline_pdf')

    if ResponseMode == 'file_id':
        return JsonResponse({"error": "Mode \"file_id\" is invalid for this API endpoint."}, status=400)

    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()
        if UserApiKeyItem:
            UserItem = UserApiKeyItem.user

    if UserItem is None:
        return JsonResponse({"error": "Permission denied."}, status=403)

    try:
        ConvertedEmailItem = ConvertedEmail.objects.get(download_token=download_token, user=UserItem)
    except ConvertedEmail.DoesNotExist:
        return JsonResponse({"error": "File does not exist or you do not have access."}, status=404)

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"
    return _GenerateContentResponse(request, UserApiKeyItem, ConvertedEmailItem.file_path, ConvertedEmailItem.file_size, ConvertedEmailItem.file_size, '/api/v1/download/')
