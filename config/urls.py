from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

from .views import HomeView, EnjeuxView, CartesView, trigger_import_view

urlpatterns = [
    path('admin/trigger-import/', trigger_import_view, name='trigger-import'),
    path('admin/', admin.site.urls),

    # API v1
    path('api/v1/', include('apps.carbone.urls')),
    path('api/v1/', include('apps.analysis.urls')),
    path('api/v1/', include('apps.geodata.urls')),
    path('api/v1/auth/', include('apps.accounts.urls')),

    # DRF browsable API auth
    path('api-auth/', include('rest_framework.urls')),

    # Back-office
    path('backoffice/', TemplateView.as_view(template_name='backoffice/dashboard.html'), name='backoffice'),
    path('backoffice/import/', TemplateView.as_view(template_name='backoffice/import_wizard.html'), name='backoffice-import'),

    # Frontend pages
    path('', HomeView.as_view(), name='home'),
    path('enjeux/', EnjeuxView.as_view(), name='enjeux'),
    path('cartes/', CartesView.as_view(), name='cartes'),
    path('carte/', TemplateView.as_view(template_name='map/index.html'), name='carte'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
