"""
Service pour interagir avec l'API Lara Translation via le SDK Python officiel.
"""
import os
import re
from typing import List, Dict
from lara_sdk import Translator, Credentials


def format_lang_code(code: str) -> str:
    """
    Formate un code de langue en UPPERCASE.
    Si 4 lettres (ex: ENUS), convertir en format locale (ex: EN-US).
    Si 2 lettres (ex: FR), retourner en majuscules.
    All language codes in the database are stored in UPPERCASE.
    """
    if len(code) == 4:
        # ENUS -> EN-US (tout en majuscules)
        return f"{code[:2].upper()}-{code[2:].upper()}"
    return code.upper()


def extract_langs_from_name(name: str) -> tuple:
    """
    Extrait les langues source et cible depuis le nom de la mémoire.
    Ex: "1.1 DROIT FINANCIER FR<>EN" -> ("FR", "EN")
    Ex: "GENERIQUE_EN_DE" -> ("EN", "DE")
    Ex: "FR<>ENUS" -> ("FR", "en-US")
    Ex: "FR<>ENus" -> ("FR", "en-US")
    Ex: "FRFR<>ENUS" -> ("fr-FR", "en-US")
    """
    # Premier pattern: FR<>ENUS ou FRFR<>EN (2 ou 4 lettres pour chaque langue, majuscules ou minuscules)
    match = re.search(r'([A-Za-z]{2,4})<>?([A-Za-z]{2,4})', name)
    if match:
        # Convertir en majuscules avant de formater
        source = format_lang_code(match.group(1).upper())
        target = format_lang_code(match.group(2).upper())
        return source, target

    # Deuxième pattern: _ENUS_DE ou _EN_DEDE (2 ou 4 lettres pour chaque langue, majuscules ou minuscules)
    match = re.search(r'_([A-Za-z]{2,4})_([A-Za-z]{2,4})', name)
    if match:
        # Convertir en majuscules avant de formater
        source = format_lang_code(match.group(1).upper())
        target = format_lang_code(match.group(2).upper())
        return source, target

    return '', ''


def fetch_lara_memories() -> List[Dict]:
    """
    Récupère la liste des mémoires de traduction depuis Lara.
    Utilise le SDK Python officiel lara-sdk.

    Returns:
        Liste de dictionnaires contenant les informations des mémoires.
    """
    import logging
    logger = logging.getLogger(__name__)

    # Récupérer les credentials
    access_key_id = os.getenv('LARA_ACCESS_KEY_ID')
    access_key_secret = os.getenv('LARA_ACCESS_KEY_SECRET')

    logger.info(f"LARA_ACCESS_KEY_ID présent: {bool(access_key_id)}")
    logger.info(f"LARA_ACCESS_KEY_SECRET présent: {bool(access_key_secret)}")

    if not access_key_id or not access_key_secret:
        raise Exception('Missing LARA_ACCESS_KEY_ID or LARA_ACCESS_KEY_SECRET')

    try:
        # Créer les credentials et le client Lara
        logger.info("Création des credentials Lara...")
        credentials = Credentials(access_key_id, access_key_secret)
        lara = Translator(credentials)
        logger.info("Client Lara créé avec succès")

        # Récupérer les mémoires via le SDK
        logger.info("Appel à lara.memories.list()...")
        memories_list = lara.memories.list()
        logger.info(f"Réponse reçue: type={type(memories_list)}, longueur={len(memories_list) if hasattr(memories_list, '__len__') else 'N/A'}")

        if memories_list:
            logger.info(f"Premier élément: {memories_list[0]}")

        # Parser la réponse
        memories = []
        for m in memories_list:
            # Extraire les langues depuis le nom (le SDK Python ne fournit pas sourceLanguage/targetLanguage)
            source, target = extract_langs_from_name(m.name)

            # Détecter si c'est une mémoire générique pour assigner le domaine "*"
            domain = ''
            if m.name and 'GENERIQUE' in m.name.upper():
                domain = '*'

            memory = {
                'id': m.id or '',
                'name': m.name or '',
                'sourceLanguage': source,
                'targetLanguage': target,
                'domain': domain
            }

            memories.append(memory)

        logger.info(f"Nombre de mémoires parsées: {len(memories)}")
        return memories

    except Exception as e:
        logger.error(f"Exception lors de la récupération des mémoires: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise Exception(f"Failed to fetch memories from Lara: {str(e)}")


def compare_memories(db_memories: List[Dict], lara_memories: List[Dict]) -> List[Dict]:
    """
    Compare les mémoires de la base de données avec celles de Lara.

    Args:
        db_memories: Liste des mémoires depuis la DB
        lara_memories: Liste des mémoires depuis Lara

    Returns:
        Liste de différences avec colonnes: memory_id, name, source_language,
        target_language, modification
    """
    import logging
    logger = logging.getLogger(__name__)

    differences = []

    # Créer des dictionnaires pour faciliter la comparaison
    # Normaliser les IDs en string pour la comparaison
    db_dict = {str(m['memory_id']): m for m in db_memories}
    lara_dict = {str(m['id']): m for m in lara_memories}

    # Debug logging
    logger.info(f"DB memories count: {len(db_dict)}")
    logger.info(f"Lara memories count: {len(lara_dict)}")
    logger.info(f"DB IDs: {list(db_dict.keys())[:5]}")  # First 5
    logger.info(f"Lara IDs: {list(lara_dict.keys())[:5]}")  # First 5

    # Trouver les nouvelles mémoires (dans Lara mais pas dans DB)
    for lara_id, lara_mem in lara_dict.items():
        if lara_id not in db_dict:
            differences.append({
                'memory_id': lara_mem['id'],
                'name': lara_mem['name'],
                'source_language': lara_mem.get('sourceLanguage', ''),
                'target_language': lara_mem.get('targetLanguage', ''),
                'domain': lara_mem.get('domain', ''),
                'modification': 'nouvelle',
                'action': 'add',
                'changes_detail': ''
            })

    # Trouver les mémoires supprimées (dans DB mais pas dans Lara)
    for db_id, db_mem in db_dict.items():
        if db_id not in lara_dict:
            differences.append({
                'memory_id': db_mem['memory_id'],
                'name': db_mem['name'],
                'source_language': db_mem.get('source_language', ''),
                'target_language': db_mem.get('target_language', ''),
                'domain': db_mem.get('domain', ''),
                'modification': 'supprimée',
                'action': 'delete',
                'changes_detail': ''
            })

    # Trouver les mémoires modifiées (dans les deux mais avec des différences)
    for db_id, db_mem in db_dict.items():
        if db_id in lara_dict:
            lara_mem = lara_dict[db_id]
            modifications = []
            changes_details = []

            # Comparer name
            if db_mem.get('name', '') != lara_mem.get('name', ''):
                old_val = db_mem.get('name', '')
                new_val = lara_mem.get('name', '')
                modifications.append('name')
                changes_details.append(f"{old_val} → {new_val}")

            # Comparer source_language
            if db_mem.get('source_language', '') != lara_mem.get('sourceLanguage', ''):
                old_val = db_mem.get('source_language', '')
                new_val = lara_mem.get('sourceLanguage', '')
                modifications.append('source_language')
                changes_details.append(f"{old_val} → {new_val}")

            # Comparer target_language
            if db_mem.get('target_language', '') != lara_mem.get('targetLanguage', ''):
                old_val = db_mem.get('target_language', '')
                new_val = lara_mem.get('targetLanguage', '')
                modifications.append('target_language')
                changes_details.append(f"{old_val} → {new_val}")

            # Comparer domain - seulement si la nouvelle valeur est "*"
            if lara_mem.get('domain', '') == '*' and db_mem.get('domain', '') != '*':
                old_val = db_mem.get('domain', '') or '(vide)'
                new_val = lara_mem.get('domain', '')
                modifications.append('domain')
                changes_details.append(f"{old_val} → {new_val}")

            if modifications:
                differences.append({
                    'memory_id': db_id,
                    'name': lara_mem.get('name', ''),
                    'source_language': lara_mem.get('sourceLanguage', ''),
                    'target_language': lara_mem.get('targetLanguage', ''),
                    'domain': lara_mem.get('domain', ''),
                    'modification': f"modifiée: {', '.join(modifications)}",
                    'action': 'update',
                    'changes_detail': ' | '.join(changes_details)
                })

    return differences
