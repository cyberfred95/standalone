"""
Django management command to migrate translations from Custom.MT to Django Lara.

Usage:
    # Dry run (count only)
    python manage.py migrate_from_custommt --dry-run

    # Full migration
    python manage.py migrate_from_custommt --api-url=https://custommt.example.com/api/v1/ --api-key=xxx

    # Migration with batch size
    python manage.py migrate_from_custommt --api-url=https://... --api-key=xxx --batch-size=50
"""
import requests
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.db import transaction
from apps.translation.models import DocumentTranslation
from urllib.parse import urlparse, unquote
import uuid
import time


class Command(BaseCommand):
    help = 'Migrate translations from Custom.MT to Django Lara DocumentTranslation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--api-url',
            type=str,
            help='Custom.MT API URL (CLOUDSTORAGE_API_URL)',
            required=False,
        )
        parser.add_argument(
            '--api-key',
            type=str,
            help='API Key for Custom.MT authentication',
            required=False,
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only count projects without migrating',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of projects to process per batch (default: 100)',
        )
        parser.add_argument(
            '--skip-files',
            action='store_true',
            help='Skip downloading files (create metadata only)',
        )
        parser.add_argument(
            '--start-page',
            type=int,
            default=1,
            help='Start from specific page (for resuming)',
        )

    def handle(self, *args, **options):
        api_url = options['api_url']
        api_key = options['api_key']
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        skip_files = options['skip_files']
        start_page = options['start_page']

        if not dry_run and (not api_url or not api_key):
            self.stderr.write(self.style.ERROR(
                'API URL and API Key are required for migration. Use --dry-run for counting only.'
            ))
            return

        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('Migration Custom.MT → Django Lara'))
        self.stdout.write(self.style.NOTICE('=' * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING('MODE: DRY RUN (aucune modification)'))
            self.count_existing_records()
            return

        # Step 1: Count total projects
        self.stdout.write('\n📊 Étape 1: Comptage des projets Custom.MT...')
        total_count, num_pages = self.count_custommt_projects(api_url, api_key, batch_size)

        if total_count == 0:
            self.stdout.write(self.style.WARNING('Aucun projet trouvé dans Custom.MT'))
            return

        self.stdout.write(self.style.SUCCESS(
            f'   → {total_count} projets trouvés sur {num_pages} pages'
        ))

        # Step 2: Migrate projects
        self.stdout.write(f'\n🚀 Étape 2: Migration des projets (à partir de la page {start_page})...')

        migrated = 0
        skipped = 0
        errors = 0

        for page in range(start_page, num_pages + 1):
            self.stdout.write(f'\n   Page {page}/{num_pages}...')

            try:
                projects = self.fetch_custommt_page(api_url, api_key, page, batch_size)

                for project in projects:
                    result = self.migrate_project(project, skip_files, api_url, api_key)
                    if result == 'migrated':
                        migrated += 1
                    elif result == 'skipped':
                        skipped += 1
                    else:
                        errors += 1

                    # Progress indicator
                    if (migrated + skipped + errors) % 10 == 0:
                        self.stdout.write(
                            f'      Progression: {migrated} migrés, {skipped} ignorés, {errors} erreurs'
                        )

            except Exception as e:
                self.stderr.write(self.style.ERROR(f'   Erreur page {page}: {e}'))
                errors += 1
                continue

            # Small delay to avoid overloading APIs
            time.sleep(0.5)

        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ Migration terminée!'))
        self.stdout.write(f'   Migrés: {migrated}')
        self.stdout.write(f'   Ignorés (déjà existants): {skipped}')
        self.stdout.write(f'   Erreurs: {errors}')
        self.stdout.write('=' * 60)

    def count_existing_records(self):
        """Count existing DocumentTranslation records."""
        count = DocumentTranslation.objects.count()
        self.stdout.write(f'\n📁 Enregistrements existants dans Django Lara: {count}')

    def count_custommt_projects(self, api_url, api_key, page_size):
        """Count total projects in Custom.MT."""
        try:
            response = requests.get(
                api_url,
                params={'page_size': 1, 'page': 1},
                headers={'token': api_key},
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            total_count = data.get('count', 0)
            num_pages = data.get('num_pages', 1)

            # Recalculate pages based on our batch size
            if total_count > 0:
                num_pages = (total_count + page_size - 1) // page_size

            return total_count, num_pages

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'Erreur de comptage: {e}'))
            return 0, 0

    def fetch_custommt_page(self, api_url, api_key, page, page_size):
        """Fetch a page of projects from Custom.MT."""
        response = requests.get(
            api_url,
            params={'page_size': page_size, 'page': page},
            headers={'token': api_key},
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])

    def migrate_project(self, project, skip_files, api_url, api_key):
        """Migrate a single project to DocumentTranslation."""
        project_id = project.get('id')

        # Check if already migrated (by lara_id)
        if DocumentTranslation.objects.filter(lara_id=f'custommt_{project_id}').exists():
            return 'skipped'

        try:
            # Extract filename from URL
            source_file_url = project.get('source_file', '')
            filename = 'unknown'
            if source_file_url:
                parsed = urlparse(source_file_url)
                filename = unquote(parsed.path.split('/')[-1])

            # Map status
            status_map = {
                'done': 'translated',
                'translated': 'translated',
                'error': 'error',
                'failed': 'error',
                'pending': 'pending',
                'processing': 'processing',
                'in_progress': 'processing',
            }
            original_status = project.get('status', 'pending')
            mapped_status = status_map.get(original_status.lower(), 'pending')

            with transaction.atomic():
                doc = DocumentTranslation(
                    filename=filename,
                    source_language=project.get('source_language', ''),
                    target_language=project.get('target_language', ''),
                    status=mapped_status,
                    user_uuid=str(project.get('user_custom_mt_token', '')) or None,
                    lara_id=f'custommt_{project_id}',
                    domain=project.get('domain_name', '') or project.get('domain', ''),
                    template_name=project.get('template_name', '') or None,
                    error_message=project.get('error_reason', '') or project.get('error_message', '') or '',
                )

                # Download and save files if not skipping
                if not skip_files:
                    # Original file
                    if source_file_url:
                        try:
                            file_content = requests.get(source_file_url, timeout=60).content
                            doc.original_file.save(filename, ContentFile(file_content), save=False)
                        except Exception as e:
                            self.stderr.write(f'      ⚠ Erreur téléchargement source {filename}: {e}')

                    # Translated file
                    translated_file_url = project.get('translated_file', '')
                    if translated_file_url and mapped_status == 'translated':
                        try:
                            target_content = requests.get(translated_file_url, timeout=60).content
                            target_filename = f'translated_{filename}'
                            doc.translated_file.save(target_filename, ContentFile(target_content), save=False)
                        except Exception as e:
                            self.stderr.write(f'      ⚠ Erreur téléchargement traduit {filename}: {e}')

                    # Reviewed file
                    reviewed_file_url = project.get('reviewed_file', '')
                    if reviewed_file_url:
                        try:
                            reviewed_content = requests.get(reviewed_file_url, timeout=60).content
                            reviewed_filename = f'reviewed_{filename}'
                            doc.reviewed_file.save(reviewed_filename, ContentFile(reviewed_content), save=False)
                        except Exception as e:
                            self.stderr.write(f'      ⚠ Erreur téléchargement reviewed {filename}: {e}')

                    # TMX file
                    tmx_file_url = project.get('tmx_file', '')
                    if tmx_file_url:
                        try:
                            tmx_content = requests.get(tmx_file_url, timeout=60).content
                            tmx_filename = filename.rsplit('.', 1)[0] + '.tmx'
                            doc.tmx_file.save(tmx_filename, ContentFile(tmx_content), save=False)
                        except Exception as e:
                            self.stderr.write(f'      ⚠ Erreur téléchargement TMX {filename}: {e}')

                    # XLIFF file
                    xliff_file_url = project.get('xliff_file', '')
                    if xliff_file_url:
                        try:
                            xliff_content = requests.get(xliff_file_url, timeout=60).content
                            xliff_filename = filename.rsplit('.', 1)[0] + '.xliff'
                            doc.xliff_file.save(xliff_filename, ContentFile(xliff_content), save=False)
                        except Exception as e:
                            self.stderr.write(f'      ⚠ Erreur téléchargement XLIFF {filename}: {e}')

                doc.save()

                # Update created_at to match original (if available)
                created_at = project.get('created_at')
                if created_at:
                    DocumentTranslation.objects.filter(id=doc.id).update(created_at=created_at)

            return 'migrated'

        except Exception as e:
            self.stderr.write(self.style.ERROR(f'      ❌ Erreur migration {project_id}: {e}'))
            return 'error'
