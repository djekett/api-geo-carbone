from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'forets', views.ForetClasseeViewSet, basename='foretclassee')
router.register(r'occupations', views.OccupationSolViewSet, basename='occupationsol')
router.register(r'placettes', views.PlacetteViewSet)
router.register(r'infrastructures', views.InfrastructureViewSet, basename='infrastructure')
router.register(r'zones-etude', views.ZoneEtudeViewSet)
router.register(r'nomenclatures', views.NomenclatureCouvertViewSet)

urlpatterns = router.urls
