"""
Data migration to transfer all translations from Custom.MT to Django Lara.
This migration runs automatically with: python manage.py migrate

To skip this migration (if already done or not needed):
    python manage.py migrate translation 0004_add_migration_fields --fake
    python manage.py migrate translation 0005_migrate_custommt_data --fake
"""
import os
import requests
from django.db import migrations
from django.core.files.base import ContentFile
from urllib.parse import urlparse, unquote


# Configuration - can be overridden via environment variables
CUSTOMMT_API_URL = os.environ.get(
    'CUSTOMMT_API_URL',
    'https://cloudstorage.stage.fileprocessing.custom.mt/translate/legal230/'
)
CUSTOMMT_API_KEY = os.environ.get(
    'CUSTOMMT_API_KEY',
    '504d0e8d-84bd-4f2b-9ca4-a76232a849ab'
)
BATCH_SIZE = int(os.environ.get('MIGRATION_BATCH_SIZE', '100'))
SKIP_FILES = os.environ.get('MIGRATION_SKIP_FILES', 'false').lower() == 'true'


def migrate_custommt_to_lara(apps, schema_editor):
    """
    Migrate all translations from Custom.MT to Django Lara DocumentTranslation.
    """
    DocumentTranslation = apps.get_model('translation', 'DocumentTranslation')

    print("\n" + "=" * 60)
    print("Migration Custom.MT → Django Lara")
    print("=" * 60)

    if not CUSTOMMT_API_URL or not CUSTOMMT_API_KEY:
        print("⚠ CUSTOMMT_API_URL ou CUSTOMMT_API_KEY non configuré. Migration ignorée.")
        print("  Configurez les variables d'environnement et relancez la migration.")
        return

    # Step 1: Count total projects
    print(f"\n📊 Comptage des projets Custom.MT...")
    try:
        response = requests.get(
            CUSTOMMT_API_URL,
            params={'page_size': 1, 'page': 1},
            headers={'token': CUSTOMMT_API_KEY},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        total_count = data.get('count', 0)

        if total_count == 0:
            print("   Aucun projet trouvé dans Custom.MT")
            return

        num_pages = (total_count + BATCH_SIZE - 1) // BATCH_SIZE
        print(f"   → {total_count} projets trouvés sur {num_pages} pages")

    except Exception as e:
        print(f"❌ Erreur de connexion à Custom.MT: {e}")
        print("   Migration ignorée. Vous pouvez relancer avec:")
        print("   python manage.py migrate translation 0005_migrate_custommt_data")
        return

    # Step 2: Migrate projects
    print(f"\n🚀 Migration des projets...")
    if SKIP_FILES:
        print("   (Mode --skip-files: métadonnées uniquement)")

    migrated = 0
    skipped = 0
    errors = 0

    for page in range(1, num_pages + 1):
        try:
            response = requests.get(
                CUSTOMMT_API_URL,
                params={'page_size': BATCH_SIZE, 'page': page},
                headers={'token': CUSTOMMT_API_KEY},
                timeout=60
            )
            response.raise_for_status()
            projects = response.json().get('results', [])

            for project in projects:
                result = migrate_single_project(DocumentTranslation, project)
                if result == 'migrated':
                    migrated += 1
                elif result == 'skipped':
                    skipped += 1
                else:
                    errors += 1

            # Progress
            processed = min(page * BATCH_SIZE, total_count)
            print(f"   Page {page}/{num_pages}: {migrated} migrés, {skipped} ignorés, {errors} erreurs")

        except Exception as e:
            print(f"   ❌ Erreur page {page}: {e}")
            errors += 1

    # Summary
    print("\n" + "=" * 60)
    print(f"✅ Migration terminée!")
    print(f"   Migrés: {migrated}")
    print(f"   Ignorés (déjà existants): {skipped}")
    print(f"   Erreurs: {errors}")
    print("=" * 60 + "\n")


def migrate_single_project(DocumentTranslation, project):
    """Migrate a single project from Custom.MT to DocumentTranslation."""
    project_id = project.get('id')

    # Check if already migrated
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

        # Create document
        doc = DocumentTranslation(
            filename=filename,
            source_language=project.get('source_language', ''),
            target_language=project.get('target_language', ''),
            status=mapped_status,
            user_token=str(project.get('user_custom_mt_token', '')) or None,
            lara_id=f'custommt_{project_id}',
            domain=project.get('domain_name', '') or project.get('domain', ''),
            template_name=project.get('template_name', '') or None,
            error_message=project.get('error_reason', '') or project.get('error_message', '') or '',
        )

        # Download files if not skipping
        if not SKIP_FILES:
            # Original file
            if source_file_url:
                try:
                    content = requests.get(source_file_url, timeout=60).content
                    doc.original_file.save(filename, ContentFile(content), save=False)
                except Exception:
                    pass

            # Translated file
            translated_url = project.get('translated_file', '')
            if translated_url and mapped_status == 'translated':
                try:
                    content = requests.get(translated_url, timeout=60).content
                    doc.translated_file.save(f'translated_{filename}', ContentFile(content), save=False)
                except Exception:
                    pass

            # Reviewed file
            reviewed_url = project.get('reviewed_file', '')
            if reviewed_url:
                try:
                    content = requests.get(reviewed_url, timeout=60).content
                    doc.reviewed_file.save(f'reviewed_{filename}', ContentFile(content), save=False)
                except Exception:
                    pass

            # TMX file
            tmx_url = project.get('tmx_file', '')
            if tmx_url:
                try:
                    content = requests.get(tmx_url, timeout=60).content
                    tmx_filename = filename.rsplit('.', 1)[0] + '.tmx'
                    doc.tmx_file.save(tmx_filename, ContentFile(content), save=False)
                except Exception:
                    pass

            # XLIFF file
            xliff_url = project.get('xliff_file', '')
            if xliff_url:
                try:
                    content = requests.get(xliff_url, timeout=60).content
                    xliff_filename = filename.rsplit('.', 1)[0] + '.xliff'
                    doc.xliff_file.save(xliff_filename, ContentFile(content), save=False)
                except Exception:
                    pass

        doc.save()

        # Update created_at to preserve original timestamp
        created_at = project.get('created_at')
        if created_at:
            DocumentTranslation.objects.filter(id=doc.id).update(created_at=created_at)

        return 'migrated'

    except Exception as e:
        print(f"      ❌ Erreur: {project_id}: {e}")
        return 'error'


def reverse_migration(apps, schema_editor):
    """
    Reverse migration: Delete all records imported from Custom.MT.
    """
    DocumentTranslation = apps.get_model('translation', 'DocumentTranslation')
    count = DocumentTranslation.objects.filter(lara_id__startswith='custommt_').count()

    if count > 0:
        print(f"\n🗑 Suppression de {count} enregistrements migrés depuis Custom.MT...")
        DocumentTranslation.objects.filter(lara_id__startswith='custommt_').delete()
        print("   ✅ Suppression terminée\n")


class Migration(migrations.Migration):

    dependencies = [
        ('translation', '0004_add_migration_fields'),
    ]

    operations = [
        migrations.RunPython(
            migrate_custommt_to_lara,
            reverse_code=reverse_migration,
        ),
    ]
