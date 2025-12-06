"""
Translation Memory models for Lara Translation.
Stores translation memory information from lara-memories.xml.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.languages.models import Language


class Memory(models.Model):
    """
    Represents a translation memory.
    """
    memory_id = models.CharField(
        _("Memory ID"),
        max_length=255,
        unique=True,
        help_text=_("Unique identifier for the memory (e.g., mem_xxx)")
    )
    name = models.CharField(
        _("Memory Name"),
        max_length=255,
        help_text=_("Name of the translation memory")
    )
    source_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='memories_as_source',
        help_text=_("Source language")
    )
    target_language = models.ForeignKey(
        Language,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='memories_as_target',
        help_text=_("Target language")
    )
    domain_group = models.CharField(
        _("Domain Group"),
        max_length=255,
        null=True,
        blank=True,
        help_text=_("Domain group name from Lexa. Use '*' for all domain groups.")
    )
    generated_at = models.DateTimeField(
        _("Generated At"),
        auto_now=True,
        help_text=_("Last time this memory was updated")
    )

    class Meta:
        verbose_name = _("Translation Memory")
        verbose_name_plural = _("Translation Memories")
        ordering = ['name']
        indexes = [
            models.Index(fields=['memory_id']),
            models.Index(fields=['source_language', 'domain_group']),
        ]

    def __str__(self):
        return f"{self.name} ({self.memory_id})"
