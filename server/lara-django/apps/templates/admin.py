"""
Admin configuration for templates app.
"""
from django.contrib import admin
from django.utils.html import format_html
from config.admin import lara_admin_site
from .models import TranslationTemplate
from apps.lexa_backend.services import get_lexa_domain, DEFAULT_DOMAIN_COLOR


class TranslationMemoryFilter(admin.SimpleListFilter):
    title = 'Translation Memory'
    parameter_name = 'has_translation_memory'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'With Translation Memory'),
            ('no', 'Without Translation Memory'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'yes':
            return queryset.exclude(translation_memory_name='').exclude(translation_memory_name__isnull=True)
        if self.value() == 'no':
            return queryset.filter(translation_memory_name='') | queryset.filter(translation_memory_name__isnull=True)


class TranslationTemplateAdmin(admin.ModelAdmin):
    list_display = ['template_id', 'domain_badge', 'source_language_display', 'target_language_display', 'glossary_name', 'translation_memory_name', 'generated_at_display']
    list_filter = ['is_default', 'source_language', 'target_language', 'domain', TranslationMemoryFilter, 'generated_at']
    search_fields = ['template_id', 'name', 'domain', 'description']
    readonly_fields = ['generated_at']
    change_list_template = 'admin/templates/translationtemplate_changelist.html'

    fieldsets = (
        ('Identification', {
            'fields': ('template_id', 'name', 'description', 'is_default')
        }),
        ('Configuration', {
            'fields': ('domain', 'source_language', 'target_language')
        }),
        ('Resources', {
            'fields': ('translation_memory_id', 'translation_memory_name', 'glossary_id', 'glossary_name')
        }),
        ('Metadata', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )

    def domain_badge(self, obj):
        """Display domain with colored badge and icon from Lexa."""
        if not obj.domain or obj.domain == '*':
            return format_html(
                '<span style="'
                'display: inline-flex; '
                'align-items: center; '
                'gap: 6px; '
                'padding: 6px 12px; '
                'background-color: #6f42c1; '
                'color: white; '
                'border-radius: 4px; '
                'font-weight: 500;">'
                '<i class="ph-asterisk" style="font-size: 14px;"></i>'
                '(All domains)</span>'
            )

        # Get domain info from Lexa (includes color)
        domain_info = get_lexa_domain(obj.domain)
        color = domain_info.get('color', DEFAULT_DOMAIN_COLOR) if domain_info else DEFAULT_DOMAIN_COLOR
        icon = domain_info.get('icon') if domain_info else None

        if icon:
            return format_html(
                '<span style="'
                'display: inline-flex; '
                'align-items: center; '
                'gap: 6px; '
                'padding: 6px 12px; '
                'background-color: {}; '
                'color: #333; '
                'border-radius: 4px; '
                'font-weight: 500;">'
                '<i class="ph-{}" style="font-size: 14px;"></i>{}</span>',
                color,
                icon,
                obj.domain
            )
        else:
            return format_html(
                '<span style="'
                'display: inline-block; '
                'padding: 6px 12px; '
                'background-color: {}; '
                'color: #333; '
                'border-radius: 4px; '
                'font-weight: 500;">'
                '{}</span>',
                color,
                obj.domain
            )
    domain_badge.short_description = 'Domain'

    def source_language_display(self, obj):
        """Display source language with badge."""
        from apps.languages.models import Language

        if not obj.source_language or obj.source_language == '*':
            return format_html('<span style="color: #999;">* (All)</span>')

        try:
            lang = Language.objects.get(abbreviation=obj.source_language)
            if lang.country_code:
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
                    '<span>{} - {}</span></span>',
                    lang.country_code,
                    lang.abbreviation,
                    lang.english_name
                )
            return f"{lang.abbreviation} - {lang.english_name}"
        except Language.DoesNotExist:
            return obj.source_language
    source_language_display.short_description = 'Source'

    def target_language_display(self, obj):
        """Display target language with badge."""
        from apps.languages.models import Language

        if not obj.target_language or obj.target_language == '*':
            return format_html('<span style="color: #999;">* (All)</span>')

        try:
            lang = Language.objects.get(abbreviation=obj.target_language)
            if lang.country_code:
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
                    '<span>{} - {}</span></span>',
                    lang.country_code,
                    lang.abbreviation,
                    lang.english_name
                )
            return f"{lang.abbreviation} - {lang.english_name}"
        except Language.DoesNotExist:
            return obj.target_language
    target_language_display.short_description = 'Target'

    def generated_at_display(self, obj):
        """Affiche la date de génération au format DD/MM/YYYY HH:MM"""
        if obj.generated_at:
            return obj.generated_at.strftime('%d/%m/%Y %H:%M')
        return '-'
    generated_at_display.short_description = 'Generated at'


# Register with both default admin and custom admin site
admin.site.register(TranslationTemplate, TranslationTemplateAdmin)
lara_admin_site.register(TranslationTemplate, TranslationTemplateAdmin)
