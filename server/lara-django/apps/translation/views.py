"""
Views for Translation API endpoints.
"""
import os
import json
import logging
from django.http import FileResponse, Http404
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response

from .models import DocumentTranslation
from .serializers import (
    TranslateTextRequestSerializer, 
    TranslateDocumentRequestSerializer,
    DocumentTranslationSerializer
)
from .services.lara_client import LaraClient
from .services.language_utils import normalize_language_code
from .services.html_cleaner import clean_html_for_lara
from apps.domains.models import Domain

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health_check(request):
    """
    GET /health
    Health check endpoint.
    """
    return Response({'status': 'ok', 'service': 'lara-django'})


@csrf_exempt
@api_view(['POST'])
def translate_text(request):
    """
    POST /api/lara/translate-text
    Translates text.
    """
    serializer = TranslateTextRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    try:
        # Initialize client with credentials provided in request
        client = LaraClient(data['accessKeyId'], data['accessKeySecret'])

        # Normalize languages
        source_lang = normalize_language_code(data.get('source'))
        target_lang = normalize_language_code(data['target'])

        # Clean HTML si fixText est True (défaut: False)
        text = data['text']
        if data.get('fixText', False):
            logger.info(f"[LARA] fixText=True, texte nettoyé avant traduction")
            text = clean_html_for_lara(text)
        else:
            logger.info(f"[LARA] fixText=False, texte envoyé tel quel")
        
        # Préparer les options pour le SDK Python
        options = {}
        if source_lang:
            options['source'] = source_lang
        if target_lang:
            options['target'] = target_lang
        if data.get('domain'):
            options['domain'] = data.get('domain')
        if data.get('style'):
            options['style'] = data.get('style')
        if data.get('instructions'):
            options['instructions'] = data.get('instructions')
        if data.get('adaptTo'):
            options['adaptTo'] = data.get('adaptTo')
        if data.get('glossaries'):
            options['glossaries'] = data.get('glossaries')

        # Appel du SDK Python
        result = client.translate_text(
            text=text,
            **options
        )
        # Correction : retourner un dict sérialisable
        if hasattr(result, 'to_dict'):
            return Response(result.to_dict())
        elif hasattr(result, '__dict__'):
            return Response(result.__dict__)
        else:
            return Response(result)
        
    except Exception as e:
        logger.error(f"Translation error: {str(e)}")
        return Response(
            {'error': str(e), 'details': 'Translation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@csrf_exempt
@api_view(['POST'])
@parser_classes([MultiPartParser, FormParser])
def translate_document(request):
    """
    POST /api/lara/translate-document
    Translates a document asynchronously using Celery.

    Supports optional parameters:
    - adaptTo: Translation memory ID(s) - comma-separated or JSON array
    - glossaries: Glossary ID(s) - comma-separated or JSON array

    Returns immediately with document ID for status polling.
    """
    from .tasks import process_document_translation

    serializer = TranslateDocumentRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    file_obj = data['file']

    try:
        # Parse adaptTo and glossaries (can be comma-separated string or JSON)
        adapt_to = None
        glossaries = None

        if data.get('adaptTo'):
            adapt_to_raw = data.get('adaptTo')
            if adapt_to_raw.startswith('['):
                adapt_to = json.loads(adapt_to_raw)
            else:
                adapt_to = [x.strip() for x in adapt_to_raw.split(',') if x.strip()]

        if data.get('glossaries'):
            glossaries_raw = data.get('glossaries')
            if glossaries_raw.startswith('['):
                glossaries = json.loads(glossaries_raw)
            else:
                glossaries = [x.strip() for x in glossaries_raw.split(',') if x.strip()]

        # Get domain name from request (sent by Lexa), fallback to DB lookup
        domain_id = data.get('domainId')
        domain_name = data.get('domain', '')  # Domain name sent directly by Lexa

        # If domain name not provided but domainId is, try to look it up (fallback)
        if not domain_name and domain_id:
            try:
                domain = Domain.objects.get(id=domain_id)
                domain_name = domain.name  # English name
                logger.info(f"[TRANSLATE_DOC] Domain found via DB lookup: id={domain_id}, name={domain_name}")
            except Domain.DoesNotExist:
                logger.warning(f"[TRANSLATE_DOC] Domain not found for id={domain_id}")

        if domain_name:
            logger.info(f"[TRANSLATE_DOC] Using domain: {domain_name} (id: {domain_id})")

        logger.info(f"[TRANSLATE_DOC] File: {file_obj.name}, domain: {domain_name}, adaptTo: {adapt_to}, glossaries: {glossaries}")

        # Get document statistics from Lexa
        words_count = data.get('wordsCount')
        characters_count = data.get('charactersCount')

        # Build payload for tracking (excluding file content and credentials)
        payload_data = {
            'filename': file_obj.name,
            'source': data.get('source', ''),
            'target': data['target'],
            'domainId': domain_id,
            'domain': domain_name,
            'templateId': data.get('templateId', ''),
            'templateName': data.get('templateName', ''),
            'adaptTo': adapt_to,
            'glossaries': glossaries,
            'userToken': data.get('userToken', ''),
            'wordsCount': words_count,
            'charactersCount': characters_count,
        }

        # Create tracking record with pending status
        doc_translation = DocumentTranslation.objects.create(
            filename=file_obj.name,
            source_language=normalize_language_code(data.get('source')),
            target_language=normalize_language_code(data['target']),
            original_file=file_obj,
            status='pending',  # Will be updated to 'processing' by Celery task
            # Store template info if available
            domain=domain_name,  # English domain name retrieved from domainId
            template_id=data.get('templateId', ''),
            template_name=data.get('templateName', ''),
            translation_memory_id=adapt_to[0] if adapt_to else '',
            glossary_id=glossaries[0] if glossaries else '',
            # User identification from Lexa
            user_uuid=data.get('userToken', ''),
            # Document statistics from Lexa
            words_count=words_count,
            characters_count=characters_count,
            # Request/Response tracking
            payload=json.dumps(payload_data, ensure_ascii=False),
            translation_started_at=timezone.now(),
        )

        logger.info(f"[TRANSLATE_DOC] Created DocumentTranslation: {doc_translation.id}")

        # Launch Celery task for async translation
        process_document_translation.delay(
            str(doc_translation.id),
            data['accessKeyId'],
            data['accessKeySecret'],
            adapt_to=adapt_to,
            glossaries=glossaries
        )

        logger.info(f"[TRANSLATE_DOC] Celery task launched for document: {doc_translation.id}")

        # Return immediately with pending status
        return Response({
            'id': str(doc_translation.id),
            'status': 'pending',
            'filename': doc_translation.filename,
            'source_language': doc_translation.source_language,
            'target_language': doc_translation.target_language,
            'downloadUrl': None,
            'message': 'Document queued for translation. Poll /document-status/{id} for updates.'
        })

    except Exception as e:
        logger.error(f"Document translation error: {str(e)}")
        return Response(
            {'error': str(e), 'details': 'Document translation failed'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def document_status(request, document_id):
    """
    GET /api/lara/document-status/:documentId
    Gets status of a document translation.
    """
    try:
        # Try to find by internal UUID first
        try:
            doc = DocumentTranslation.objects.get(id=document_id)
            
            # If still processing, check with Lara API (if we had a real client)
            # For now return local status
            
            return Response({
                'id': str(doc.id),
                'status': doc.status,
                'filename': doc.filename,
                'downloadUrl': f"/lara-django/api/lara/download/{doc.id}" if doc.status == 'translated' else None
            })
            
        except DocumentTranslation.DoesNotExist:
            # If not found locally, maybe it's a Lara ID directly?
            # For now return 404
            return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def download_document(request, document_id):
    """
    GET /api/lara/download/:documentId
    Downloads a translated document.
    """
    try:
        doc = DocumentTranslation.objects.get(id=document_id)
        
        if not doc.translated_file:
            return Response({'error': 'Translation not ready or file missing'}, status=status.HTTP_404_NOT_FOUND)
            
        return FileResponse(doc.translated_file.open(), as_attachment=True, filename=f"translated_{doc.filename}")
        
    except DocumentTranslation.DoesNotExist:
        return Response({'error': 'Document not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def download_file(request, filename):
    """
    GET /api/lara/download-file/:filename
    Downloads a specific file (legacy endpoint).
    """
    # Security risk: validate filename to prevent directory traversal
    if '..' in filename or filename.startswith('/'):
        return Response({'error': 'Invalid filename'}, status=status.HTTP_400_BAD_REQUEST)
        
    file_path = os.path.join(settings.MEDIA_ROOT, 'uploads', 'translated', filename)
    
    if os.path.exists(file_path):
        return FileResponse(open(file_path, 'rb'), as_attachment=True, filename=filename)
    else:
        return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def get_lara_memories(request):
    """
    GET /api/lara/memories
    Proxy to Lara SDK memories.
    """
    # This endpoint usually requires credentials too, but GET request params?
    # Or maybe it uses env vars? Node.js server.js uses env vars if not passed?
    # Let's check if we can get credentials from headers or query params
    
    access_key_id = request.query_params.get('accessKeyId') or settings.LARA_ACCESS_KEY_ID
    access_key_secret = request.query_params.get('accessKeySecret') or settings.LARA_ACCESS_KEY_SECRET
    
    if not access_key_id or not access_key_secret:
        return Response({'error': 'Credentials required'}, status=status.HTTP_401_UNAUTHORIZED)
        
    client = LaraClient(access_key_id, access_key_secret)
    memories = client.get_memories()
    return Response(memories)


@api_view(['GET'])
def get_lara_glossaries(request):
    """
    GET /api/lara/glossaries
    Proxy to Lara SDK glossaries.
    """
    access_key_id = request.query_params.get('accessKeyId') or settings.LARA_ACCESS_KEY_ID
    access_key_secret = request.query_params.get('accessKeySecret') or settings.LARA_ACCESS_KEY_SECRET

    if not access_key_id or not access_key_secret:
        return Response({'error': 'Credentials required'}, status=status.HTTP_401_UNAUTHORIZED)

    client = LaraClient(access_key_id, access_key_secret)
    glossaries = client.get_glossaries()
    return Response(glossaries)


@api_view(['GET'])
def list_documents(request):
    """
    GET /api/lara/documents
    Lists documents for a user with pagination.

    Query params:
    - user_uuid: User UUID (required for non-staff, optional for staff to see all)
    - page: Page number (default 1)
    - page_size: Items per page (default 10)
    """
    user_uuid = request.query_params.get('user_uuid')
    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 10))

    # Build query
    queryset = DocumentTranslation.objects.all().order_by('-created_at')

    # Filter by user_uuid if provided
    # If not provided (admin mode), return all documents
    if user_uuid:
        queryset = queryset.filter(user_uuid=user_uuid)
    # else: admin mode - no filter, return all documents

    # Pagination
    total_count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    documents = queryset[start:end]

    # Build response matching Custom.MT format
    results = []
    for doc in documents:
        # Build download URL
        download_url = f"/lara-django/api/lara/download/{doc.id}" if doc.status == 'translated' and doc.translated_file else None

        # Build source file URL
        source_file_url = f"/lara-django/media/{doc.original_file.name}" if doc.original_file else None

        # Build additional file URLs
        reviewed_file_url = f"/lara-django/media/{doc.reviewed_file.name}" if doc.reviewed_file else None
        xliff_file_url = f"/lara-django/media/{doc.xliff_file.name}" if doc.xliff_file else None
        tmx_file_url = f"/lara-django/media/{doc.tmx_file.name}" if doc.tmx_file else None

        results.append({
            'id': str(doc.id),
            'source_file': source_file_url,
            'source_file_name': doc.filename,  # Original filename for display
            'translated_file': download_url,
            'reviewed_file': reviewed_file_url,
            'xliff_file': xliff_file_url,
            'tmx_file': tmx_file_url,
            'source_language': doc.source_language,
            'target_language': doc.target_language,
            'status': 'Translated' if doc.status == 'translated' else 'Being translated' if doc.status in ['pending', 'processing'] else 'Error',
            'created_at': doc.created_at.isoformat(),
            'user_uuid': doc.user_uuid,
            'domain_name': doc.domain,
            'template_name': doc.template_name,
            'error_reason': [doc.error_message] if doc.error_message else None,
        })

    return Response({
        'count': total_count,
        'page_size': page_size,
        'current_page': page,
        'results': results
    })
