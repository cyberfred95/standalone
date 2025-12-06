"""
Template models for Lara Translation.
Stores translation templates from templates.xml.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class TranslationTemplate(models.Model):
    """
    Represents a translation template configuration.
    """
    template_id = models.CharField(
        _("Template ID"),
        max_length=255,
        unique=True,
        help_text=_("Unique identifier for the template")
    )
    name = models.CharField(
        _("Template Name"),
        max_length=255,
        help_text=_("Name of the template")
    )
    is_default = models.BooleanField(
        _("Is Default"),
        default=False,
        help_text=_("Whether this is the default template")
    )
    domain = models.CharField(
        _("Domain"),
        max_length=255,
        help_text=_("Domain associated with this template")
    )
    source_language = models.CharField(
        _("Source Language"),
        max_length=10,
        help_text=_("Source language code")
    )
    target_language = models.CharField(
        _("Target Language"),
        max_length=10,
        help_text=_("Target language code")
    )
    translation_memory_id = models.CharField(
        _("Translation Memory ID"),
        max_length=255,
        blank=True,
        help_text=_("ID of the associated translation memory")
    )
    translation_memory_name = models.CharField(
        _("Translation Memory Name"),
        max_length=255,
        blank=True,
        help_text=_("Name of the associated translation memory")
    )
    glossary_id = models.CharField(
        _("Glossary ID"),
        max_length=255,
        blank=True,
        help_text=_("ID of the associated glossary")
    )
    glossary_name = models.CharField(
        _("Glossary Name"),
        max_length=255,
        blank=True,
        help_text=_("Name of the associated glossary")
    )
    description = models.TextField(
        _("Description"),
        blank=True,
        help_text=_("Description of the template")
    )
    generated_at = models.DateTimeField(
        _("Generated At"),
        auto_now=True,
        help_text=_("Last time this template was updated")
    )
    
    class Meta:
        verbose_name = _("Translation Template")
        verbose_name_plural = _("Translation Templates")
        ordering = ['name']
        indexes = [
            models.Index(fields=['template_id']),
            models.Index(fields=['domain', 'source_language', 'target_language']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.template_id})"
