"""
LARA SDK interactions for glossaries.

Handles all communication with the LARA Translation API via the official Python SDK.
"""
import os
import logging
from typing import Dict, List, Optional
from lara_sdk import Translator, Credentials

logger = logging.getLogger(__name__)


def get_lara_client() -> Translator:
    """
    Creates and returns a LARA SDK client.

    Returns:
        Translator: Configured LARA SDK client

    Raises:
        Exception: If credentials are not configured
    """
    access_key_id = os.getenv('LARA_ACCESS_KEY_ID')
    access_key_secret = os.getenv('LARA_ACCESS_KEY_SECRET')

    if not access_key_id or not access_key_secret:
        raise Exception('Missing LARA_ACCESS_KEY_ID or LARA_ACCESS_KEY_SECRET')

    credentials = Credentials(access_key_id, access_key_secret)
    return Translator(credentials)


def list_glossaries_from_lara() -> List:
    """
    Lists all glossaries from LARA.

    Returns:
        List of glossary objects from LARA SDK
    """
    lara = get_lara_client()
    return lara.glossaries.list()


def create_glossary_in_lara(name: str, csv_path: str) -> Dict:
    """
    Creates a glossary in LARA Server via SDK.

    Args:
        name: Normalized name for the glossary
        csv_path: Path to the CSV file

    Returns:
        Dict with created glossary information

    Raises:
        ValueError: If CSV format is invalid
        Exception: If LARA API fails
    """
    try:
        lara = get_lara_client()

        logger.info(f"Creating glossary '{name}' in LARA...")

        # 1. Create empty glossary
        glossary = lara.glossaries.create(name)
        logger.info(f"Glossary created with ID: {glossary.id}")

        # 2. Import CSV
        logger.info(f"Importing CSV: {csv_path}")
        import_job = lara.glossaries.import_csv(glossary.id, csv_path)

        # 3. Wait for import completion
        logger.info("Waiting for import completion...")
        result = lara.glossaries.wait_for_import(import_job, max_wait_time=300)

        if result.progress < 1.0:
            raise Exception(f"Import incomplete: {result.progress * 100:.0f}%")

        logger.info("Import completed successfully")

        return {
            'glossary_id': glossary.id,
            'name': glossary.name,
            'created_at': glossary.created_at,
            'updated_at': glossary.updated_at
        }

    except Exception as e:
        logger.error(f"Error creating glossary in LARA: {e}")
        import traceback
        logger.error(traceback.format_exc())

        error_msg = str(e)
        if 'invalid' in error_msg.lower() or 'format' in error_msg.lower():
            raise ValueError(f"CSV format error: {error_msg}")
        raise Exception(f"LARA error: {error_msg}")


def update_glossary_in_lara(glossary_id: str, csv_path: str) -> Dict:
    """
    Updates an existing glossary in LARA Server by re-importing a CSV.

    Args:
        glossary_id: ID of the glossary to update
        csv_path: Path to the new CSV file

    Returns:
        Dict with updated glossary information

    Raises:
        ValueError: If CSV format is invalid
        Exception: If LARA API fails
    """
    try:
        lara = get_lara_client()

        logger.info(f"Updating glossary '{glossary_id}' in LARA...")

        # Import new CSV (replaces existing entries)
        logger.info(f"Importing CSV: {csv_path}")
        import_job = lara.glossaries.import_csv(glossary_id, csv_path)

        # Wait for import completion
        logger.info("Waiting for import completion...")
        result = lara.glossaries.wait_for_import(import_job, max_wait_time=300)

        if result.progress < 1.0:
            raise Exception(f"Import incomplete: {result.progress * 100:.0f}%")

        logger.info("Update completed successfully")

        return {
            'glossary_id': glossary_id,
            'status': 'updated',
            'import_progress': result.progress
        }

    except Exception as e:
        logger.error(f"Error updating glossary in LARA: {e}")
        import traceback
        logger.error(traceback.format_exc())

        error_msg = str(e)
        if 'invalid' in error_msg.lower() or 'format' in error_msg.lower():
            raise ValueError(f"CSV format error: {error_msg}")
        raise Exception(f"LARA error: {error_msg}")


def delete_glossary_in_lara(glossary_id: str) -> bool:
    """
    Deletes a glossary from LARA Server.

    Args:
        glossary_id: ID of the glossary to delete

    Returns:
        True if deletion was successful

    Raises:
        Exception: If LARA API fails
    """
    try:
        lara = get_lara_client()

        logger.info(f"Deleting glossary '{glossary_id}' from LARA...")
        lara.glossaries.delete(glossary_id)
        logger.info(f"Glossary '{glossary_id}' deleted successfully")

        return True

    except Exception as e:
        logger.error(f"Error deleting glossary from LARA: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"LARA error: {str(e)}")


def download_glossary_csv(glossary_id: str, source_lang: str) -> Optional[str]:
    """
    Downloads a glossary CSV file from LARA and saves it locally.

    Args:
        glossary_id: ID of the glossary
        source_lang: Source language code

    Returns:
        Path to the downloaded file, or None on error
    """
    from django.conf import settings

    try:
        lara = get_lara_client()

        # Create glossaries directory if needed
        glossaries_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries')
        os.makedirs(glossaries_dir, exist_ok=True)

        # Download CSV
        logger.info(f"Downloading glossary {glossary_id} (source: {source_lang})...")
        csv_content = lara.glossaries.export(glossary_id, 'csv/table-uni', source_lang.lower())

        # Save file
        filename = f"{glossary_id}.csv"
        filepath = os.path.join(glossaries_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(csv_content)

        logger.info(f"Glossary downloaded: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error downloading glossary {glossary_id}: {e}")
        return None
