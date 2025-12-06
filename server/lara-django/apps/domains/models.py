# Stub models - domains app has been removed
# These models exist only to satisfy migration references
from django.db import models


class Domain(models.Model):
    """Stub Domain model for migration compatibility.
    Only includes columns that exist in the actual database table.
    """
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        managed = False  # Don't create/modify the table
        db_table = 'domains_domain'

    def __str__(self):
        return self.name


class RelatedDomain(models.Model):
    """Stub RelatedDomain model for migration compatibility."""
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='related_domains')
    related_domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name='related_to')

    class Meta:
        managed = False  # Don't create/modify the table
        db_table = 'domains_relateddomain'
