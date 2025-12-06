"""
URL configuration for translation app.
"""
from django.urls import path
from . import views

app_name = 'translation'

urlpatterns = [
    path('translate-text', views.translate_text, name='translate-text'),
    path('translate-document', views.translate_document, name='translate-document'),
    path('document-status/<str:document_id>', views.document_status, name='document-status'),
    path('download/<str:document_id>', views.download_document, name='download-document'),
    path('download-file/<str:filename>', views.download_file, name='download-file'),

    # Documents list endpoint (replaces Custom.MT CLOUDSTORAGE_API_URL)
    path('documents', views.list_documents, name='list-documents'),

    # Proxy endpoints to Lara SDK
    path('memories', views.get_lara_memories, name='lara-memories'),
    path('glossaries', views.get_lara_glossaries, name='lara-glossaries'),
]
