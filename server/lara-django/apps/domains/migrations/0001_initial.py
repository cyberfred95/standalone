# Stub migration - domains app has been removed
# This file exists to satisfy migration dependencies from other apps
# The Domain model definition is kept to allow Django to reconstruct historical state
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Domain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True, verbose_name='Domain Name')),
                ('french_name', models.CharField(blank=True, max_length=255, null=True, verbose_name='French Name')),
                ('icon', models.CharField(blank=True, max_length=50, null=True, verbose_name='Icon')),
                ('color', models.CharField(blank=True, max_length=7, null=True, verbose_name='Color')),
            ],
            options={
                'verbose_name': 'Domain',
                'verbose_name_plural': 'Domains',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='RelatedDomain',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_domains', to='domains.domain')),
                ('related_domain', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='related_to', to='domains.domain')),
            ],
            options={
                'verbose_name': 'Related Domain',
                'verbose_name_plural': 'Related Domains',
            },
        ),
    ]
