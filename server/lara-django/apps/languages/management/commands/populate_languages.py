"""
Management command to populate supported languages.
"""
from django.core.management.base import BaseCommand
from apps.languages.models import Language


class Command(BaseCommand):
    help = 'Populate supported languages with their French and English names'

    # Language data: (abbreviation, french_name, english_name)
    LANGUAGES = [
        ('AR', 'Arabe', 'Arabic'),
        ('BG', 'Bulgare', 'Bulgarian'),
        ('zh-Hans', 'Chinois (Simplifié)', 'Chinese (Simplified)'),
        ('zh-TW', 'Chinois (Traditionnel)', 'Chinese (Traditional)'),
        ('HR', 'Croate', 'Croatian'),
        ('CS', 'Tchèque', 'Czech'),
        ('DA', 'Danois', 'Danish'),
        ('NL', 'Néerlandais', 'Dutch'),
        ('EN', 'Anglais (UK)', 'English (UK)'),
        ('en-US', 'Anglais (USA)', 'English (US)'),
        ('ET', 'Estonien', 'Estonian'),
        ('FI', 'Finnois', 'Finnish'),
        ('FR', 'Francais', 'French'),
        ('DE', 'Allemand', 'German'),
        ('EL', 'Grec', 'Greek'),
        ('HU', 'Hongrois', 'Hungarian'),
        ('IT', 'Italien', 'Italian'),
        ('JA', 'Japonais', 'Japanese'),
        ('KO', 'Coréen', 'Korean'),
        ('LV', 'Letton', 'Latvian'),
        ('LT', 'Lituanien', 'Lithuanian'),
        ('MT', 'Maltais', 'Maltese'),
        ('nb', 'Norvégien', 'Norwegian'),
        ('PL', 'Polonais', 'Polish'),
        ('PT', 'Portugais', 'Portuguese'),
        ('pt-br', 'Portugais (BR)', 'Portuguese (BR)'),
        ('RO', 'Roumain', 'Romanian'),
        ('RU', 'Russe', 'Russian'),
        ('SK', 'Slovaque', 'Slovak'),
        ('SL', 'Slovène', 'Slovenian'),
        ('ES', 'Espagnol', 'Spanish'),
        ('SV', 'Suédois', 'Swedish'),
        ('TR', 'Turc', 'Turkish'),
        ('UK', 'Ukrainien', 'Ukrainian'),
    ]

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting language population...'))

        created_count = 0
        updated_count = 0

        for abbr, fr_name, en_name in self.LANGUAGES:
            language, created = Language.objects.update_or_create(
                abbreviation=abbr,
                defaults={
                    'french_name': fr_name,
                    'english_name': en_name
                }
            )

            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created {abbr}: {en_name} / {fr_name}')
                )
                created_count += 1
            else:
                self.stdout.write(
                    self.style.WARNING(f'↻ Updated {abbr}: {en_name} / {fr_name}')
                )
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✓ Population completed!\n'
                f'  - {created_count} languages created\n'
                f'  - {updated_count} languages updated\n'
                f'  - {len(self.LANGUAGES)} total languages'
            )
        )
