"""
Admin configuration for languages app.
"""
from django.contrib import admin
from django.utils.html import format_html
from config.admin import lara_admin_site
from .models import Language


class LanguageAdmin(admin.ModelAdmin):
    list_display = ['abbreviation', 'english_name', 'french_name', 'country_badge']
    search_fields = ['abbreviation', 'english_name', 'french_name']
    ordering = ['english_name']

    def flag_display(self, obj):
        """Affiche le drapeau du pays"""
        if obj.country_code:
            return format_html(
                '<span class="fi fi-{}" style="font-size: 1.5em;"></span>',
                obj.country_code
            )
        return format_html('<span style="color: #999;">-</span>')
    flag_display.short_description = 'Flag'

    def country_badge(self, obj):
        """Affiche un badge avec le drapeau et le code pays"""
        if obj.country_code:
            return format_html(
                '<span style="'
                'display: inline-flex; '
                'align-items: center; '
                'gap: 8px; '
                'padding: 6px 12px; '
                'background-color: #f5f5f5; '
                'border-radius: 4px; '
                'font-family: monospace; '
                'font-weight: 500;">'
                '<span class="fi fi-{}" style="font-size: 1.2em;"></span>'
                '<span>{}</span>'
                '</span>',
                obj.country_code,
                obj.country_code.upper()
            )
        return format_html('<span style="color: #999;">-</span>')
    country_badge.short_description = 'Country Code'


# Register with both default admin and custom admin site
admin.site.register(Language, LanguageAdmin)
lara_admin_site.register(Language, LanguageAdmin)
