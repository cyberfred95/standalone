"""
URL configuration for memories app.
"""
from django.urls import path
from . import views

app_name = 'memories'

urlpatterns = [
    path('', views.memory_list, name='memory-list'),
]
