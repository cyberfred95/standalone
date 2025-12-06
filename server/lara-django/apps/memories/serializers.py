"""
Serializers for Memory models.
"""
from rest_framework import serializers
from .models import Memory


class MemorySerializer(serializers.ModelSerializer):
    """Serializer for Memory model matching Node.js API format."""
    id = serializers.CharField(source='memory_id', read_only=True)
    sourceLanguage = serializers.SerializerMethodField()
    targetLanguage = serializers.SerializerMethodField()
    domainGroup = serializers.CharField(source='domain_group', allow_null=True)

    class Meta:
        model = Memory
        fields = ['id', 'name', 'sourceLanguage', 'targetLanguage', 'domainGroup']

    def get_sourceLanguage(self, obj):
        """Return source language abbreviation with name."""
        if obj.source_language:
            return f"{obj.source_language.abbreviation} - {obj.source_language.english_name}"
        return None

    def get_targetLanguage(self, obj):
        """Return target language abbreviation."""
        if obj.target_language:
            return obj.target_language.abbreviation
        return None
