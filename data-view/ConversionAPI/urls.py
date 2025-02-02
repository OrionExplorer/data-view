from django.urls import path
from . import views

urlpatterns = [
    path('email-to-pdf/', views.EmailToPDFView, name='email_to_pdf'),
    path('attachment-to-pdf/', views.AttachmentToPDFView, name='attachment_to_pdf'),
    path('download/<str:download_token>/', views.DownloadPDFView, name='download_pdf'),
]
