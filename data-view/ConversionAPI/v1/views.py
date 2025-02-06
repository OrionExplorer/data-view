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


def _GenerateContentResponse(request, UserApiKeyItem, PDFPath, SourceFileSize, OutputFileSize, ViewName):
    ResponseMode = request.GET.get('mode', 'file_id')

    ViewName = f"{ViewName}?mode={ResponseMode}"

    UserItem = UserApiKeyItem.user

    DownloadToken = _InternalIdentifierGenerator(32)

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
        data_request_uri=ViewName,
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
    if ResponseMode != 'file_id':
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
        if os.path.exists(PDFPath):  # Nie przechowujemy pliku
            os.remove(PDFPath)

    return PreparedResponse


@csrf_exempt
@valid_api_key
def EmailToPDFView(request):
    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

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
            attachments = data.get('attachments', [])
            SourceFileSize = len(body)

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

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    if request.method == 'POST':

        SourceFileSize = 0

        if request.content_type == 'application/json':
            data = json.loads(request.body)
            filename = data.get('filename')
            content = data.get('content')
            SourceFileSize = len(content)
            PDFPath, PDFFileSize = ConvertAttachmentToPDF(content=content, filename=filename, api_key=UserApiKeyItem.api_key)
        else:
            SourceFileSize = int(request.headers['Content-Length'])
            file = request.FILES['file']
            PDFPath, PDFFileSize = ConvertAttachmentToPDF(file=file, api_key=UserApiKeyItem.api_key)

        if PDFPath is None or PDFFileSize is None:
            return JsonResponse({"error": "Conversion failed."}, status=400)

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

    CreditsLeft = UserApiKeyItem.credits
    BillingInfo = {
        'chunk_KB': UserApiKeyItem.billing_chunk_kb,
        'credits': UserApiKeyItem.billing_credit_cost,
        'min_chunk_KB': UserApiKeyItem.billing_min_chunk_kb
    }

    EncodedPDF = None
    TransferSize = ConvertedEmailItem.file_size

    # Obliczenie rzeczywistego rozmiaru przesyłanych danych
    if ResponseMode == 'base64_pdf':
        with open(ConvertedEmailItem.file_path, 'rb') as PDFFile:
            EncodedPDF = base64.b64encode(PDFFile.read()).decode('utf-8')
            TransferSize = len(EncodedPDF)
    else:
        TransferSize = ConvertedEmailItem.file_size

    TransferSize = round(TransferSize / 1000, 1)
    CreditCalculateData = _CalculateCreditCost(model='ConvertedEmail', transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
    CreditTransferCost = CreditCalculateData['credit_to_charge']
    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"  - PDF size in {ResponseMode} mode is {TransferSize} KB.")
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
            status=400,
        )
    UserIPAddress = None

    if 'HTTP_X_FORWARDED_FOR' in request.META:
        UserIPAddress = request.META['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    else:
        UserIPAddress = request.META['REMOTE_ADDR']

    QueryString = "&".join(f"{key}={value}" for key, value in request.GET.items())

    if os.path.exists(ConvertedEmailItem.file_path):
        PreparedResponse = None

        if ResponseMode == 'base64_pdf':
            PreparedResponse = JsonResponse({"pdf_base64": EncodedPDF})
        else:
            PreparedResponse = FileResponse(open(ConvertedEmailItem.file_path, 'rb'), content_type='application/pdf')

        # Sprawdzenie, czy użytkownik chce usunąć plik po pobraniu
        if 'remove' in request.GET:
            DoRemoveFile = request.GET.get('remove', 'false').lower()
            if DoRemoveFile != 'true' and DoRemoveFile != 'false':
                return JsonResponse(
                    {
                        "error": f"Parameter \"remove\" has incorrect value: \"{DoRemoveFile}\". Available values are: [\"true\", \"false\"]."
                    },
                    json_dumps_params={'indent': 2},
                    status=400,
                )

            if DoRemoveFile == 'true':
                if os.path.exists(ConvertedEmailItem.file_path):
                    os.remove(ConvertedEmailItem.file_path)

        DownloadLog.objects.create(user=UserItem, file=ConvertedEmailItem, ip_address=UserIPAddress)
        UserApiKeyItem.credits = max(0, PredictedBallance)
        UserApiKeyItem.save()
        _AddApiKeyCreditHistory(
            UserApiKeyItem=UserApiKeyItem,
            data_request_uri=f"/api/v1/download/{download_token}/ [{QueryString}] <{os.path.basename(ConvertedEmailItem.file_path)}>",
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

        return PreparedResponse
    else:
        return JsonResponse({"error": "File does not exist or you do not have access."}, status=404)
