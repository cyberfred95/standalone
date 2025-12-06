"""
Management command to load translation templates from XML file.
Usage: python manage.py load_templates [path_to_templates.xml]
"""
import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.templates.models import TranslationTemplate


class Command(BaseCommand):
    help = 'Load translation templates from templates.xml file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'xml_file',
            nargs='?',
            type=str,
            default='data/templates.xml',
            help='Path to the templates.xml file (default: data/templates.xml)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing templates before loading'
        )

    def handle(self, *args, **options):
        xml_file = options['xml_file']
        clear = options['clear']
        
        # Resolve the path relative to the manage.py location
        if not os.path.isabs(xml_file):
            # In Docker container the project root is /app
            xml_file = os.path.join('/app', xml_file)
        
        if not os.path.exists(xml_file):
            raise CommandError(f'XML file not found: {xml_file}')
        
        self.stdout.write(f'Loading templates from: {xml_file}')
        
        try:
            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            if root.tag != 'translation-templates':
                raise CommandError('Invalid XML format: root element should be <translation-templates>')
            
            with transaction.atomic():
                if clear:
                    self.stdout.write('Clearing existing templates...')
                    TranslationTemplate.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('Existing templates cleared'))
                
                templates_created = 0
                templates_updated = 0
                
                # Process each template
                for template_elem in root.findall('template'):
                    template_id = template_elem.get('id')
                    name = template_elem.get('name')
                    is_default = template_elem.get('is-default') == 'true'
                    
                    domain_elem = template_elem.find('domain')
                    source_lang_elem = template_elem.find('source-language')
                    target_lang_elem = template_elem.find('target-language')
                    tm_id_elem = template_elem.find('translation-memory-id')
                    tm_name_elem = template_elem.find('translation-memory-name')
                    gls_id_elem = template_elem.find('glossary-id')
                    gls_name_elem = template_elem.find('glossary-name')
                    desc_elem = template_elem.find('description')
                    
                    if not template_id or not name:
                        continue
                    
                    # Extract text content safely
                    domain = domain_elem.text if domain_elem is not None and domain_elem.text else ''
                    # Normalize language codes to uppercase (all language codes are stored in UPPERCASE)
                    source_lang = (source_lang_elem.text.upper() if source_lang_elem is not None and source_lang_elem.text else '')
                    target_lang = (target_lang_elem.text.upper() if target_lang_elem is not None and target_lang_elem.text else '')
                    tm_id = tm_id_elem.text if tm_id_elem is not None and tm_id_elem.text else ''
                    tm_name = tm_name_elem.text if tm_name_elem is not None and tm_name_elem.text else ''
                    gls_id = gls_id_elem.text if gls_id_elem is not None and gls_id_elem.text else ''
                    gls_name = gls_name_elem.text if gls_name_elem is not None and gls_name_elem.text else ''
                    description = desc_elem.text if desc_elem is not None and desc_elem.text else ''
                    
                    # Get or create template
                    template, created = TranslationTemplate.objects.update_or_create(
                        template_id=template_id,
                        defaults={
                            'name': name,
                            'is_default': is_default,
                            'domain': domain,
                            'source_language': source_lang,
                            'target_language': target_lang,
                            'translation_memory_id': tm_id,
                            'translation_memory_name': tm_name,
                            'glossary_id': gls_id,
                            'glossary_name': gls_name,
                            'description': description
                        }
                    )
                    
                    if created:
                        templates_created += 1
                        if templates_created % 100 == 0:
                            self.stdout.write(f'  Created {templates_created} templates...')
                    else:
                        templates_updated += 1
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
            self.stdout.write(self.style.SUCCESS(f'Templates created: {templates_created}'))
            self.stdout.write(self.style.SUCCESS(f'Templates updated: {templates_updated}'))
            self.stdout.write(self.style.SUCCESS('\nTemplates loaded successfully!'))
            
        except ET.ParseError as e:
            raise CommandError(f'Error parsing XML file: {e}')
        except Exception as e:
            raise CommandError(f'Error loading templates: {e}')
