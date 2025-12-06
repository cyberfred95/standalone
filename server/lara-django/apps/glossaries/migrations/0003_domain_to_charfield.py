"""
Migration to convert domain ForeignKey to CharField.
Replaces the ForeignKey to Domain with a CharField storing the domain name.
"""
from django.db import migrations, models


def copy_domain_name(apps, schema_editor):
    """Copy domain.name to domain_name field using raw SQL."""
    # Use raw SQL to get domain names since Domain model may not exist
    cursor = schema_editor.connection.cursor()
    cursor.execute("""
        UPDATE glossaries_glossary g
        SET domain_name = d.name
        FROM domains_domain d
        WHERE g.domain_id = d.id
        AND g.domain_id IS NOT NULL
    """)


def reverse_copy_domain(apps, schema_editor):
    """Reverse is not supported since domains app is removed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('glossaries', '0002_auto_20251129_2112'),
    ]

    operations = [
        # Step 1: Add temporary domain_name field
        migrations.AddField(
            model_name='glossary',
            name='domain_name',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                verbose_name='Domain Name (temp)'
            ),
        ),
        # Step 2: Copy domain.name to domain_name
        migrations.RunPython(copy_domain_name, reverse_copy_domain),
        # Step 3: Remove the old domain ForeignKey
        migrations.RemoveField(
            model_name='glossary',
            name='domain',
        ),
        # Step 4: Rename domain_name to domain
        migrations.RenameField(
            model_name='glossary',
            old_name='domain_name',
            new_name='domain',
        ),
        # Step 5: Update field properties
        migrations.AlterField(
            model_name='glossary',
            name='domain',
            field=models.CharField(
                max_length=255,
                null=True,
                blank=True,
                verbose_name='Domain',
                help_text='Domain name from Lexa'
            ),
        ),
    ]
