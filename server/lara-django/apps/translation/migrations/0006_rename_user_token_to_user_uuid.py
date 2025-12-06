"""
Migration to rename user_token field to user_uuid for consistency with Lexa.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('translation', '0005_migrate_custommt_data'),
    ]

    operations = [
        migrations.RenameField(
            model_name='documenttranslation',
            old_name='user_token',
            new_name='user_uuid',
        ),
    ]
