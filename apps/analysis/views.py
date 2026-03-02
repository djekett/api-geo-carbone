"""
AI Query View -- Chat-to-Map v4.0 "Extraordinaire"

Nouveautes v4:
- chart_data : donnees pre-formatees pour Chart.js (labels, datasets, colors)
- coordinates : centre geographique des forets pour fly-to map
- fun_fact : fait ecologique aleatoire contextuel
- suggestions : 3-4 suggestions de suivi intelligentes
- confidence : score 0-100 de certitude du parsing
"""
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .nlp_engine import (
    NLPEngine,
    FOREST_CENTERS,
    get_fun_fact,
    get_suggestions,
    compute_confidence,
)
from .models import RequeteNLP
from apps.carbone.serializers import OccupationSolSerializer


class AIQueryView(APIView):
    """
    Endpoint de requete en langage naturel (Chat-to-Map).

    POST /api/v1/ai/query/
    Body: {"query": "texte en francais"}
    """

    GEOJSON_LIMIT = 200

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Le champ "query" est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if len(query) > 500:
            query = query[:500]

        start = time.time()
        engine = NLPEngine()
        parsed = engine.parse(query)

        # ----------------------------------------------------------
        # Session-based conversational context
        # ----------------------------------------------------------
        session_context = request.session.get('nlp_context', {})

        if parsed['intent'] != 'help':
            if not parsed['forests'] and session_context.get('forests'):
                parsed['forests'] = session_context['forests']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['forests']
            if not parsed['years'] and session_context.get('years'):
                parsed['years'] = session_context['years']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['years']
            if not parsed['cover_types'] and session_context.get('cover_types'):
                parsed['cover_types'] = session_context['cover_types']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['cover_types']

            request.session['nlp_context'] = {
                'forests': parsed['forests'],
                'cover_types': parsed['cover_types'],
                'years': parsed['years'],
            }

        nb_results = 0
        orm_desc = ''

        # ----------------------------------------------------------
        # Handle intents
        # ----------------------------------------------------------

        # HELP
        if parsed['intent'] == 'help':
            response_data = {
                'type': 'help',
                'parsed': parsed,
                'data': {
                    'message': (
                        "Je suis l'assistant IA de la plateforme API.GEO.Carbone. "
                        "Je peux analyser les donnees forestieres du departement d'Oume "
                        "(6 forets classees, 3 annees : 1986, 2003, 2023)."
                    ),
                    'examples': [
                        "Montre les zones de foret dense a DOKA en 2003",
                        "Quelle est la superficie de foret claire a SANGOUE ?",
                        "Compare TENE entre 1986 et 2023",
                        "Deforestation a LAHOUDA",
                        "Stock carbone pour 2023",
                        "Classement des forets par carbone",
                        "Resume global pour 2023",
                        "Active le mode CO2 sur la carte",
                    ],
                    'capabilities': [
                        "Afficher des couches sur la carte (foret dense, claire, degradee...)",
                        "Calculer des statistiques de superficie et stock carbone",
                        "Comparer l'evolution entre deux annees (1986, 2003, 2023)",
                        "Analyser la deforestation (perte de couvert forestier)",
                        "Classer les forets par superficie ou par carbone",
                        "Generer une synthese globale (resume)",
                        "Activer la spatialisation du stock carbone (mode CO2)",
                    ],
                    'forests': ['TENE', 'DOKA', 'SANGOUE', 'LAHOUDA', 'ZOUEKE_1', 'ZOUEKE_2'],
                    'years': [1986, 2003, 2023],
                },
            }
            orm_desc = 'help'
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # STOCK CARBONE
        if parsed['intent'] == 'stock_carbone':
            response_data = {
                'type': 'stock_carbone',
                'parsed': parsed,
                'data': {
                    'message': (
                        "Activation du mode Stock Carbone (CO2) sur la carte. "
                        "Les 4 classes forestieres sont affichees avec un gradient vert "
                        "proportionnel au stock de carbone (tCO2/ha)."
                    ),
                    'action': 'activate_carbone_mode',
                },
            }
            orm_desc = 'stock_carbone'
            return self._finalize(request, query, parsed, response_data, 4, orm_desc, start)

        # RESUME
        if parsed['intent'] == 'resume':
            resume = engine.build_resume(parsed)
            nb_results = len(resume.get('par_type', []))
            # Build chart data for resume
            chart_data = self._build_chart_data(resume.get('par_type', []))
            response_data = {
                'type': 'resume',
                'parsed': parsed,
                'data': resume,
                'chart_data': chart_data,
            }
            orm_desc = f"resume {resume.get('annee', '?')}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # COMPARE
        if parsed['intent'] == 'compare' and len(parsed['years']) >= 2:
            comparison = engine.build_comparison(parsed)
            # Build comparison chart data
            chart_data = self._build_comparison_chart(comparison) if comparison else None
            response_data = {
                'type': 'comparison',
                'parsed': parsed,
                'data': comparison,
                'chart_data': chart_data,
            }
            orm_desc = f"compare {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # DEFORESTATION
        if parsed['intent'] == 'deforestation' and len(parsed['years']) >= 2:
            deforestation = engine.build_deforestation(parsed)
            response_data = {
                'type': 'deforestation',
                'parsed': parsed,
                'data': deforestation,
            }
            orm_desc = f"deforestation {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # STATS / CARBON
        if parsed['intent'] in ('stats', 'carbon'):
            stats = list(engine.build_stats(parsed))
            nb_results = len(stats)
            if nb_results == 0:
                return self._no_results(request, query, parsed, engine, start)
            chart_data = self._build_chart_data(stats)
            response_data = {
                'type': 'stats',
                'parsed': parsed,
                'data': stats,
                'chart_data': chart_data,
            }
            orm_desc = f"stats {nb_results} types"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # RANKING
        if parsed['intent'] == 'ranking':
            ranking = engine.build_ranking(parsed)
            nb_results = len(ranking)
            response_data = {
                'type': 'ranking',
                'parsed': parsed,
                'data': ranking,
                'ranking_by': parsed.get('ranking_by', 'superficie'),
            }
            orm_desc = f"ranking {nb_results} forets"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # DEFAULT: SHOW -> return GeoJSON features
        qs = engine.build_queryset(parsed)
        count = qs.count()

        if count == 0:
            return self._no_results(request, query, parsed, engine, start)

        features = qs[:self.GEOJSON_LIMIT]
        serializer = OccupationSolSerializer(features, many=True)
        truncated = count > self.GEOJSON_LIMIT
        response_data = {
            'type': 'geojson',
            'parsed': parsed,
            'count': count,
            'displayed': min(count, self.GEOJSON_LIMIT),
            'truncated': truncated,
            'data': serializer.data,
        }
        nb_results = count
        orm_desc = f"geojson {count} features"
        return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

    # ----------------------------------------------------------
    # Chart data builders
    # ----------------------------------------------------------
    def _build_chart_data(self, stats_list):
        """Pre-format stats for Chart.js doughnut/bar."""
        if not stats_list:
            return None
        labels = []
        superficie_values = []
        carbone_values = []
        colors = []
        for s in stats_list:
            label = s.get('nomenclature__libelle_fr') or s.get('nomenclature__code', '?')
            labels.append(label)
            superficie_values.append(round(float(s.get('total_superficie_ha', 0)), 1))
            carbone_values.append(round(float(s.get('total_carbone', 0)), 1))
            colors.append(s.get('nomenclature__couleur_hex', '#999'))
        return {
            'labels': labels,
            'colors': colors,
            'superficie': superficie_values,
            'carbone': carbone_values,
        }

    def _build_comparison_chart(self, comparison):
        """Pre-format comparison for Chart.js."""
        if not comparison:
            return None
        a1 = comparison.get('annee1', {})
        a2 = comparison.get('annee2', {})
        labels = []
        values1 = []
        values2 = []
        colors = []
        for s in (a1.get('data') or []):
            code = s.get('nomenclature__code', '')
            labels.append(s.get('nomenclature__libelle_fr', code))
            values1.append(round(float(s.get('superficie_ha', 0)), 1))
            colors.append(s.get('nomenclature__couleur_hex', '#999'))
        # Map year 2 by code
        map2 = {}
        for s in (a2.get('data') or []):
            map2[s.get('nomenclature__code', '')] = round(float(s.get('superficie_ha', 0)), 1)
        for s in (a1.get('data') or []):
            code = s.get('nomenclature__code', '')
            values2.append(map2.get(code, 0))
        return {
            'labels': labels,
            'colors': colors,
            'annee1': a1.get('annee'),
            'values1': values1,
            'annee2': a2.get('annee'),
            'values2': values2,
        }

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------
    def _no_results(self, request, query, parsed, engine, start):
        """Return a no-results response with smart suggestions."""
        suggestions = engine.suggest_queries(parsed)
        response_data = {
            'type': 'no_results',
            'parsed': parsed,
            'suggestions': suggestions,
            'data': None,
        }
        return self._finalize(request, query, parsed, response_data, 0, 'no_results', start)

    def _finalize(self, request, query, parsed, response_data, nb_results, orm_desc, start):
        """Add timing, enrichments, log the query, and return the response."""
        processing_ms = int((time.time() - start) * 1000)
        response_data['processing_ms'] = processing_ms

        # Explanation
        explanation = parsed.get('_explanation', '')
        if explanation:
            response_data['explanation'] = explanation.strip()

        # ── v4 enrichments ──
        # Confidence score
        response_data['confidence'] = compute_confidence(parsed)

        # Fun fact
        response_data['fun_fact'] = get_fun_fact(
            parsed.get('intent', 'general'),
            parsed.get('cover_types', []),
        )

        # Smart suggestions
        session_ctx = request.session.get('nlp_context', {})
        response_data['suggestions'] = get_suggestions(parsed, session_ctx)

        # Coordinates for fly-to (centers of mentioned forests)
        forests = parsed.get('forests', [])
        if forests:
            coords = []
            for f in forests:
                if f in FOREST_CENTERS:
                    coords.append({'code': f, 'center': FOREST_CENTERS[f]})
            if coords:
                response_data['coordinates'] = coords

        # Log (non-blocking)
        try:
            RequeteNLP.objects.create(
                texte_requete=query,
                entites_extraites=parsed,
                filtre_orm=orm_desc,
                nombre_resultats=nb_results,
                temps_traitement_ms=processing_ms,
            )
        except Exception:
            pass

        return Response(response_data)
