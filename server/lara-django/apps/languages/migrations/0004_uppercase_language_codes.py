"""
Migration to normalize all language codes to UPPERCASE.
This migration updates:
- Language.abbreviation (primary key)
- TranslationTemplate.source_language and target_language
- DocumentTranslation.source_language and target_language
- Resource.target_languages (comma-separated text field)
- Glossary.target_languages (comma-separated text field)
- ForeignKey references in Resource, Glossary, Memory
"""
from django.db import migrations


def normalize_to_uppercase(apps, schema_editor):
    """Normalize all language codes to UPPERCASE."""
    Language = apps.get_model('languages', 'Language')
    TranslationTemplate = apps.get_model('templates', 'TranslationTemplate')
    DocumentTranslation = apps.get_model('translation', 'DocumentTranslation')
    Resource = apps.get_model('resources', 'Resource')
    Glossary = apps.get_model('glossaries', 'Glossary')
    Memory = apps.get_model('memories', 'Memory')

    # Step 1: Find languages that need uppercase conversion
    languages_to_update = []
    for lang in Language.objects.all():
        upper_abbr = lang.abbreviation.upper()
        if lang.abbreviation != upper_abbr:
            languages_to_update.append((lang.abbreviation, upper_abbr))

    print(f"\n[MIGRATION] Found {len(languages_to_update)} languages to convert to uppercase")

    # Step 2: Update ForeignKey references BEFORE updating Language primary keys
    for old_abbr, new_abbr in languages_to_update:
        print(f"[MIGRATION] Converting '{old_abbr}' -> '{new_abbr}'")

        # Check if the new abbreviation already exists
        if Language.objects.filter(abbreviation=new_abbr).exists():
            print(f"[MIGRATION] Warning: '{new_abbr}' already exists, updating FKs to point to it")

            # Update FKs to point to existing uppercase record
            Resource.objects.filter(source_language_id=old_abbr).update(source_language_id=new_abbr)
            Glossary.objects.filter(source_language_id=old_abbr).update(source_language_id=new_abbr)
            Memory.objects.filter(source_language_id=old_abbr).update(source_language_id=new_abbr)
            Memory.objects.filter(target_language_id=old_abbr).update(target_language_id=new_abbr)

            # Delete the old lowercase language record
            Language.objects.filter(abbreviation=old_abbr).delete()
        else:
            # Use raw SQL to update PK and FKs
            with schema_editor.connection.cursor() as cursor:
                # Update FKs in resources
                cursor.execute(
                    "UPDATE resources_resource SET source_language_id = %s WHERE source_language_id = %s",
                    [new_abbr, old_abbr]
                )

                # Update FKs in glossaries
                cursor.execute(
                    "UPDATE glossaries_glossary SET source_language_id = %s WHERE source_language_id = %s",
                    [new_abbr, old_abbr]
                )

                # Update FKs in memories (both source and target)
                cursor.execute(
                    "UPDATE memories_memory SET source_language_id = %s WHERE source_language_id = %s",
                    [new_abbr, old_abbr]
                )
                cursor.execute(
                    "UPDATE memories_memory SET target_language_id = %s WHERE target_language_id = %s",
                    [new_abbr, old_abbr]
                )

                # Now update the Language primary key
                cursor.execute(
                    "UPDATE languages_language SET abbreviation = %s WHERE abbreviation = %s",
                    [new_abbr, old_abbr]
                )

    # Step 3: Update TranslationTemplate source_language and target_language
    templates_updated = 0
    for template in TranslationTemplate.objects.all():
        changed = False
        if template.source_language and template.source_language != template.source_language.upper():
            template.source_language = template.source_language.upper()
            changed = True
        if template.target_language and template.target_language != template.target_language.upper():
            template.target_language = template.target_language.upper()
            changed = True
        if changed:
            template.save()
            templates_updated += 1

    print(f"[MIGRATION] Updated {templates_updated} TranslationTemplate records")

    # Step 4: Update DocumentTranslation source_language and target_language
    docs_updated = 0
    for doc in DocumentTranslation.objects.all():
        changed = False
        if doc.source_language and doc.source_language != doc.source_language.upper():
            doc.source_language = doc.source_language.upper()
            changed = True
        if doc.target_language and doc.target_language != doc.target_language.upper():
            doc.target_language = doc.target_language.upper()
            changed = True
        if changed:
            doc.save()
            docs_updated += 1

    print(f"[MIGRATION] Updated {docs_updated} DocumentTranslation records")

    # Step 5: Update Resource.target_languages (comma-separated text field)
    resources_updated = 0
    for resource in Resource.objects.all():
        if resource.target_languages:
            upper_targets = ','.join([lang.strip().upper() for lang in resource.target_languages.split(',')])
            if resource.target_languages != upper_targets:
                resource.target_languages = upper_targets
                resource.save()
                resources_updated += 1

    print(f"[MIGRATION] Updated {resources_updated} Resource records")

    # Step 6: Update Glossary.target_languages (comma-separated text field)
    glossaries_updated = 0
    for glossary in Glossary.objects.all():
        if glossary.target_languages:
            upper_targets = ','.join([lang.strip().upper() for lang in glossary.target_languages.split(',')])
            if glossary.target_languages != upper_targets:
                glossary.target_languages = upper_targets
                glossary.save()
                glossaries_updated += 1

    print(f"[MIGRATION] Updated {glossaries_updated} Glossary records")

    print("[MIGRATION] Language code normalization complete!")


def reverse_migration(apps, schema_editor):
    """
    Reverse migration - this is a one-way migration.
    We cannot reliably reverse to the original case.
    """
    print("[MIGRATION] Warning: Cannot reverse uppercase normalization - original case is lost")


class Migration(migrations.Migration):

    dependencies = [
        ('languages', '0003_populate_country_codes'),
        ('templates', '0001_initial'),
        ('translation', '0005_migrate_custommt_data'),
        ('resources', '0002_alter_resource_source_language'),
        ('glossaries', '0002_auto_20251129_2112'),
        ('memories', '0003_auto_20251129_2121'),
    ]

    operations = [
        migrations.RunPython(normalize_to_uppercase, reverse_migration),
    ]
