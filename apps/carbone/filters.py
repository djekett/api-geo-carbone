import django_filters
from .models import OccupationSol, Placette, Infrastructure, ZoneEtude


class OccupationSolFilter(django_filters.FilterSet):
    annee = django_filters.NumberFilter(field_name='annee')
    foret = django_filters.NumberFilter(field_name='foret__id')
    foret_code = django_filters.CharFilter(field_name='foret__code', lookup_expr='iexact')
    type = django_filters.CharFilter(field_name='nomenclature__code', lookup_expr='iexact')

    class Meta:
        model = OccupationSol
        fields = ['annee', 'foret', 'foret_code', 'type']


class PlacetteFilter(django_filters.FilterSet):
    foret = django_filters.NumberFilter(field_name='foret__id')
    foret_code = django_filters.CharFilter(field_name='foret__code', lookup_expr='iexact')
    annee = django_filters.NumberFilter(field_name='annee_mesure')

    class Meta:
        model = Placette
        fields = ['foret', 'foret_code', 'annee']


class InfrastructureFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name='type_infra', lookup_expr='iexact')

    class Meta:
        model = Infrastructure
        fields = ['type']


class ZoneEtudeFilter(django_filters.FilterSet):
    type = django_filters.CharFilter(field_name='type_zone', lookup_expr='iexact')
    niveau = django_filters.NumberFilter(field_name='niveau')

    class Meta:
        model = ZoneEtude
        fields = ['type', 'niveau']
