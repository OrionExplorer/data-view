import os
import logging
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .utils.auth import GetUserFromApiKey
from .models import ConvertedEmail
from .models import DownloadLog
from .utils.email_to_pdf import ConvertEmailToPDF
from .utils.email_to_pdf import _InternalIdentifierGenerator
from .utils.attachment_to_pdf import convert_attachment_to_pdf
from API.decorators import valid_api_key
from django.http import FileResponse, Http404
from django.core.exceptions import PermissionDenied
from API.views import _CalculateCreditCost
from API.views import LOG_data
from API.views import _AddApiKeyCreditHistory
from API.models import ApiKey
from decimal import Decimal
from django.shortcuts import render
from email import message_from_binary_file
from email.message import EmailMessage
from io import BytesIO
import base64


logger = logging.getLogger("django")


def landing_page(request):
    return render(request, 'dataview_landing_page.html')


@csrf_exempt
@valid_api_key
def EmailToPDFView(request):
    try:
        UserItem = GetUserFromApiKey(request)
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    if request.method == 'POST':
        if request.content_type.startswith('multipart/form-data'):
            file = request.FILES['file']
            PDFPath, FileSize = ConvertEmailToPDF(file)
        elif request.content_type == 'application/json':
            data = json.loads(request.body)
            sender = data.get('sender')
            recipient = data.get('recipient')
            subject = data.get('subject', 'No Subject')
            body = data.get('body')
            attachments = data.get('attachments', [])

            if not sender or not recipient or not body:
                return JsonResponse({'error': 'Missing required fields.'}, status=400)

            # Tworzenie wiadomości e-mail w formacie EML (tymczasowy plik)
            msg = EmailMessage()
            msg['From'] = sender
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.set_content(body)

            # Przetwarzanie załączników
            for attachment in attachments:
                filename = attachment.get('filename')
                content = attachment.get('content')
                if filename and content:
                    file_data = base64.b64decode(content)
                    msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=filename)

            # Konwersja do PDF
            eml_file = BytesIO(msg.as_bytes())
            PDFPath, FileSize = ConvertEmailToPDF(eml_file)

        CreditsLeft = UserApiKeyItem.credits
        BillingInfo = ConvertedEmail.get_billing()

        TransferSize = round(FileSize / 1000, 1)
        CreditCalculateData = _CalculateCreditCost(model='ConvertedEmail', transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
        CreditTransferCost = CreditCalculateData['credit_to_charge']
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Transfer size: {TransferSize} KB")
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before data transfer: {CreditsLeft}")
        PredictedBallance = round(CreditsLeft - Decimal.from_float(CreditTransferCost), 1)
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

        # Generowanie unikalnego tokena
        DownloadToken = _InternalIdentifierGenerator(32)

        # Zapis pliku z powiązaniem do użytkownika i tokena
        converted_email = ConvertedEmail.objects.create(
            user=UserItem,
            file_path=PDFPath,
            file_size=FileSize,
            download_token=DownloadToken
        )

        return JsonResponse({
            "file_id": converted_email.download_token,
            "file_size": converted_email.file_size
        })

    return JsonResponse({"error": "No email received."}, status=400)


@csrf_exempt
@valid_api_key
def AttachmentToPDFView(request):
    try:
        UserItem = GetUserFromApiKey(request)
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    if request.method == 'POST':
        if request.content_type == 'application/json':
            data = json.loads(request.body)
            filename = data.get('filename')
            content = data.get('content')
            PDFPath, FileSize = convert_attachment_to_pdf(content=content, filename=filename, api_key=UserApiKeyItem.api_key)
        else:
            file = request.FILES['file']
            PDFPath, FileSize = convert_attachment_to_pdf(file=file, api_key=UserApiKeyItem.api_key)

        if PDFPath is None or FileSize is None:
            return JsonResponse({"error": "Conversion failed."}, status=400)

        CreditsLeft = UserApiKeyItem.credits
        BillingInfo = ConvertedEmail.get_billing()

        TransferSize = round(FileSize / 1000, 1)
        CreditCalculateData = _CalculateCreditCost(model='ConvertedEmail', transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
        CreditTransferCost = CreditCalculateData['credit_to_charge']
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Transfer size: {TransferSize} KB")
        LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before data transfer: {CreditsLeft}")
        PredictedBallance = round(CreditsLeft - Decimal.from_float(CreditTransferCost), 1)
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

        # Generowanie unikalnego tokena
        DownloadToken = _InternalIdentifierGenerator(32)

        # Zapis pliku z powiązaniem do użytkownika i tokena
        converted_email = ConvertedEmail.objects.create(
            user=UserItem,
            file_path=PDFPath,
            file_size=FileSize,
            download_token=DownloadToken
        )

        return JsonResponse({
            "file_id": converted_email.download_token,
            "file_size": converted_email.file_size
        })
        return JsonResponse({'pdf_url': f'{PDFPath}'})

    return JsonResponse({"error": "No attachment files received."}, status=400)


@csrf_exempt
@valid_api_key
def DownloadPDFView(request, download_token):
    try:
        user = GetUserFromApiKey(request)
    except PermissionDenied as e:
        return JsonResponse({"error": str(e)}, status=403)

    try:
        converted_email = ConvertedEmail.objects.get(download_token=download_token, user=user)
    except ConvertedEmail.DoesNotExist:
        return JsonResponse({"error": "Requested file does not exist or you do not have access to it."}, status=404)

    UserApiKeyItem = None
    if 'x-api-id' in request.META:
        UserApiKeyItem = ApiKey.objects.filter(id=request.META['x-api-id']).last()

    request.META['data-view-uid'] = f"{_InternalIdentifierGenerator(8)}-{UserApiKeyItem.api_key}"

    CreditsLeft = UserApiKeyItem.credits
    BillingInfo = ConvertedEmail.get_billing()

    FileSize = converted_email.file_size
    TransferSize = round(FileSize / 1000, 1)
    CreditCalculateData = _CalculateCreditCost(model='ConvertedEmail', transfer_size_KB=TransferSize, billing_info=BillingInfo, request_uid=request.META['data-view-uid'])
    CreditTransferCost = CreditCalculateData['credit_to_charge']
    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Transfer size: {TransferSize} KB")
    LOG_data(request_uid=request.META['data-view-uid'], log_fn=logger.info, text=f"Credits for {UserApiKeyItem.api_key} before data transfer: {CreditsLeft}")
    PredictedBallance = round(CreditsLeft - Decimal.from_float(CreditTransferCost), 1)
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
    UserApiKeyItem.credits = max(0, PredictedBallance)
    UserApiKeyItem.save()
    UserIPAddress = None

    if 'HTTP_X_FORWARDED_FOR' in request.META:
        UserIPAddress = request.META['HTTP_X_FORWARDED_FOR'].split(',')[-1].strip()
    else:
        UserIPAddress = request.META['REMOTE_ADDR']

    _AddApiKeyCreditHistory(
        UserApiKeyItem=UserApiKeyItem,
        data_request_uri=f"{request.META['RAW_URI']} <{os.path.basename(converted_email.file_path)}>",
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

    DownloadLog.objects.create(user=user, file=converted_email, ip_address=UserIPAddress)

    return FileResponse(open(converted_email.file_path, 'rb'), content_type='application/pdf')
