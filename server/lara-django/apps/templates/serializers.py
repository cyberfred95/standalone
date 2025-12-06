"""
Serializers for TranslationTemplate models.
"""
from rest_framework import serializers
from .models import TranslationTemplate


class TranslationTemplateSerializer(serializers.ModelSerializer):
    """Serializer for TranslationTemplate model matching Node.js API format."""
    id = serializers.CharField(source='template_id', read_only=True)
    isDefault = serializers.BooleanField(source='is_default')
    sourceLanguage = serializers.CharField(source='source_language')
    targetLanguage = serializers.CharField(source='target_language')
    translationMemoryId = serializers.CharField(source='translation_memory_id', allow_blank=True)
    translationMemoryName = serializers.CharField(source='translation_memory_name', allow_blank=True)
    glossaryId = serializers.CharField(source='glossary_id', allow_blank=True)
    glossaryName = serializers.CharField(source='glossary_name', allow_blank=True)
    
    class Meta:
        model = TranslationTemplate
        fields = [
            'id', 'name', 'isDefault', 'domain', 
            'sourceLanguage', 'targetLanguage',
            'translationMemoryId', 'translationMemoryName',
            'glossaryId', 'glossaryName',
            'description'
        ]
