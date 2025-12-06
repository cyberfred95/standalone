"""
App configuration for lexa_backend.
"""
import os
from django.apps import AppConfig


class LexaBackendConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.lexa_backend'
    verbose_name = 'Lexa Backend Objects'

    def ready(self):
        """Initialize Lexa cache at application startup."""
        # Avoid running during migrations or in certain management commands
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv or 'collectstatic' in sys.argv:
            return

        # Only run once in main process (avoid double init with autoreload)
        if os.environ.get('RUN_MAIN') == 'true' or not os.environ.get('RUN_MAIN'):
            from apps.lexa_backend.services import init_lexa_cache
            try:
                init_lexa_cache()
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"[LEXA_CACHE] Failed to initialize cache at startup: {e}")
