"""
URL configuration for glossaries app.
"""
from django.urls import path
from .views import (
    glossary_list,
    create_glossary,
    update_glossary,
    delete_glossary,
    search_glossaries,
)

app_name = 'glossaries'

urlpatterns = [
    # List all glossaries
    path('', glossary_list, name='glossary-list'),

    # Create a new glossary
    path('create/', create_glossary, name='glossary-create'),

    # Search glossaries by criteria
    path('search/', search_glossaries, name='glossary-search'),

    # Update an existing glossary
    path('<str:glossary_id>/update/', update_glossary, name='glossary-update'),

    # Delete a glossary
    path('<str:glossary_id>/delete/', delete_glossary, name='glossary-delete'),
]
