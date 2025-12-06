"""
Glossary name and CSV parsing utilities.
"""
import re
import csv
import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

# Domain name mapping from glossary names
DOMAIN_MAPPING = {
    'accounting': 'Accounting',
    'arbitration': 'Arbitration',
    'banking': 'Banking',
    'compliance': 'Compliance',
    'competition': 'Competition',
    'corporate': 'Corporate',
    'employment': 'Employment',
    'finance': 'Finance',
    'gdpr': 'GDPR',
    'hr': 'HR',
    'ip': 'Intellectual Property',
    'litigation': 'Litigation',
    'ma': 'M&A',
    'privacy': 'Privacy',
    'realestate': 'Real Estate',
    'tax': 'Tax',
}


def parse_system_glossary_name(name: str) -> Optional[Tuple[str, str]]:
    """
    Parse a system glossary name of the form Legal_<Domain>_<SourceLang>.

    Example: Legal_Accounting_BG -> (domain="Accounting", source_lang="BG")

    Args:
        name: Glossary name to parse

    Returns:
        Tuple (domain, source_lang) if match, None otherwise
    """
    match = re.match(r'^Legal_([A-Za-z]+)_([A-Z]{2,4})$', name, re.IGNORECASE)
    if match:
        domain_key = match.group(1).lower()
        source_lang = match.group(2).upper()
        domain = DOMAIN_MAPPING.get(domain_key, domain_key.capitalize())
        return (domain, source_lang)
    return None


def parse_personal_glossary_name(name: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse a personal glossary name of the form <uuid>_<SourceLang>_<TargetLang>.

    Example: b2a7d16c-e62a-4abf-87f0-f8695e04eeb4_FR_EN -> (uuid, "FR", "EN")

    Args:
        name: Glossary name to parse

    Returns:
        Tuple (uuid, source_lang, target_lang) if match, None otherwise
    """
    match = re.match(r'^([a-f0-9-]{36})_([A-Z]{2,4})_([A-Z]{2,4})$', name, re.IGNORECASE)
    if match:
        uuid = match.group(1)
        source_lang = match.group(2).upper()
        target_lang = match.group(3).upper()
        return (uuid, source_lang, target_lang)
    return None


def read_csv_languages(filepath: str) -> Tuple[str, List[str]]:
    """
    Read the first line of a CSV file to extract source and target languages.

    Args:
        filepath: Path to the CSV file

    Returns:
        Tuple (source_language, target_languages_list)

    Raises:
        ValueError: If format is invalid
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if not header or len(header) < 2:
                raise ValueError("CSV file must contain at least 2 columns (source and at least one target)")

            source_lang = header[0].strip().upper()
            target_langs = [lang.strip().upper() for lang in header[1:] if lang.strip()]

            if not source_lang:
                raise ValueError("Source language (first column) is empty")

            if not target_langs:
                raise ValueError("No target language found in CSV")

            return source_lang, target_langs

    except csv.Error as e:
        raise ValueError(f"CSV read error: {str(e)}")
    except UnicodeDecodeError as e:
        raise ValueError(f"CSV encoding error (use UTF-8): {str(e)}")


def read_csv_target_languages(filepath: str) -> List[str]:
    """
    Read the first line of a glossary CSV to extract target languages.

    Expected format: source_lang, target_lang1, target_lang2, ...

    Args:
        filepath: Path to the CSV file

    Returns:
        List of target language codes
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header and len(header) >= 2:
                target_langs = [lang.strip().upper() for lang in header[1:] if lang.strip()]
                return target_langs

    except Exception as e:
        logger.error(f"Error reading CSV {filepath}: {e}")

    return []


def get_valid_domains() -> List[str]:
    """
    Retrieve list of valid domains from Lexa cache.

    Returns:
        List of domain names
    """
    from apps.lexa_backend.services import get_lexa_domains

    domains = get_lexa_domains()
    if domains:
        return [d.get('name') for d in domains if d.get('name')]
    return []


def validate_system_glossary_name(user_glossary_name: str, source_from_csv: str) -> Tuple[str, str]:
    """
    Validate and parse a system glossary name.

    Expected format: Legal_<Domain>_<SourceLang>

    Args:
        user_glossary_name: Name given by user (e.g., Legal_Accounting_FR)
        source_from_csv: Source language read from CSV

    Returns:
        Tuple (domain, source_language)

    Raises:
        ValueError: If format is invalid or domain doesn't exist
    """
    parsed = parse_system_glossary_name(user_glossary_name)
    if not parsed:
        raise ValueError(
            f"Invalid name format for system glossary. "
            f"Expected format: Legal_<Domain>_<SourceLang> (e.g., Legal_Accounting_FR)"
        )

    domain, source_lang = parsed

    if source_lang != source_from_csv:
        raise ValueError(
            f"Source language in name ({source_lang}) does not match "
            f"CSV source language ({source_from_csv})"
        )

    valid_domains = get_valid_domains()
    if valid_domains and domain not in valid_domains:
        raise ValueError(
            f"Domain '{domain}' is not valid. "
            f"Available domains: {', '.join(valid_domains)}"
        )

    return domain, source_lang
