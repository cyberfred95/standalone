"""
Views for Glossary API endpoints and admin actions.
"""
import json
from datetime import datetime, timedelta
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.http import StreamingHttpResponse
from django.core.cache import cache
from .models import Glossary
from .serializers import GlossarySerializer
from .lara_service_glossaries import (
    fetch_lara_glossaries,
    fetch_lara_glossaries_with_progress,
    compare_glossaries,
    save_glossary_file,
    read_csv_languages,
    validate_system_glossary_name,
    create_glossary_in_lara
)
from apps.languages.models import Language


@api_view(['GET'])
def glossary_list(request):
    """
    GET /api/lara/glossaries-list/
    Returns list of all glossaries.
    Matches the Node.js API format.
    """
    try:
        glossaries = Glossary.objects.all().select_related('source_language')
        serializer = GlossarySerializer(glossaries, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'details': 'Error retrieving glossaries'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class GlossaryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Glossary model.
    Provides list and retrieve actions.
    """
    queryset = Glossary.objects.all()
    serializer_class = GlossarySerializer
    lookup_field = 'glossary_id'


@staff_member_required
def refresh_glossaries_form(request):
    """
    Display the form to select the date from which to refresh glossaries.
    """
    # Default: 1 month ago
    default_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    context = {
        'title': 'Refresh Glossaries from Lara',
        'default_date': default_date
    }

    return render(request, 'admin/glossaries/refresh_form.html', context)


@staff_member_required
def loading_page(request):
    """
    Display the loading page with progress bar.
    """
    since_date = request.GET.get('since_date', '')

    context = {
        'since_date': since_date
    }

    return render(request, 'admin/glossaries/loading.html', context)


@staff_member_required
def fetch_progress(request):
    """
    SSE endpoint that streams progress while fetching glossaries from Lara.
    """
    since_date_str = request.GET.get('since_date', '')
    since_date = None

    if since_date_str:
        try:
            since_date = datetime.strptime(since_date_str, '%Y-%m-%d')
        except ValueError:
            pass

    def event_stream():
        for event in fetch_lara_glossaries_with_progress(since_date):
            if event['type'] == 'complete':
                # Store glossaries in cache for compare_with_lara to retrieve
                cache_key = f'lara_glossaries_{request.user.id}'
                cache.set(cache_key, event['glossaries'], timeout=300)  # 5 minutes
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            else:
                yield f"data: {json.dumps(event)}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@staff_member_required
def compare_with_lara(request):
    """
    Compare current database glossaries with Lara API glossaries.
    Display differences in a comparison table.
    """
    try:
        # Get the since_date from GET or POST
        since_date_str = request.GET.get('since_date') or request.POST.get('since_date')
        from_loading = request.GET.get('from_loading') == '1'
        since_date = None

        if since_date_str:
            try:
                since_date = datetime.strptime(since_date_str, '%Y-%m-%d')
            except ValueError:
                messages.error(request, "Format de date invalide. Utilisez YYYY-MM-DD")
                return redirect('glossaries_refresh_form')

        # Fetch current DB glossaries
        db_glossaries_list = []
        for g in Glossary.objects.all().select_related('source_language'):
            db_glossaries_list.append({
                'glossary_id': g.glossary_id,
                'name': g.name,
                'uuid': g.uuid,
                'source_language': g.source_language.abbreviation if g.source_language else '',
                'target_languages': g.target_languages,
                'domain': g.domain or ''
            })

        # Try to get from cache if coming from loading page
        lara_glossaries = None
        if from_loading:
            cache_key = f'lara_glossaries_{request.user.id}'
            lara_glossaries = cache.get(cache_key)
            if lara_glossaries:
                cache.delete(cache_key)  # Clean up

        # Fallback to direct fetch if not in cache
        if lara_glossaries is None:
            lara_glossaries = fetch_lara_glossaries(since_date)

        # Compare
        differences = compare_glossaries(db_glossaries_list, lara_glossaries)

        context = {
            'differences': differences,
            'differences_json': json.dumps(differences),
            'title': 'Refresh Glossaries from Lara - Comparison',
            'since_date': since_date_str or 'Toutes'
        }

        return render(request, 'admin/glossaries/compare_lara.html', context)

    except Exception as e:
        messages.error(request, f"Error fetching glossaries from Lara: {str(e)}")
        return redirect('admin:glossaries_glossary_changelist')


@staff_member_required
def apply_lara_changes(request):
    """
    Apply the changes from Lara to the database.
    """
    if request.method != 'POST':
        return redirect('admin:glossaries_glossary_changelist')

    try:
        # Get all differences and selected indices
        all_differences_json = request.POST.get('all_differences', '[]')
        all_differences = json.loads(all_differences_json)

        # Get selected change indices
        selected_indices = request.POST.getlist('selected_changes')

        if not selected_indices:
            messages.warning(request, "Aucun changement sélectionné")
            return redirect('admin:glossaries_glossary_changelist')

        # Filter to only selected differences
        differences = [all_differences[int(idx)] for idx in selected_indices if int(idx) < len(all_differences)]

        stats = {
            'added': 0,
            'updated': 0
        }

        with transaction.atomic():
            for diff in differences:
                action = diff.get('action')
                glossary_id = diff.get('glossary_id')

                # Get source language
                source_lang_code = diff.get('source_language', '').upper()
                source_lang = None
                if source_lang_code:
                    source_lang = Language.objects.filter(abbreviation=source_lang_code).first()

                if action == 'add':
                    # Add new glossary
                    Glossary.objects.create(
                        glossary_id=glossary_id,
                        name=diff.get('name', ''),
                        uuid=diff.get('uuid', ''),
                        source_language=source_lang,
                        target_languages=diff.get('target_languages', ''),
                        domain=diff.get('domain', '')
                    )
                    stats['added'] += 1

                elif action == 'update':
                    # Update existing glossary
                    glossary = Glossary.objects.filter(glossary_id=glossary_id).first()
                    if glossary:
                        glossary.name = diff.get('name', glossary.name)

                        if diff.get('uuid'):
                            glossary.uuid = diff.get('uuid')

                        if source_lang:
                            glossary.source_language = source_lang

                        if diff.get('target_languages'):
                            glossary.target_languages = diff.get('target_languages')

                        if diff.get('domain'):
                            glossary.domain = diff.get('domain')

                        glossary.save()
                        stats['updated'] += 1

        # Create success message
        msg_parts = []
        if stats['added'] > 0:
            msg_parts.append(f"{stats['added']} nouveau(x) glossaire(s) ajouté(s)")
        if stats['updated'] > 0:
            msg_parts.append(f"{stats['updated']} glossaire(s) mis à jour")

        if msg_parts:
            messages.success(request, "Synchronisation réussie: " + ", ".join(msg_parts))
        else:
            messages.info(request, "Aucun changement à appliquer")

        return redirect('admin:glossaries_glossary_changelist')

    except Exception as e:
        messages.error(request, f"Erreur lors de l'application des changements: {str(e)}")
        return redirect('admin:glossaries_glossary_changelist')


@api_view(['POST'])
def create_glossary(request):
    """
    POST /api/lara/glossaries-list/create/

    Crée un nouveau glossaire.

    Paramètres:
        - user_glossary_name: Nom du glossaire donné par l'utilisateur
        - uuid: (optionnel) UUID de l'utilisateur pour un glossaire personnel
        - glossary_file: Fichier CSV du glossaire

    Pour un glossaire personnel (uuid fourni):
        - Le nom normalisé sera: <uuid>_<source>_<target>
        - Le domain sera: "*"

    Pour un glossaire système (pas de uuid):
        - Le nom doit être au format: Legal_<Domain>_<SourceLang>
        - Le domain est extrait du nom et doit exister dans Lexa

    Returns:
        201: Glossaire créé avec succès
        400: Erreur de validation
        500: Erreur serveur ou Lara
    """
    import os
    import logging

    logger = logging.getLogger(__name__)

    try:
        # Récupérer les paramètres
        user_glossary_name = request.POST.get('user_glossary_name') or request.data.get('user_glossary_name')
        uuid = request.POST.get('uuid') or request.data.get('uuid')
        glossary_file = request.FILES.get('glossary_file')

        # Validation des paramètres requis
        if not user_glossary_name:
            return Response(
                {'error': 'Le paramètre user_glossary_name est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not glossary_file:
            return Response(
                {'error': 'Le fichier glossary_file est requis'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Sauvegarder le fichier
        try:
            filepath = save_glossary_file(glossary_file, uuid)
            logger.info(f"Fichier glossaire sauvegardé: {filepath}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde du fichier: {e}")
            return Response(
                {'error': f'Erreur lors de la sauvegarde du fichier: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Lire les langues depuis le CSV
        try:
            source_lang, target_langs = read_csv_languages(filepath)
            logger.info(f"Langues détectées - Source: {source_lang}, Cibles: {target_langs}")
        except ValueError as e:
            # Nettoyer le fichier en cas d'erreur
            os.remove(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Déterminer le type de glossaire et normaliser le nom
        if uuid:
            # Glossaire personnel
            # Format: <uuid>_<source>_<target>
            # Pour plusieurs langues cibles, on prend la première
            target_lang = target_langs[0] if len(target_langs) == 1 else '_'.join(sorted(target_langs))
            normalized_name = f"{uuid}_{source_lang}_{target_lang}"
            domain = '*'
            glossary_type = 'personal'

            logger.info(f"Glossaire personnel - Nom normalisé: {normalized_name}")
        else:
            # Glossaire système
            try:
                domain, validated_source = validate_system_glossary_name(user_glossary_name, source_lang)
                normalized_name = user_glossary_name
                glossary_type = 'system'

                logger.info(f"Glossaire système - Domain: {domain}, Source: {validated_source}")
            except ValueError as e:
                os.remove(filepath)
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Créer le glossaire dans Lara
        try:
            lara_result = create_glossary_in_lara(normalized_name, filepath)
            logger.info(f"Glossaire créé dans Lara: {lara_result}")
        except ValueError as e:
            # Erreur de format CSV
            os.remove(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            os.remove(filepath)
            return Response(
                {'error': f'Erreur lors de la création dans Lara: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Récupérer l'objet Language pour source_language
        source_language_obj = Language.objects.filter(abbreviation=source_lang).first()

        # Sauvegarder dans la base de données
        try:
            glossary = Glossary.objects.create(
                glossary_id=lara_result['glossary_id'],
                name=normalized_name,
                user_glossary_name=user_glossary_name,
                uuid=uuid if uuid else '*',
                source_language=source_language_obj,
                target_languages=','.join(target_langs),
                domain=domain
            )
            logger.info(f"Glossaire sauvegardé en DB: {glossary.glossary_id}")
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde en DB: {e}")
            # Le glossaire existe dans Lara mais pas en DB
            # On retourne quand même un succès partiel
            return Response(
                {
                    'warning': f'Glossaire créé dans Lara mais erreur DB: {str(e)}',
                    'glossary_id': lara_result['glossary_id'],
                    'name': normalized_name
                },
                status=status.HTTP_201_CREATED
            )

        # Succès complet
        return Response(
            {
                'message': 'Glossaire créé avec succès',
                'glossary_id': glossary.glossary_id,
                'name': glossary.name,
                'user_glossary_name': glossary.user_glossary_name,
                'uuid': glossary.uuid,
                'source_language': source_lang,
                'target_languages': target_langs,
                'domain': domain,
                'type': glossary_type
            },
            status=status.HTTP_201_CREATED
        )

    except Exception as e:
        logger.error(f"Erreur inattendue lors de la création du glossaire: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': f'Erreur inattendue: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def get_glossaries(request):
    """
    GET /api/lara/glossaries-list/search/

    Recherche des glossaires selon les critères fournis.

    Paramètres (query params):
        - uuid: UUID de l'utilisateur (défaut: "*" pour glossaires système)
        - source_language: Code de la langue source (ex: "FR")
        - target_languages: Code(s) de langue(s) cible(s), séparés par virgule (ex: "EN" ou "EN,DE")
        - domain: Nom du domaine (défaut: "*" pour tous les domaines)

    Returns:
        200: Liste des user_glossary_name correspondants
    """
    try:
        # Récupérer les paramètres avec valeurs par défaut
        uuid = request.query_params.get('uuid', '*')
        source_language = request.query_params.get('source_language', '').upper()
        target_languages = request.query_params.get('target_languages', '').upper()
        domain = request.query_params.get('domain', '*')

        # Construire la requête
        queryset = Glossary.objects.all()

        # Filtrer par uuid
        queryset = queryset.filter(uuid=uuid)

        # Filtrer par source_language si fourni
        if source_language:
            queryset = queryset.filter(source_language__abbreviation=source_language)

        # Filtrer par domain
        queryset = queryset.filter(domain=domain)

        # Filtrer par target_languages si fourni
        if target_languages:
            # Normaliser les langues cibles demandées
            requested_targets = set(lang.strip() for lang in target_languages.split(',') if lang.strip())

            # Filtrer les glossaires qui contiennent toutes les langues cibles demandées
            matching_glossaries = []
            for glossary in queryset:
                glossary_targets = set(glossary.get_target_languages_list())
                # Le glossaire doit contenir au moins toutes les langues demandées
                if requested_targets.issubset(glossary_targets):
                    matching_glossaries.append(glossary)
        else:
            # Pas de filtre sur target_languages
            matching_glossaries = list(queryset)

        # Retourner les glossaires avec leur ID et nom
        glossary_list = [
            {
                'glossary_id': g.glossary_id,
                'name': g.user_glossary_name or g.name
            }
            for g in matching_glossaries
        ]

        return Response({
            'glossaries': glossary_list,
            'count': len(glossary_list)
        })

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Erreur lors de la recherche de glossaires: {e}")
        return Response(
            {'error': f'Erreur lors de la recherche: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
