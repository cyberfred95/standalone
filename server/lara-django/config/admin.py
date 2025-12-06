"""
Custom admin site configuration to group apps under custom sections.
"""
from django.contrib.admin import AdminSite
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin, GroupAdmin
from django.urls import path


class LaraAdminSite(AdminSite):
    site_header = "Lara Translation Admin"
    site_title = "Lara Admin"
    index_title = "Welcome to Lara Translation Administration"

    def get_urls(self):
        """Add custom URLs for Lexa backend views."""
        urls = super().get_urls()
        from apps.lexa_backend.admin import get_lexa_admin_urls
        custom_urls = get_lexa_admin_urls()
        return custom_urls + urls

    def get_app_list(self, request):
        """
        Override to group apps under custom sections.
        """
        app_list = super().get_app_list(request)

        # Apps to merge under "Lara Server Objects" (glossaries, memories)
        server_apps = {'glossaries', 'memories'}
        # Apps to merge under "Lara Backend Objects" (languages)
        backend_apps = {'languages'}
        # Apps to merge under "Lara Backend Generated" (resources, templates)
        generated_apps = {'resources', 'templates'}

        server_models = []
        backend_models = []
        generated_models = []
        auth_app = None
        other_apps = []

        for app in app_list:
            app_name = app.get('app_label', '')
            if app_name in server_apps:
                server_models.extend(app.get('models', []))
            elif app_name in backend_apps:
                backend_models.extend(app.get('models', []))
            elif app_name in generated_apps:
                generated_models.extend(app.get('models', []))
            elif app_name == 'auth':
                auth_app = app
            else:
                other_apps.append(app)

        # Build final list
        final_apps = []

        # 1. Auth at the top
        if auth_app:
            final_apps.append(auth_app)

        # 2. LEXA BACKEND Objects section (Lexa Users, Domain Groups)
        lexa_backend_app = {
            'name': 'Lexa Backend Objects',
            'app_label': 'lexa_backend',
            'app_url': '#',
            'has_module_perms': True,
            'models': [
                {
                    'name': 'Lexa Users',
                    'object_name': 'LexaUser',
                    'admin_url': '/lara-django/admin/lexa_backend/lexauser/',
                    'view_only': True,
                },
                {
                    'name': 'Lexa Domain Groups',
                    'object_name': 'LexaDomainGroup',
                    'admin_url': '/lara-django/admin/lexa_backend/lexadomaingroup/',
                    'view_only': True,
                },
            ],
        }
        final_apps.append(lexa_backend_app)

        # 3. Lara Server Objects section (Glossary, Memory)
        if server_models:
            server_models.sort(key=lambda x: x.get('name', ''))
            lara_server_app = {
                'name': 'Lara Server Objects',
                'app_label': 'lara_server_objects',
                'app_url': '#',
                'has_module_perms': True,
                'models': server_models,
            }
            final_apps.append(lara_server_app)

        # 4. Lara Backend Objects section (Languages)
        if backend_models:
            backend_models.sort(key=lambda x: x.get('name', ''))
            lara_local_backend_app = {
                'name': 'Lara Backend Objects',
                'app_label': 'lara_backend_objects',
                'app_url': '#',
                'has_module_perms': True,
                'models': backend_models,
            }
            final_apps.append(lara_local_backend_app)

        # 5. Lara Backend Generated section (Resources, Translation Templates)
        if generated_models:
            # Custom order: Resources first, then Translation templates
            order = {'Resources': 0, 'Translation templates': 1}
            generated_models.sort(key=lambda x: order.get(x.get('name', ''), 99))
            lara_generated_app = {
                'name': 'Lara Backend Generated',
                'app_label': 'lara_backend_generated',
                'app_url': '#',
                'has_module_perms': True,
                'models': generated_models,
            }
            final_apps.append(lara_generated_app)

        # 6. Other apps (rename translation to "Document Translations")
        for app in other_apps:
            if app.get('app_label') == 'translation':
                app['name'] = 'Document Translations'
            final_apps.append(app)

        return final_apps


# Create the custom admin site instance
lara_admin_site = LaraAdminSite(name='lara_admin')

# Register auth models
lara_admin_site.register(User, UserAdmin)
lara_admin_site.register(Group, GroupAdmin)
