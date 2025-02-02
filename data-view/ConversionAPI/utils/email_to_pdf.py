import email
from email import policy
from bs4 import BeautifulSoup
from weasyprint import HTML
import os
import random
import base64
import requests


def _InternalIdentifierGenerator(length=32):
    return ''.join(random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for _ in range(length))


def FetchExternalImage(url, max_size=10 * 1024 * 1024):  # 10 MB = 10 * 1024 * 1024 bajtów
    try:
        response = requests.get(url, stream=True, timeout=5)
        response.raise_for_status()

        content_type = response.headers.get('Content-Type', '')
        content_length = response.headers.get('Content-Length')

        # 1️⃣ Jeśli Content-Length jest dostępny
        if content_length:
            content_length = int(content_length)

            if content_length > max_size:
                return None  # Odrzucenie pliku większego niż 10 MB

            # Pobranie całego pliku, bo rozmiar jest bezpieczny
            image_data = response.content

        else:
            # 2️⃣ Jeśli brak Content-Length, pobieramy dane fragmentami
            image_data = b""
            for chunk in response.iter_content(chunk_size=8192):
                image_data += chunk
                if len(image_data) > max_size:
                    return None  # Przerwanie pobierania, gdy przekroczymy 10 MB

        # 3️⃣ Sprawdzenie, czy to faktycznie obraz
        if not content_type.startswith('image/'):
            return None  # Odrzucenie, jeśli to nie jest obraz

        # Konwersja do Base64
        base64_image = base64.b64encode(image_data).decode('utf-8')
        return f"data:{content_type};base64,{base64_image}"

    except (requests.RequestException, ValueError):
        return None  # Bezpieczne zakończenie w przypadku błędów


def ConvertEmailToPDF(file):
    msg = email.message_from_binary_file(file, policy=policy.default)
    subject = msg.get('subject', 'No Subject')
    sender = msg.get('from', 'Unknown Sender')
    recipient = msg.get('to', 'Unknown Recipient')
    date = msg.get('date', 'Unknown Date')

    body_html = None
    body_text = None
    links = []
    inline_images = {}

    # 1️⃣ Przetwarzanie części wiadomości
    for part in msg.walk():
        content_type = part.get_content_type()
        content_id = part.get('Content-ID')

        if content_type == "text/html" and body_html is None:
            body_html = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'))

        elif content_type == "text/plain" and body_text is None:
            body_text = part.get_payload(decode=True).decode(part.get_content_charset('utf-8'))

        elif content_id and content_type.startswith('image/'):
            image_data = part.get_payload(decode=True)
            base64_image = base64.b64encode(image_data).decode('utf-8')
            content_id_clean = content_id.strip('<>')
            inline_images[content_id_clean] = f"data:{content_type};base64,{base64_image}"

    # 2️⃣ Przetwarzanie HTML
    if body_html:
        soup = BeautifulSoup(body_html, 'html.parser')

        # Zastąpienie klikalnych linków
        for a in soup.find_all('a', href=True):
            links.append(a['href'])
            a.replace_with(a.text)

        # Obsługa obrazów (inline + zewnętrzne)
        for img in soup.find_all('img', src=True):
            src = img['src']

            # 1. Obrazki inline (cid)
            if src.startswith('cid:'):
                cid = src[4:]
                if cid in inline_images:
                    img['src'] = inline_images[cid]

            # 2. Obrazki zewnętrzne (http/https)
            elif src.startswith('http://') or src.startswith('https://'):
                embedded_image = FetchExternalImage(src)
                if embedded_image:
                    img['src'] = embedded_image
                else:
                    img.decompose()  # Usunięcie obrazka, jeśli przekroczono limit lub wystąpił błąd

        body = str(soup)
    else:
        body = f"<pre>{body_text}</pre>"

    # 3️⃣ Dodanie linków na końcu
    if links:
        body += "<hr><strong>Links from the email:</strong><br>" + "<br>".join(links)

    # 4️⃣ Generowanie PDF
    unique_id = _InternalIdentifierGenerator(12)
    output_dir = "media/conversion-api/emails"
    os.makedirs(output_dir, exist_ok=True)
    output_file = f"{output_dir}/{unique_id}.pdf"

    html_content = f"""
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                font-size: 14px;
            }}
            img {{
                max-width: 100%;
                height: auto;
            }}
            pre {{
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <h2>{subject}</h2>
        <p><strong>From:</strong> {sender}</p>
        <p><strong>To:</strong> {recipient}</p>
        <p><strong>Date:</strong> {date}</p>
        <hr>
        {body}
    </body>
    </html>
    """

    HTML(string=html_content).write_pdf(output_file)

    file_size = os.path.getsize(output_file)

    return output_file, file_size
