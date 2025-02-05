from django.test import TestCase

# Create your tests here.
"""
## INLINE PDF OUTPUT (multipart)
* attachment file:
  * curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@test.docx" https://data-view.eu/api/v1/attachment-to-pdf/?mode=inline_pdf --output downloaded_inline_attachment.pdf
* email file:
  * curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@testmail.eml" https://data-view.eu/api/v1/email-to-pdf/?mode=inline_pdf --output downloaded_inline_email.pdf
* email JSON:
  * curl -X POST "https://data-view.eu/api/v1/email-to-pdf/?mode=inline_pdf" -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -H "Content-Type: application/json" -d '{"subject": "Monthly Report", "sender": "john.doe@example.com", "recipient": "jane.smith@example.com", "body": "Hi Jane, here is the monthly report.", "attachments": [{"filename": "report.docx", "content": "JVBERi0xLjMKJf////8KOSAwIG9iago8PAovVHlwZSAvRXh0R1N0YXRlCi9jYSAxCj4+CmVuZG9iago4IDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMSAwIFIKL01lZGlhQm94IFswIDAgNTk1LjI4MDAyOSA4NDEuODkwMDE1XQovQ29udGVudHMgNiAwIFIKL1Jlc291cmNlcyA3IDAgUgovVXNlclVuaXQgMQo+PgplbmRvYmoKNyAwIG9iago8PAovUHJvY1NldCBbL1BERiAvVGV4dCAvSW1hZ2VCIC9JbWFnZUMgL0ltYWdlSV0KL0V4dEdTdGF0ZSA8PAovR3MxIDkgMCBSCj4+Ci9Gb250IDw8Ci9GMSAxMCAwIFIKL0YyIDExIDAgUgo+Pgo+PgplbmRvYmoKMTMgMCBvYmoKKHJlYWN0LXBkZikKZW5kb2JqCjE0IDAgb2JqCihyZWFjdC1wZGYpCmVuZG9iagoxNSAwIG9iagooRDoyMDI0MDkwNDIwMzEwN1opCmVuZG9iagoxMiAwIG9iago8PAovUHJvZHVjZXIgMTMgMCBSCi9DcmVhdG9yIDE0IDAgUgovQ3JlYXRpb25EYXRlIDE1IDAgUgo+PgplbmRvYmoKMTAgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL0Jhc2VGb250IC9IZWx2ZXRpY2EKL1N1YnR5cGUgL1R5cGUxCi9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nCj4+CmVuZG9iagoxMSAwIG9iago8PAovVHlwZSAvRm9udAovQmFzZUZvbnQgL0hlbHZldGljYS1Cb2xkCi9TdWJ0eXBlIC9UeXBlMQovRW5jb2RpbmcgL1dpbkFuc2lFbmNvZGluZwo+PgplbmRvYmoKNCAwIG9iago8PAo+PgplbmRvYmoKMyAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMSAwIFIKL05hbWVzIDIgMCBSCi9WaWV3ZXJQcmVmZXJlbmNlcyA1IDAgUgo+PgplbmRvYmoKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWzggMCBSXQo+PgplbmRvYmoKMiAwIG9iago8PAovRGVzdHMgPDwKICAvTmFtZXMgWwpdCj4+Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9EaXNwbGF5RG9jVGl0bGUgdHJ1ZQo+PgplbmRvYmoKNiAwIG9iago8PAovTGVuZ3RoIDc2MQovRmlsdGVyIC9GbGF0ZURlY29kZQo+PgpzdHJlYW0KeJztmttqGzEQhu/3KfYFomhGo5EEwRehbaB3KYZelN50Y7eFJJAa+vwdadfx2tX6QKjtrrUya3RYWf/o16c4FtRa0hXIzRMoH7QGWzdP1YukWPVU2WAVeq0xSPZxPTucafoNe10/DpQfUtpUer3LtexwpkmKHtN9mZrqR/W5fq6u7xZQf19U1+9mv382s093t3WzqLQ8SgCOyWnrPRqu9ytaNM/pY/ICfs2qeXUvEYY0hvbeBX1ZhBRfG4Wv7VYFCIpj2cbAU30cxVLYS+8DM/N9O+312auaSs8f0mim8+rLDeFE6m94zuCQSTJf6+nH6v1Uel8+z6S0wXakGZH3Ka2rMqRIy4WbgoH/jkwmCMAK/30QwLdBsCj6zaTGGIlv+4TEe8XsDwoJBOVCvE6hFVdaYVKDyLN2Ult5JyBCbQhnBvJSQQXDO6RuyrXoFbrY7xlON+qsUKu0pv9nSld6BiYOtAjqPHqcgTifHUjYwzw5EwmjAOjEfDQtDICx40PD1pmsTkcK9SFQiALJKxMtNLw1rMHzKk5qDqwnX1WXBFFisQE4AacVlphkEEdRfUQre9RkWstAZxkpcRKMhuMznaesRCZEN0kl8IxdbCgN5v1cNnLGRbkHbchB2Rg3f2pUGTLa6AEEkzB4udccZ0D80M7FQ3Y8GFTwuxy6Ze9b2tWd3Wod8Z6BaFLUvS9ILUgdP1LtIE5RcIqFpkeYg7ynRkHTEBRElw/jsdC00HQ0NKUtPDWRp0ddzxcL1PH+eWocJac7LkAtQB0/UGHL9/0C1ALUNwOVSGZNLg4FqAWo4weqKUA9g7Vq8r8BjQGoFm36TYpNAWoB6viBigWoZ7BWDY4WqKx1ijq6zRAf9zBDBINNBBQI2PrGuQ4GsupfEeCs007LQg+DBx2ASQU88KQDy1KK/0i2sN+ucn7nhi5qNwmdHWjebii05pvWMYRik15IIkN9PFvG6VETpEkg2/aTt5JASWHYtW9sAZrw8OyMMqYv2zH9ARt7NWYKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgMTYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwNzk1IDAwMDAwIG4gCjAwMDAwMDA4NTIgMDAwMDAgbiAKMDAwMDAwMDcwOCAwMDAwMCBuIAowMDAwMDAwNjg3IDAwMDAwIG4gCjAwMDAwMDA4OTkgMDAwMDAgbiAKMDAwMDAwMDk0MiAwMDAwMCBuIAowMDAwMDAwMTg5IDAwMDAwIG4gCjAwMDAwMDAwNTkgMDAwMDAgbiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwNDg2IDAwMDAwIG4gCjAwMDAwMDA1ODQgMDAwMDAgbiAKMDAwMDAwMDQxMCAwMDAwMCBuIAowMDAwMDAwMzE4IDAwMDAwIG4gCjAwMDAwMDAzNDYgMDAwMDAgbiAKMDAwMDAwMDM3NCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDE2Ci9Sb290IDMgMCBSCi9JbmZvIDEyIDAgUgovSUQgWzwwY2EzYTZhODIyMzk5MWU3Zjg0MTViMWIxZTIxYWRmZT4gPDBjYTNhNmE4MjIzOTkxZTdmODQxNWIxYjFlMjFhZGZlPl0KPj4Kc3RhcnR4cmVmCjE3NzUKJSVFT0YK" } ] }' --output downloaded_inline_json_mail.pdf

## BASE64 PDF OUTPUT (json)
* attachment file:
  * curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@test.docx" https://data-view.eu/api/v1/attachment-to-pdf/?mode=base64_pdf --output downloaded_json_attachment.pdf
* email file:
  * curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@testmail.eml" https://data-view.eu/api/v1/email-to-pdf/?mode=base64_pdf --output downloaded_json_email.pdf
* email JSON:
  * curl -X POST "https://data-view.eu/api/v1/email-to-pdf/?mode=base64_pdf" -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -H "Content-Type: application/json" -d '{"subject": "Monthly Report", "sender": "john.doe@example.com", "recipient": "jane.smith@example.com", "body": "Hi Jane, here is the monthly report.", "attachments": [{"filename": "report.docx", "content": "JVBERi0xLjMKJf////8KOSAwIG9iago8PAovVHlwZSAvRXh0R1N0YXRlCi9jYSAxCj4+CmVuZG9iago4IDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMSAwIFIKL01lZGlhQm94IFswIDAgNTk1LjI4MDAyOSA4NDEuODkwMDE1XQovQ29udGVudHMgNiAwIFIKL1Jlc291cmNlcyA3IDAgUgovVXNlclVuaXQgMQo+PgplbmRvYmoKNyAwIG9iago8PAovUHJvY1NldCBbL1BERiAvVGV4dCAvSW1hZ2VCIC9JbWFnZUMgL0ltYWdlSV0KL0V4dEdTdGF0ZSA8PAovR3MxIDkgMCBSCj4+Ci9Gb250IDw8Ci9GMSAxMCAwIFIKL0YyIDExIDAgUgo+Pgo+PgplbmRvYmoKMTMgMCBvYmoKKHJlYWN0LXBkZikKZW5kb2JqCjE0IDAgb2JqCihyZWFjdC1wZGYpCmVuZG9iagoxNSAwIG9iagooRDoyMDI0MDkwNDIwMzEwN1opCmVuZG9iagoxMiAwIG9iago8PAovUHJvZHVjZXIgMTMgMCBSCi9DcmVhdG9yIDE0IDAgUgovQ3JlYXRpb25EYXRlIDE1IDAgUgo+PgplbmRvYmoKMTAgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL0Jhc2VGb250IC9IZWx2ZXRpY2EKL1N1YnR5cGUgL1R5cGUxCi9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nCj4+CmVuZG9iagoxMSAwIG9iago8PAovVHlwZSAvRm9udAovQmFzZUZvbnQgL0hlbHZldGljYS1Cb2xkCi9TdWJ0eXBlIC9UeXBlMQovRW5jb2RpbmcgL1dpbkFuc2lFbmNvZGluZwo+PgplbmRvYmoKNCAwIG9iago8PAo+PgplbmRvYmoKMyAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMSAwIFIKL05hbWVzIDIgMCBSCi9WaWV3ZXJQcmVmZXJlbmNlcyA1IDAgUgo+PgplbmRvYmoKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWzggMCBSXQo+PgplbmRvYmoKMiAwIG9iago8PAovRGVzdHMgPDwKICAvTmFtZXMgWwpdCj4+Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9EaXNwbGF5RG9jVGl0bGUgdHJ1ZQo+PgplbmRvYmoKNiAwIG9iago8PAovTGVuZ3RoIDc2MQovRmlsdGVyIC9GbGF0ZURlY29kZQo+PgpzdHJlYW0KeJztmttqGzEQhu/3KfYFomhGo5EEwRehbaB3KYZelN50Y7eFJJAa+vwdadfx2tX6QKjtrrUya3RYWf/o16c4FtRa0hXIzRMoH7QGWzdP1YukWPVU2WAVeq0xSPZxPTucafoNe10/DpQfUtpUer3LtexwpkmKHtN9mZrqR/W5fq6u7xZQf19U1+9mv382s093t3WzqLQ8SgCOyWnrPRqu9ytaNM/pY/ICfs2qeXUvEYY0hvbeBX1ZhBRfG4Wv7VYFCIpj2cbAU30cxVLYS+8DM/N9O+312auaSs8f0mim8+rLDeFE6m94zuCQSTJf6+nH6v1Uel8+z6S0wXakGZH3Ka2rMqRIy4WbgoH/jkwmCMAK/30QwLdBsCj6zaTGGIlv+4TEe8XsDwoJBOVCvE6hFVdaYVKDyLN2Ult5JyBCbQhnBvJSQQXDO6RuyrXoFbrY7xlON+qsUKu0pv9nSld6BiYOtAjqPHqcgTifHUjYwzw5EwmjAOjEfDQtDICx40PD1pmsTkcK9SFQiALJKxMtNLw1rMHzKk5qDqwnX1WXBFFisQE4AacVlphkEEdRfUQre9RkWstAZxkpcRKMhuMznaesRCZEN0kl8IxdbCgN5v1cNnLGRbkHbchB2Rg3f2pUGTLa6AEEkzB4udccZ0D80M7FQ3Y8GFTwuxy6Ze9b2tWd3Wod8Z6BaFLUvS9ILUgdP1LtIE5RcIqFpkeYg7ynRkHTEBRElw/jsdC00HQ0NKUtPDWRp0ddzxcL1PH+eWocJac7LkAtQB0/UGHL9/0C1ALUNwOVSGZNLg4FqAWo4weqKUA9g7Vq8r8BjQGoFm36TYpNAWoB6viBigWoZ7BWDY4WqKx1ijq6zRAf9zBDBINNBBQI2PrGuQ4GsupfEeCs007LQg+DBx2ASQU88KQDy1KK/0i2sN+ucn7nhi5qNwmdHWjebii05pvWMYRik15IIkN9PFvG6VETpEkg2/aTt5JASWHYtW9sAZrw8OyMMqYv2zH9ARt7NWYKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgMTYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwNzk1IDAwMDAwIG4gCjAwMDAwMDA4NTIgMDAwMDAgbiAKMDAwMDAwMDcwOCAwMDAwMCBuIAowMDAwMDAwNjg3IDAwMDAwIG4gCjAwMDAwMDA4OTkgMDAwMDAgbiAKMDAwMDAwMDk0MiAwMDAwMCBuIAowMDAwMDAwMTg5IDAwMDAwIG4gCjAwMDAwMDAwNTkgMDAwMDAgbiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwNDg2IDAwMDAwIG4gCjAwMDAwMDA1ODQgMDAwMDAgbiAKMDAwMDAwMDQxMCAwMDAwMCBuIAowMDAwMDAwMzE4IDAwMDAwIG4gCjAwMDAwMDAzNDYgMDAwMDAgbiAKMDAwMDAwMDM3NCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDE2Ci9Sb290IDMgMCBSCi9JbmZvIDEyIDAgUgovSUQgWzwwY2EzYTZhODIyMzk5MWU3Zjg0MTViMWIxZTIxYWRmZT4gPDBjYTNhNmE4MjIzOTkxZTdmODQxNWIxYjFlMjFhZGZlPl0KPj4Kc3RhcnR4cmVmCjE3NzUKJSVFT0YK" } ] }' --output downloaded_json_mail.json


"""


"""
$base64Content = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\\Users\\Marcin\\Downloads\\test.docx"))
$jsonBody = @{filename = "test.docx" content  = $base64Content } | ConvertTo-Json -Depth 3
$response = Invoke-RestMethod -Uri "https://data-view.eu/api/v1/attachment-to-pdf/" ` -Method POST ` -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } ` -ContentType "application/json" ` -Body $jsonBody
$response

# 5️⃣ Pobranie przekonwertowanego PDF
Invoke-WebRequest -Uri "https://data-view.eu/api/v1/download/$response.download_link" `
                  -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } `
                  -OutFile "converted_test.pdf"
"""


"""
flake8 --ignore=E501,F401,E402,E902 .
"""


from django.test import TestCase, Client
from django.urls import reverse
from django.test.utils import setup_test_environment
from API.models import ApiKey
import base64

class DataViewAPITest(TestCase):
    def setUp(self):
        self.client = Client()
        self.api_key = "ghijkl-654321-ghijkl-654321"
        self.headers = {"x-api-key": self.api_key}

        self.email_data = {
            "subject": "Test Email",
            "sender": "test@example.com",
            "recipient": "recipient@example.com",
            "body": "This is a test email."
        }

        self.attachment_data = {
            "filename": "test.txt",
            "content": base64.b64encode(b"This is a test attachment.").decode('utf-8')
        }

    def test_email_to_pdf(self):
        modes = ["file_id", "inline_pdf", "base64_pdf"]
        for mode in modes:
            response = self.client.post(f"/api/v1/email-to-pdf/?mode={mode}", 
                                        data=self.email_data, 
                                        content_type="application/json", 
                                        headers=self.headers)
            self.assertEqual(response.status_code, 200, f"Failed for mode={mode}")

    def test_attachment_to_pdf(self):
        modes = ["file_id", "inline_pdf", "base64_pdf"]
        for mode in modes:
            response = self.client.post(f"/api/v1/attachment-to-pdf/?mode={mode}", 
                                        data=self.attachment_data, 
                                        content_type="application/json", 
                                        headers=self.headers)
            self.assertEqual(response.status_code, 200, f"Failed for mode={mode}")

    def test_download_converted_file(self):
        # First, create a file to download
        response = self.client.post("/api/v1/email-to-pdf/?mode=file_id", 
                                    data=self.email_data, 
                                    content_type="application/json", 
                                    headers=self.headers)
        self.assertEqual(response.status_code, 200)
        file_id = response.json().get("file_id")

        # Now test downloading the file
        download_response = self.client.get(f"/api/v1/download/{file_id}/", headers=self.headers)
        self.assertEqual(download_response.status_code, 200)

    def test_invalid_api_key(self):
        invalid_headers = {"HTTP_X_API_KEY": "invalid_api_key"}
        response = self.client.post("/api/v1/email-to-pdf/", 
                                    data=self.email_data, 
                                    content_type="application/json", 
                                    **invalid_headers)
        self.assertEqual(response.status_code, 403)

    def test_missing_api_key(self):
        response = self.client.post("/api/v1/email-to-pdf/", 
                                    data=self.email_data, 
                                    content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_insufficient_credits(self):
        # Simulate insufficient credits scenario
        # This would require modifying the API key credits in the test DB setup
        self.api_key = "abcdef-123456-abcdef-123456"
        low_credit_headers = {"HTTP_X_API_KEY": self.api_key}

        response = self.client.post("/api/v1/email-to-pdf/", 
                                    data=self.email_data, 
                                    content_type="application/json", 
                                    **low_credit_headers)
        self.assertEqual(response.status_code, 402)
