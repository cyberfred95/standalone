"""
Glossary views module.

Separates API endpoints from admin views for better maintainability.
"""
from .api import (
    glossary_list,
    create_glossary,
    update_glossary,
    delete_glossary,
    search_glossaries,
    GlossaryViewSet,
)
from .admin_views import (
    refresh_glossaries_form,
    loading_page,
    fetch_progress,
    compare_with_lara,
    apply_lara_changes,
)

__all__ = [
    # API endpoints
    'glossary_list',
    'create_glossary',
    'update_glossary',
    'delete_glossary',
    'search_glossaries',
    'GlossaryViewSet',
    # Admin views
    'refresh_glossaries_form',
    'loading_page',
    'fetch_progress',
    'compare_with_lara',
    'apply_lara_changes',
]
