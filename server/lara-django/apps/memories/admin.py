"""
Admin configuration for memories app.
"""
from django import forms
from django.contrib import admin
from django.utils.html import format_html
from config.admin import lara_admin_site
from .models import Memory
from apps.lexa_backend.services import get_lexa_domain_groups


class MemoryAdminForm(forms.ModelForm):
    """Custom form for Memory admin with domain_group dropdown from Lexa."""

    domain_group = forms.ChoiceField(
        required=False,
        label="Domain Group",
        help_text="Domain group name from Lexa. Use '*' for all domain groups."
    )

    class Meta:
        model = Memory
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Build choices from Lexa domain groups
        choices = [
            ('', '---------'),
            ('*', '* (All Domain Groups)'),
        ]

        # Fetch domain groups from Lexa API
        try:
            domain_groups = get_lexa_domain_groups()
            for group in sorted(domain_groups, key=lambda x: x.get('name', '')):
                group_name = group.get('name', '')
                if group_name:
                    choices.append((group_name, group_name))
        except Exception:
            # If API fails, still allow manual entry
            pass

        self.fields['domain_group'].choices = choices

        # Set initial value if editing existing memory
        if self.instance and self.instance.pk:
            self.fields['domain_group'].initial = self.instance.domain_group or ''

    def clean_domain_group(self):
        """Convert empty string to None for database storage."""
        value = self.cleaned_data.get('domain_group')
        return value if value else None


class MemoryAdmin(admin.ModelAdmin):
    form = MemoryAdminForm
    list_display = ['memory_id_display', 'name', 'source_language_display', 'target_language_display', 'domain_group_badge', 'generated_at_display']
    list_filter = ['source_language', 'target_language', 'domain_group', 'generated_at']
    search_fields = ['memory_id', 'name', 'domain_group']
    readonly_fields = ['generated_at']
    change_list_template = 'admin/memories/memory_changelist.html'

    def memory_id_display(self, obj):
        """Display memory_id in compact format."""
        if not obj.memory_id:
            return format_html('<span style="color: #999;">-</span>')
        return format_html(
            '<span style="white-space: nowrap;">{}</span>',
            obj.memory_id
        )
    memory_id_display.short_description = 'Memory ID'

    fieldsets = (
        ('Identification', {
            'fields': ('memory_id', 'name')
        }),
        ('Languages', {
            'fields': ('source_language', 'target_language')
        }),
        ('Association', {
            'fields': ('domain_group',)
        }),
        ('Metadata', {
            'fields': ('generated_at',),
            'classes': ('collapse',)
        }),
    )

    def domain_group_badge(self, obj):
        """Display domain group with colored badge."""
        if not obj.domain_group:
            return format_html('<span style="color: #999;">-</span>')

        # Special display for "*" (all domain groups)
        if obj.domain_group == '*':
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
                'All Domain Groups</span>'
            )

        # Regular domain group display
        return format_html(
            '<span style="'
            'display: inline-flex; '
            'align-items: center; '
            'gap: 6px; '
            'padding: 6px 12px; '
            'background-color: #28a745; '
            'color: white; '
            'border-radius: 4px; '
            'font-weight: 500;">'
            '<i class="ph-folders" style="font-size: 14px;"></i>'
            '{}</span>',
            obj.domain_group
        )
    domain_group_badge.short_description = 'Domain Group'

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

    def target_language_display(self, obj):
        """Display target language with badge."""
        if obj.target_language:
            lang = obj.target_language
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
    target_language_display.short_description = 'Target'

    def generated_at_display(self, obj):
        """Affiche la date de génération au format DD/MM/YYYY HH:MM"""
        if obj.generated_at:
            return obj.generated_at.strftime('%d/%m/%Y %H:%M')
        return '-'
    generated_at_display.short_description = 'Generated at'


# Register with both default admin and custom admin site
admin.site.register(Memory, MemoryAdmin)
lara_admin_site.register(Memory, MemoryAdmin)
