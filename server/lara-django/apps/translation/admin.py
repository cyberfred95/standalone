"""
Admin configuration for translation app.
"""
from django.contrib import admin
from django.utils.html import format_html
from config.admin import lara_admin_site
from .models import DocumentTranslation


class DocumentTranslationAdmin(admin.ModelAdmin):
    list_display = ['user_uuid_display', 'filename_display', 'status_badge', 'domain_badge', 'source_display', 'target_display', 'template_display', 'tm_display', 'glossary_display', 'source_doc', 'translated_doc', 'words_display', 'chars_display', 'sec_display', 'created_at_display']
    list_filter = ['status', 'source_language', 'target_language', 'domain', 'created_at']
    search_fields = ['filename', 'lara_id', 'error_message', 'domain', 'user_uuid']
    readonly_fields = ['id', 'created_at', 'updated_at', 'payload', 'lara_sdk_request', 'response', 'translation_sec', 'words_count', 'characters_count']

    def user_uuid_display(self, obj):
        """Display user email from Lexa (cached)."""
        from apps.lexa_backend.services import get_lexa_user_by_uuid

        if not obj.user_uuid:
            return '-'

        # Get user info from Lexa cache
        user_info = get_lexa_user_by_uuid(obj.user_uuid)

        if user_info and user_info.get('email'):
            return user_info.get('email')

        # Fallback to short UUID if user not found
        return obj.user_uuid[:8] + '...' if len(obj.user_uuid) > 8 else obj.user_uuid
    user_uuid_display.short_description = 'User'

    def filename_display(self, obj):
        """Display filename truncated with full name in tooltip."""
        if not obj.filename:
            return format_html('<span style="color: #999;">-</span>')

        max_length = 20
        if len(obj.filename) > max_length:
            short_name = obj.filename[:max_length] + '...'
            return format_html(
                '<span style="cursor: help;" title="{}">{}</span>',
                obj.filename,
                short_name
            )
        return obj.filename
    filename_display.short_description = 'Filename'

    def status_badge(self, obj):
        """Display status as colored badge with error tooltip."""
        status_colors = {
            'pending': '#6c757d',      # grey
            'processing': '#007bff',   # blue
            'translated': '#28a745',   # green
            'error': '#dc3545',        # red
        }
        color = status_colors.get(obj.status, '#6c757d')

        # Add tooltip with error message if status is error
        if obj.status == 'error' and obj.error_message:
            return format_html(
                '<span style="'
                'display: inline-block; '
                'padding: 6px 12px; '
                'background-color: {}; '
                'color: white; '
                'border-radius: 4px; '
                'font-weight: 500; '
                'cursor: help;" '
                'title="{}">'
                '{} ⚠</span>',
                color,
                obj.error_message,
                obj.get_status_display()
            )

        return format_html(
            '<span style="'
            'display: inline-block; '
            'padding: 6px 12px; '
            'background-color: {}; '
            'color: white; '
            'border-radius: 4px; '
            'font-weight: 500;">'
            '{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    def source_doc(self, obj):
        """Display source document download link."""
        if obj.original_file:
            return format_html(
                '<a href="{}" download style="'
                'display: inline-flex; '
                'align-items: center; '
                'gap: 6px; '
                'padding: 6px 12px; '
                'background-color: #17a2b8; '
                'color: white; '
                'border-radius: 4px; '
                'font-weight: 500; '
                'text-decoration: none;">'
                '<i class="ph-download-simple" style="font-size: 14px;"></i>'
                'Download</a>',
                obj.original_file.url
            )
        return format_html('<span style="color: #999;">-</span>')
    source_doc.short_description = 'Source Doc'

    def translated_doc(self, obj):
        """Display translated document download link."""
        if obj.translated_file:
            return format_html(
                '<a href="{}" download style="'
                'display: inline-flex; '
                'align-items: center; '
                'gap: 6px; '
                'padding: 6px 12px; '
                'background-color: #28a745; '
                'color: white; '
                'border-radius: 4px; '
                'font-weight: 500; '
                'text-decoration: none;">'
                '<i class="ph-download-simple" style="font-size: 14px;"></i>'
                'Download</a>',
                obj.translated_file.url
            )
        return format_html('<span style="color: #999;">-</span>')
    translated_doc.short_description = 'Translated Doc'

    def source_display(self, obj):
        """Display source language with badge."""
        from apps.languages.models import Language

        if not obj.source_language:
            return format_html('<span style="color: #999;">-</span>')

        try:
            lang = Language.objects.get(abbreviation=obj.source_language.upper())
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
    source_display.short_description = 'Source'

    def target_display(self, obj):
        """Display target language with badge."""
        from apps.languages.models import Language

        if not obj.target_language:
            return format_html('<span style="color: #999;">-</span>')

        try:
            lang = Language.objects.get(abbreviation=obj.target_language.upper())
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
    target_display.short_description = 'Target'

    def created_at_display(self, obj):
        """Affiche la date de création au format DD/MM/YYYY HH:MM"""
        if obj.created_at:
            return obj.created_at.strftime('%d/%m/%Y %H:%M')
        return '-'
    created_at_display.short_description = 'Created at'

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

    def template_display(self, obj):
        """Display template name."""
        from apps.templates.models import TranslationTemplate

        if not obj.template_id:
            return format_html('<span style="color: #999;">-</span>')

        try:
            template = TranslationTemplate.objects.get(template_id=obj.template_id)
            return template.name or template.template_id
        except TranslationTemplate.DoesNotExist:
            return obj.template_id
    template_display.short_description = 'Template'

    def tm_display(self, obj):
        """Display translation memory name."""
        from apps.memories.models import Memory

        if not obj.translation_memory_id:
            return format_html('<span style="color: #999;">-</span>')

        try:
            memory = Memory.objects.get(memory_id=obj.translation_memory_id)
            return memory.name
        except Memory.DoesNotExist:
            return obj.translation_memory_id
    tm_display.short_description = 'TM'

    def glossary_display(self, obj):
        """Display glossary name."""
        from apps.glossaries.models import Glossary

        if not obj.glossary_id:
            return format_html('<span style="color: #999;">-</span>')

        try:
            glossary = Glossary.objects.get(glossary_id=obj.glossary_id)
            return glossary.name
        except Glossary.DoesNotExist:
            return obj.glossary_id
    glossary_display.short_description = 'Glossary'

    def words_display(self, obj):
        """Display word count."""
        if obj.words_count is not None:
            formatted = f"{obj.words_count:,}"
            return format_html(
                '<span style="font-family: monospace;">{}</span>',
                formatted
            )
        return format_html('<span style="color: #999;">-</span>')
    words_display.short_description = 'Words'

    def chars_display(self, obj):
        """Display character count."""
        if obj.characters_count is not None:
            formatted = f"{obj.characters_count:,}"
            return format_html(
                '<span style="font-family: monospace;">{}</span>',
                formatted
            )
        return format_html('<span style="color: #999;">-</span>')
    chars_display.short_description = 'Chars'

    def sec_display(self, obj):
        """Display translation time in seconds."""
        if obj.translation_sec is not None:
            formatted = f"{obj.translation_sec:.1f}"
            return format_html(
                '<span style="font-family: monospace;">{}</span>',
                formatted
            )
        return format_html('<span style="color: #999;">-</span>')
    sec_display.short_description = 'Sec'

    fieldsets = (
        ('User Info', {
            'fields': ('user_uuid',)
        }),
        ('Task Info', {
            'fields': ('id', 'status', 'lara_id')
        }),
        ('File Info', {
            'fields': ('filename', 'original_file', 'translated_file', 'words_count', 'characters_count')
        }),
        ('Languages', {
            'fields': ('source_language', 'target_language')
        }),
        ('Translation Resources', {
            'fields': ('domain', 'template_id', 'translation_memory_id', 'glossary_id')
        }),
        ('Status & Errors', {
            'fields': ('error_message',)
        }),
        ('Request/Response', {
            'fields': ('payload', 'lara_sdk_request', 'response', 'translation_sec'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Register with both default admin and custom admin site
admin.site.register(DocumentTranslation, DocumentTranslationAdmin)
lara_admin_site.register(DocumentTranslation, DocumentTranslationAdmin)
