"""
Admin views for Lexa Backend data.
These are custom admin views that display data fetched from Lexa's internal API.
"""
from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.urls import path
from django.utils.decorators import method_decorator
from django.views import View
from django.utils.html import format_html

from config.admin import lara_admin_site
from .services import get_lexa_users, get_lexa_domain_groups, get_lexa_domain, clear_lexa_cache, DEFAULT_DOMAIN_COLOR


@method_decorator(staff_member_required, name='dispatch')
class LexaUsersView(View):
    """Admin view to display Lexa users."""

    ITEMS_PER_PAGE = 25

    def get(self, request):
        users = get_lexa_users()

        # Get filter parameters
        filter_username = request.GET.get('username', '').strip()
        filter_email = request.GET.get('email', '').strip()
        filter_status = request.GET.get('status', '')
        page = request.GET.get('page', '1')

        try:
            page = int(page)
        except ValueError:
            page = 1

        # Format users for display
        formatted_users = []
        for user in users:
            formatted_users.append({
                'id': user.get('id'),
                'uuid': user.get('uuid', '-')[:8] + '...' if user.get('uuid') else '-',
                'uuid_full': user.get('uuid', '-'),
                'username': user.get('username', '-'),
                'email': user.get('email') or '-',
                'first_name': user.get('first_name') or '-',
                'last_name': user.get('last_name') or '-',
                'customer_id': user.get('customer_id') or '-',
                'language': user.get('language', 'en'),
                'is_active': user.get('is_active', False),
            })

        # Apply filters
        if filter_username:
            formatted_users = [u for u in formatted_users if filter_username.lower() in u['username'].lower()]
        if filter_email:
            formatted_users = [u for u in formatted_users if filter_email.lower() in u['email'].lower()]
        if filter_status == 'active':
            formatted_users = [u for u in formatted_users if u['is_active']]
        elif filter_status == 'inactive':
            formatted_users = [u for u in formatted_users if not u['is_active']]

        # Pagination
        total_count = len(formatted_users)
        total_pages = (total_count + self.ITEMS_PER_PAGE - 1) // self.ITEMS_PER_PAGE
        if page < 1:
            page = 1
        if page > total_pages and total_pages > 0:
            page = total_pages

        start_idx = (page - 1) * self.ITEMS_PER_PAGE
        end_idx = start_idx + self.ITEMS_PER_PAGE
        paginated_users = formatted_users[start_idx:end_idx]

        # Build pagination info
        page_range = range(max(1, page - 2), min(total_pages + 1, page + 3))

        context = {
            **lara_admin_site.each_context(request),
            'title': 'Lexa Users',
            'users': paginated_users,
            'users_count': total_count,
            'opts': {'app_label': 'lexa_backend', 'model_name': 'lexauser'},
            'has_permission': True,
            # Filters
            'filter_username': filter_username,
            'filter_email': filter_email,
            'filter_status': filter_status,
            # Pagination
            'page': page,
            'total_pages': total_pages,
            'page_range': page_range,
            'has_previous': page > 1,
            'has_next': page < total_pages,
            'previous_page': page - 1,
            'next_page': page + 1,
            'start_index': start_idx + 1,
            'end_index': min(end_idx, total_count),
        }
        return render(request, 'admin/lexa_backend/lexa_users.html', context)


@method_decorator(staff_member_required, name='dispatch')
class LexaDomainGroupsView(View):
    """Admin view to display Lexa domain groups."""

    def get(self, request):
        # Clear cache if refresh requested
        if request.GET.get('refresh') == '1':
            clear_lexa_cache()

        domain_groups = get_lexa_domain_groups()

        # Format domain groups for display
        formatted_groups = []
        total_domains = 0
        for group in domain_groups:
            domains = group.get('domains', [])
            total_domains += len(domains)

            # Add color to each domain from cached domain info
            domains_with_colors = []
            for domain in domains:
                domain_name = domain.get('name', '')
                domain_info = get_lexa_domain(domain_name)
                color = domain_info.get('color', DEFAULT_DOMAIN_COLOR) if domain_info else DEFAULT_DOMAIN_COLOR
                domains_with_colors.append({
                    **domain,
                    'color': color,
                })

            formatted_groups.append({
                'id': group.get('id'),
                'name': group.get('name', '-'),
                'french_name': group.get('french_name') or '-',
                'icon': group.get('icon') or 'folder',
                'domains': domains_with_colors,
                'domains_count': len(domains),
            })

        context = {
            **lara_admin_site.each_context(request),
            'title': 'Lexa Domain Groups',
            'domain_groups': formatted_groups,
            'groups_count': len(formatted_groups),
            'total_domains': total_domains,
            'opts': {'app_label': 'lexa_backend', 'model_name': 'lexadomaingroup'},
            'has_permission': True,
        }
        return render(request, 'admin/lexa_backend/lexa_domain_groups.html', context)


def get_lexa_admin_urls():
    """Return URL patterns for Lexa admin views."""
    return [
        path('lexa_backend/lexauser/', LexaUsersView.as_view(), name='lexa_backend_lexauser_changelist'),
        path('lexa_backend/lexadomaingroup/', LexaDomainGroupsView.as_view(), name='lexa_backend_lexadomaingroup_changelist'),
    ]
