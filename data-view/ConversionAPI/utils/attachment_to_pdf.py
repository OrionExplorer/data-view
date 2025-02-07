import requests
import os
import random
import base64
from django.conf import settings
from .system import get_system_setting
from API.views import LOG_data
from ConversionAPI.utils.system import GetRandomLibreOfficeInstance


SUPPORTED_FORMATS = {
    '.doc': 'application/msword',
    '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    '.dot': 'application/msword',
    '.dotx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.template',
    '.odt': 'application/vnd.oasis.opendocument.text',
    '.ott': 'application/vnd.oasis.opendocument.text-template',
    '.rtf': 'application/rtf',
    '.txt': 'text/plain',
    '.html': 'text/html',
    '.htm': 'text/html',
    '.xls': 'application/vnd.ms-excel',
    '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    '.xlsm': 'application/vnd.ms-excel.sheet.macroEnabled.12',
    '.xlt': 'application/vnd.ms-excel',
    '.xltx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.template',
    '.ods': 'application/vnd.oasis.opendocument.spreadsheet',
    '.ots': 'application/vnd.oasis.opendocument.spreadsheet-template',
    '.csv': 'text/csv',
    '.tsv': 'text/tab-separated-values',
    '.ppt': 'application/vnd.ms-powerpoint',
    '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    '.pps': 'application/vnd.ms-powerpoint',
    '.ppsx': 'application/vnd.openxmlformats-officedocument.presentationml.slideshow',
    '.odp': 'application/vnd.oasis.opendocument.presentation',
    '.otp': 'application/vnd.oasis.opendocument.presentation-template'
}


def _InternalIdentifierGenerator(length=32):
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in range(length))


def is_file_format_valid(file):
    MAGIC_NUMBERS = {
        'doc': [b'\xD0\xCF\x11\xE0'],  # Stary format DOC (OLE Compound)
        'docx': [b'\x50\x4B\x03\x04'],  # Nowoczesny DOCX (ZIP)
        'xls': [b'\xD0\xCF\x11\xE0'],   # Stary Excel (OLE)
        'xlsx': [b'\x50\x4B\x03\x04'],  # Nowoczesny XLSX (ZIP)
        'ppt': [b'\xD0\xCF\x11\xE0'],   # Stary PPT
        'pptx': [b'\x50\x4B\x03\x04'],  # Nowoczesny PPTX
        'pdf': [b'\x25\x50\x44\x46'],   # PDF (%PDF)
        'rtf': [b'\x7B\x5C\x72\x74\x66'],  # RTF ({\rtf)
        'odt': [b'\x50\x4B\x03\x04'],   # ODT (ZIP)
        'ods': [b'\x50\x4B\x03\x04'],   # ODS (ZIP)
        'odp': [b'\x50\x4B\x03\x04'],   # ODP (ZIP)
    }

    # Odczytanie pierwszych 8 bajtów (wystarczające dla większości formatów)
    file.seek(0)
    file_header = file.read(8)
    file.seek(0)  # Cofnięcie wskaźnika pliku po odczycie

    file_extension = os.path.splitext(file.name)[1].lower().lstrip('.')

    # Jeśli rozszerzenie nie jest na liście – pomiń sprawdzanie
    if file_extension not in MAGIC_NUMBERS:
        return True  # Nie ma magic number, uznajemy za prawidłowe (np. CSV, TXT)

    # Sprawdzenie, czy magic number się zgadza
    valid_magic_numbers = MAGIC_NUMBERS[file_extension]
    for magic in valid_magic_numbers:
        if file_header.startswith(magic):
            return True

    return False


def ConvertAttachmentToPDF(file=None, content=None, filename=None, api_key=None):
    try:
        LibreOfficeInstance = None

        try:
            LibreOfficeInstance = GetRandomLibreOfficeInstance()
        except RuntimeError as e:
            return {
                'status': 503,
                'data': {
                    'error': 'Service unavailable'
                }
            }

        if LibreOfficeInstance is None:
            return {
                'status': 503,
                'data': {
                    'error': 'Service unavailable'
                }
            }

        if file:
            file_extension = os.path.splitext(file.name)[1].lower()
            expected_mime_type = SUPPORTED_FORMATS.get(file_extension)

            if not expected_mime_type:
                LOG_data(text=f"Unsupported file format: {file_extension}")
                return {
                    'status': 400,
                    'data': {
                        'error': f"Unsupported file format: {file_extension}"
                    }
                }

            actual_mime_type = file.content_type
            if actual_mime_type != expected_mime_type:
                LOG_data(text=f"Invalid MIME-Type for {file.name}: expected {expected_mime_type}, got {actual_mime_type}")
                # return None

            if get_system_setting('CHECK_MAGIC_NUMBER', default=True) and not is_file_format_valid(file):
                LOG_data(text=f"Magic number mismatch for file: {file.name}")
                return {
                    'status': 400,
                    'data': {
                        'error': f"Magic number mismatch for file: {file.name}"
                    }
                }

            max_file_size = get_system_setting('MAX_FILE_SIZE', default=50) * 1024 * 1024
            if file.size > max_file_size:
                LOG_data(text=f"File {file.name} exceeds the maximum allowed size ({max_file_size} MB).")
                return {
                    'status': 400,
                    'data': {
                        'error': f"File {file.name} exceeds the maximum allowed size ({max_file_size} MB)."
                    }
                }

            LOG_data(text=f"LibreOffice instance: {LibreOfficeInstance}.")
            response = requests.post(
                f'{LibreOfficeInstance}/convert',
                files={'file': (file.name, file)}
            )
        elif content and filename:
            LOG_data(text=f"LibreOffice instance: {LibreOfficeInstance}.")
            response = requests.post(
                f'{LibreOfficeInstance}/convert',
                json={'filename': filename, 'content': content}
            )
        else:
            return {
                'status': 500,
                'data': {
                    'error': "No file or content specified.",
                }
            }

        if response.status_code == 200:
            data = response.json()
            LOG_data(text=f"[ConvertAttachmentToPDF] response from converter: {data}")
            pdf_path = data.get('pdf_path')
            file_size = data.get('file_size')
            return {
                'status': 200,
                'data': {
                    'pdf_path': pdf_path,
                    'file_size': file_size
                }
            }
        else:
            LOG_data(text=f"Conversion failed: {response.text}")
            return {
                'status': 500,
                'error': f"Conversion failed: {response.text}"
            }
    except requests.exceptions.RequestException as e:
        LOG_data(text=f"Error connecting to LibreOffice API: {e}")
        return {
            'status': 500,
            'data': {
                'error': f"Error connecting to LibreOffice API."
            }
        }
