"""
Management command to load glossaries from XML file.
Usage: python manage.py load_glossaries [path_to_lara-glossaries.xml]
"""
import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.glossaries.models import Glossary
from apps.languages.models import Language


class Command(BaseCommand):
    help = 'Load glossaries from lara-glossaries.xml file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'xml_file',
            nargs='?',
            type=str,
            default='data/lara-glossaries.xml',
            help='Path to the lara-glossaries.xml file (default: data/lara-glossaries.xml)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing glossaries before loading'
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
        
        self.stdout.write(f'Loading glossaries from: {xml_file}')
        
        try:
            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()
            
            if root.tag != 'glossaries':
                raise CommandError('Invalid XML format: root element should be <glossaries>')
            
            with transaction.atomic():
                if clear:
                    self.stdout.write('Clearing existing glossaries...')
                    Glossary.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('Existing glossaries cleared'))
                
                glossaries_created = 0
                glossaries_updated = 0
                
                # Process each glossary
                for glossary_elem in root.findall('glossary'):
                    glossary_id = glossary_elem.find('id')
                    name = glossary_elem.find('name')
                    source_lang = glossary_elem.find('sourceLanguage')
                    target_langs = glossary_elem.find('targetLanguages')
                    domain_elem = glossary_elem.find('domain')
                    
                    if glossary_id is None or name is None:
                        self.stdout.write(self.style.WARNING('Skipping glossary without id or name'))
                        continue
                    
                    glossary_id_text = glossary_id.text
                    name_text = name.text
                    # Normalize language codes to uppercase (all language codes are stored in UPPERCASE)
                    source_lang_text = source_lang.text.upper() if source_lang is not None and source_lang.text else ''
                    target_langs_text = target_langs.text.upper() if target_langs is not None and target_langs.text else ''
                    domain_name = domain_elem.text if domain_elem is not None else None

                    # Get Language object for source_language FK
                    source_language = None
                    if source_lang_text:
                        source_language = Language.objects.filter(abbreviation=source_lang_text).first()
                        if not source_language:
                            self.stdout.write(self.style.WARNING(f'  Source language not found: {source_lang_text}'))

                    # Get or create glossary (domain is now a CharField)
                    glossary, created = Glossary.objects.update_or_create(
                        glossary_id=glossary_id_text,
                        defaults={
                            'name': name_text,
                            'source_language': source_language,
                            'target_languages': target_langs_text,
                            'domain': domain_name
                        }
                    )
                    
                    if created:
                        glossaries_created += 1
                        if glossaries_created % 100 == 0:
                            self.stdout.write(f'  Created {glossaries_created} glossaries...')
                    else:
                        glossaries_updated += 1
            
            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
            self.stdout.write(self.style.SUCCESS(f'Glossaries created: {glossaries_created}'))
            self.stdout.write(self.style.SUCCESS(f'Glossaries updated: {glossaries_updated}'))
            self.stdout.write(self.style.SUCCESS('\nGlossaries loaded successfully!'))
            
        except ET.ParseError as e:
            raise CommandError(f'Error parsing XML file: {e}')
        except Exception as e:
            raise CommandError(f'Error loading glossaries: {e}')
