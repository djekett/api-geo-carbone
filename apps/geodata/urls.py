from django.urls import path
from . import views

urlpatterns = [
    path('admin/import/upload/', views.ImportUploadView.as_view(), name='import-upload'),
    path('admin/import/execute/', views.ImportExecuteView.as_view(), name='import-execute'),
]
