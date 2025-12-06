"""
Serializers for Glossary models.
"""
from rest_framework import serializers
from .models import Glossary


class GlossarySerializer(serializers.ModelSerializer):
    """Serializer for Glossary model matching Node.js API format."""
    id = serializers.CharField(source='glossary_id', read_only=True)
    sourceLanguage = serializers.CharField(source='source_language')
    targetLanguages = serializers.SerializerMethodField()
    domain = serializers.CharField(source='domain.name', allow_null=True)
    
    class Meta:
        model = Glossary
        fields = ['id', 'name', 'sourceLanguage', 'targetLanguages', 'domain']
    
    def get_targetLanguages(self, obj):
        """Return target languages as comma-separated string."""
        return obj.target_languages
