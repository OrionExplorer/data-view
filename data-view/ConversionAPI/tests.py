from django.test import TestCase

# Create your tests here.
"""
curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@test.docx" https://data-view.eu/api/attachment-to-pdf/



$base64Content = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\\Users\\Marcin\\Downloads\\test.docx"))
$jsonBody = @{filename = "test.docx" content  = $base64Content } | ConvertTo-Json -Depth 3
$response = Invoke-RestMethod -Uri "https://data-view.eu/api/attachment-to-pdf/" ` -Method POST ` -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } ` -ContentType "application/json" ` -Body $jsonBody
$response

# 5️⃣ Pobranie przekonwertowanego PDF
Invoke-WebRequest -Uri "https://data-view.eu/api/download/$response.download_link" `
                  -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } `
                  -OutFile "converted_test.pdf"
"""


"""
curl -X POST "https://data-view.eu/api/email-to-pdf/" -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -H "Content-Type: application/json" -d '{"subject": "Monthly Report", "sender": "john.doe@example.com", "recipient": "jane.smith@example.com", "body": "Hi Jane, here is the monthly report.", "attachments": [{"filename": "report.docx", "content": "JVBERi0xLjMKJf////8KOSAwIG9iago8PAovVHlwZSAvRXh0R1N0YXRlCi9jYSAxCj4+CmVuZG9iago4IDAgb2JqCjw8Ci9UeXBlIC9QYWdlCi9QYXJlbnQgMSAwIFIKL01lZGlhQm94IFswIDAgNTk1LjI4MDAyOSA4NDEuODkwMDE1XQovQ29udGVudHMgNiAwIFIKL1Jlc291cmNlcyA3IDAgUgovVXNlclVuaXQgMQo+PgplbmRvYmoKNyAwIG9iago8PAovUHJvY1NldCBbL1BERiAvVGV4dCAvSW1hZ2VCIC9JbWFnZUMgL0ltYWdlSV0KL0V4dEdTdGF0ZSA8PAovR3MxIDkgMCBSCj4+Ci9Gb250IDw8Ci9GMSAxMCAwIFIKL0YyIDExIDAgUgo+Pgo+PgplbmRvYmoKMTMgMCBvYmoKKHJlYWN0LXBkZikKZW5kb2JqCjE0IDAgb2JqCihyZWFjdC1wZGYpCmVuZG9iagoxNSAwIG9iagooRDoyMDI0MDkwNDIwMzEwN1opCmVuZG9iagoxMiAwIG9iago8PAovUHJvZHVjZXIgMTMgMCBSCi9DcmVhdG9yIDE0IDAgUgovQ3JlYXRpb25EYXRlIDE1IDAgUgo+PgplbmRvYmoKMTAgMCBvYmoKPDwKL1R5cGUgL0ZvbnQKL0Jhc2VGb250IC9IZWx2ZXRpY2EKL1N1YnR5cGUgL1R5cGUxCi9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nCj4+CmVuZG9iagoxMSAwIG9iago8PAovVHlwZSAvRm9udAovQmFzZUZvbnQgL0hlbHZldGljYS1Cb2xkCi9TdWJ0eXBlIC9UeXBlMQovRW5jb2RpbmcgL1dpbkFuc2lFbmNvZGluZwo+PgplbmRvYmoKNCAwIG9iago8PAo+PgplbmRvYmoKMyAwIG9iago8PAovVHlwZSAvQ2F0YWxvZwovUGFnZXMgMSAwIFIKL05hbWVzIDIgMCBSCi9WaWV3ZXJQcmVmZXJlbmNlcyA1IDAgUgo+PgplbmRvYmoKMSAwIG9iago8PAovVHlwZSAvUGFnZXMKL0NvdW50IDEKL0tpZHMgWzggMCBSXQo+PgplbmRvYmoKMiAwIG9iago8PAovRGVzdHMgPDwKICAvTmFtZXMgWwpdCj4+Cj4+CmVuZG9iago1IDAgb2JqCjw8Ci9EaXNwbGF5RG9jVGl0bGUgdHJ1ZQo+PgplbmRvYmoKNiAwIG9iago8PAovTGVuZ3RoIDc2MQovRmlsdGVyIC9GbGF0ZURlY29kZQo+PgpzdHJlYW0KeJztmttqGzEQhu/3KfYFomhGo5EEwRehbaB3KYZelN50Y7eFJJAa+vwdadfx2tX6QKjtrrUya3RYWf/o16c4FtRa0hXIzRMoH7QGWzdP1YukWPVU2WAVeq0xSPZxPTucafoNe10/DpQfUtpUer3LtexwpkmKHtN9mZrqR/W5fq6u7xZQf19U1+9mv382s093t3WzqLQ8SgCOyWnrPRqu9ytaNM/pY/ICfs2qeXUvEYY0hvbeBX1ZhBRfG4Wv7VYFCIpj2cbAU30cxVLYS+8DM/N9O+312auaSs8f0mim8+rLDeFE6m94zuCQSTJf6+nH6v1Uel8+z6S0wXakGZH3Ka2rMqRIy4WbgoH/jkwmCMAK/30QwLdBsCj6zaTGGIlv+4TEe8XsDwoJBOVCvE6hFVdaYVKDyLN2Ult5JyBCbQhnBvJSQQXDO6RuyrXoFbrY7xlON+qsUKu0pv9nSld6BiYOtAjqPHqcgTifHUjYwzw5EwmjAOjEfDQtDICx40PD1pmsTkcK9SFQiALJKxMtNLw1rMHzKk5qDqwnX1WXBFFisQE4AacVlphkEEdRfUQre9RkWstAZxkpcRKMhuMznaesRCZEN0kl8IxdbCgN5v1cNnLGRbkHbchB2Rg3f2pUGTLa6AEEkzB4udccZ0D80M7FQ3Y8GFTwuxy6Ze9b2tWd3Wod8Z6BaFLUvS9ILUgdP1LtIE5RcIqFpkeYg7ynRkHTEBRElw/jsdC00HQ0NKUtPDWRp0ddzxcL1PH+eWocJac7LkAtQB0/UGHL9/0C1ALUNwOVSGZNLg4FqAWo4weqKUA9g7Vq8r8BjQGoFm36TYpNAWoB6viBigWoZ7BWDY4WqKx1ijq6zRAf9zBDBINNBBQI2PrGuQ4GsupfEeCs007LQg+DBx2ASQU88KQDy1KK/0i2sN+ucn7nhi5qNwmdHWjebii05pvWMYRik15IIkN9PFvG6VETpEkg2/aTt5JASWHYtW9sAZrw8OyMMqYv2zH9ARt7NWYKZW5kc3RyZWFtCmVuZG9iagp4cmVmCjAgMTYKMDAwMDAwMDAwMCA2NTUzNSBmIAowMDAwMDAwNzk1IDAwMDAwIG4gCjAwMDAwMDA4NTIgMDAwMDAgbiAKMDAwMDAwMDcwOCAwMDAwMCBuIAowMDAwMDAwNjg3IDAwMDAwIG4gCjAwMDAwMDA4OTkgMDAwMDAgbiAKMDAwMDAwMDk0MiAwMDAwMCBuIAowMDAwMDAwMTg5IDAwMDAwIG4gCjAwMDAwMDAwNTkgMDAwMDAgbiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwNDg2IDAwMDAwIG4gCjAwMDAwMDA1ODQgMDAwMDAgbiAKMDAwMDAwMDQxMCAwMDAwMCBuIAowMDAwMDAwMzE4IDAwMDAwIG4gCjAwMDAwMDAzNDYgMDAwMDAgbiAKMDAwMDAwMDM3NCAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9TaXplIDE2Ci9Sb290IDMgMCBSCi9JbmZvIDEyIDAgUgovSUQgWzwwY2EzYTZhODIyMzk5MWU3Zjg0MTViMWIxZTIxYWRmZT4gPDBjYTNhNmE4MjIzOTkxZTdmODQxNWIxYjFlMjFhZGZlPl0KPj4Kc3RhcnR4cmVmCjE3NzUKJSVFT0YK" } ] }'
"""