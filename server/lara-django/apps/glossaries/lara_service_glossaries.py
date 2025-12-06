"""
Service pour interagir avec l'API Lara Translation pour les glossaires via le SDK Python officiel.
"""
import os
import re
import csv
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta, timezone
from lara_sdk import Translator, Credentials

logger = logging.getLogger(__name__)

# Mapping des noms de domaine depuis les noms de glossaires
# Legal_Accounting_BG -> domain = "Accounting"
DOMAIN_MAPPING = {
    'accounting': 'Accounting',
    'banking': 'Banking',
    'compliance': 'Compliance',
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


def get_lara_client() -> Translator:
    """
    Crée et retourne un client Lara SDK.
    """
    access_key_id = os.getenv('LARA_ACCESS_KEY_ID')
    access_key_secret = os.getenv('LARA_ACCESS_KEY_SECRET')

    if not access_key_id or not access_key_secret:
        raise Exception('Missing LARA_ACCESS_KEY_ID or LARA_ACCESS_KEY_SECRET')

    credentials = Credentials(access_key_id, access_key_secret)
    return Translator(credentials)


def parse_system_glossary_name(name: str) -> Optional[Tuple[str, str]]:
    """
    Parse un nom de glossaire système de la forme Legal_<Domain>_<SourceLang>.

    Exemple: Legal_Accounting_BG -> (domain="Accounting", source_lang="BG")

    Returns:
        Tuple (domain, source_lang) si match, None sinon
    """
    # Pattern: Legal_<Domain>_<Lang>
    match = re.match(r'^Legal_([A-Za-z]+)_([A-Z]{2,4})$', name, re.IGNORECASE)
    if match:
        domain_key = match.group(1).lower()
        source_lang = match.group(2).upper()

        # Mapper le nom de domaine
        domain = DOMAIN_MAPPING.get(domain_key, domain_key.capitalize())

        return (domain, source_lang)

    return None


def parse_personal_glossary_name(name: str) -> Optional[Tuple[str, str, str]]:
    """
    Parse un nom de glossaire personnel de la forme <uuid>_<SourceLang>_<TargetLang>.

    Exemple: b2a7d16c-e62a-4abf-87f0-f8695e04eeb4_FR_EN -> (uuid, source_lang="FR", target_lang="EN")

    Returns:
        Tuple (uuid, source_lang, target_lang) si match, None sinon
    """
    # Pattern: <uuid>_<Lang>_<Lang>
    match = re.match(r'^([a-f0-9-]{36})_([A-Z]{2,4})_([A-Z]{2,4})$', name, re.IGNORECASE)
    if match:
        uuid = match.group(1)
        source_lang = match.group(2).upper()
        target_lang = match.group(3).upper()
        return (uuid, source_lang, target_lang)

    return None


def download_glossary_csv(glossary_id: str, source_lang: str) -> Optional[str]:
    """
    Télécharge le fichier CSV d'un glossaire et le sauvegarde dans media/glossaries/.

    Returns:
        Chemin du fichier téléchargé ou None en cas d'erreur
    """
    from django.conf import settings

    try:
        lara = get_lara_client()

        # Créer le répertoire media/glossaries si nécessaire
        glossaries_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries')
        os.makedirs(glossaries_dir, exist_ok=True)

        # Télécharger le CSV
        logger.info(f"Téléchargement du glossaire {glossary_id} (source: {source_lang})...")
        csv_content = lara.glossaries.export(glossary_id, 'csv/table-uni', source_lang.lower())

        # Sauvegarder le fichier
        filename = f"{glossary_id}.csv"
        filepath = os.path.join(glossaries_dir, filename)

        with open(filepath, 'wb') as f:
            f.write(csv_content)

        logger.info(f"Glossaire téléchargé: {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Erreur lors du téléchargement du glossaire {glossary_id}: {e}")
        return None


def read_csv_target_languages(filepath: str) -> List[str]:
    """
    Lit la première ligne d'un fichier CSV de glossaire pour extraire les langues cibles.

    Le format attendu est: source_lang, target_lang1, target_lang2, ...

    Returns:
        Liste des codes de langues cibles
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if header and len(header) >= 2:
                # Ignorer la première colonne (source) et retourner les autres
                target_langs = [lang.strip().upper() for lang in header[1:] if lang.strip()]
                return target_langs

    except Exception as e:
        logger.error(f"Erreur lors de la lecture du CSV {filepath}: {e}")

    return []


def fetch_lara_glossaries_with_progress(since_date: Optional[datetime] = None):
    """
    Générateur qui récupère les glossaires depuis Lara avec progression.

    Yields:
        dict: Messages de progression {'type': 'progress', 'current': n, 'total': total, 'message': '...'}
              ou {'type': 'complete', 'glossaries': [...]}
              ou {'type': 'error', 'message': '...'}
    """
    try:
        lara = get_lara_client()

        yield {'type': 'progress', 'current': 0, 'total': 1, 'message': 'Connexion à Lara...'}

        logger.info("Récupération des glossaires depuis Lara...")
        glossaries_list = lara.glossaries.list()
        total = len(glossaries_list)
        logger.info(f"{total} glossaires récupérés depuis Lara")

        yield {'type': 'progress', 'current': 0, 'total': total, 'message': f'{total} glossaires trouvés'}

        glossaries = []
        processed = 0

        for g in glossaries_list:
            # Filtrer par date si spécifié
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

            # Essayer de parser comme glossaire système
            system_match = parse_system_glossary_name(g.name)
            if system_match:
                domain, source_lang = system_match
                glossary_info['uuid'] = '*'
                glossary_info['domain'] = domain
                glossary_info['source_language'] = source_lang
                glossary_info['type'] = 'system'

                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Téléchargement CSV: {g.name}'}

                # Télécharger le CSV pour obtenir les langues cibles
                csv_path = download_glossary_csv(g.id, source_lang)
                if csv_path:
                    target_langs = read_csv_target_languages(csv_path)
                    glossary_info['target_languages'] = ','.join(target_langs)

                glossaries.append(glossary_info)
                processed += 1
                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Traité: {g.name}'}
                continue

            # Essayer de parser comme glossaire personnel
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
                yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Traité: {g.name}'}
                continue

            # Format non reconnu
            glossary_info['type'] = 'unknown'
            glossaries.append(glossary_info)
            processed += 1
            yield {'type': 'progress', 'current': processed, 'total': total, 'message': f'Traité: {g.name}'}

        logger.info(f"{len(glossaries)} glossaires traités")
        yield {'type': 'complete', 'glossaries': glossaries}

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des glossaires: {e}")
        import traceback
        logger.error(traceback.format_exc())
        yield {'type': 'error', 'message': str(e)}


def fetch_lara_glossaries(since_date: Optional[datetime] = None) -> List[Dict]:
    """
    Récupère la liste des glossaires depuis Lara.

    Args:
        since_date: Date à partir de laquelle filtrer les glossaires (updated_at >= since_date)

    Returns:
        Liste de dictionnaires contenant les informations des glossaires parsées.
    """
    try:
        lara = get_lara_client()

        logger.info("Récupération des glossaires depuis Lara...")
        glossaries_list = lara.glossaries.list()
        logger.info(f"{len(glossaries_list)} glossaires récupérés depuis Lara")

        glossaries = []

        for g in glossaries_list:
            # Filtrer par date si spécifié
            # Le SDK retourne des dates timezone-aware (UTC), on doit rendre since_date aware aussi
            if since_date and g.updated_at:
                # Convertir since_date en UTC si nécessaire
                since_date_aware = since_date.replace(tzinfo=timezone.utc) if since_date.tzinfo is None else since_date
                if g.updated_at < since_date_aware:
                    logger.debug(f"Glossaire {g.name} ignoré (updated_at={g.updated_at} < {since_date_aware})")
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

            # Essayer de parser comme glossaire système
            system_match = parse_system_glossary_name(g.name)
            if system_match:
                domain, source_lang = system_match
                glossary_info['uuid'] = '*'
                glossary_info['domain'] = domain
                glossary_info['source_language'] = source_lang
                glossary_info['type'] = 'system'

                # Télécharger le CSV pour obtenir les langues cibles
                csv_path = download_glossary_csv(g.id, source_lang)
                if csv_path:
                    target_langs = read_csv_target_languages(csv_path)
                    glossary_info['target_languages'] = ','.join(target_langs)

                glossaries.append(glossary_info)
                continue

            # Essayer de parser comme glossaire personnel
            personal_match = parse_personal_glossary_name(g.name)
            if personal_match:
                uuid, source_lang, target_lang = personal_match
                glossary_info['uuid'] = uuid
                glossary_info['domain'] = '*'  # Tous les domaines
                glossary_info['source_language'] = source_lang
                glossary_info['target_languages'] = target_lang
                glossary_info['type'] = 'personal'

                glossaries.append(glossary_info)
                continue

            # Format non reconnu - ajouter avec valeurs vides
            glossary_info['type'] = 'unknown'
            glossaries.append(glossary_info)

        if since_date:
            logger.info(f"{len(glossaries)} glossaires retenus (modifiés depuis {since_date.strftime('%Y-%m-%d')}) sur {len(glossaries_list)} au total")
        else:
            logger.info(f"{len(glossaries)} glossaires traités (aucun filtre de date)")

        # Compter par type
        system_count = sum(1 for g in glossaries if g['type'] == 'system')
        personal_count = sum(1 for g in glossaries if g['type'] == 'personal')
        unknown_count = sum(1 for g in glossaries if g['type'] == 'unknown')
        logger.info(f"Types: {system_count} système, {personal_count} personnel, {unknown_count} inconnu")

        return glossaries

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des glossaires: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"Failed to fetch glossaries from Lara: {str(e)}")


def normalize_target_languages(target_languages: str) -> str:
    """
    Normalise une liste de langues cibles en la triant alphabétiquement.
    Permet de comparer deux listes qui contiennent les mêmes langues dans un ordre différent.
    """
    if not target_languages:
        return ''
    langs = [lang.strip().upper() for lang in target_languages.split(',') if lang.strip()]
    return ','.join(sorted(langs))


def compare_glossaries(db_glossaries: List[Dict], lara_glossaries: List[Dict]) -> List[Dict]:
    """
    Compare les glossaires de la base de données avec ceux de Lara.

    Note: On ne détecte pas les suppressions, seulement les ajouts et modifications.

    Args:
        db_glossaries: Liste des glossaires depuis la DB
        lara_glossaries: Liste des glossaires depuis Lara

    Returns:
        Liste de différences avec colonnes: glossary_id, name, uuid, source_language,
        target_languages, domain, modification, action
    """
    differences = []

    # Créer un dictionnaire pour faciliter la comparaison
    db_dict = {g['glossary_id']: g for g in db_glossaries}

    for lara_g in lara_glossaries:
        glossary_id = lara_g['glossary_id']

        if glossary_id not in db_dict:
            # Nouveau glossaire
            differences.append({
                'glossary_id': glossary_id,
                'name': lara_g['name'],
                'uuid': lara_g['uuid'],
                'source_language': lara_g['source_language'],
                'target_languages': lara_g['target_languages'],
                'domain': lara_g['domain'],
                'type': lara_g['type'],
                'modification': 'nouveau',
                'action': 'add',
                'changes_detail': ''
            })
        else:
            # Vérifier si modifié
            db_g = db_dict[glossary_id]
            modifications = []
            changes_details = []

            # Comparer les champs
            if db_g.get('name', '') != lara_g.get('name', ''):
                modifications.append('name')
                changes_details.append(f"{db_g.get('name', '')} → {lara_g.get('name', '')}")

            if db_g.get('uuid', '') != lara_g.get('uuid', '') and lara_g.get('uuid', ''):
                modifications.append('uuid')
                changes_details.append(f"{db_g.get('uuid', '')} → {lara_g.get('uuid', '')}")

            if db_g.get('source_language', '') != lara_g.get('source_language', '') and lara_g.get('source_language', ''):
                modifications.append('source_language')
                changes_details.append(f"{db_g.get('source_language', '')} → {lara_g.get('source_language', '')}")

            # Comparer target_languages en normalisant (tri alphabétique) pour ignorer l'ordre
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
                    'modification': f"modifié: {', '.join(modifications)}",
                    'action': 'update',
                    'changes_detail': ' | '.join(changes_details)
                })

    return differences


def get_valid_domains() -> List[str]:
    """
    Récupère la liste des domaines valides depuis le cache Lexa.
    """
    from apps.lexa_backend.services import get_lexa_domains

    domains = get_lexa_domains()
    if domains:
        return [d.get('name') for d in domains if d.get('name')]
    return []


def read_csv_languages(filepath: str) -> Tuple[str, List[str]]:
    """
    Lit la première ligne d'un fichier CSV pour extraire la langue source et les langues cibles.

    Returns:
        Tuple (source_language, target_languages_list)

    Raises:
        ValueError si le format est invalide
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)

            if not header or len(header) < 2:
                raise ValueError("Le fichier CSV doit contenir au moins 2 colonnes (source et au moins une cible)")

            source_lang = header[0].strip().upper()
            target_langs = [lang.strip().upper() for lang in header[1:] if lang.strip()]

            if not source_lang:
                raise ValueError("La langue source (première colonne) est vide")

            if not target_langs:
                raise ValueError("Aucune langue cible trouvée dans le CSV")

            return source_lang, target_langs

    except csv.Error as e:
        raise ValueError(f"Erreur de lecture CSV: {str(e)}")
    except UnicodeDecodeError as e:
        raise ValueError(f"Erreur d'encodage du fichier CSV (utilisez UTF-8): {str(e)}")


def validate_system_glossary_name(user_glossary_name: str, source_from_csv: str) -> Tuple[str, str]:
    """
    Valide et parse le nom d'un glossaire système.

    Le format attendu est: Legal_<Domain>_<SourceLang>

    Args:
        user_glossary_name: Nom donné par l'utilisateur (ex: Legal_Accounting_FR)
        source_from_csv: Langue source lue depuis le CSV

    Returns:
        Tuple (domain, source_language)

    Raises:
        ValueError si le format est invalide ou le domaine n'existe pas
    """
    # Parser le nom
    parsed = parse_system_glossary_name(user_glossary_name)
    if not parsed:
        raise ValueError(
            f"Format de nom invalide pour un glossaire système. "
            f"Format attendu: Legal_<Domain>_<SourceLang> (ex: Legal_Accounting_FR)"
        )

    domain, source_lang = parsed

    # Vérifier que la langue source correspond au CSV
    if source_lang != source_from_csv:
        raise ValueError(
            f"La langue source dans le nom ({source_lang}) ne correspond pas "
            f"à celle du CSV ({source_from_csv})"
        )

    # Vérifier que le domaine existe
    valid_domains = get_valid_domains()
    if valid_domains and domain not in valid_domains:
        raise ValueError(
            f"Le domaine '{domain}' n'est pas valide. "
            f"Domaines disponibles: {', '.join(valid_domains)}"
        )

    return domain, source_lang


def save_glossary_file(glossary_file, uuid: Optional[str]) -> str:
    """
    Sauvegarde le fichier glossaire dans le répertoire approprié.

    Args:
        glossary_file: Fichier uploadé
        uuid: UUID utilisateur ou None pour système

    Returns:
        Chemin complet du fichier sauvegardé
    """
    from django.conf import settings
    import uuid as uuid_module

    # Déterminer le répertoire de destination
    if uuid:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries', uuid)
    else:
        dest_dir = os.path.join(settings.MEDIA_ROOT, 'glossaries', 'system')

    os.makedirs(dest_dir, exist_ok=True)

    # Générer un nom de fichier unique
    original_name = glossary_file.name if hasattr(glossary_file, 'name') else 'glossary.csv'
    base_name, ext = os.path.splitext(original_name)
    unique_name = f"{base_name}_{uuid_module.uuid4().hex[:8]}{ext}"

    filepath = os.path.join(dest_dir, unique_name)

    # Sauvegarder le fichier
    with open(filepath, 'wb') as dest:
        for chunk in glossary_file.chunks():
            dest.write(chunk)

    return filepath


def create_glossary_in_lara(name: str, csv_path: str) -> Dict:
    """
    Crée un glossaire dans Lara Server via le SDK.

    Args:
        name: Nom normalisé du glossaire
        csv_path: Chemin vers le fichier CSV

    Returns:
        Dict avec les informations du glossaire créé

    Raises:
        Exception en cas d'erreur Lara
    """
    try:
        lara = get_lara_client()

        logger.info(f"Création du glossaire '{name}' dans Lara...")

        # 1. Créer le glossaire vide
        glossary = lara.glossaries.create(name)
        logger.info(f"Glossaire créé avec ID: {glossary.id}")

        # 2. Importer le CSV
        logger.info(f"Import du CSV: {csv_path}")
        import_job = lara.glossaries.import_csv(glossary.id, csv_path)

        # 3. Attendre la fin de l'import
        logger.info("Attente de la fin de l'import...")
        result = lara.glossaries.wait_for_import(import_job, max_wait_time=300)

        if result.progress < 1.0:
            raise Exception(f"Import incomplet: {result.progress * 100:.0f}%")

        logger.info(f"Import terminé avec succès")

        return {
            'glossary_id': glossary.id,
            'name': glossary.name,
            'created_at': glossary.created_at,
            'updated_at': glossary.updated_at
        }

    except Exception as e:
        logger.error(f"Erreur lors de la création du glossaire dans Lara: {e}")
        import traceback
        logger.error(traceback.format_exc())

        # Re-raise avec un message clair
        error_msg = str(e)
        if 'invalid' in error_msg.lower() or 'format' in error_msg.lower():
            raise ValueError(f"Erreur de format CSV: {error_msg}")
        raise Exception(f"Erreur Lara: {error_msg}")
