"""
Management command to load translation memories from XML file.
Usage: python manage.py load_memories [path_to_lara-memories.xml]
"""
import os
import xml.etree.ElementTree as ET
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.memories.models import Memory
from apps.languages.models import Language


class Command(BaseCommand):
    help = 'Load translation memories from lara-memories.xml file into the database'

    def add_arguments(self, parser):
        parser.add_argument(
            'xml_file',
            nargs='?',
            type=str,
            default='/app/data/lara-memories.xml',
            help='Path to the lara-memories.xml file (default: /app/data/lara-memories.xml)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing memories before loading'
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

        self.stdout.write(f'Loading memories from: {xml_file}')

        try:
            # Parse XML file
            tree = ET.parse(xml_file)
            root = tree.getroot()

            if root.tag != 'memories':
                raise CommandError('Invalid XML format: root element should be <memories>')

            with transaction.atomic():
                if clear:
                    self.stdout.write('Clearing existing memories...')
                    Memory.objects.all().delete()
                    self.stdout.write(self.style.SUCCESS('Existing memories cleared'))

                memories_created = 0
                memories_updated = 0

                # Process each memory
                for memory_elem in root.findall('memory'):
                    memory_id = memory_elem.find('id')
                    name = memory_elem.find('name')
                    source_lang = memory_elem.find('sourceLanguage')
                    target_lang = memory_elem.find('targetLanguage')
                    domains_elem = memory_elem.find('domains')

                    if memory_id is None or name is None:
                        self.stdout.write(self.style.WARNING('Skipping memory without id or name'))
                        continue

                    memory_id_text = memory_id.text
                    name_text = name.text
                    # Normalize language codes to uppercase (all language codes are stored in UPPERCASE)
                    source_lang_text = source_lang.text.upper() if source_lang is not None and source_lang.text else ''
                    target_lang_text = target_lang.text.upper() if target_lang is not None and target_lang.text else ''

                    # Domain group is now a CharField - store "*" for generic memories, NULL for others
                    # The domain_group field stores the domain group name from Lexa
                    domains_text = domains_elem.text if domains_elem is not None and domains_elem.text else ''

                    # Set domain_group = "*" only if it's explicitly "*" in the XML
                    # All other domain_group values are set to NULL (will be assigned manually later)
                    domain_group = None
                    if domains_text.strip() == '*':
                        domain_group = '*'

                    # Get Language objects for ForeignKey fields
                    source_language = None
                    target_language = None

                    if source_lang_text:
                        source_language = Language.objects.filter(abbreviation=source_lang_text).first()
                        if not source_language:
                            self.stdout.write(self.style.WARNING(f'  Source language not found: {source_lang_text}'))

                    if target_lang_text:
                        target_language = Language.objects.filter(abbreviation=target_lang_text).first()
                        if not target_language:
                            self.stdout.write(self.style.WARNING(f'  Target language not found: {target_lang_text}'))

                    # Get or create memory
                    memory, created = Memory.objects.update_or_create(
                        memory_id=memory_id_text,
                        defaults={
                            'name': name_text,
                            'source_language': source_language,
                            'target_language': target_language,
                            'domain_group': domain_group
                        }
                    )

                    if created:
                        memories_created += 1
                        self.stdout.write(f'  Created memory: {name_text}')
                    else:
                        memories_updated += 1

            # Summary
            self.stdout.write(self.style.SUCCESS('\n=== Summary ==='))
            self.stdout.write(self.style.SUCCESS(f'Memories created: {memories_created}'))
            self.stdout.write(self.style.SUCCESS(f'Memories updated: {memories_updated}'))
            self.stdout.write(self.style.SUCCESS('\nMemories loaded successfully!'))

        except ET.ParseError as e:
            raise CommandError(f'Error parsing XML file: {e}')
        except Exception as e:
            raise CommandError(f'Error loading memories: {e}')
