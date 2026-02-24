from django.views.generic import TemplateView
from apps.carbone.constants import (
    FORETS_DATA, NOMENCLATURE_DATA, SUPERFICIE_TOTALE_HA,
    BIOMASSE_REFERENCE, CARBONE_TOTAL_REFERENCE, STOCK_CARBONE_REFERENCE,
)


class HomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forets'] = FORETS_DATA
        context['superficie_totale'] = SUPERFICIE_TOTALE_HA
        return context


class EnjeuxView(TemplateView):
    template_name = 'enjeux.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['nomenclatures'] = NOMENCLATURE_DATA
        context['forets'] = FORETS_DATA
        context['superficie_totale'] = SUPERFICIE_TOTALE_HA
        # Only nomenclatures with non-zero carbon for the reference table
        context['nomenclatures_carbone'] = [
            n for n in NOMENCLATURE_DATA if n['stock_carbone_reference'] > 0
        ]
        return context


class CartesView(TemplateView):
    template_name = 'cartes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['forets'] = FORETS_DATA
        return context
