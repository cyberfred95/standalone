"""
Admin views for glossaries.

Provides Django admin interface views for glossary management.
"""
import json
from datetime import datetime, timedelta

from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import transaction
from django.http import StreamingHttpResponse
from django.core.cache import cache

from ..models import Glossary
from ..services import (
    fetch_lara_glossaries,
    fetch_lara_glossaries_with_progress,
    compare_glossaries,
)
from apps.languages.models import Language


@staff_member_required
def refresh_glossaries_form(request):
    """
    Display the form to select the date from which to refresh glossaries.
    """
    default_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')

    context = {
        'title': 'Refresh Glossaries from Lara',
        'default_date': default_date
    }

    return render(request, 'admin/glossaries/refresh_form.html', context)


@staff_member_required
def loading_page(request):
    """
    Display the loading page with progress bar.
    """
    since_date = request.GET.get('since_date', '')

    context = {
        'since_date': since_date
    }

    return render(request, 'admin/glossaries/loading.html', context)


@staff_member_required
def fetch_progress(request):
    """
    SSE endpoint that streams progress while fetching glossaries from Lara.
    """
    since_date_str = request.GET.get('since_date', '')
    since_date = None

    if since_date_str:
        try:
            since_date = datetime.strptime(since_date_str, '%Y-%m-%d')
        except ValueError:
            pass

    def event_stream():
        for event in fetch_lara_glossaries_with_progress(since_date):
            if event['type'] == 'complete':
                cache_key = f'lara_glossaries_{request.user.id}'
                cache.set(cache_key, event['glossaries'], timeout=300)
                yield f"data: {json.dumps({'type': 'complete'})}\n\n"
            else:
                yield f"data: {json.dumps(event)}\n\n"

    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@staff_member_required
def compare_with_lara(request):
    """
    Compare current database glossaries with Lara API glossaries.
    Display differences in a comparison table.
    """
    try:
        since_date_str = request.GET.get('since_date') or request.POST.get('since_date')
        from_loading = request.GET.get('from_loading') == '1'
        since_date = None

        if since_date_str:
            try:
                since_date = datetime.strptime(since_date_str, '%Y-%m-%d')
            except ValueError:
                messages.error(request, "Invalid date format. Use YYYY-MM-DD")
                return redirect('glossaries_refresh_form')

        # Fetch current DB glossaries
        db_glossaries_list = []
        for g in Glossary.objects.all().select_related('source_language'):
            db_glossaries_list.append({
                'glossary_id': g.glossary_id,
                'name': g.name,
                'uuid': g.uuid,
                'source_language': g.source_language.abbreviation if g.source_language else '',
                'target_languages': g.target_languages,
                'domain': g.domain or ''
            })

        # Try to get from cache if coming from loading page
        lara_glossaries = None
        if from_loading:
            cache_key = f'lara_glossaries_{request.user.id}'
            lara_glossaries = cache.get(cache_key)
            if lara_glossaries:
                cache.delete(cache_key)

        # Fallback to direct fetch if not in cache
        if lara_glossaries is None:
            lara_glossaries = fetch_lara_glossaries(since_date)

        # Compare
        differences = compare_glossaries(db_glossaries_list, lara_glossaries)

        context = {
            'differences': differences,
            'differences_json': json.dumps(differences),
            'title': 'Refresh Glossaries from Lara - Comparison',
            'since_date': since_date_str or 'All'
        }

        return render(request, 'admin/glossaries/compare_lara.html', context)

    except Exception as e:
        messages.error(request, f"Error fetching glossaries from Lara: {str(e)}")
        return redirect('admin:glossaries_glossary_changelist')


@staff_member_required
def apply_lara_changes(request):
    """
    Apply the changes from Lara to the database.
    """
    if request.method != 'POST':
        return redirect('admin:glossaries_glossary_changelist')

    try:
        all_differences_json = request.POST.get('all_differences', '[]')
        all_differences = json.loads(all_differences_json)

        selected_indices = request.POST.getlist('selected_changes')

        if not selected_indices:
            messages.warning(request, "No changes selected")
            return redirect('admin:glossaries_glossary_changelist')

        differences = [all_differences[int(idx)] for idx in selected_indices if int(idx) < len(all_differences)]

        stats = {
            'added': 0,
            'updated': 0
        }

        with transaction.atomic():
            for diff in differences:
                action = diff.get('action')
                glossary_id = diff.get('glossary_id')

                source_lang_code = diff.get('source_language', '').upper()
                source_lang = None
                if source_lang_code:
                    source_lang = Language.objects.filter(abbreviation=source_lang_code).first()

                if action == 'add':
                    Glossary.objects.create(
                        glossary_id=glossary_id,
                        name=diff.get('name', ''),
                        uuid=diff.get('uuid', ''),
                        source_language=source_lang,
                        target_languages=diff.get('target_languages', ''),
                        domain=diff.get('domain', '')
                    )
                    stats['added'] += 1

                elif action == 'update':
                    glossary = Glossary.objects.filter(glossary_id=glossary_id).first()
                    if glossary:
                        glossary.name = diff.get('name', glossary.name)

                        if diff.get('uuid'):
                            glossary.uuid = diff.get('uuid')

                        if source_lang:
                            glossary.source_language = source_lang

                        if diff.get('target_languages'):
                            glossary.target_languages = diff.get('target_languages')

                        if diff.get('domain'):
                            glossary.domain = diff.get('domain')

                        glossary.save()
                        stats['updated'] += 1

        msg_parts = []
        if stats['added'] > 0:
            msg_parts.append(f"{stats['added']} glossary(ies) added")
        if stats['updated'] > 0:
            msg_parts.append(f"{stats['updated']} glossary(ies) updated")

        if msg_parts:
            messages.success(request, "Synchronization successful: " + ", ".join(msg_parts))
        else:
            messages.info(request, "No changes to apply")

        return redirect('admin:glossaries_glossary_changelist')

    except Exception as e:
        messages.error(request, f"Error applying changes: {str(e)}")
        return redirect('admin:glossaries_glossary_changelist')
