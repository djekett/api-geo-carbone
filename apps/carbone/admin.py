from django.contrib.gis import admin as geo_admin
from django.contrib import admin
from .models import (
    ZoneEtude, ForetClassee, NomenclatureCouvert,
    OccupationSol, Placette, Infrastructure,
)


@admin.register(ZoneEtude)
class ZoneEtudeAdmin(geo_admin.GISModelAdmin):
    list_display = ('nom', 'type_zone', 'niveau', 'created_at')
    list_filter = ('type_zone', 'niveau')
    search_fields = ('nom',)


@admin.register(ForetClassee)
class ForetClasseeAdmin(geo_admin.GISModelAdmin):
    list_display = ('code', 'nom', 'superficie_legale_ha', 'autorite_gestion')
    search_fields = ('nom', 'code')
    list_filter = ('autorite_gestion',)


@admin.register(NomenclatureCouvert)
class NomenclatureCouvertAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle_fr', 'stock_carbone_reference', 'couleur_hex', 'ordre_affichage')
    ordering = ('ordre_affichage',)


@admin.register(OccupationSol)
class OccupationSolAdmin(geo_admin.GISModelAdmin):
    list_display = ('foret', 'nomenclature', 'annee', 'superficie_ha', 'stock_carbone_calcule')
    list_filter = ('annee', 'foret', 'nomenclature')
    search_fields = ('foret__nom', 'foret__code')
    raw_id_fields = ('foret', 'nomenclature')


@admin.register(Placette)
class PlacetteAdmin(geo_admin.GISModelAdmin):
    list_display = ('code_placette', 'foret', 'annee_mesure', 'biomasse_tonne_ha', 'stock_carbone_mesure')
    list_filter = ('foret', 'annee_mesure')
    search_fields = ('code_placette',)


@admin.register(Infrastructure)
class InfrastructureAdmin(geo_admin.GISModelAdmin):
    list_display = ('type_infra', 'nom', 'categorie')
    list_filter = ('type_infra',)
    search_fields = ('nom',)
