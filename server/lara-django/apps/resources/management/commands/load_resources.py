"""
Management command for resources app.
This module is now a stub - the Resource model has been deleted.
"""
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'This command is deprecated - the Resource model has been deleted.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            'This command is deprecated. The Resource model has been deleted.\n'
            'Templates are now generated from Memories and Glossaries tables.'
        ))
