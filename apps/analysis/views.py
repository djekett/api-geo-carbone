"""
AI Query View — Chat-to-Map v3.0

Nouveautes:
- Intent stock_carbone → active le mode CO2 sur la carte
- Intent resume → synthese globale (par type + par foret)
- Compare auto-default 1986 vs 2023 si annees manquantes
- Heritage de contexte etendu (cover_types aussi)
- Limite de features geojson communiquee au frontend
- Explication du parsing renvoyee dans la reponse
"""
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .nlp_engine import NLPEngine
from .models import RequeteNLP
from apps.carbone.serializers import OccupationSolSerializer


class AIQueryView(APIView):
    """
    Endpoint de requete en langage naturel (Chat-to-Map).

    POST /api/v1/ai/query/
    Body: {"query": "texte en francais"}

    Retourne un JSON avec:
    - type: help | geojson | stats | comparison | deforestation |
            ranking | resume | stock_carbone | no_results
    - parsed: entites extraites
    - data: donnees selon le type
    """

    GEOJSON_LIMIT = 200

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {'error': 'Le champ "query" est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Limit query length
        if len(query) > 500:
            query = query[:500]

        start = time.time()
        engine = NLPEngine()
        parsed = engine.parse(query)

        # ----------------------------------------------------------
        # Session-based conversational context
        # Inherit missing entities from the previous query
        # ----------------------------------------------------------
        session_context = request.session.get('nlp_context', {})

        if parsed['intent'] != 'help':
            # Inherit forests
            if not parsed['forests'] and session_context.get('forests'):
                parsed['forests'] = session_context['forests']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['forests']
            # Inherit years
            if not parsed['years'] and session_context.get('years'):
                parsed['years'] = session_context['years']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['years']
            # Inherit cover types (new in v3)
            if not parsed['cover_types'] and session_context.get('cover_types'):
                parsed['cover_types'] = session_context['cover_types']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['cover_types']

            # Save current context for next query
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

        # HELP intent
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

        # STOCK CARBONE intent → tells frontend to activate CO2 mode
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

        # RESUME intent → full overview
        if parsed['intent'] == 'resume':
            resume = engine.build_resume(parsed)
            nb_results = len(resume.get('par_type', []))
            response_data = {
                'type': 'resume',
                'parsed': parsed,
                'data': resume,
            }
            orm_desc = f"resume {resume.get('annee', '?')}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # COMPARE intent
        if parsed['intent'] == 'compare' and len(parsed['years']) >= 2:
            comparison = engine.build_comparison(parsed)
            response_data = {
                'type': 'comparison',
                'parsed': parsed,
                'data': comparison,
            }
            orm_desc = f"compare {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # DEFORESTATION intent
        if parsed['intent'] == 'deforestation' and len(parsed['years']) >= 2:
            deforestation = engine.build_deforestation(parsed)
            response_data = {
                'type': 'deforestation',
                'parsed': parsed,
                'data': deforestation,
            }
            orm_desc = f"deforestation {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # STATS / CARBON intent
        if parsed['intent'] in ('stats', 'carbon'):
            stats = list(engine.build_stats(parsed))
            nb_results = len(stats)
            if nb_results == 0:
                return self._no_results(request, query, parsed, engine, start)
            response_data = {
                'type': 'stats',
                'parsed': parsed,
                'data': stats,
            }
            orm_desc = f"stats {nb_results} types"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # RANKING intent
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

        # DEFAULT: SHOW intent → return GeoJSON features
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
        """Add timing, explanation, log the query, and return the response."""
        processing_ms = int((time.time() - start) * 1000)
        response_data['processing_ms'] = processing_ms

        # Include explanation if available
        explanation = parsed.get('_explanation', '')
        if explanation:
            response_data['explanation'] = explanation.strip()

        # Log the query (non-blocking)
        try:
            RequeteNLP.objects.create(
                texte_requete=query,
                entites_extraites=parsed,
                filtre_orm=orm_desc,
                nombre_resultats=nb_results,
                temps_traitement_ms=processing_ms,
            )
        except Exception:
            pass  # Ne pas bloquer la reponse si le log echoue

        return Response(response_data)
