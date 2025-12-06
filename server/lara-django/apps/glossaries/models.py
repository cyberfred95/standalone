"""
Glossary models for Lara Translation.
Stores glossary information from lara-glossaries.xml.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.languages.models import Language


class Glossary(models.Model):
    """
    Represents a translation glossary.

    Le champ `uuid` permet de distinguer les glossaires système des glossaires personnels:
    - uuid = '*' : glossaire système, utilisable par tous et pris en compte pour la génération des templates
    - uuid = <user_uuid> : glossaire personnel, utilisable uniquement par l'utilisateur correspondant
    """
    glossary_id = models.CharField(
        _("Glossary ID"),
        max_length=255,
        unique=True,
        help_text=_("Unique identifier for the glossary (e.g., gls_xxx)")
    )
    uuid = models.CharField(
        _("UUID"),
        max_length=255,
        default='*',
        db_index=True,
        help_text=_("'*' for system glossaries (available to all), or user UUID for personal glossaries")
    )
    name = models.CharField(
        _("Glossary Name"),
        max_length=255,
        help_text=_("Normalized name of the glossary (e.g., Legal_Accounting_FR or <uuid>_FR_EN)")
    )
    user_glossary_name = models.CharField(
        _("User Glossary Name"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Original name given by the user for personal glossaries")
    )
    source_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='glossaries_as_source',
        help_text=_("Source language")
    )
    target_languages = models.TextField(
        _("Target Languages"),
        help_text=_("Comma-separated list of target language codes")
    )
    domain = models.CharField(
        _("Domain"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Domain name from Lexa")
    )
    generated_at = models.DateTimeField(
        _("Generated At"),
        auto_now=True,
        help_text=_("Last time this glossary was updated")
    )
    
    class Meta:
        verbose_name = _("Glossary")
        verbose_name_plural = _("Glossaries")
        ordering = ['name']
        indexes = [
            models.Index(fields=['glossary_id']),
            models.Index(fields=['source_language', 'domain']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.glossary_id})"
    
    def get_target_languages_list(self):
        """Return target languages as a list."""
        return [lang.strip() for lang in self.target_languages.split(',') if lang.strip()]
