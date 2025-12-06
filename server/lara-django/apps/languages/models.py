"""
Language models for Lara Translation.
Stores supported languages with their codes and names.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class Language(models.Model):
    """
    Represents a supported language for translation.
    """
    abbreviation = models.CharField(
        _("Abbreviation"),
        max_length=10,
        unique=True,
        primary_key=True,
        help_text=_("Language code (ISO 639-1 or custom)")
    )
    french_name = models.CharField(
        _("French Name"),
        max_length=100,
        help_text=_("Name of the language in French")
    )
    english_name = models.CharField(
        _("English Name"),
        max_length=100,
        help_text=_("Name of the language in English")
    )
    country_code = models.CharField(
        _("Country Code"),
        max_length=2,
        blank=True,
        help_text=_("ISO 3166-1 alpha-2 country code for flag display")
    )

    class Meta:
        verbose_name = _("Language")
        verbose_name_plural = _("Languages")
        ordering = ['english_name']

    def __str__(self):
        return f"{self.abbreviation} - {self.english_name}"

    def get_flag_html(self):
        """Return HTML for displaying the country flag"""
        if self.country_code:
            return f'<span class="fi fi-{self.country_code}" style="font-size: 1.5em;"></span>'
        return ''
