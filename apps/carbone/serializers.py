from rest_framework import serializers
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from .models import (
    ZoneEtude, ForetClassee, NomenclatureCouvert,
    OccupationSol, Placette, Infrastructure,
)


class NomenclatureCouvertSerializer(serializers.ModelSerializer):
    class Meta:
        model = NomenclatureCouvert
        fields = ('id', 'code', 'libelle_fr', 'stock_carbone_reference', 'couleur_hex', 'ordre_affichage')


class ZoneEtudeSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ZoneEtude
        geo_field = 'geom'
        fields = ('id', 'nom', 'type_zone', 'niveau', 'created_at')


class ForetClasseeSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = ForetClassee
        geo_field = 'geom'
        fields = ('id', 'code', 'nom', 'superficie_legale_ha', 'statut_juridique',
                  'autorite_gestion', 'created_at')


class ForetClasseeListSerializer(serializers.ModelSerializer):
    """Serializer leger sans geometrie pour les listes."""
    class Meta:
        model = ForetClassee
        fields = ('id', 'code', 'nom', 'superficie_legale_ha')


class OccupationSolSerializer(GeoFeatureModelSerializer):
    foret_code = serializers.CharField(source='foret.code', read_only=True)
    foret_nom = serializers.CharField(source='foret.nom', read_only=True)
    type_couvert = serializers.CharField(source='nomenclature.code', read_only=True)
    libelle = serializers.CharField(source='nomenclature.libelle_fr', read_only=True)
    couleur = serializers.CharField(source='nomenclature.couleur_hex', read_only=True)

    class Meta:
        model = OccupationSol
        geo_field = 'geom'
        fields = ('id', 'foret', 'foret_code', 'foret_nom', 'nomenclature',
                  'type_couvert', 'libelle', 'couleur', 'annee',
                  'superficie_ha', 'stock_carbone_calcule', 'source_donnee')


class OccupationSolWriteSerializer(serializers.ModelSerializer):
    """Serializer pour la creation/modification (POST/PUT)."""
    class Meta:
        model = OccupationSol
        fields = ('foret', 'nomenclature', 'annee', 'superficie_ha',
                  'stock_carbone_calcule', 'source_donnee', 'fiabilite_pct',
                  'notes_admin', 'geom')


class PlacetteSerializer(GeoFeatureModelSerializer):
    foret_code = serializers.CharField(source='foret.code', read_only=True, default='')
    foret_nom = serializers.CharField(source='foret.nom', read_only=True, default='')

    class Meta:
        model = Placette
        geo_field = 'geom'
        fields = ('id', 'code_placette', 'foret', 'foret_code', 'foret_nom',
                  'annee_mesure', 'type_foret_observe', 'biomasse_tonne_ha',
                  'stock_carbone_mesure', 'donnees')


class InfrastructureSerializer(GeoFeatureModelSerializer):
    class Meta:
        model = Infrastructure
        geo_field = 'geom'
        fields = ('id', 'type_infra', 'nom', 'categorie', 'donnees')


class StatsSerializer(serializers.Serializer):
    """Serializer pour les statistiques agregees."""
    type_couvert__code = serializers.CharField()
    type_couvert__libelle_fr = serializers.CharField()
    type_couvert__couleur_hex = serializers.CharField()
    total_superficie_ha = serializers.FloatField()
    total_carbone = serializers.FloatField()
    nombre_polygones = serializers.IntegerField()
