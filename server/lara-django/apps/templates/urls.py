"""
URL configuration for templates app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'templates'

router = DefaultRouter()
router.register(r'', views.TemplateViewSet)

urlpatterns = [
    # Custom endpoints first to avoid conflict with router
    path('find/', views.find_template, name='template-find'),
    
    # Router endpoints (CRUD)
    path('', include(router.urls)),
]
