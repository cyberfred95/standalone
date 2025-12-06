"""
Serializers for Translation API.
"""
import json
from rest_framework import serializers
from .models import DocumentTranslation


class FlexibleListField(serializers.Field):
    """
    A flexible field that accepts either a list or a string.
    If a string is provided, it will be converted to a list:
    - JSON string: parsed as JSON
    - Comma-separated string: split by comma
    - Single value: wrapped in a list
    """
    def to_internal_value(self, data):
        if data is None or data == '':
            return []
        if isinstance(data, list):
            return data
        if isinstance(data, str):
            # Try to parse as JSON first
            try:
                parsed = json.loads(data)
                if isinstance(parsed, list):
                    return parsed
                return [parsed]
            except json.JSONDecodeError:
                # Treat as comma-separated string
                if ',' in data:
                    return [item.strip() for item in data.split(',') if item.strip()]
                return [data]
        return [data]

    def to_representation(self, value):
        return value if isinstance(value, list) else []


class TranslateTextRequestSerializer(serializers.Serializer):
    """Serializer for text translation request."""
    accessKeyId = serializers.CharField(required=True)
    accessKeySecret = serializers.CharField(required=True)
    text = serializers.CharField(required=True)
    source = serializers.CharField(required=False, allow_blank=True)
    target = serializers.CharField(required=True)
    domain = serializers.CharField(required=False, allow_blank=True)
    style = serializers.CharField(required=False, allow_blank=True)
    instructions = FlexibleListField(required=False)
    adaptTo = FlexibleListField(required=False)
    glossaries = FlexibleListField(required=False)
    fixText = serializers.BooleanField(required=False, default=False)


class TranslateDocumentRequestSerializer(serializers.Serializer):
    """Serializer for document translation request."""
    accessKeyId = serializers.CharField(required=True)
    accessKeySecret = serializers.CharField(required=True)
    file = serializers.FileField(required=True)
    source = serializers.CharField(required=False, allow_blank=True)
    target = serializers.CharField(required=True)
    domainId = serializers.IntegerField(required=False, allow_null=True)  # Domain ID from Lexa
    domain = serializers.CharField(required=False, allow_blank=True)  # Domain name (English) from Lexa
    style = serializers.CharField(required=False, allow_blank=True)
    adaptTo = serializers.CharField(required=False, allow_blank=True) # Can be JSON string or comma-separated
    glossaries = serializers.CharField(required=False, allow_blank=True) # Can be JSON string or comma-separated
    outputFormat = serializers.CharField(required=False, allow_blank=True)
    userToken = serializers.CharField(required=False, allow_blank=True) # User UUID from Lexa
    templateId = serializers.CharField(required=False, allow_blank=True) # Template ID from find endpoint
    templateName = serializers.CharField(required=False, allow_blank=True) # Template name for display
    wordsCount = serializers.IntegerField(required=False, allow_null=True) # Word count from Lexa
    charactersCount = serializers.IntegerField(required=False, allow_null=True) # Character count from Lexa


class DocumentTranslationSerializer(serializers.ModelSerializer):
    """Serializer for DocumentTranslation model."""
    class Meta:
        model = DocumentTranslation
        fields = ['id', 'filename', 'source_language', 'target_language', 'status', 'created_at', 'error_message']
