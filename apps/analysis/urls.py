from django.urls import path
from . import views

urlpatterns = [
    path('ai/query/', views.AIQueryView.as_view(), name='ai-query'),
]
