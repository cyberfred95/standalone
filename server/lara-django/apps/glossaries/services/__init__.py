"""
Glossary services module.

Provides services for interacting with LARA SDK and managing glossaries.
"""
from .lara_sdk import (
    get_lara_client,
    create_glossary_in_lara,
    update_glossary_in_lara,
    delete_glossary_in_lara,
    list_glossaries_from_lara,
    download_glossary_csv,
)
from .parser import (
    parse_system_glossary_name,
    parse_personal_glossary_name,
    read_csv_languages,
    read_csv_target_languages,
    get_valid_domains,
    validate_system_glossary_name,
)
from .file_utils import save_glossary_file
from .sync import (
    fetch_lara_glossaries,
    fetch_lara_glossaries_with_progress,
    compare_glossaries,
    normalize_target_languages,
)

__all__ = [
    # LARA SDK
    'get_lara_client',
    'create_glossary_in_lara',
    'update_glossary_in_lara',
    'delete_glossary_in_lara',
    'list_glossaries_from_lara',
    'download_glossary_csv',
    # Parser
    'parse_system_glossary_name',
    'parse_personal_glossary_name',
    'read_csv_languages',
    'read_csv_target_languages',
    'get_valid_domains',
    'validate_system_glossary_name',
    # File utils
    'save_glossary_file',
    # Sync
    'fetch_lara_glossaries',
    'fetch_lara_glossaries_with_progress',
    'compare_glossaries',
    'normalize_target_languages',
]
