"""
Translation models for Lara Translation.
Stores document translation status and metadata.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
import uuid


class DocumentTranslation(models.Model):
    """
    Represents a document translation task.
    """
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('translated', 'Translated'),
        ('error', 'Error'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    filename = models.CharField(_("Filename"), max_length=255)
    source_language = models.CharField(_("Source Language"), max_length=10, blank=True)
    target_language = models.CharField(_("Target Language"), max_length=10)
    status = models.CharField(_("Status"), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # User identification (UUID from Lexa)
    user_uuid = models.CharField(_("User UUID"), max_length=255, blank=True, null=True, db_index=True, help_text="User UUID from Lexa")

    # Lara API specific fields
    lara_id = models.CharField(_("Lara ID"), max_length=255, blank=True, help_text="ID returned by Lara API")
    error_message = models.TextField(_("Error Message"), blank=True)

    # Template and resources used for translation
    template_id = models.CharField(_("Template ID"), max_length=255, blank=True, null=True, help_text="ID of the template found via find request")
    translation_memory_id = models.CharField(_("Translation Memory ID"), max_length=255, blank=True, null=True, help_text="ID of the translation memory used")
    glossary_id = models.CharField(_("Glossary ID"), max_length=255, blank=True, null=True, help_text="ID of the glossary used")
    domain = models.CharField(_("Domain"), max_length=100, blank=True, null=True, help_text="Domain used for translation")
    
    # Template name (from Custom.MT)
    template_name = models.CharField(_("Template Name"), max_length=255, blank=True, null=True, help_text="Template name used for translation")

    # File paths
    original_file = models.FileField(_("Original File"), upload_to='uploads/originals/')
    translated_file = models.FileField(_("Translated File"), upload_to='uploads/translated/', blank=True, null=True)
    reviewed_file = models.FileField(_("Reviewed File"), upload_to='uploads/reviewed/', blank=True, null=True)
    xliff_file = models.FileField(_("XLIFF File"), upload_to='uploads/xliff/', blank=True, null=True)
    tmx_file = models.FileField(_("TMX File"), upload_to='uploads/tmx/', blank=True, null=True)

    # Request/Response tracking
    payload = models.TextField(
        _("Lexa Request"),
        blank=True,
        null=True,
        help_text=_("Parameters received from Lexa (domainId, templateId, glossaries, etc.)")
    )
    lara_sdk_request = models.TextField(
        _("LARA SDK Request"),
        blank=True,
        null=True,
        help_text=_("Parameters sent to LARA SDK (filename, source, target, adapt_to, glossaries)")
    )
    response = models.TextField(
        _("Translation Result"),
        blank=True,
        null=True,
        help_text=_("Translation result metadata (status, duration, file size) or SDK error details")
    )
    translation_sec = models.FloatField(
        _("Translation Time (seconds)"),
        blank=True,
        null=True,
        help_text=_("Time taken for translation in seconds")
    )
    translation_started_at = models.DateTimeField(
        _("Translation Started At"),
        blank=True,
        null=True,
        help_text=_("Timestamp when translation processing started")
    )

    # Document statistics from Lexa
    words_count = models.IntegerField(
        _("Word Count"),
        blank=True,
        null=True,
        help_text=_("Number of words in the source document")
    )
    characters_count = models.IntegerField(
        _("Character Count"),
        blank=True,
        null=True,
        help_text=_("Number of characters in the source document")
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _("Document Translation")
        verbose_name_plural = _("Document Translations")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.filename} ({self.status})"
