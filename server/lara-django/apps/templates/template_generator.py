"""
Service pour générer les templates de traduction depuis les Memories et Glossaries.

Nouvelle logique:
1. Partir des Memories (chaque Memory est associée à un domain_group et un couple de langues)
2. Pour chaque Memory, récupérer tous les domains du domain_group (via cache Lexa)
3. Pour chaque domain et chaque direction de langue (source→target ET target→source):
   - Chercher un Glossary correspondant (domain + langues)
   - Créer le template avec: domain, source, target, glossary?, memory
"""
import logging
from typing import List, Dict, Optional
from apps.memories.models import Memory
from apps.glossaries.models import Glossary

logger = logging.getLogger(__name__)


def find_glossary_for_domain_and_languages(domain: str, source_lang: str, target_lang: str) -> Optional[Glossary]:
    """
    Trouve un Glossary SYSTÈME pour un domain et un couple de langues.

    Le glossaire doit avoir:
    - uuid = '*' (glossaire système)
    - domain = domain (exact match)
    - source_language = source_lang
    - target_languages contient target_lang
    """
    source_upper = source_lang.upper()
    target_upper = target_lang.upper()

    # Chercher les glossaires SYSTÈME pour ce domain et cette source language
    # Seuls les glossaires avec uuid='*' sont pris en compte pour les templates
    glossaries = Glossary.objects.filter(
        uuid='*',  # Uniquement les glossaires système
        domain=domain,
        source_language__abbreviation=source_upper
    ).select_related('source_language')

    for glossary in glossaries:
        # Vérifier que target_lang est dans la liste des target_languages
        target_langs = glossary.get_target_languages_list()
        target_langs_upper = [lang.upper() for lang in target_langs]
        if target_upper in target_langs_upper:
            return glossary

    return None


def generate_templates_from_memories() -> List[Dict]:
    """
    Génère les templates depuis les Memories de la base de données.

    Pour chaque Memory avec un domain_group:
    1. Récupérer tous les domains du domain_group (via cache Lexa)
    2. Pour chaque domain, créer des templates dans les 2 sens (source→target et target→source)
    3. Pour chaque template, chercher un Glossary correspondant

    Returns:
        Liste de templates au format:
        {
            'template_id': str,
            'name': str,
            'is_default': bool,
            'domain': str,
            'source_language': str,
            'target_language': str,
            'translation_memory_id': str,
            'translation_memory_name': str,
            'glossary_id': str,
            'glossary_name': str,
            'description': str
        }
    """
    from apps.lexa_backend.services import get_lexa_domain_groups

    templates = []
    existing_combinations = set()  # Pour éviter les doublons: (domain, source, target)
    templates_by_combo = {}  # Pour pouvoir retrouver et mettre à jour un template existant

    # 1. Template par défaut
    templates.append({
        'template_id': 'default',
        'name': 'Default Template',
        'is_default': True,
        'domain': '*',
        'source_language': '*',
        'target_language': '*',
        'translation_memory_id': '',
        'translation_memory_name': '',
        'glossary_id': '',
        'glossary_name': '',
        'description': 'Template par défaut utilisé lorsqu\'aucune configuration spécifique n\'est trouvée'
    })

    # 2. Récupérer les domain groups depuis Lexa
    domain_groups = get_lexa_domain_groups()

    # Construire un dict domain_group_name → list of domains
    domains_by_group = {}
    for group in domain_groups:
        group_name = group.get('name', '')
        group_domains = group.get('domains', [])
        domain_names = [d.get('name') for d in group_domains if d.get('name')]
        domains_by_group[group_name] = domain_names

    logger.info(f"[TEMPLATE_GEN] {len(domains_by_group)} domain groups trouvés dans Lexa")

    # 3. Récupérer toutes les Memories avec un domain_group
    # Note: on inclut les mémoires génériques (domain_group='*') qui génèreront
    # un template avec domain='*' (pas un template par domaine)
    memories = Memory.objects.filter(
        domain_group__isnull=False
    ).exclude(
        domain_group=''
    ).select_related('source_language', 'target_language')

    logger.info(f"[TEMPLATE_GEN] {memories.count()} memories avec domain_group trouvées")

    # 4. Pour chaque Memory, générer les templates
    memory_count = 0
    total_memories = memories.count()
    templates_created = 0

    for memory in memories:
        memory_count += 1
        if memory_count % 10 == 0 or memory_count == total_memories:
            logger.info(f"[TEMPLATE_GEN] Progression: {memory_count}/{total_memories} memories traitées...")

        # Vérifier que la Memory a bien des langues définies
        if not memory.source_language or not memory.target_language:
            logger.warning(f"[TEMPLATE_GEN] Memory {memory.memory_id} sans langues source/target, ignorée")
            continue

        domain_group = memory.domain_group
        mem_source = memory.source_language.abbreviation
        mem_target = memory.target_language.abbreviation

        # Cas spécial: mémoire générique avec domain_group = "*"
        # On génère UN seul template avec domain = "*"
        if domain_group == '*':
            domains = ['*']
        else:
            # Récupérer tous les domains de ce domain_group
            domains = domains_by_group.get(domain_group, [])
            if not domains:
                logger.warning(f"[TEMPLATE_GEN] Domain group '{domain_group}' non trouvé dans Lexa pour memory {memory.memory_id}")
                continue

        # Pour chaque domain, créer des templates dans les 2 sens
        for domain in domains:
            # Direction 1: source → target
            combo1 = (domain.lower(), mem_source.lower(), mem_target.lower())
            if combo1 not in existing_combinations:
                glossary = find_glossary_for_domain_and_languages(domain, mem_source, mem_target)
                template = _create_template(
                    domain=domain,
                    source_lang=mem_source,
                    target_lang=mem_target,
                    memory=memory,
                    glossary=glossary
                )
                templates.append(template)
                existing_combinations.add(combo1)
                templates_by_combo[combo1] = template  # Stocker pour mise à jour ultérieure
                templates_created += 1

            # Direction 2: target → source (inverse)
            combo2 = (domain.lower(), mem_target.lower(), mem_source.lower())
            if combo2 not in existing_combinations:
                glossary = find_glossary_for_domain_and_languages(domain, mem_target, mem_source)
                template = _create_template(
                    domain=domain,
                    source_lang=mem_target,
                    target_lang=mem_source,
                    memory=memory,
                    glossary=glossary
                )
                templates.append(template)
                existing_combinations.add(combo2)
                templates_by_combo[combo2] = template  # Stocker pour mise à jour ultérieure
                templates_created += 1

    logger.info(f"[TEMPLATE_GEN] ✓ Étape 1/2: {templates_created} templates créés depuis les memories")

    # 5. Compléter avec les templates depuis les Glossaries SYSTÈME
    # Pour chaque Glossary système (uuid='*'):
    # - Si un template existe déjà (créé depuis une Memory), mettre à jour sa propriété glossary
    # - Sinon, créer un nouveau template avec seulement le Glossary
    # Note: Les glossaires personnels (uuid != '*') ne sont pas pris en compte pour la génération des templates
    glossaries = Glossary.objects.filter(
        uuid='*',  # Uniquement les glossaires système
        domain__isnull=False
    ).exclude(
        domain=''
    ).select_related('source_language')

    logger.info(f"[TEMPLATE_GEN] Traitement de {glossaries.count()} glossaries système...")

    templates_from_glossaries = 0
    templates_updated_with_glossary = 0
    for glossary in glossaries:
        domain = glossary.domain
        if not domain or not glossary.source_language:
            continue

        source_lang = glossary.source_language.abbreviation
        target_langs = glossary.get_target_languages_list()

        for target_lang in target_langs:
            # Normaliser
            target_lang_upper = target_lang.upper()

            combo = (domain.lower(), source_lang.lower(), target_lang_upper.lower())

            if combo in existing_combinations:
                # Template existe déjà (créé depuis une Memory)
                # Mettre à jour ses propriétés glossary si elles sont vides
                existing_template = templates_by_combo.get(combo)
                if existing_template and not existing_template.get('glossary_id'):
                    existing_template['glossary_id'] = glossary.glossary_id
                    existing_template['glossary_name'] = glossary.name
                    templates_updated_with_glossary += 1
            else:
                # Créer un nouveau template sans Memory, seulement avec le Glossary
                template = _create_template(
                    domain=domain,
                    source_lang=source_lang,
                    target_lang=target_lang_upper,
                    memory=None,
                    glossary=glossary
                )
                templates.append(template)
                existing_combinations.add(combo)
                templates_by_combo[combo] = template
                templates_from_glossaries += 1

    logger.info(f"[TEMPLATE_GEN] ✓ Étape 2/2: {templates_from_glossaries} templates créés depuis les glossaires système (sans memory)")
    logger.info(f"[TEMPLATE_GEN] ✓ {templates_updated_with_glossary} templates existants mis à jour avec un glossaire système")
    logger.info(f"[TEMPLATE_GEN] ✅ Génération terminée: {len(templates)} templates générés au total")
    return templates


def _create_template(domain: str, source_lang: str, target_lang: str,
                     memory: Optional[Memory], glossary: Optional[Glossary]) -> Dict:
    """
    Crée un dictionnaire template.
    """
    template_id = f"{domain.lower().replace(' ', '-').replace('/', '-')}-{source_lang.lower()}-{target_lang.lower()}"

    return {
        'template_id': template_id,
        'name': f"{domain} {source_lang} to {target_lang}",
        'is_default': False,
        'domain': domain,
        'source_language': source_lang,
        'target_language': target_lang,
        'translation_memory_id': memory.memory_id if memory else '',
        'translation_memory_name': memory.name if memory else '',
        'glossary_id': glossary.glossary_id if glossary else '',
        'glossary_name': glossary.name if glossary else '',
        'description': f"Template pour la traduction du domaine {domain} de {source_lang} vers {target_lang}"
    }


# Alias pour compatibilité avec le code existant
generate_templates_from_resources = generate_templates_from_memories


def compare_templates(db_templates: List[Dict], generated_templates: List[Dict]) -> List[Dict]:
    """
    Compare les templates actuels de la DB avec les templates générés.

    Args:
        db_templates: Liste des templates depuis la DB
        generated_templates: Liste des templates générés

    Returns:
        Liste de différences avec: template_id, name, domain, source_language,
        target_language, memory_name, glossary_name, modification, action
    """
    differences = []

    # Créer des dictionnaires pour faciliter la comparaison
    db_dict = {t['template_id']: t for t in db_templates}
    gen_dict = {t['template_id']: t for t in generated_templates}

    logger.info(f"[TEMPLATE_COMPARE] 🔍 Début de la comparaison: {len(db_dict)} templates DB vs {len(gen_dict)} templates générés")

    # Trouver les nouveaux templates
    for template_id, gen_template in gen_dict.items():
        if template_id not in db_dict:
            differences.append({
                'template_id': template_id,
                'name': gen_template['name'],
                'domain': gen_template['domain'],
                'source_language': gen_template['source_language'],
                'target_language': gen_template['target_language'],
                'translation_memory_name': gen_template['translation_memory_name'],
                'glossary_name': gen_template['glossary_name'],
                'modification': 'nouveau',
                'action': 'add',
                'changes_detail': '',
                'data': gen_template  # Stocker toutes les données pour l'ajout
            })

    # Trouver les templates supprimés
    for template_id, db_template in db_dict.items():
        if template_id not in gen_dict:
            differences.append({
                'template_id': template_id,
                'name': db_template['name'],
                'domain': db_template['domain'],
                'source_language': db_template['source_language'],
                'target_language': db_template['target_language'],
                'translation_memory_name': db_template.get('translation_memory_name', ''),
                'glossary_name': db_template.get('glossary_name', ''),
                'modification': 'supprimé',
                'action': 'delete',
                'changes_detail': ''
            })

    # Trouver les templates modifiés
    for template_id in db_dict.keys():
        if template_id in gen_dict:
            db_t = db_dict[template_id]
            gen_t = gen_dict[template_id]
            modifications = []
            changes_details = []

            # Comparer les champs importants
            if db_t.get('name', '') != gen_t.get('name', ''):
                modifications.append('name')
                changes_details.append(f"{db_t.get('name', '')} → {gen_t.get('name', '')}")

            if db_t.get('translation_memory_name', '') != gen_t.get('translation_memory_name', ''):
                modifications.append('memory')
                old_mem = db_t.get('translation_memory_name', '') or '(vide)'
                new_mem = gen_t.get('translation_memory_name', '') or '(vide)'
                changes_details.append(f"{old_mem} → {new_mem}")

            if db_t.get('glossary_name', '') != gen_t.get('glossary_name', ''):
                modifications.append('glossary')
                old_gls = db_t.get('glossary_name', '') or '(vide)'
                new_gls = gen_t.get('glossary_name', '') or '(vide)'
                changes_details.append(f"{old_gls} → {new_gls}")

            if modifications:
                differences.append({
                    'template_id': template_id,
                    'name': gen_t['name'],
                    'domain': gen_t['domain'],
                    'source_language': gen_t['source_language'],
                    'target_language': gen_t['target_language'],
                    'translation_memory_name': gen_t['translation_memory_name'],
                    'glossary_name': gen_t['glossary_name'],
                    'modification': f"modifié: {', '.join(modifications)}",
                    'action': 'update',
                    'changes_detail': ' | '.join(changes_details),
                    'data': gen_t  # Stocker toutes les données pour la mise à jour
                })

    # Compter les types de différences
    add_count = sum(1 for d in differences if d['action'] == 'add')
    update_count = sum(1 for d in differences if d['action'] == 'update')
    delete_count = sum(1 for d in differences if d['action'] == 'delete')

    logger.info(f"[TEMPLATE_COMPARE] ✅ Comparaison terminée: {len(differences)} différences trouvées")
    logger.info(f"[TEMPLATE_COMPARE]    - {add_count} ajouts")
    logger.info(f"[TEMPLATE_COMPARE]    - {update_count} modifications")
    logger.info(f"[TEMPLATE_COMPARE]    - {delete_count} suppressions")
    return differences
