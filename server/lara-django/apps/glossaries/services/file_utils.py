"""
File handling utilities for glossaries.
"""
import os
import uuid as uuid_module
from typing import Optional


def save_glossary_file(glossary_file, user_uuid: Optional[str] = None) -> str:
    """
    Save an uploaded glossary file to the appropriate directory.

    Args:
        glossary_file: Uploaded file object
        user_uuid: User UUID for personal glossaries, None for system

    Returns:
        Full path to the saved file
    """
    from django.conf import settings

    # Determine destination directory
    if user_uuid:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries', user_uuid)
    else:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries', 'system')

    os.makedirs(dest_dir, exist_ok=True)

    # Generate unique filename
    original_name = glossary_file.name if hasattr(glossary_file, 'name') else 'glossary.csv'
    base_name, ext = os.path.splitext(original_name)
    unique_name = f"{base_name}_{uuid_module.uuid4().hex[:8]}{ext}"

    filepath = os.path.join(dest_dir, unique_name)

    # Save file
    with open(filepath, 'wb') as dest:
        for chunk in glossary_file.chunks():
            dest.write(chunk)

    return filepath


def cleanup_file(filepath: str) -> bool:
    """
    Safely remove a file.

    Args:
        filepath: Path to the file to remove

    Returns:
        True if file was removed, False otherwise
    """
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception:
        pass
    return False
