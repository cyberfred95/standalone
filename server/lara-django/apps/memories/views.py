"""
Views for Memory API endpoints and admin actions.
"""
import json
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from .models import Memory
from .serializers import MemorySerializer
from .lara_service_memories import fetch_lara_memories, compare_memories
from apps.languages.models import Language
from apps.templates.models import TranslationTemplate
from apps.templates.template_generator import generate_templates_from_memories, compare_templates


@api_view(['GET'])
def memory_list(request):
    """
    GET /api/lara/memories-list/
    Returns list of all translation memories.
    Matches the Node.js API format.
    """
    try:
        memories = Memory.objects.all()
        serializer = MemorySerializer(memories, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'details': 'Error retrieving memories'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class MemoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Memory model.
    Provides list and retrieve actions.
    """
    queryset = Memory.objects.all()
    serializer_class = MemorySerializer
    lookup_field = 'memory_id'


@staff_member_required
def compare_with_lara(request):
    """
    Compare current database memories with Lara API memories.
    Display differences in a comparison table.
    """
    try:
        # Fetch current DB memories
        db_memories_list = []
        for mem in Memory.objects.all().select_related('source_language', 'target_language'):
            db_memories_list.append({
                'memory_id': mem.memory_id,
                'name': mem.name,
                'source_language': mem.source_language.abbreviation if mem.source_language else '',
                'target_language': mem.target_language.abbreviation if mem.target_language else '',
                'domain_group': mem.domain_group or ''
            })

        # Fetch Lara memories
        lara_memories = fetch_lara_memories()

        # Compare
        differences = compare_memories(db_memories_list, lara_memories)

        context = {
            'differences': differences,
            'differences_json': json.dumps(differences),
            'title': 'Refresh from Lara - Comparison'
        }

        return render(request, 'admin/memories/compare_lara.html', context)

    except Exception as e:
        messages.error(request, f"Error fetching memories from Lara: {str(e)}")
        return redirect('admin:memories_memory_changelist')


@staff_member_required
def apply_lara_changes(request):
    """
    Apply the changes from Lara to the database.
    Update both Memory and Resource tables.
    """
    if request.method != 'POST':
        return redirect('admin:memories_memory_changelist')

    try:
        # Get all differences and selected indices
        all_differences_json = request.POST.get('all_differences', '[]')
        all_differences = json.loads(all_differences_json)

        # Get selected change indices
        selected_indices = request.POST.getlist('selected_changes')

        if not selected_indices:
            messages.warning(request, "Aucun changement sélectionné")
            return redirect('admin:memories_memory_changelist')

        # Filter to only selected differences
        differences = [all_differences[int(idx)] for idx in selected_indices if int(idx) < len(all_differences)]

        stats = {
            'added': 0,
            'updated': 0,
            'deleted': 0
        }

        with transaction.atomic():
            for diff in differences:
                action = diff.get('action')
                memory_id = diff.get('memory_id')

                if action == 'add':
                    # Add new memory
                    # Normalize language codes to uppercase for lookup
                    source_lang = Language.objects.filter(
                        abbreviation=diff.get('source_language', '').upper()
                    ).first()
                    target_lang = Language.objects.filter(
                        abbreviation=diff.get('target_language', '').upper()
                    ).first()

                    # Détecter si c'est une mémoire générique pour assigner domain_group "*"
                    memory_name = diff.get('name', '')
                    domain_group = None
                    if 'GENERIQUE' in memory_name.upper():
                        domain_group = '*'

                    Memory.objects.create(
                        memory_id=memory_id,
                        name=memory_name,
                        source_language=source_lang,
                        target_language=target_lang,
                        domain_group=domain_group
                    )
                    stats['added'] += 1

                elif action == 'delete':
                    # Delete memory
                    Memory.objects.filter(memory_id=memory_id).delete()
                    stats['deleted'] += 1

                elif action == 'update':
                    # Update existing memory
                    memory = Memory.objects.filter(memory_id=memory_id).first()
                    if memory:
                        memory.name = diff.get('name', memory.name)

                        # Normalize language codes to uppercase for lookup
                        source_lang = Language.objects.filter(
                            abbreviation=diff.get('source_language', '').upper()
                        ).first()
                        if source_lang:
                            memory.source_language = source_lang

                        target_lang = Language.objects.filter(
                            abbreviation=diff.get('target_language', '').upper()
                        ).first()
                        if target_lang:
                            memory.target_language = target_lang

                        # Mettre à jour domain_group si c'est une mémoire générique
                        if 'GENERIQUE' in memory.name.upper():
                            memory.domain_group = '*'

                        memory.save()
                        stats['updated'] += 1

        # Create success message
        msg_parts = []
        if stats['added'] > 0:
            msg_parts.append(f"{stats['added']} nouvelle(s) mémoire(s) ajoutée(s)")
        if stats['updated'] > 0:
            msg_parts.append(f"{stats['updated']} mémoire(s) mise(s) à jour")
        if stats['deleted'] > 0:
            msg_parts.append(f"{stats['deleted']} mémoire(s) supprimée(s)")

        if msg_parts:
            messages.success(request, "Synchronisation réussie: " + ", ".join(msg_parts))
        else:
            messages.info(request, "Aucun changement à appliquer")

        return redirect('admin:memories_memory_changelist')

    except Exception as e:
        messages.error(request, f"Erreur lors de l'application des changements: {str(e)}")
        return redirect('admin:memories_memory_changelist')


@staff_member_required
def compare_templates_from_memories(request):
    """
    Compare current database templates with templates generated from Memories.
    Display differences in a comparison table.
    """
    import logging
    logger = logging.getLogger(__name__)

    try:
        logger.info("[TEMPLATE_VIEW] Début de la comparaison des templates depuis les memories")

        # Fetch current DB templates
        db_templates_list = []
        for template in TranslationTemplate.objects.all():
            db_templates_list.append({
                'template_id': template.template_id,
                'name': template.name,
                'is_default': template.is_default,
                'domain': template.domain,
                'source_language': template.source_language,
                'target_language': template.target_language,
                'translation_memory_id': template.translation_memory_id,
                'translation_memory_name': template.translation_memory_name,
                'glossary_id': template.glossary_id,
                'glossary_name': template.glossary_name,
                'description': template.description
            })

        logger.info(f"[TEMPLATE_VIEW] {len(db_templates_list)} templates chargés depuis la DB")

        # Generate templates from memories
        generated_templates = generate_templates_from_memories()
        logger.info(f"[TEMPLATE_VIEW] {len(generated_templates)} templates générés depuis les memories")

        # Compare
        differences = compare_templates(db_templates_list, generated_templates)
        logger.info(f"[TEMPLATE_VIEW] {len(differences)} différences trouvées")

        context = {
            'differences': differences,
            'differences_json': json.dumps(differences),
            'title': 'Refresh Templates from Memories - Comparison'
        }

        return render(request, 'admin/memories/compare_templates.html', context)

    except Exception as e:
        messages.error(request, f"Error generating templates from memories: {str(e)}")
        return redirect('admin:memories_memory_changelist')


@staff_member_required
def apply_template_changes(request):
    """
    Apply the template changes generated from Memories to the database.
    """
    if request.method != 'POST':
        return redirect('admin:memories_memory_changelist')

    try:
        # Get all differences and selected indices
        all_differences_json = request.POST.get('all_differences', '[]')
        all_differences = json.loads(all_differences_json)

        # Get selected change indices
        selected_indices = request.POST.getlist('selected_changes')

        if not selected_indices:
            messages.warning(request, "Aucun changement sélectionné")
            return redirect('admin:memories_memory_changelist')

        # Filter to only selected differences
        differences = [all_differences[int(idx)] for idx in selected_indices if int(idx) < len(all_differences)]

        stats = {
            'added': 0,
            'updated': 0,
            'deleted': 0
        }

        with transaction.atomic():
            for diff in differences:
                action = diff.get('action')
                template_id = diff.get('template_id')

                if action == 'add':
                    # Add new template
                    template_data = diff.get('data', {})
                    TranslationTemplate.objects.create(
                        template_id=template_id,
                        name=template_data.get('name', ''),
                        is_default=template_data.get('is_default', False),
                        domain=template_data.get('domain', ''),
                        source_language=template_data.get('source_language', ''),
                        target_language=template_data.get('target_language', ''),
                        translation_memory_id=template_data.get('translation_memory_id', ''),
                        translation_memory_name=template_data.get('translation_memory_name', ''),
                        glossary_id=template_data.get('glossary_id', ''),
                        glossary_name=template_data.get('glossary_name', ''),
                        description=template_data.get('description', '')
                    )
                    stats['added'] += 1

                elif action == 'delete':
                    # Delete template
                    TranslationTemplate.objects.filter(template_id=template_id).delete()
                    stats['deleted'] += 1

                elif action == 'update':
                    # Update existing template
                    template = TranslationTemplate.objects.filter(template_id=template_id).first()
                    if template:
                        template_data = diff.get('data', {})
                        template.name = template_data.get('name', template.name)
                        template.translation_memory_id = template_data.get('translation_memory_id', '')
                        template.translation_memory_name = template_data.get('translation_memory_name', '')
                        template.glossary_id = template_data.get('glossary_id', '')
                        template.glossary_name = template_data.get('glossary_name', '')
                        template.description = template_data.get('description', template.description)
                        template.save()
                        stats['updated'] += 1

        # Create success message
        msg_parts = []
        if stats['added'] > 0:
            msg_parts.append(f"{stats['added']} nouveau(x) template(s) ajouté(s)")
        if stats['updated'] > 0:
            msg_parts.append(f"{stats['updated']} template(s) mis à jour")
        if stats['deleted'] > 0:
            msg_parts.append(f"{stats['deleted']} template(s) supprimé(s)")

        if msg_parts:
            messages.success(request, "Synchronisation des templates réussie: " + ", ".join(msg_parts))
        else:
            messages.info(request, "Aucun changement de template à appliquer")

        return redirect('admin:memories_memory_changelist')

    except Exception as e:
        messages.error(request, f"Erreur lors de l'application des changements de templates: {str(e)}")
        return redirect('admin:memories_memory_changelist')
