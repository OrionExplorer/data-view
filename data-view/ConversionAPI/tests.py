from django.test import TestCase

# Create your tests here.
"""
curl -X POST -H "x-api-key: 7tumuz-t3xlhg-mjonnx-crubl1" -F "file=@test.docx" https://data-view.eu/api/attachment-to-pdf/



# 1️⃣ Zakodowanie pliku do Base64
$base64Content = [Convert]::ToBase64String([IO.File]::ReadAllBytes("C:\\Users\\orion\\Downloads\\test.docx"))

# 2️⃣ Utworzenie JSON
$jsonBody = @{
    filename = "test.docx"
    content  = $base64Content
} | ConvertTo-Json -Depth 3

# 3️⃣ Wysłanie żądania POST do API
$response = Invoke-RestMethod -Uri "https://data-view.eu/api/attachment-to-pdf/" `
                              -Method POST `
                              -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } `
                              -ContentType "application/json" `
                              -Body $jsonBody

# 4️⃣ Wyświetlenie odpowiedzi
$response

# 5️⃣ Pobranie przekonwertowanego PDF
Invoke-WebRequest -Uri "https://data-view.eu/api/download/$response.download_link" `
                  -Headers @{ "x-api-key" = "7tumuz-t3xlhg-mjonnx-crubl1" } `
                  -OutFile "converted_test.pdf"
"""