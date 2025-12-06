"""
API endpoints for glossaries.

Provides REST API for glossary CRUD operations.
"""
import os
import logging

from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Glossary
from ..serializers import GlossarySerializer
from ..services import (
    save_glossary_file,
    read_csv_languages,
    validate_system_glossary_name,
    create_glossary_in_lara,
    update_glossary_in_lara,
    delete_glossary_in_lara,
)
from ..services.file_utils import cleanup_file
from apps.languages.models import Language

logger = logging.getLogger(__name__)


@api_view(['GET'])
def glossary_list(request):
    """
    GET /api/lara/glossaries-list/

    Returns list of all glossaries.
    """
    try:
        glossaries = Glossary.objects.all().select_related('source_language')
        serializer = GlossarySerializer(glossaries, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {'error': str(e), 'details': 'Error retrieving glossaries'},
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


@api_view(['POST'])
def create_glossary(request):
    """
    POST /api/lara/glossaries-list/create/

    Creates a new glossary.

    Parameters:
        - user_glossary_name: Name given by the user
        - uuid: (optional) User UUID for personal glossary
        - glossary_file: CSV file

    For personal glossary (uuid provided):
        - Normalized name: <uuid>_<source>_<target>
        - Domain: "*"

    For system glossary (no uuid):
        - Name must be: Legal_<Domain>_<SourceLang>
        - Domain extracted from name

    Returns:
        201: Glossary created successfully
        400: Validation error
        500: Server or LARA error
    """
    try:
        # Get parameters
        user_glossary_name = request.POST.get('user_glossary_name') or request.data.get('user_glossary_name')
        uuid = request.POST.get('uuid') or request.data.get('uuid')
        glossary_file = request.FILES.get('glossary_file')

        # Validate required parameters
        if not user_glossary_name:
            return Response(
                {'error': 'Parameter user_glossary_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not glossary_file:
            return Response(
                {'error': 'File glossary_file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save file
        try:
            filepath = save_glossary_file(glossary_file, uuid)
            logger.info(f"Glossary file saved: {filepath}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return Response(
                {'error': f'Error saving file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Read languages from CSV
        try:
            source_lang, target_langs = read_csv_languages(filepath)
            logger.info(f"Detected languages - Source: {source_lang}, Targets: {target_langs}")
        except ValueError as e:
            cleanup_file(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Determine glossary type and normalize name
        if uuid:
            # Personal glossary
            target_lang = target_langs[0] if len(target_langs) == 1 else '_'.join(sorted(target_langs))
            normalized_name = f"{uuid}_{source_lang}_{target_lang}"
            domain = '*'
            glossary_type = 'personal'
            logger.info(f"Personal glossary - Normalized name: {normalized_name}")
        else:
            # System glossary
            try:
                domain, validated_source = validate_system_glossary_name(user_glossary_name, source_lang)
                normalized_name = user_glossary_name
                glossary_type = 'system'
                logger.info(f"System glossary - Domain: {domain}, Source: {validated_source}")
            except ValueError as e:
                cleanup_file(filepath)
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Create glossary in LARA
        try:
            lara_result = create_glossary_in_lara(normalized_name, filepath)
            logger.info(f"Glossary created in LARA: {lara_result}")
        except ValueError as e:
            cleanup_file(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            cleanup_file(filepath)
            return Response(
                {'error': f'Error creating in LARA: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Get Language object for source_language
        source_language_obj = Language.objects.filter(abbreviation=source_lang).first()

        # Save to database
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
            logger.info(f"Glossary saved to DB: {glossary.glossary_id}")
        except Exception as e:
            logger.error(f"Error saving to DB: {e}")
            return Response(
                {
                    'warning': f'Glossary created in LARA but DB error: {str(e)}',
                    'glossary_id': lara_result['glossary_id'],
                    'name': normalized_name
                },
                status=status.HTTP_201_CREATED
            )

        # Cleanup file after successful creation
        cleanup_file(filepath)

        # Success
        return Response(
            {
                'message': 'Glossary created successfully',
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
        logger.error(f"Unexpected error creating glossary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT', 'POST'])
def update_glossary(request, glossary_id):
    """
    PUT/POST /api/lara/glossaries-list/<glossary_id>/update/

    Updates an existing glossary by re-importing a CSV file.

    Parameters:
        - glossary_file: New CSV file
        - user_glossary_name: (optional) New display name

    Returns:
        200: Glossary updated successfully
        400: Validation error
        404: Glossary not found
        500: Server or LARA error
    """
    try:
        # Find glossary
        try:
            glossary = Glossary.objects.get(glossary_id=glossary_id)
        except Glossary.DoesNotExist:
            return Response(
                {'error': f'Glossary {glossary_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        glossary_file = request.FILES.get('glossary_file')
        user_glossary_name = request.POST.get('user_glossary_name') or request.data.get('user_glossary_name')

        if not glossary_file:
            return Response(
                {'error': 'File glossary_file is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Save file temporarily
        try:
            filepath = save_glossary_file(glossary_file, glossary.uuid if glossary.uuid != '*' else None)
            logger.info(f"Glossary file saved for update: {filepath}")
        except Exception as e:
            logger.error(f"Error saving file: {e}")
            return Response(
                {'error': f'Error saving file: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Read languages from CSV
        try:
            source_lang, target_langs = read_csv_languages(filepath)
            logger.info(f"Detected languages - Source: {source_lang}, Targets: {target_langs}")
        except ValueError as e:
            cleanup_file(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update glossary in LARA
        try:
            lara_result = update_glossary_in_lara(glossary_id, filepath)
            logger.info(f"Glossary updated in LARA: {lara_result}")
        except ValueError as e:
            cleanup_file(filepath)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            cleanup_file(filepath)
            return Response(
                {'error': f'Error updating in LARA: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Update local database
        try:
            source_language_obj = Language.objects.filter(abbreviation=source_lang).first()

            glossary.source_language = source_language_obj
            glossary.target_languages = ','.join(target_langs)

            if user_glossary_name:
                glossary.user_glossary_name = user_glossary_name

            glossary.save()
            logger.info(f"Glossary updated in DB: {glossary.glossary_id}")
        except Exception as e:
            logger.error(f"Error updating DB: {e}")
            # LARA was updated, return partial success
            return Response(
                {
                    'warning': f'Glossary updated in LARA but DB error: {str(e)}',
                    'glossary_id': glossary_id
                },
                status=status.HTTP_200_OK
            )

        # Cleanup file
        cleanup_file(filepath)

        # Success
        return Response(
            {
                'message': 'Glossary updated successfully',
                'glossary_id': glossary.glossary_id,
                'name': glossary.name,
                'user_glossary_name': glossary.user_glossary_name,
                'source_language': source_lang,
                'target_languages': target_langs,
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Unexpected error updating glossary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE', 'POST'])
def delete_glossary(request, glossary_id):
    """
    DELETE/POST /api/lara/glossaries-list/<glossary_id>/delete/

    Deletes a glossary from both LARA and local database.

    Returns:
        200: Glossary deleted successfully
        404: Glossary not found
        500: Server or LARA error
    """
    try:
        # Find glossary
        try:
            glossary = Glossary.objects.get(glossary_id=glossary_id)
        except Glossary.DoesNotExist:
            return Response(
                {'error': f'Glossary {glossary_id} not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        glossary_name = glossary.name
        glossary_uuid = glossary.uuid

        # Delete from LARA
        try:
            delete_glossary_in_lara(glossary_id)
            logger.info(f"Glossary deleted from LARA: {glossary_id}")
        except Exception as e:
            logger.error(f"Error deleting from LARA: {e}")
            # Continue with local deletion even if LARA fails
            # The glossary might already be deleted in LARA

        # Delete from local database
        try:
            glossary.delete()
            logger.info(f"Glossary deleted from DB: {glossary_id}")
        except Exception as e:
            logger.error(f"Error deleting from DB: {e}")
            return Response(
                {'error': f'Error deleting from database: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # Success
        return Response(
            {
                'message': 'Glossary deleted successfully',
                'glossary_id': glossary_id,
                'name': glossary_name,
                'uuid': glossary_uuid
            },
            status=status.HTTP_200_OK
        )

    except Exception as e:
        logger.error(f"Unexpected error deleting glossary: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return Response(
            {'error': f'Unexpected error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def search_glossaries(request):
    """
    GET /api/lara/glossaries-list/search/

    Search glossaries by criteria.

    Query parameters:
        - uuid: User UUID (default: "*" for system glossaries)
        - source_language: Source language code (e.g., "FR")
        - target_languages: Target language code(s), comma-separated (e.g., "EN" or "EN,DE")
        - domain: Domain name (default: "*" for all domains)

    Returns:
        200: List of matching glossaries
    """
    try:
        # Get parameters with defaults
        uuid = request.query_params.get('uuid', '*')
        source_language = request.query_params.get('source_language', '').upper()
        target_languages = request.query_params.get('target_languages', '').upper()
        domain = request.query_params.get('domain', '*')

        # Build query
        queryset = Glossary.objects.all()

        # Filter by uuid
        queryset = queryset.filter(uuid=uuid)

        # Filter by source_language if provided
        if source_language:
            queryset = queryset.filter(source_language__abbreviation=source_language)

        # Filter by domain
        queryset = queryset.filter(domain=domain)

        # Filter by target_languages if provided
        if target_languages:
            requested_targets = set(lang.strip() for lang in target_languages.split(',') if lang.strip())

            matching_glossaries = []
            for glossary in queryset:
                glossary_targets = set(glossary.get_target_languages_list())
                if requested_targets.issubset(glossary_targets):
                    matching_glossaries.append(glossary)
        else:
            matching_glossaries = list(queryset)

        # Return glossaries with ID and name
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
        logger.error(f"Error searching glossaries: {e}")
        return Response(
            {'error': f'Search error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
