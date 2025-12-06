"""
Celery tasks for translation app.
"""
import json
import logging
import tempfile
import os
from celery import shared_task
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils import timezone
from .models import DocumentTranslation
from .services.lara_client import LaraClient, TranslationError

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def process_document_translation(self, translation_id, access_key_id, access_key_secret, adapt_to=None, glossaries=None):
    """
    Task to process document translation in background.

    Args:
        translation_id: UUID of the DocumentTranslation record
        access_key_id: Lara API access key ID
        access_key_secret: Lara API access key secret
        adapt_to: Optional list of translation memory IDs
        glossaries: Optional list of glossary IDs
    """
    try:
        doc = DocumentTranslation.objects.get(id=translation_id)
        logger.info(f"[CELERY] Starting translation for document: {doc.filename} (ID: {translation_id})")

        # Update status to processing
        doc.status = 'processing'
        doc.save(update_fields=['status'])

        # Initialize Lara client
        client = LaraClient(access_key_id, access_key_secret)

        # Create a file-like object from the stored file
        # The SDK expects a file with .name, .chunks() and .content_type attributes
        class FileWrapper:
            def __init__(self, file_field):
                self.file = file_field
                self.name = os.path.basename(file_field.name)
                self.content_type = 'application/octet-stream'

            def chunks(self, chunk_size=8192):
                self.file.seek(0)
                while True:
                    chunk = self.file.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk

        file_wrapper = FileWrapper(doc.original_file)

        # Build translation options
        translate_options = {}
        if adapt_to:
            translate_options['adapt_to'] = adapt_to
        if glossaries:
            translate_options['glossaries'] = glossaries

        logger.info(f"[CELERY] Calling Lara SDK for document: {doc.filename}, options: {translate_options}")

        # Call Lara SDK to translate
        translation_result = client.translate_document(
            file_obj=file_wrapper,
            source=doc.source_language,
            target=doc.target_language,
            **translate_options
        )

        # Extract content and SDK request from result
        translated_content = translation_result['content']
        sdk_request = translation_result['sdk_request']

        # Store the SDK request for tracking
        doc.lara_sdk_request = json.dumps(sdk_request, ensure_ascii=False)

        # Save the translated file
        translated_filename = f"translated_{doc.filename}"
        doc.translated_file.save(
            translated_filename,
            ContentFile(translated_content),
            save=False
        )

        # Calculate translation time
        translation_sec = None
        if doc.translation_started_at:
            time_diff = timezone.now() - doc.translation_started_at
            translation_sec = time_diff.total_seconds()

        # Build response data for tracking
        response_data = {
            'status': 'translated',
            'filename': doc.filename,
            'translated_filename': translated_filename,
            'translated_file_size': len(translated_content),
            'translation_sec': translation_sec,
            'completed_at': timezone.now().isoformat(),
        }

        # Update status to translated with response tracking
        doc.status = 'translated'
        doc.response = json.dumps(response_data, ensure_ascii=False)
        doc.translation_sec = translation_sec
        doc.save(update_fields=['status', 'translated_file', 'response', 'translation_sec', 'lara_sdk_request'])

        logger.info(f"[CELERY] Successfully translated document: {doc.filename} (ID: {translation_id}) in {translation_sec:.2f}s" if translation_sec else f"[CELERY] Successfully translated document: {doc.filename} (ID: {translation_id})")

        return {'status': 'success', 'translation_id': str(translation_id)}

    except DocumentTranslation.DoesNotExist:
        logger.error(f"[CELERY] Document translation not found: {translation_id}")
        return {'status': 'error', 'message': 'Document not found'}

    except TranslationError as e:
        # Handle TranslationError with detailed SDK error information
        logger.error(f"[CELERY] Translation SDK error for {translation_id}: {e.details}")

        try:
            doc = DocumentTranslation.objects.get(id=translation_id)

            # Calculate translation time even for errors
            translation_sec = None
            if doc.translation_started_at:
                time_diff = timezone.now() - doc.translation_started_at
                translation_sec = time_diff.total_seconds()

            # Build error response data with SDK details
            error_response_data = {
                'status': 'error',
                'sdk_error': e.details,  # Contains error_type, error_message, sdk_response, status_code
                'translation_sec': translation_sec,
                'failed_at': timezone.now().isoformat(),
            }

            doc.status = 'error'
            doc.error_message = e.details.get('error_message', str(e))
            doc.response = json.dumps(error_response_data, ensure_ascii=False)
            doc.translation_sec = translation_sec
            doc.save(update_fields=['status', 'error_message', 'response', 'translation_sec'])
        except Exception:
            pass

        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            logger.info(f"[CELERY] Retrying translation {translation_id}, attempt {self.request.retries + 1}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))

        return {'status': 'error', 'message': str(e.details)}

    except Exception as e:
        logger.error(f"[CELERY] Error processing document translation {translation_id}: {e}")

        # Update document status to error
        try:
            doc = DocumentTranslation.objects.get(id=translation_id)

            # Calculate translation time even for errors
            translation_sec = None
            if doc.translation_started_at:
                time_diff = timezone.now() - doc.translation_started_at
                translation_sec = time_diff.total_seconds()

            # Build error response data
            error_response_data = {
                'status': 'error',
                'error_type': type(e).__name__,
                'error_message': str(e),
                'translation_sec': translation_sec,
                'failed_at': timezone.now().isoformat(),
            }

            doc.status = 'error'
            doc.error_message = str(e)
            doc.response = json.dumps(error_response_data, ensure_ascii=False)
            doc.translation_sec = translation_sec
            doc.save(update_fields=['status', 'error_message', 'response', 'translation_sec'])
        except Exception:
            pass

        # Retry the task if retries are available
        if self.request.retries < self.max_retries:
            logger.info(f"[CELERY] Retrying translation {translation_id}, attempt {self.request.retries + 1}")
            raise self.retry(exc=e, countdown=60 * (self.request.retries + 1))  # Exponential backoff

        return {'status': 'error', 'message': str(e)}
