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