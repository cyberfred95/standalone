"""
Lara API Client.
Handles communication with Translated's Lara API.
"""

import logging
from django.conf import settings
import lara_sdk

logger = logging.getLogger(__name__)

class LaraClient:
    """
    Client for interacting with Lara Translation API.
    Replaces the @translated/lara Node.js SDK.
    """
    
    def __init__(self, access_key_id, access_key_secret):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        credentials = lara_sdk.Credentials(access_key_id=access_key_id, access_key_secret=access_key_secret)
        self.client = lara_sdk.Translator(credentials)
        # Use the documents property from Translator instead of creating separate Documents instance
        self.documents = self.client.documents
        
    # _get_headers is no longer needed

    def translate_text(self, text, source=None, target=None, **options):
        """
        Translates text using Lara SDK Python, en passant SEULEMENT les options supportées comme kwargs.
        """
        try:
            kwargs = {}
            if source:
                kwargs['source'] = source
            if target:
                kwargs['target'] = target
            # Liste blanche des arguments supportés par le SDK Python
            allowed = {
                'adapt_to', 'glossaries', 'instructions', 'style', 'content_type',
                'timeout_ms', 'priority', 'use_cache', 'cache_ttl', 'no_trace', 'verbose'
            }
            for k, v in options.items():
                if v is not None and k in allowed:
                    kwargs[k] = v
            result = self.client.translate(text, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            raise

    def translate_document(self, file_obj, source, target, **options):
        """
        Translates a document using Lara SDK Python Documents.translate().
        Returns a dict with:
            - 'content': bytes of the translated document
            - 'sdk_request': the kwargs sent to the SDK (for tracking)
        """
        try:
            import tempfile
            import os

            # Le SDK Python attend un file_path (string), pas un objet file
            # On doit sauvegarder temporairement le fichier uploadé
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file_obj.name)[1]) as temp_file:
                # Écrire le contenu du fichier uploadé dans le fichier temporaire
                for chunk in file_obj.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name

            try:
                # Préparer les arguments pour le SDK
                # Le SDK attend: file_path, filename, target (requis), source (optionnel), autres options
                kwargs = {
                    'file_path': temp_file_path,
                    'filename': file_obj.name,
                    'target': target
                }

                # Ajouter source seulement s'il est fourni
                if source:
                    kwargs['source'] = source

                # Ajouter les autres options seulement si elles sont fournies
                for key, value in options.items():
                    if value is not None:
                        kwargs[key] = value

                # Log pour déboguer
                logger.info(f"Calling documents.translate with kwargs: {kwargs}")

                # Build sdk_request for tracking (exclude file_path as it's a temp path)
                sdk_request = {k: v for k, v in kwargs.items() if k != 'file_path'}

                # Appeler le SDK avec les arguments préparés
                # La méthode translate() retourne bytes du document traduit
                result = self.documents.translate(**kwargs)

                return {
                    'content': result,
                    'sdk_request': sdk_request
                }
            finally:
                # Nettoyer le fichier temporaire
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        except Exception as e:
            logger.error(f"Error translating document: {e}")
            # Re-raise with additional context if available
            error_details = {
                'error_type': type(e).__name__,
                'error_message': str(e),
            }
            # Try to extract more details from SDK exceptions
            if hasattr(e, 'response'):
                try:
                    error_details['sdk_response'] = e.response.json() if hasattr(e.response, 'json') else str(e.response)
                except Exception:
                    error_details['sdk_response'] = str(e.response) if hasattr(e, 'response') else None
            if hasattr(e, 'status_code'):
                error_details['status_code'] = e.status_code

            # Create a new exception with enriched details
            raise TranslationError(error_details) from e

    def get_document_status(self, document_id):
        """
        Gets status of document translation using Lara SDK Python.
        """
        try:
            result = self.documents.status(document_id)
            return result
        except Exception as e:
            logger.error(f"Error getting document status: {e}")
            raise

    def download_document(self, document_id):
        """
        Downloads a translated document using Lara SDK Python.
        """
        try:
            result = self.documents.download(document_id)
            return result
        except Exception as e:
            logger.error(f"Error downloading document: {e}")
            raise
        
    def get_memories(self):
        """
        Retrieves memories from Lara using Lara SDK Python.
        """
        try:
            result = self.client.list_memories()
            return result
        except Exception as e:
            logger.error(f"Error getting memories: {e}")
            raise

    def get_glossaries(self):
        """
        Retrieves glossaries from Lara using Lara SDK Python.
        """
        try:
            result = self.client.list_glossaries()
            return result
        except Exception as e:
            logger.error(f"Error getting glossaries: {e}")
            raise


class TranslationError(Exception):
    """Custom exception for translation errors with detailed information."""
    def __init__(self, details):
        self.details = details
        super().__init__(str(details))
