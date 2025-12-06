"""
Migration to replace domain ForeignKey with domain_group CharField.
- Memories with domain="*" keep domain_group="*" (all domain groups)
- All other memories get domain_group=NULL
"""
from django.db import migrations, models


def migrate_domain_to_domain_group(apps, schema_editor):
    """Migrate domain data to domain_group field."""
    Memory = apps.get_model('memories', 'Memory')

    # Set domain_group = "*" for memories that have domain.name = "*"
    for memory in Memory.objects.select_related('domain').all():
        if memory.domain and memory.domain.name == '*':
            memory.domain_group = '*'
            memory.save(update_fields=['domain_group'])
        # All others remain NULL (default)


def reverse_migration(apps, schema_editor):
    """Reverse migration - restore domain from domain_group."""
    Memory = apps.get_model('memories', 'Memory')
    Domain = apps.get_model('domains', 'Domain')

    # Get or create the "*" domain
    star_domain, _ = Domain.objects.get_or_create(name='*')

    for memory in Memory.objects.all():
        if memory.domain_group == '*':
            memory.domain = star_domain
            memory.save(update_fields=['domain'])


class Migration(migrations.Migration):

    dependencies = [
        ('memories', '0003_auto_20251129_2121'),
    ]

    operations = [
        # Step 1: Add domain_group field
        migrations.AddField(
            model_name='memory',
            name='domain_group',
            field=models.CharField(
                blank=True,
                help_text='Domain group name from Lexa. Use \'*\' for all domain groups.',
                max_length=255,
                null=True,
                verbose_name='Domain Group'
            ),
        ),

        # Step 2: Migrate data
        migrations.RunPython(migrate_domain_to_domain_group, reverse_migration),

        # Step 3: Remove old index that references domain
        migrations.RemoveIndex(
            model_name='memory',
            name='memories_me_source__a6229c_idx',
        ),

        # Step 4: Remove domain field
        migrations.RemoveField(
            model_name='memory',
            name='domain',
        ),

        # Step 5: Add new index with domain_group
        migrations.AddIndex(
            model_name='memory',
            index=models.Index(fields=['source_language', 'domain_group'], name='memories_me_source__new_idx'),
        ),
    ]
