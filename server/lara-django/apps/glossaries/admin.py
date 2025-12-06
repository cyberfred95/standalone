"""
Admin configuration for glossaries app.
"""
from django.contrib import admin
from django.utils.html import format_html
from config.admin import lara_admin_site
from .models import Glossary


class GlossaryTypeFilter(admin.SimpleListFilter):
    """Filter glossaries by type: System (uuid='*') or Personal (uuid!='*')."""
    title = 'Type'
    parameter_name = 'type'

    def lookups(self, request, model_admin):
        return (
            ('system', 'System'),
            ('personal', 'Personal'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'system':
            return queryset.filter(uuid='*')
        if self.value() == 'personal':
            return queryset.exclude(uuid='*')
        return queryset


class GlossaryAdmin(admin.ModelAdmin):
    list_display = ['glossary_id_display', 'uuid', 'user_glossary_name', 'name', 'source_language_display', 'domain_badge', 'target_count', 'generated_at_display']
    list_filter = [GlossaryTypeFilter, 'source_language', 'domain', 'generated_at']
    search_fields = ['glossary_id', 'name', 'user_glossary_name', 'source_language', 'target_languages', 'uuid']
    readonly_fields = ['generated_at']
    change_list_template = 'admin/glossaries/glossary_changelist.html'

    def glossary_id_display(self, obj):
        """Display glossary_id in compact format."""
        if not obj.glossary_id:
            return format_html('<span style="color: #999;">-</span>')
        return format_html(
            '<span style="white-space: nowrap;">{}</span>',
            obj.glossary_id
        )
    glossary_id_display.short_description = 'Glossary ID'
    
    fieldsets = (
        ('Type', {
            'fields': ('uuid',),
            'description': "'*' pour glossaire système, UUID utilisateur pour glossaire personnel"
        }),
        ('Identification', {
            'fields': ('glossary_id', 'user_glossary_name', 'name')
        }),
        ('Languages', {
            'fields': ('source_language', 'target_languages')
        }),
        ('Association', {
            'fields': ('domain',)
        }),
        ('Metadata', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )

    def domain_badge(self, obj):
        """Display domain with colored badge and icon from Lexa."""
        from apps.lexa_backend.services import get_lexa_domain, DEFAULT_DOMAIN_COLOR

        if not obj.domain:
            return format_html('<span style="color: #999;">-</span>')

        # Get domain info from Lexa cache (includes color)
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

    def target_count(self, obj):
        """Display target languages with badges if count <= 2, otherwise show count."""
        from apps.languages.models import Language

        target_langs = obj.get_target_languages_list()
        count = len(target_langs)

        if count <= 2 and count > 0:
            # Display languages with badges
            lang_displays = []
            for lang_code in target_langs:
                try:
                    lang = Language.objects.get(abbreviation=lang_code)
                    if lang.country_code:
                        lang_displays.append(
                            format_html(
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
                        )
                    else:
                        lang_displays.append(f"{lang.abbreviation} - {lang.english_name}")
                except Language.DoesNotExist:
                    lang_displays.append(lang_code)

            return format_html('<br>'.join(str(ld) for ld in lang_displays))

        return count
    target_count.short_description = 'Target'

    def source_language_display(self, obj):
        """Display source language with badge."""
        if obj.source_language:
            lang = obj.source_language
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
        return "-"
    source_language_display.short_description = 'Source'

    def generated_at_display(self, obj):
        """Affiche la date de génération au format DD/MM/YYYY HH:MM"""
        if obj.generated_at:
            return obj.generated_at.strftime('%d/%m/%Y %H:%M')
        return '-'
    generated_at_display.short_description = 'Generated at'


# Register with both default admin and custom admin site
admin.site.register(Glossary, GlossaryAdmin)
lara_admin_site.register(Glossary, GlossaryAdmin)
