"""
URL configuration for Lara Django backend.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework import routers
from apps.translation.views import health_check
from apps.memories import views as memory_views
from apps.glossaries import views as glossary_views
from config.admin import lara_admin_site

# Create main router
router = routers.DefaultRouter()

urlpatterns = [
    # Custom admin views for memories
    path('lara-django/admin/memories/compare-lara/', memory_views.compare_with_lara, name='memories_compare_lara'),
    path('lara-django/admin/memories/apply-lara-changes/', memory_views.apply_lara_changes, name='memories_apply_lara_changes'),

    # Custom admin views for template generation from memories
    path('lara-django/admin/memories/compare-templates/', memory_views.compare_templates_from_memories, name='memories_compare_templates'),
    path('lara-django/admin/memories/apply-template-changes/', memory_views.apply_template_changes, name='memories_apply_template_changes'),

    # Custom admin views for glossaries
    path('lara-django/admin/glossaries/refresh/', glossary_views.refresh_glossaries_form, name='glossaries_refresh_form'),
    path('lara-django/admin/glossaries/loading/', glossary_views.loading_page, name='glossaries_loading'),
    path('lara-django/admin/glossaries/fetch-progress/', glossary_views.fetch_progress, name='glossaries_fetch_progress'),
    path('lara-django/admin/glossaries/compare-lara/', glossary_views.compare_with_lara, name='glossaries_compare_lara'),
    path('lara-django/admin/glossaries/apply-lara-changes/', glossary_views.apply_lara_changes, name='glossaries_apply_lara_changes'),

    path('lara-django/admin/', lara_admin_site.urls),

    # Health check
    path('lara-django/health/', health_check, name='health_check'),

    # API endpoints - maintaining compatibility with Node.js backend

    # Translation endpoints (translate-text, translate-document, etc.)
    path('lara-django/api/lara/', include('apps.translation.urls')),

    # Templates endpoints
    path('lara-django/api/templates/', include(('apps.templates.urls', 'templates'), namespace='templates')),
    # Alias for templates to match some Node.js routes if needed
    path('lara-django/api/lara/templates/', include(('apps.templates.urls', 'templates'), namespace='templates-alias')),

    # Resources endpoints
    path('lara-django/api/lara/glossaries-list/', include('apps.glossaries.urls')),
    path('lara-django/api/lara/memories-list/', include('apps.memories.urls')),

    # Router URLs
    path('lara-django/api/', include(router.urls)),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
