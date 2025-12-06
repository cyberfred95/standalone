"""
Migration to delete the Resource model.
The Resource model is no longer used - templates are now generated from Memories and Glossaries.
"""
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('resources', '0002_alter_resource_source_language'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Resource',
        ),
    ]
