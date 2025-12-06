"""
Views for TranslationTemplate API endpoints.
"""
from django.db.models import Q
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import TranslationTemplate
from .serializers import TranslationTemplateSerializer


@api_view(['GET'])
def template_list(request):
    """
    GET /api/templates/ or /api/lara/templates/
    Returns list of all templates.
    """
    try:
        templates = TranslationTemplate.objects.all()
        serializer = TranslationTemplateSerializer(templates, many=True)
        return Response(serializer.data)
    except Exception as e:
        return Response(
            {
                'error': str(e),
                'details': 'Error retrieving templates'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def find_template(request):
    """
    GET /api/templates/find or /api/lara/templates/find
    Finds templates matching criteria.
    Query params:
    - domain (optional)
    - sourceLanguage (optional)
    - targetLanguage (required)
    """
    domain = request.query_params.get('domain')
    source_lang = request.query_params.get('sourceLanguage')
    target_lang = request.query_params.get('targetLanguage')

    if not target_lang:
        return Response(
            {'error': 'targetLanguage is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Normalize language codes to uppercase (templates are stored in uppercase)
    target_lang = target_lang.upper() if target_lang else None
    source_lang = source_lang.upper() if source_lang else None

    try:
        # Start with base query
        query = Q(target_language=target_lang)

        # Add source language filter if provided
        if source_lang:
            query &= Q(source_language=source_lang)

        # Add domain filter if provided
        if domain:
            query &= Q(domain__iexact=domain)

        # Execute query
        templates = TranslationTemplate.objects.filter(query)

        # If no exact match found, try to find default template or fallback
        if not templates.exists():
            # Try finding templates with wildcard domain if domain was specified
            if domain:
                fallback_query = Q(target_language=target_lang) & Q(domain='*')
                if source_lang:
                    fallback_query &= Q(source_language=source_lang)
                templates = TranslationTemplate.objects.filter(fallback_query)

        serializer = TranslationTemplateSerializer(templates, many=True)
        return Response(serializer.data)

    except Exception as e:
        return Response(
            {
                'error': str(e),
                'details': 'Error finding templates'
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


class TemplateViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TranslationTemplate model.
    Provides CRUD actions.
    """
    queryset = TranslationTemplate.objects.all()
    serializer_class = TranslationTemplateSerializer
    lookup_field = 'template_id'

    def create(self, request, *args, **kwargs):
        # Custom create to handle camelCase to snake_case conversion if needed
        # But DRF serializer with source=... handles this mostly.
        return super().create(request, *args, **kwargs)
