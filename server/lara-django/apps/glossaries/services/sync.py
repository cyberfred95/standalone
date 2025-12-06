"""
Glossary synchronization services.

Handles fetching and comparing glossaries between local DB and LARA.
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .lara_sdk import get_lara_client, download_glossary_csv
from .parser import (
    parse_system_glossary_name,
    parse_personal_glossary_name,
    read_csv_target_languages
)

logger = logging.getLogger(__name__)


def normalize_target_languages(target_languages: str) -> str:
    """
    Normalize target languages list by sorting alphabetically.
    Allows comparing lists with same languages in different order.

    Args:
        target_languages: Comma-separated language codes

    Returns:
        Sorted, comma-separated language codes
    """
    if not target_languages:
        return ''
    langs = [lang.strip().upper() for lang in target_languages.split(',') if lang.strip()]
    return ','.join(sorted(langs))


def fetch_lara_glossaries(since_date: Optional[datetime] = None) -> List[Dict]:
    """
    Fetch glossaries from LARA.

    Args:
        since_date: Filter glossaries updated after this date

    Returns:
        List of glossary dictionaries with parsed information
    """
    try:
        lara = get_lara_client()

        logger.info("Fetching glossaries from LARA...")
        glossaries_list = lara.glossaries.list()
        logger.info(f"{len(glossaries_list)} glossaries fetched from LARA")

        glossaries = []

        for g in glossaries_list:
            # Filter by date if specified
            if since_date and g.updated_at:
                since_date_aware = since_date.replace(tzinfo=timezone.utc) if since_date.tzinfo is None else since_date
                if g.updated_at < since_date_aware:
                    continue

            glossary_info = {
                'glossary_id': g.id,
                'name': g.name,
                'uuid': '',
                'source_language': '',
                'target_languages': '',
                'domain': '',
                'type': 'unknown',
                'updated_at': g.updated_at
            }

            # Try to parse as system glossary
            system_match = parse_system_glossary_name(g.name)
            if system_match:
                domain, source_lang = system_match
                glossary_info['uuid'] = '*'
                glossary_info['domain'] = domain
                glossary_info['source_language'] = source_lang
                glossary_info['type'] = 'system'

                # Download CSV to get target languages
                csv_path = download_glossary_csv(g.id, source_lang)
                if csv_path:
                    target_langs = read_csv_target_languages(csv_path)
                    glossary_info['target_languages'] = ','.join(target_langs)

                glossaries.append(glossary_info)
                continue

            # Try to parse as personal glossary
            personal_match = parse_personal_glossary_name(g.name)
            if personal_match:
                uuid, source_lang, target_lang = personal_match
                glossary_info['uuid'] = uuid
                glossary_info['domain'] = '*'
                glossary_info['source_language'] = source_lang
                glossary_info['target_languages'] = target_lang
                glossary_info['type'] = 'personal'

                glossaries.append(glossary_info)
                continue

            # Unknown format
            glossary_info['type'] = 'unknown'
            glossaries.append(glossary_info)

        logger.info(f"{len(glossaries)} glossaries processed")
        return glossaries

    except Exception as e:
        logger.error(f"Error fetching glossaries: {e}")
        raise Exception(f"Failed to fetch glossaries from LARA: {str(e)}")


def fetch_lara_glossaries_with_progress(since_date: Optional[datetime] = None):
    """
    Generator that fetches glossaries from LARA with progress updates.

    Yields:
        dict: Progress messages or completion result
    """
    try:
        lara = get_lara_client()

        yield {'type': 'progress', 'current': 0, 'total': 1, 'message': 'Connecting to LARA...'}

        logger.info("Fetching glossaries from LARA...")
        glossaries_list = lara.glossaries.list()
        total = len(glossaries_list)
        logger.info(f"{total} glossaries fetched from LARA")

        yield {'type': 'progress', 'current': 0, 'total': total, 'message': f'{total} glossaries found'}

        glossaries = []
        processed = 0

        for g in glossaries_list:
            # Filter by date if specified
            if since_date and g.updated_at:
                since_date_aware = since_date.replace(tzinfo=timezone.utc) if since_date.tzinfo is None else since_date
                if g.updated_at < since_date_aware:
                    processed += 1
                    continue

            glossary_info = {
                'glossary_id': g.id,
                'name': g.name,
                'uuid': '',
                'source_language': '',
                'target_languages': '',
                'domain': '',
                'type': 'unknown',
                'updated_at': g.updated_at.isoformat() if g.updated_at else None
            }

            # Try to parse as system glossary
            system_match = parse_system_glossary_name(g.name)
            if system_match:
                domain, source_lang = system_match
                glossary_info['uuid'] = '*'
                glossary_info['domain'] = domain
                glossary_info['source_language'] = source_lang
                glossary_info['type'] = 'system'

                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Downloading CSV: {g.name}'}

                csv_path = download_glossary_csv(g.id, source_lang)
                if csv_path:
                    target_langs = read_csv_target_languages(csv_path)
                    glossary_info['target_languages'] = ','.join(target_langs)

                glossaries.append(glossary_info)
                processed += 1
                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Processed: {g.name}'}
                continue

            # Try to parse as personal glossary
            personal_match = parse_personal_glossary_name(g.name)
            if personal_match:
                uuid, source_lang, target_lang = personal_match
                glossary_info['uuid'] = uuid
                glossary_info['domain'] = '*'
                glossary_info['source_language'] = source_lang
                glossary_info['target_languages'] = target_lang
                glossary_info['type'] = 'personal'

                glossaries.append(glossary_info)
                processed += 1
                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Processed: {g.name}'}
                continue

            # Unknown format
            glossary_info['type'] = 'unknown'
            glossaries.append(glossary_info)
            processed += 1
            yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Processed: {g.name}'}

        logger.info(f"{len(glossaries)} glossaries processed")
        yield {'type': 'complete', 'glossaries': glossaries}

    except Exception as e:
        logger.error(f"Error fetching glossaries: {e}")
        yield {'type': 'error', 'message': str(e)}


def compare_glossaries(db_glossaries: List[Dict], lara_glossaries: List[Dict]) -> List[Dict]:
    """
    Compare database glossaries with LARA glossaries.

    Note: Only detects additions and modifications, not deletions.

    Args:
        db_glossaries: Glossaries from local database
        lara_glossaries: Glossaries from LARA

    Returns:
        List of differences with action (add/update)
    """
    differences = []
    db_dict = {g['glossary_id']: g for g in db_glossaries}

    for lara_g in lara_glossaries:
        glossary_id = lara_g['glossary_id']

        if glossary_id not in db_dict:
            # New glossary
            differences.append({
                'glossary_id': glossary_id,
                'name': lara_g['name'],
                'uuid': lara_g['uuid'],
                'source_language': lara_g['source_language'],
                'target_languages': lara_g['target_languages'],
                'domain': lara_g['domain'],
                'type': lara_g['type'],
                'modification': 'new',
                'action': 'add',
                'changes_detail': ''
            })
        else:
            # Check for modifications
            db_g = db_dict[glossary_id]
            modifications = []
            changes_details = []

            if db_g.get('name', '') != lara_g.get('name', ''):
                modifications.append('name')
                changes_details.append(f"{db_g.get('name', '')} → {lara_g.get('name', '')}")

            if db_g.get('uuid', '') != lara_g.get('uuid', '') and lara_g.get('uuid', ''):
                modifications.append('uuid')
                changes_details.append(f"{db_g.get('uuid', '')} → {lara_g.get('uuid', '')}")

            if db_g.get('source_language', '') != lara_g.get('source_language', '') and lara_g.get('source_language', ''):
                modifications.append('source_language')
                changes_details.append(f"{db_g.get('source_language', '')} → {lara_g.get('source_language', '')}")

            db_targets = normalize_target_languages(db_g.get('target_languages', ''))
            lara_targets = normalize_target_languages(lara_g.get('target_languages', ''))
            if db_targets != lara_targets and lara_targets:
                modifications.append('target_languages')
                changes_details.append(f"{db_g.get('target_languages', '')} → {lara_g.get('target_languages', '')}")

            if db_g.get('domain', '') != lara_g.get('domain', '') and lara_g.get('domain', ''):
                modifications.append('domain')
                changes_details.append(f"{db_g.get('domain', '')} → {lara_g.get('domain', '')}")

            if modifications:
                differences.append({
                    'glossary_id': glossary_id,
                    'name': lara_g['name'],
                    'uuid': lara_g['uuid'],
                    'source_language': lara_g['source_language'],
                    'target_languages': lara_g['target_languages'],
                    'domain': lara_g['domain'],
                    'type': lara_g['type'],
                    'modification': f"modified: {', '.join(modifications)}",
                    'action': 'update',
                    'changes_detail': ' | '.join(changes_details)
                })

    return differences
