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

    Version 3.0 :
    - Memoire de session (entites heritees de la requete precedente)
    - Intents enrichis : help, deforestation, ranking, prediction, export, area_calc
    - Suggestions intelligentes quand aucun resultat
    - Metadata enrichie : entites heritees, score de confiance
    - Messages d'erreur detailles
    """

    def post(self, request):
        query = request.data.get('query', '').strip()
        if not query:
            return Response(
                {
                    'error': 'Le champ "query" est requis.',
                    'hint': 'Envoyez une requete en francais, par exemple : '
                            '"Montre les zones de foret dense a TENE en 2023"',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if len(query) > 500:
            return Response(
                {
                    'error': 'La requete est trop longue (max 500 caracteres).',
                    'hint': 'Essayez une question plus courte et directe.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        start = time.time()
        engine = NLPEngine()
        parsed = engine.parse(query)

        # ----------------------------------------------------------
        # Session-based conversational context
        # Inherit missing entities from the previous query
        # ----------------------------------------------------------
        session_context = request.session.get('nlp_context', {})

        if parsed['intent'] != 'help':
            if not parsed['forests'] and session_context.get('forests'):
                parsed['forests'] = session_context['forests']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['forests']
            if not parsed['years'] and session_context.get('years'):
                parsed['years'] = session_context['years']
                parsed['_inherited'] = parsed.get('_inherited', []) + ['years']

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
                        "Je peux analyser les donnees forestieres du departement d'Oume."
                    ),
                    'examples': [
                        "Montre les zones de foret dense a DOKA en 2003",
                        "Quelle est la superficie de foret claire a SANGOUE ?",
                        "Compare TENE entre 1986 et 2023",
                        "Deforestation a LAHOUDA",
                        "Statistiques de carbone pour 2023",
                        "Classement des forets par superficie",
                        "Prevision de deforestation pour 2030",
                        "Exporter les donnees de TENE",
                        "Calculer la superficie de foret dense a DOKA",
                        "Pourcentage de cacao a SANGOUE en 2023",
                        "Compare TENE et DOKA en 2023",
                    ],
                    'capabilities': [
                        "Afficher des couches sur la carte",
                        "Calculer des statistiques de superficie et carbone",
                        "Comparer l'evolution entre deux annees",
                        "Analyser la deforestation",
                        "Classer les forets par taille ou carbone",
                        "Predire les tendances futures (2030, 2040, 2050)",
                        "Exporter un rapport de synthese",
                        "Calculer les superficies par type d'occupation",
                        "Analyser les pourcentages de couverture",
                        "Comparer plusieurs forets simultanement",
                    ],
                },
            }
            orm_desc = 'help'
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # PREDICTION intent
        if parsed['intent'] == 'prediction':
            prediction = engine.build_prediction(parsed)
            nb_results = len(prediction.get('predictions', []))
            if nb_results == 0:
                return self._no_results(
                    request, query, parsed, engine, start,
                    detail="Aucune donnee historique suffisante pour generer une prediction. "
                           "Il faut au moins deux annees de donnees."
                )
            response_data = {
                'type': 'prediction',
                'parsed': parsed,
                'data': prediction,
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"prediction -> {prediction['target_year']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # EXPORT intent
        if parsed['intent'] == 'export':
            # Build stats for export
            stats = list(engine.build_stats(parsed))
            nb_results = len(stats)

            # Build area calculation for enriched export
            area_data = None
            try:
                area_data = engine.build_area_calculation(parsed)
            except Exception:
                pass

            response_data = {
                'type': 'export',
                'parsed': parsed,
                'data': {
                    'stats': stats,
                    'area': area_data,
                    'forests': parsed['forests'],
                    'years': parsed['years'],
                    'cover_types': parsed['cover_types'],
                },
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"export {nb_results} types"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # AREA_CALC intent
        if parsed['intent'] == 'area_calc':
            area_data = engine.build_area_calculation(parsed)
            nb_results = len(area_data.get('detail', []))
            if nb_results == 0:
                return self._no_results(
                    request, query, parsed, engine, start,
                    detail="Aucune donnee de superficie trouvee pour les filtres specifies."
                )
            response_data = {
                'type': 'area_calc',
                'parsed': parsed,
                'data': area_data,
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"area_calc {nb_results} types"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # COMPARE intent
        if parsed['intent'] == 'compare' and len(parsed['years']) >= 2:
            comparison = engine.build_comparison(parsed)
            response_data = {
                'type': 'comparison',
                'parsed': parsed,
                'data': comparison,
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"compare {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        if parsed['intent'] == 'compare' and len(parsed['years']) < 2:
            return self._no_results(
                request, query, parsed, engine, start,
                detail="Pour comparer, precisez deux annees (ex: 'entre 1986 et 2023'). "
                       "Annees disponibles : 1986, 2003, 2023."
            )

        # DEFORESTATION intent
        if parsed['intent'] == 'deforestation' and len(parsed['years']) >= 2:
            deforestation = engine.build_deforestation(parsed)
            response_data = {
                'type': 'deforestation',
                'parsed': parsed,
                'data': deforestation,
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"deforestation {parsed['years']}"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        if parsed['intent'] == 'deforestation' and len(parsed['years']) < 2:
            return self._no_results(
                request, query, parsed, engine, start,
                detail="L'analyse de deforestation necessite deux annees. "
                       "Annees disponibles : 1986, 2003, 2023."
            )

        # STATS intent
        if parsed['intent'] in ('stats', 'carbon'):
            stats = list(engine.build_stats(parsed))
            nb_results = len(stats)
            if nb_results == 0:
                return self._no_results(
                    request, query, parsed, engine, start,
                    detail="Aucune statistique trouvee pour les filtres specifies. "
                           "Verifiez le nom de la foret et l'annee."
                )
            response_data = {
                'type': 'stats',
                'parsed': parsed,
                'data': stats,
                'metadata': self._build_metadata(parsed),
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
                'metadata': self._build_metadata(parsed),
            }
            orm_desc = f"ranking {nb_results} forets"
            return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

        # DEFAULT: SHOW intent -> return GeoJSON features
        qs = engine.build_queryset(parsed)
        count = qs.count()

        if count == 0:
            return self._no_results(
                request, query, parsed, engine, start,
                detail="Aucun polygone trouve. Essayez de preciser une foret "
                       "(TENE, DOKA, SANGOUE, LAHOUDA, ZOUEKE) et/ou une annee (1986, 2003, 2023)."
            )

        features = qs[:200]
        serializer = OccupationSolSerializer(features, many=True)
        response_data = {
            'type': 'geojson',
            'parsed': parsed,
            'count': count,
            'data': serializer.data,
            'metadata': self._build_metadata(parsed),
        }
        nb_results = count
        orm_desc = f"geojson {count} features"
        return self._finalize(request, query, parsed, response_data, nb_results, orm_desc, start)

    # ----------------------------------------------------------
    # Helpers
    # ----------------------------------------------------------
    def _build_metadata(self, parsed):
        """Build response metadata: inherited entities, confidence, etc."""
        return {
            'inherited_entities': parsed.get('_inherited', []),
            'confidence': parsed.get('confidence', 0.0),
            'percentage_mode': parsed.get('percentage_mode', False),
            'sort_order': parsed.get('sort_order'),
            'target_year': parsed.get('target_year'),
            'temporal': parsed.get('temporal'),
        }

    def _no_results(self, request, query, parsed, engine, start, detail=None):
        """Return a no-results response with smart suggestions and optional detail."""
        suggestions = engine.suggest_queries(parsed)
        response_data = {
            'type': 'no_results',
            'parsed': parsed,
            'suggestions': suggestions,
            'data': None,
            'metadata': self._build_metadata(parsed),
        }
        if detail:
            response_data['detail'] = detail
        return self._finalize(request, query, parsed, response_data, 0, 'no_results', start)

    def _finalize(self, request, query, parsed, response_data, nb_results, orm_desc, start):
        """Add timing, log the query, and return the response."""
        processing_ms = int((time.time() - start) * 1000)
        response_data['processing_ms'] = processing_ms

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
